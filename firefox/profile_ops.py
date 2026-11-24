#!/usr/bin/env python3
"""Profile discovery, journaled backup, marker-block installation, and
byte-for-byte restoration engine for Platinum for Firefox (Milestone 6).

Invoked by firefox/install.sh and firefox/uninstall.sh after they validate
XDG paths and acquire the state flock (on non-dry runs).

Safety guarantees (docs/FIREFOX-PLAN.md Milestone 6):
  - Discovers profiles from both $XDG_CONFIG_HOME/mozilla/firefox/profiles.ini
    and $HOME/.mozilla/firefox/profiles.ini, prioritizing [Install*] Default=
    over [Profile*] Default=1 (XDG preferred over legacy ~/.mozilla).
  - Never touches more than the single chosen profile.
  - Refuses while the target profile is in use (lock file, live or unknown lock symlink, or an active
    POSIX fcntl / BSD flock lock on .parentlock) or if any target path/parent
    is a symbolic link or was repointed since installation.
  - Journals and backs up (with SHA-256 verification) the entire pre-existing
    chrome/ folder, user.js, and prefs.js + exact per-pref snapshot BEFORE any
    profile file is modified.
  - Installs chrome/platinum/, prepends one marker-delimited @import block to
    chrome/userChrome.css and chrome/userContent.css (after @charset if present,
    preserving @namespace and all user rules below it), and appends one
    marker-delimited user_pref block to user.js.
  - On reinstall or upgrade, preserves the original pre-install backup and
    prefs_snapshot, updates chrome/platinum/ and marker blocks cleanly, and
    restores any retired managed pref.
  - On undo, restores untouched files byte for byte (exact bytes + file mode),
    preserves later user edits outside markers, restores each managed pref's
    original value or absence directly in prefs.js, and refuses with a clear
    conflict message (without overwriting) if markers or managed files were
    modified/conflicted.

SPDX-License-Identifier: BSD-2-Clause
"""

from __future__ import annotations

import argparse
import configparser
from contextlib import ExitStack
import datetime as dt
import fcntl
import hashlib
import json
import os
import pathlib
import re
import secrets
import shutil
import stat
import sys
from typing import Any

PROG_INSTALL = "firefox/install.sh"
PROG_UNINSTALL = "firefox/uninstall.sh"

MARKER_BEGIN = "/* >>> macos9-theme-firefox begin >>> */"
MARKER_END = "/* <<< macos9-theme-firefox end <<< */"

USERCHROME_BLOCK = (
    f"{MARKER_BEGIN}\n"
    '@import url("platinum/platinum.css");\n'
    f"{MARKER_END}\n"
)

USERCONTENT_BLOCK = (
    f"{MARKER_BEGIN}\n"
    '@import url("platinum/content.css");\n'
    f"{MARKER_END}\n"
)

# Managed prefs written into user.js (in deterministic order).
# Overrideable via M9_FF_MANAGED_PREFS_JSON in tests to verify upgrade path
# (adding/retiring a managed pref across theme versions).
DEFAULT_MANAGED_PREFS: list[tuple[str, str]] = [
    ("toolkit.legacyUserProfileCustomizations.stylesheets", "true"),
    ("browser.tabs.inTitlebar", "0"),
    ("browser.toolbars.bookmarks.visibility", '"always"'),
    ("browser.theme.dark-private-windows", "false"),
    ("widget.gtk.overlay-scrollbars.enabled", "false"),
    ("widget.non-native-theme.scrollbar.style", "4"),
    ("widget.non-native-theme.scrollbar.size.override", "16"),
    ("widget.gtk.theme-scrollbar-colors.enabled", "true"),
]


def get_managed_prefs() -> list[tuple[str, str]]:
    override = os.environ.get("M9_FF_MANAGED_PREFS_JSON", "").strip()
    if override:
        raw = json.loads(override)
        return [(str(k), str(v)) for k, v in raw]
    return list(DEFAULT_MANAGED_PREFS)


def build_userjs_block(prefs: list[tuple[str, str]]) -> str:
    lines = [MARKER_BEGIN]
    for k, raw_val in prefs:
        lines.append(f'user_pref("{k}", {raw_val});')
    lines.append(MARKER_END)
    return "\n".join(lines) + "\n"


def die(prog: str, msg: str, code: int = 1) -> int:
    print(f"{prog}: {msg}", file=sys.stderr)
    return code


def warn(prog: str, msg: str) -> None:
    print(f"{prog}: warning: {msg}", file=sys.stderr)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def real_parent_path(path: pathlib.Path) -> str:
    """Resolve symlinks in parent directories without following path itself."""
    parent_real = os.path.realpath(str(path.parent))
    return os.path.join(parent_real, path.name)


def profile_key(prof_dir: pathlib.Path) -> str:
    return hashlib.sha256(os.path.realpath(str(prof_dir)).encode("utf-8")).hexdigest()[:16]


def maybe_inject_fault(step: str) -> None:
    """Test-only crash hook (M9_FF_FAULT_AFTER=<step>) for interrupted-run tests."""
    target = os.environ.get("M9_FF_FAULT_AFTER", "").strip()
    if target and target == step:
        os._exit(99)


def fsync_dir(path: pathlib.Path) -> None:
    try:
        fd = os.open(str(path), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass


def atomic_write_bytes(target: pathlib.Path, data: bytes, mode: int = 0o644) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.parent / f".macos9-ff-tmp.{secrets.token_hex(6)}"
    fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        with os.fdopen(fd, "wb", closefd=False) as stream:
            stream.write(data)
        os.fsync(fd)
    except BaseException:
        os.close(fd)
        try:
            tmp.unlink()
        except OSError:
            pass
        raise
    os.close(fd)
    os.chmod(str(tmp), mode)
    os.replace(str(tmp), str(target))
    fsync_dir(target.parent)


def atomic_write_json(target: pathlib.Path, obj: Any) -> None:
    raw = (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode("utf-8")
    atomic_write_bytes(target, raw, 0o600)


# ---------------------------------------------------------------------------
# Version gate
# ---------------------------------------------------------------------------

def check_firefox_version(repo_ff_dir: pathlib.Path, prog: str) -> dict[str, Any]:
    ver_cfg = json.loads((repo_ff_dir / "version.json").read_text(encoding="utf-8"))
    min_maj = int(ver_cfg["tested_major_min"])
    max_maj = int(ver_cfg["tested_major_max"])
    env_ini = os.environ.get("M9_FIREFOX_APP_INI", "").strip()
    candidates = [pathlib.Path(env_ini)] if env_ini else [pathlib.Path(p) for p in ver_cfg.get("application_ini_paths", [])]

    ver_str: str | None = None
    major: int | None = None
    used_ini: str | None = None
    for p in candidates:
        if p.is_file():
            cp = configparser.RawConfigParser()
            cp.read(p, encoding="utf-8")
            if cp.has_option("App", "Version"):
                ver_str = cp.get("App", "Version").strip()
                m = re.match(r"^(\d+)", ver_str)
                major = int(m.group(1)) if m else None
                used_ini = str(p)
                break

    if ver_str is None or major is None:
        warn(prog, f"could not determine installed Firefox version (tested major: {min_maj}..{max_maj})")
        return {"version": None, "major": None, "tested": False, "ini": used_ini}

    tested = min_maj <= major <= max_maj
    if not tested:
        warn(
            prog,
            f"installed Firefox {ver_str} (major {major}) is outside tested major range "
            f"{min_maj}..{max_maj}; run tools/check-firefox-selectors.py to check selectors",
        )
    return {"version": ver_str, "major": major, "tested": tested, "ini": used_ini}


# ---------------------------------------------------------------------------
# Profile discovery & lock / symlink checks
# ---------------------------------------------------------------------------

def discover_profiles(home: pathlib.Path, config_home: pathlib.Path, state_dir: pathlib.Path) -> list[dict[str, Any]]:
    stores = [
        ("xdg", config_home / "mozilla" / "firefox"),
        ("legacy", home / ".mozilla" / "firefox"),
    ]
    raw_profiles: list[dict[str, Any]] = []
    seen_real: dict[str, dict[str, Any]] = {}

    for store_name, base_dir in stores:
        ini_path = base_dir / "profiles.ini"
        if not ini_path.is_file() or ini_path.is_symlink():
            continue
        cp = configparser.RawConfigParser()
        try:
            with ini_path.open(encoding="utf-8-sig") as source:
                cp.read_file(source)
        except (configparser.Error, UnicodeError, OSError) as error:
            print(f"Warning: skipping unreadable profile registry {ini_path}: {error}", file=sys.stderr)
            continue

        install_defaults: list[pathlib.Path] = []
        for sec in cp.sections():
            if sec.startswith("Install") and cp.has_option(sec, "Default"):
                dval = cp.get(sec, "Default").strip()
                if dval:
                    dp = pathlib.Path(dval) if dval.startswith("/") else (base_dir / dval)
                    install_defaults.append(dp)

        install_default_reals = {os.path.realpath(str(p)) for p in install_defaults if p.exists()}
        install_default_raws = {str(p) for p in install_defaults}

        for sec_idx, sec in enumerate(cp.sections()):
            if not sec.startswith("Profile"):
                continue
            if not cp.has_option(sec, "Path"):
                continue
            raw_p = cp.get(sec, "Path").strip()
            if not raw_p:
                continue
            is_rel = cp.get(sec, "IsRelative", fallback="1").strip() != "0"
            prof_path = (base_dir / raw_p) if (is_rel and not raw_p.startswith("/")) else pathlib.Path(raw_p)
            if not prof_path.is_absolute() or not prof_path.is_dir():
                continue

            real_str = os.path.realpath(str(prof_path))

            name = cp.get(sec, "Name", fallback=prof_path.name).strip() or prof_path.name
            leg_def = cp.get(sec, "Default", fallback="0").strip() == "1"
            inst_def = (real_str in install_default_reals) or (str(prof_path) in install_default_raws)

            if real_str in seen_real:
                prior = seen_real[real_str]
                prior["install_default"] |= inst_def
                prior["legacy_default"] |= leg_def
                continue

            pkey = profile_key(prof_path)
            pstate_dir = state_dir / "profiles" / pkey
            status = "not-installed"
            if (pstate_dir / "journal.json").is_file():
                try:
                    j = json.loads((pstate_dir / "journal.json").read_text(encoding="utf-8"))
                    status = j.get("phase", "unknown")
                except Exception:
                    status = "damaged"
            elif (pstate_dir / "state.json").is_file():
                status = "installed"

            raw_profiles.append(
                {
                    "name": name,
                    "store": store_name,
                    "path": str(prof_path),
                    "real_path": real_str,
                    "basename": prof_path.name,
                    "install_default": inst_def,
                    "legacy_default": leg_def,
                    "sec_idx": sec_idx,
                    "key": pkey,
                    "status": status,
                }
            )

            seen_real[real_str] = raw_profiles[-1]

    if not raw_profiles:
        return []

    # Determine the single default profile with [Install*] Default= > [Profile*] Default=1
    # and XDG > ~/.mozilla precedence.
    def default_rank(p: dict[str, Any]) -> tuple[int, int, int]:
        if p["install_default"] and p["store"] == "xdg":
            tier = 0
        elif p["install_default"]:
            tier = 1
        elif p["legacy_default"] and p["store"] == "xdg":
            tier = 2
        elif p["legacy_default"]:
            tier = 3
        elif p["store"] == "xdg":
            tier = 4
        else:
            tier = 5
        return (tier, 0 if p["store"] == "xdg" else 1, p["sec_idx"])

    best = min(raw_profiles, key=default_rank)
    for p in raw_profiles:
        p["is_default"] = p is best

    # Put the default profile first ([1]) so pressing Enter at [1] selects it cleanly.
    raw_profiles.sort(key=lambda p: (not p["is_default"], 0 if p["store"] == "xdg" else 1, p["sec_idx"]))
    for i, p in enumerate(raw_profiles, start=1):
        p["index"] = i
    return raw_profiles


def discover_installed_profiles(home: pathlib.Path, config_home: pathlib.Path, state_dir: pathlib.Path) -> list[dict[str, Any]]:
    discovered = {p["key"]: p for p in discover_profiles(home, config_home, state_dir)}
    out: list[dict[str, Any]] = []
    profs_root = state_dir / "profiles"
    if not profs_root.is_dir() or profs_root.is_symlink():
        return []

    for child in sorted(profs_root.iterdir()):
        if not child.is_dir() or child.is_symlink():
            continue
        jpath = child / "journal.json"
        spath = child / "state.json"
        meta: dict[str, Any] = {}
        if spath.is_file():
            meta = json.loads(spath.read_text(encoding="utf-8"))
        elif jpath.is_file():
            meta = json.loads(jpath.read_text(encoding="utf-8"))
        else:
            continue

        phase = "installed"
        if jpath.is_file():
            phase = json.loads(jpath.read_text(encoding="utf-8")).get("phase", phase)

        ppath = meta.get("profile_path")
        if not ppath:
            continue
        disc = discovered.get(child.name)
        out.append(
            {
                "key": child.name,
                "name": disc["name"] if disc else pathlib.Path(ppath).name,
                "store": disc["store"] if disc else "recorded",
                "path": ppath,
                "real_path": meta.get("profile_real", ""),
                "basename": pathlib.Path(ppath).name,
                "is_default": bool(disc and disc["is_default"]),
                "status": phase,
            }
        )

    out.sort(key=lambda p: (not p["is_default"], p["path"]))
    for i, p in enumerate(out, start=1):
        p["index"] = i
    return out


def format_profile_line(p: dict[str, Any]) -> str:
    tags: list[str] = [p["store"]]
    if p.get("is_default"):
        tags.append("default")
    if p.get("status") and p["status"] != "not-installed":
        tags.append(p["status"])
    return f"  [{p['index']}] {p['name']} ({', '.join(tags)}) — {p['path']}"


def select_profile(
    candidates: list[dict[str, Any]],
    spec: str | None,
    prog: str,
    action_verb: str,
) -> dict[str, Any] | None:
    if spec is not None:
        spec = spec.strip()
        if not spec:
            die(prog, "empty --profile value", 2)
            return None
        # 1. Exact index match
        if spec.isdigit():
            idx = int(spec)
            for p in candidates:
                if p["index"] == idx:
                    return p
            die(prog, f"profile index {idx} out of range (1..{len(candidates)})")
            return None
        # 2. Exact path or realpath match
        spec_exp = os.path.expanduser(spec).rstrip("/")
        spec_real = os.path.realpath(spec_exp) if os.path.exists(spec_exp) else None
        path_matches = [
            p
            for p in candidates
            if p["path"].rstrip("/") == spec_exp or (spec_real and p["real_path"] == spec_real)
        ]
        if len(path_matches) == 1:
            return path_matches[0]
        # 3. Exact directory basename or profile Name match
        name_matches = [p for p in candidates if p["basename"] == spec or p["name"] == spec]
        if len(name_matches) == 1:
            return name_matches[0]
        if len(name_matches) > 1:
            die(prog, f"--profile '{spec}' matches multiple profiles; pass the full path or index")
            return None
        die(prog, f"no discovered Firefox profile matches '{spec}'")
        return None

    # No --profile passed: list profiles and require interactive selection on TTY.
    print("Discovered Firefox profiles:")
    for p in candidates:
        print(format_profile_line(p))

    if not sys.stdin.isatty():
        die(
            prog,
            "multiple or discovered profiles require explicit selection; "
            "run interactively in a terminal or pass --profile <index|name|path>; nothing was changed",
        )
        return None

    sys.stdout.write(f"Select profile to {action_verb} [1]: ")
    sys.stdout.flush()
    ans = sys.stdin.readline()
    if ans == "":
        die(prog, "aborted (EOF); nothing was changed")
        return None
    choice = ans.strip()
    if choice.lower() in ("q", "quit", "n", "no"):
        die(prog, "cancelled; nothing was changed")
        return None
    if choice == "":
        choice = "1"
    if not choice.isdigit() or not (1 <= int(choice) <= len(candidates)):
        die(prog, f"invalid selection '{choice}'; nothing was changed")
        return None
    return candidates[int(choice) - 1]


def stale_loopback_lock(target: str) -> bool:
    """Recognize a Firefox loopback lock whose PID no longer exists."""
    match = re.fullmatch(r"127\.(\d{1,3})\.(\d{1,3})\.(\d{1,3}):\+([1-9]\d{0,9})", target, re.ASCII)
    if not match or any(int(octet) > 255 for octet in match.groups()[:3]):
        return False

    try:
        os.kill(int(match[4]), 0)
    except ProcessLookupError:
        return True
    except (OSError, OverflowError):
        pass
    return False


def hold_profile_lock(prof_dir: pathlib.Path, prog: str, handles: ExitStack) -> bool:
    """Hold the existing Firefox advisory locks until this command finishes."""
    lock_link = prof_dir / "lock"
    try:
        target = os.readlink(lock_link)
    except FileNotFoundError:
        target = None
    except OSError as error:
        die(prog, f"cannot verify {lock_link}: {error}; refusing to touch profile")
        return False

    if target is not None and not stale_loopback_lock(target):
        die(prog, f"profile is in use or has an unknown lock ({lock_link} -> {target}); nothing was changed")
        return False

    plock = prof_dir / ".parentlock"
    try:
        fd = os.open(plock, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK)
    except FileNotFoundError:
        if target is None:
            return True  # Fresh profile without Firefox lock artifacts.
        die(prog, f"cannot verify leftover {lock_link} without {plock}; nothing was changed")
        return False
    except OSError as error:
        die(prog, f"cannot open {plock}: {error}; nothing was changed")
        return False

    handles.callback(os.close, fd)
    if not stat.S_ISREG(os.fstat(fd).st_mode):
        die(prog, f"{plock} is not a regular lock file; nothing was changed")
        return False
    try:
        fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as error:
        die(prog, f"cannot lock {plock}: {error}; close Firefox and try again; nothing was changed")
        return False
    return True


def check_profile_symlinks(prof_dir: pathlib.Path, prog: str) -> bool:
    """Refuse if profile dir or any managed file/folder (or child of chrome/) is a symlink."""
    if prof_dir.is_symlink():
        die(prog, f"profile path {prof_dir} is a symbolic link; nothing was changed")
        return False
    if not prof_dir.is_dir():
        die(prog, f"profile folder {prof_dir} does not exist; nothing was changed")
        return False

    for rel in ("chrome", "chrome/userChrome.css", "chrome/userContent.css", "chrome/platinum", "user.js", "prefs.js"):
        p = prof_dir / rel
        if p.is_symlink():
            die(
                prog,
                f"{p} is a symbolic link; {prog} refuses to write through symlinks. "
                "Replace it with a regular file/folder and try again; nothing was changed",
            )
            return False

    for rel in ("chrome/userChrome.css", "chrome/userContent.css", "user.js", "prefs.js", "chrome/platinum"):
        path = prof_dir / rel
        if path.exists() and not path.is_file() and not (rel == "chrome/platinum" and path.is_dir()):
            die(prog, f"unexpected file type at {path}; nothing was changed")
            return False

    chrome_dir = prof_dir / "chrome"
    if chrome_dir.exists():
        if not chrome_dir.is_dir():
            die(prog, f"{chrome_dir} is not a folder; nothing was changed")
            return False
        for root, dirs, files in os.walk(str(chrome_dir), followlinks=False):
            rp = pathlib.Path(root)
            for name in dirs + files:
                cand = rp / name
                if cand.is_symlink() or not (cand.is_file() or cand.is_dir()):
                    die(
                        prog,
                        f"{cand} inside {chrome_dir} is a symbolic link or special file; "
                        "replace it with a regular file/folder first; nothing was changed",
                    )
                    return False
    return True


# ---------------------------------------------------------------------------
# Marker-block & prefs.js surgery helpers
# ---------------------------------------------------------------------------

def inspect_markers(text: str) -> tuple[str, str, str, str]:
    """Inspect marker block in text.

    Returns (state, before, inner_block_with_markers, after) where state is:
      - "absent": neither marker appears anywhere in text
      - "present": exactly one well-formed marker block
      - "corrupt": unbalanced, reversed, or duplicate markers
    """
    b_count = text.count(MARKER_BEGIN)
    e_count = text.count(MARKER_END)
    if b_count == 0 and e_count == 0:
        return ("absent", text, "", "")
    if b_count != 1 or e_count != 1:
        return ("corrupt", "", "", "")

    b_idx = text.find(MARKER_BEGIN)
    e_idx = text.find(MARKER_END)
    if e_idx < b_idx:
        return ("corrupt", "", "", "")

    # Include trailing newline immediately after MARKER_END if present.
    end_pos = e_idx + len(MARKER_END)
    if end_pos < len(text) and text[end_pos : end_pos + 2] == "\r\n":
        end_pos += 2
    elif end_pos < len(text) and text[end_pos] == "\n":
        end_pos += 1

    return ("present", text[:b_idx], text[b_idx:end_pos], text[end_pos:])


def insert_userchrome_block(existing_text: str, block: str) -> tuple[str, str]:
    """Insert block at top of userChrome.css (immediately after @charset if present),
    keeping @namespace and all existing user rules below it.
    Returns (new_full_text, inserted_chunk_for_removal).
    """
    if not existing_text:
        return (block, block)

    # Preserve optional UTF-8 BOM + @charset "..."; at byte 0 per CSS Syntax Level 3.
    m = re.match(r'^(\ufeff?@charset\s+"[^"]*"\s*;[ \t]*(?:\r?\n)?)', existing_text)
    prefix_len = m.end() if m else int(existing_text.startswith("\ufeff"))
    rest = existing_text[prefix_len:]
    sep = "\n" if rest and not rest.startswith(("\n", "\r\n")) else ""
    chunk = block + sep
    return (existing_text[:prefix_len] + chunk + rest, chunk)


def insert_userjs_block(existing_text: str, block: str) -> tuple[str, str]:
    """Append block to user.js, keeping existing user lines intact above it."""
    if not existing_text:
        return (block, block)
    lead = "" if existing_text.endswith("\n") else "\n"
    sep = "\n" if not existing_text.endswith("\n\n") else ""
    chunk_prefix = lead + sep
    return (existing_text + chunk_prefix + block, chunk_prefix + block)


USER_PREF_LINE_RE = re.compile(
    r'^[ \t]*user_pref\(\s*"((?:[^"\\]|\\.)*)"\s*,\s*(.*?)\s*\)\s*;[ \t]*$'
)


def parse_prefs_snapshot(prefs_path: pathlib.Path, pref_names: list[str]) -> dict[str, Any]:
    """Read current values (or absence) of each pref in pref_names from prefs.js."""
    wanted = set(pref_names)
    snap: dict[str, Any] = {}
    for k in pref_names:
        snap[k] = {"present": False, "raw_value": None, "raw_line": None}

    if not prefs_path.is_file():
        return snap

    text = prefs_path.read_bytes().decode("utf-8", errors="surrogateescape")
    for line in text.splitlines(keepends=True):
        stripped = line.rstrip("\r\n")
        m = USER_PREF_LINE_RE.match(stripped)
        if not m:
            continue
        key = m.group(1)
        if key in wanted:
            snap[key] = {
                "present": True,
                "raw_value": m.group(2),
                "raw_line": line if line.endswith("\n") else (line + "\n"),
            }
    return snap


def strip_prefs_from_lines(lines: list[str], keys: set[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        m = USER_PREF_LINE_RE.match(line.rstrip("\r\n"))
        if m and m.group(1) in keys:
            continue
        out.append(line)
    return out


def restore_prefs_in_text(current_text: str, backup_bytes: bytes | None, prefs_snapshot: dict[str, Any]) -> bytes:
    """Restore each managed pref's original value or absence in prefs.js.

    Fast byte-exact path: if all non-managed lines in current_text match
    backup_bytes, return backup_bytes verbatim so untouched profiles recover
    the exact byte-for-byte original prefs.js (line order, whitespace, comments).
    Otherwise surgically update/remove only the managed pref lines while
    keeping every later Firefox session/user pref change intact.
    """
    managed_keys = set(prefs_snapshot.keys())
    cur_lines = current_text.splitlines(keepends=True)

    if backup_bytes is not None:
        bak_text = backup_bytes.decode("utf-8", errors="surrogateescape")
        bak_lines = bak_text.splitlines(keepends=True)
        if strip_prefs_from_lines(cur_lines, managed_keys) == strip_prefs_from_lines(bak_lines, managed_keys):
            return backup_bytes

    out_lines: list[str] = []
    restored_keys: set[str] = set()

    for line in cur_lines:
        m = USER_PREF_LINE_RE.match(line.rstrip("\r\n"))
        if m and m.group(1) in managed_keys:
            key = m.group(1)
            info = prefs_snapshot[key]
            if info.get("present") and key not in restored_keys:
                raw_line = info.get("raw_line") or f'user_pref("{key}", {info["raw_value"]});\n'
                out_lines.append(raw_line)
                restored_keys.add(key)
            # If originally absent (or duplicate occurrence), drop the line.
            continue
        out_lines.append(line)

    # Any originally-present pref whose line Firefox dropped in the meantime: re-add cleanly.
    for key, info in prefs_snapshot.items():
        if info.get("present") and key not in restored_keys:
            if out_lines and not out_lines[-1].endswith("\n"):
                out_lines[-1] += "\n"
            raw_line = info.get("raw_line") or f'user_pref("{key}", {info["raw_value"]});\n'
            out_lines.append(raw_line)
            restored_keys.add(key)

    return "".join(out_lines).encode("utf-8", errors="surrogateescape")


# ---------------------------------------------------------------------------
# Backup & tree checksum helpers
# ---------------------------------------------------------------------------

def tree_sums(root: pathlib.Path) -> dict[str, str]:
    sums: dict[str, str] = {}
    if not root.is_dir():
        return sums
    for dirpath, dirnames, filenames in os.walk(str(root), followlinks=False):
        dirnames.sort()
        filenames.sort()
        dp = pathlib.Path(dirpath)
        for fn in filenames:
            fp = dp / fn
            if fp.is_symlink() or not fp.is_file():
                raise RuntimeError(f"unexpected non-regular file in {fp}")
            rel = str(fp.relative_to(root))
            sums[rel] = sha256_file(fp)
    return sums


def matches_installed_theme(path: pathlib.Path, manifests: list[dict[str, str]]) -> bool:
    if not path.is_dir():
        return False
    sums = tree_sums(path)
    if sums not in manifests:
        return False
    expected_dirs = {parent for name in sums for parent in (path / name).parents}
    return all(entry in expected_dirs for entry in path.rglob("*") if entry.is_dir())


def remove_stage(chrome: pathlib.Path, journal: dict) -> None:
    name = journal.get("stage")
    if name and re.fullmatch(r"\.macos9-ff-tmp\.[0-9a-f]{24}", name):
        stage = chrome / name
        if stage.is_dir() and not stage.is_symlink():
            shutil.rmtree(stage)


def original_platinum_matches(path: pathlib.Path, backup: pathlib.Path) -> bool:
    if path.is_file() and backup.is_file():
        return sha256_file(path) == sha256_file(backup)
    if path.is_dir() and backup.is_dir():
        return tree_sums(path) == tree_sums(backup) and {
            p.relative_to(path) for p in path.rglob("*") if p.is_dir()
        } == {p.relative_to(backup) for p in backup.rglob("*") if p.is_dir()}
    return False


def backup_modes(backup: pathlib.Path) -> dict[str, int]:
    """Include empty directories, entry types and permissions in the manifest."""
    result = {}
    for entry in backup.rglob("*"):
        rel = str(entry.relative_to(backup))
        if rel == "BACKUP_META.json":
            continue
        mode = entry.lstat().st_mode
        if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            raise ValueError(f"unexpected entry in backup: {entry}")
        result[rel] = mode
    return result


def take_initial_backup(prof_dir: pathlib.Path, pstate_dir: pathlib.Path, managed_prefs: list[tuple[str, str]]) -> dict[str, Any]:
    """Create checksummed initial backup of chrome/, user.js, and prefs.js BEFORE any change."""
    bak_tmp = pstate_dir / f".backup-tmp.{secrets.token_hex(6)}"
    bak_final = pstate_dir / "backup"
    if bak_tmp.exists():
        shutil.rmtree(bak_tmp)
    bak_tmp.mkdir(parents=True, mode=0o700)

    chrome_dir = prof_dir / "chrome"
    uc_file = chrome_dir / "userChrome.css"
    ucnt_file = chrome_dir / "userContent.css"
    plat_dir = chrome_dir / "platinum"
    ujs_file = prof_dir / "user.js"
    pjs_file = prof_dir / "prefs.js"

    meta: dict[str, Any] = {
        "chrome_existed": chrome_dir.exists(),
        "chrome_mode": (stat.S_IMODE(chrome_dir.stat().st_mode) if chrome_dir.exists() else 0o755),
        "userChrome_existed": uc_file.is_file(),
        "userChrome_mode": (stat.S_IMODE(uc_file.stat().st_mode) if uc_file.is_file() else 0o644),
        "userContent_existed": ucnt_file.is_file(),
        "userContent_mode": (stat.S_IMODE(ucnt_file.stat().st_mode) if ucnt_file.is_file() else 0o644),
        "foreign_platinum_existed": plat_dir.exists(),
        "foreign_platinum_is_dir": plat_dir.is_dir() if plat_dir.exists() else False,
        "user_js_existed": ujs_file.is_file(),
        "user_js_mode": (stat.S_IMODE(ujs_file.stat().st_mode) if ujs_file.is_file() else 0o644),
        "prefs_js_existed": pjs_file.is_file(),
        "prefs_js_mode": (stat.S_IMODE(pjs_file.stat().st_mode) if pjs_file.is_file() else 0o600),
        "prefs_js_sha256": sha256_file(pjs_file) if pjs_file.is_file() else None,
        "prefs_snapshot": parse_prefs_snapshot(pjs_file, [k for k, _ in managed_prefs]),
    }

    if chrome_dir.exists():
        shutil.copytree(chrome_dir, bak_tmp / "chrome", symlinks=False, copy_function=shutil.copy2)
    if ujs_file.is_file():
        shutil.copy2(ujs_file, bak_tmp / "user.js")
    if pjs_file.is_file():
        shutil.copy2(pjs_file, bak_tmp / "prefs.js")

    sums = tree_sums(bak_tmp)
    atomic_write_json(bak_tmp / "BACKUP_META.json", {"meta": meta, "sums": sums, "modes": backup_modes(bak_tmp)})

    if bak_final.exists():
        shutil.rmtree(bak_final)
    os.replace(str(bak_tmp), str(bak_final))
    fsync_dir(pstate_dir)
    return meta


def verify_backup(bak: pathlib.Path) -> tuple[bool, dict[str, Any], str]:
    meta_file = bak / "BACKUP_META.json"
    if not bak.is_dir() or bak.is_symlink() or not meta_file.is_file() or meta_file.is_symlink():
        return (False, {}, f"backup folder {bak} is missing or incomplete")

    try:
        payload = json.loads(meta_file.read_text(encoding="utf-8"))
        modes = backup_modes(bak)
        if "modes" in payload and modes != payload["modes"]:
            return (False, {}, f"backup entries or permissions changed in {bak}")
        recorded_sums = payload["sums"]
        meta = payload["meta"]
        original = bak / "chrome/platinum"
        if meta["foreign_platinum_existed"] != original.exists() or meta["foreign_platinum_is_dir"] != original.is_dir():
            return (False, {}, f"original platinum backup missing or replaced in {bak}")
        actual_sums = tree_sums(bak)
        actual_sums.pop("BACKUP_META.json", None)
    except (KeyError, TypeError, ValueError, OSError, RuntimeError) as error:
        return (False, {}, f"cannot verify backup {bak}: {error}")
    if actual_sums != recorded_sums:
        return (False, {}, f"backup checksum verification failed in {bak}")
    return (True, payload["meta"], "")


def backup_usercontent_info(bak_dir: pathlib.Path, bak_meta: dict[str, Any]) -> tuple[bool, int]:
    """Return (existed, mode) for chrome/userContent.css, compatible with older backups."""
    bak_ucnt = bak_dir / "chrome" / "userContent.css"
    existed = bool(bak_meta["userContent_existed"]) if "userContent_existed" in bak_meta else bak_ucnt.is_file()
    if "userContent_mode" in bak_meta:
        mode = int(bak_meta["userContent_mode"])
    elif bak_ucnt.is_file():
        mode = stat.S_IMODE(bak_ucnt.stat().st_mode)
    else:
        mode = 0o644
    return (existed, mode)


# ---------------------------------------------------------------------------
# Install / Reinstall / Upgrade
# ---------------------------------------------------------------------------

def content_backup(state_dir: pathlib.Path, backup_dir: pathlib.Path, meta: dict,
                   adoption: dict | None) -> tuple[pathlib.Path, bool, int]:
    """Use the file as it existed when this installer first managed it."""
    if adoption is None:
        existed, mode = backup_usercontent_info(backup_dir, meta)
        return backup_dir / "chrome/userContent.css", existed, mode
    path = state_dir / "adopted-userContent.css"
    return path, adoption["sha256"] is not None, adoption["mode"]


def valid_adoption(path: pathlib.Path, adoption: dict | None) -> bool:
    if adoption is None or adoption["sha256"] is None:
        return True
    return path.is_file() and not path.is_symlink() and sha256_file(path) == adoption["sha256"]


def cmd_install(args: argparse.Namespace, handles: ExitStack) -> int:
    prog = PROG_INSTALL
    home = pathlib.Path(args.home)
    config_home = pathlib.Path(args.config_home)
    state_dir = pathlib.Path(args.state_dir)
    repo_ff_dir = pathlib.Path(args.repo_firefox_dir)
    dry_run = bool(args.dry_run)

    src_platinum = repo_ff_dir / "chrome" / "platinum"
    if (
        not src_platinum.is_dir()
        or not (src_platinum / "platinum.css").is_file()
        or not (src_platinum / "content.css").is_file()
    ):
        return die(prog, f"missing theme stylesheets in {src_platinum}; nothing was changed")

    ver_info = check_firefox_version(repo_ff_dir, prog)
    if ver_info["version"] and ver_info["tested"]:
        print(f"Detected Firefox {ver_info['version']} (tested major range).")

    profiles = discover_profiles(home, config_home, state_dir)
    if args.list:
        if not profiles:
            print("No Firefox profiles found in ~/.config/mozilla/firefox or ~/.mozilla/firefox.")
            return 0
        print("Discovered Firefox profiles:")
        for p in profiles:
            print(format_profile_line(p))
        return 0

    if not profiles:
        return die(
            prog,
            f"no Firefox profiles found in {config_home / 'mozilla/firefox/profiles.ini'} "
            f"or {home / '.mozilla/firefox/profiles.ini'}; launch Firefox once first",
        )

    chosen = select_profile(profiles, args.profile, prog, "install Platinum into")
    if chosen is None:
        return 1

    prof_dir = pathlib.Path(chosen["path"])
    if not check_profile_symlinks(prof_dir, prog):
        return 1
    if not hold_profile_lock(prof_dir, prog, handles):
        return 1

    pkey = chosen["key"]
    pstate_dir = state_dir / "profiles" / pkey
    jpath = pstate_dir / "journal.json"
    spath = pstate_dir / "state.json"

    if pstate_dir.is_dir() and any(pstate_dir.iterdir()) and not (jpath.is_file() or spath.is_file()):
        return die(prog, f"unrecognized profile state in {pstate_dir}; refusing to replace it")

    existing_journal: dict[str, Any] | None = None
    if jpath.is_file():
        existing_journal = json.loads(jpath.read_text(encoding="utf-8"))
        if existing_journal.get("phase") == "uninstalling":
            return die(
                prog,
                f"an earlier uninstall in {prof_dir} did not finish. "
                "Run firefox/uninstall.sh first to complete it; nothing was changed",
            )

    existing_state: dict[str, Any] | None = None
    if spath.is_file():
        existing_state = json.loads(spath.read_text(encoding="utf-8"))

    # Verify profile path wasn't symlink-redirected since an earlier install.
    cur_real = os.path.realpath(str(prof_dir))
    cur_parent_real = real_parent_path(prof_dir)
    for rec in (existing_state, existing_journal):
        if rec:
            if rec.get("profile_real") and rec["profile_real"] != cur_real:
                return die(
                    prog,
                    f"{prof_dir} now resolves to {cur_real} (was {rec['profile_real']}); "
                    "point the directory link back first; nothing was changed",
                )
            if rec.get("profile_parent_real") and rec["profile_parent_real"] != cur_parent_real:
                return die(
                    prog,
                    f"parent path of {prof_dir} moved ({cur_parent_real} vs {rec['profile_parent_real']}); "
                    "nothing was changed",
                )

    managed_prefs = get_managed_prefs()
    new_ujs_block = build_userjs_block(managed_prefs)

    # Determine whether we already hold a valid pre-install backup (reinstall,
    # upgrade, or resuming an interrupted install after backup completed).
    has_prior_backup = False
    bak_meta: dict[str, Any] = {}
    if existing_state is not None or (existing_journal and existing_journal.get("backup_complete")):
        ok, bak_meta, err = verify_backup(pstate_dir / "backup")
        if not ok:
            return die(prog, f"existing state backup is damaged ({err}); nothing was changed")
        has_prior_backup = True
    elif existing_journal and not existing_journal.get("backup_complete"):
        # Earlier install aborted before backup completed (zero profile mutations happened).
        if not dry_run and pstate_dir.exists():
            shutil.rmtree(pstate_dir)
        existing_journal = None

    # Pre-check existing chrome/platinum, userChrome.css, userContent.css, and user.js for conflicts BEFORE writing!
    chrome_dir = prof_dir / "chrome"
    plat_dir = chrome_dir / "platinum"
    uc_file = chrome_dir / "userChrome.css"
    ucnt_file = chrome_dir / "userContent.css"
    ujs_file = prof_dir / "user.js"
    pjs_file = prof_dir / "prefs.js"

    recovering = (existing_journal or {}).get("phase") == "installing" and has_prior_backup
    pending = (existing_journal or {}).get("pending", {}) if recovering else {}
    records = [pending, existing_state or {}]
    if existing_state or recovering:
        original = pstate_dir / "backup/chrome/platinum"
        known = [r["platinum_sums"] for r in records if "platinum_sums" in r]
        if recovering and not pending:
            known.append(tree_sums(src_platinum))  # Legacy journal
        if plat_dir.exists() and not matches_installed_theme(plat_dir, known):
            if not (recovering and not existing_state and original_platinum_matches(plat_dir, original)):
                return die(prog, f"conflict in {plat_dir}; nothing was changed")

    # Inspect userChrome.css markers
    uc_existing_text = uc_file.read_bytes().decode("utf-8", errors="surrogateescape") if uc_file.is_file() else ""
    uc_mstate, uc_before, uc_inner, uc_after = inspect_markers(uc_existing_text)
    if uc_mstate == "absent" and existing_state and uc_file.exists():
        return die(prog, f"conflict in {uc_file}: installed markers are missing; nothing was changed")
    if uc_mstate == "corrupt":
        return die(prog, f"corrupted {MARKER_BEGIN} markers in {uc_file}; fix them first; nothing was changed")
    uc_record = None
    if uc_mstate == "present":
        if not has_prior_backup:
            return die(prog, f"{uc_file} already contains macos9-theme-firefox markers without an install record; nothing was changed")
        uc_record = next((r for r in records if r.get("installed_userchrome_block") == uc_inner), None)
        if uc_record is None and (any(records) or uc_inner != USERCHROME_BLOCK):
            return die(prog, f"conflict in {uc_file}: lines inside macos9-theme-firefox markers were edited; nothing was changed")

    # Inspect userContent.css markers (older installs before userContent.css support
    # lack installed_usercontent_block in existing_state, so an absent marker block
    # is expected when upgrading from those versions).
    ucnt_existing_raw = ucnt_file.read_bytes() if ucnt_file.is_file() else b""
    ucnt_existing_text = ucnt_existing_raw.decode("utf-8", errors="surrogateescape")
    ucnt_mstate, ucnt_before, ucnt_inner, ucnt_after = inspect_markers(ucnt_existing_text)
    ucnt_managed_before = bool(existing_state and "installed_usercontent_block" in existing_state)
    if ucnt_mstate == "absent" and "installed_usercontent_block" in pending:
        observed = sha256_bytes(ucnt_existing_raw) if ucnt_file.is_file() else None
        if observed != pending.get("pre_usercontent_sha256"):
            return die(prog, f"conflict in {ucnt_file}: stylesheet changed during interrupted install")
    if ucnt_mstate == "absent" and ucnt_managed_before and ucnt_file.exists():
        return die(prog, f"conflict in {ucnt_file}: installed markers are missing; nothing was changed")
    if ucnt_mstate == "corrupt":
        return die(prog, f"corrupted {MARKER_BEGIN} markers in {ucnt_file}; fix them first; nothing was changed")
    ucnt_record = None
    if ucnt_mstate == "present":
        if not has_prior_backup:
            return die(prog, f"{ucnt_file} already contains macos9-theme-firefox markers without an install record; nothing was changed")
        ucnt_record = next((r for r in records if r.get("installed_usercontent_block") == ucnt_inner), None)
        if ucnt_record is None and (any(records) or ucnt_inner != USERCONTENT_BLOCK):
            return die(prog, f"conflict in {ucnt_file}: lines inside macos9-theme-firefox markers were edited; nothing was changed")

    # Inspect user.js markers
    ujs_existing_text = ujs_file.read_bytes().decode("utf-8", errors="surrogateescape") if ujs_file.is_file() else ""
    ujs_mstate, ujs_before, ujs_inner, ujs_after = inspect_markers(ujs_existing_text)
    if ujs_mstate == "absent" and existing_state and ujs_file.exists():
        return die(prog, f"conflict in {ujs_file}: installed markers are missing; nothing was changed")
    if ujs_mstate == "corrupt":
        return die(prog, f"corrupted {MARKER_BEGIN} markers in {ujs_file}; fix them first; nothing was changed")
    ujs_record = None
    if ujs_mstate == "present":
        if not has_prior_backup:
            return die(prog, f"{ujs_file} already contains macos9-theme-firefox markers without an install record; nothing was changed")
        ujs_record = next((r for r in records if r.get("installed_userjs_block") == ujs_inner), None)
        if ujs_record is None and (any(records) or ujs_inner != new_ujs_block):
            return die(prog, f"conflict in {ujs_file}: lines inside macos9-theme-firefox markers were edited; nothing was changed")

    adoption = pending.get("content_adoption", (existing_state or {}).get("content_adoption"))
    first_adoption = existing_state is not None and not ucnt_managed_before and not pending
    if first_adoption:
        adoption = {"sha256": sha256_bytes(ucnt_existing_raw) if ucnt_file.is_file() else None,
                    "mode": stat.S_IMODE(ucnt_file.stat().st_mode) if ucnt_file.is_file() else 0o644}
    content_path, _, ucnt_mode = content_backup(pstate_dir, pstate_dir / "backup", bak_meta, adoption)
    if not first_adoption and not valid_adoption(content_path, adoption):
        return die(prog, "damaged userContent.css upgrade backup")

    if dry_run:
        print("Dry run: nothing is changed.")
        print(f"  target profile: {chosen['name']} ({prof_dir})")
        if not has_prior_backup:
            print(f"  would back up existing chrome/, user.js, and prefs.js snapshot to {pstate_dir / 'backup'}")
            if plat_dir.exists():
                print(f"  would preserve {plat_dir} in the backup")
        else:
            print(f"  would preserve original pre-install backup in {pstate_dir / 'backup'}")
        print(f"  would install {src_platinum} -> {plat_dir}/")
        print(f"  would write marker-delimited @import block in {uc_file}")
        print(f"  would write marker-delimited @import block in {ucnt_file}")
        print(f"  would write marker-delimited user_pref block in {ujs_file}")
        return 0

    if recovering:
        remove_stage(chrome_dir, existing_journal)
    pstate_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Journal & take initial backup if first install; on upgrade, extend
    # prefs_snapshot for any newly introduced managed prefs while keeping original
    # snapshots for already-managed prefs!
    if not has_prior_backup:
        atomic_write_json(
            jpath,
            {
                "phase": "installing",
                "backup_complete": False,
                "profile_path": str(prof_dir),
                "profile_real": cur_real,
                "profile_parent_real": cur_parent_real,
            },
        )
        bak_meta = take_initial_backup(prof_dir, pstate_dir, managed_prefs)
        prefs_snapshot = dict(bak_meta["prefs_snapshot"])
    else:
        prefs_snapshot = dict(pending.get("prefs_snapshot", (existing_state or {}).get("prefs_snapshot", bak_meta["prefs_snapshot"])))
        new_keys = [k for k, _ in managed_prefs if k not in prefs_snapshot]
        if new_keys:
            extra = parse_prefs_snapshot(pjs_file, new_keys)
            prefs_snapshot.update(extra)

    if first_adoption and adoption["sha256"] is not None:
        atomic_write_bytes(content_path, ucnt_existing_raw, 0o600)

    # Record the planned marker blocks before publishing any file.
    if uc_mstate == "present":
        # Replace existing marker block in place, keeping surrounding bytes intact.
        new_uc_text = uc_before + USERCHROME_BLOCK + uc_after
        inserted_uc_chunk = (uc_record or {}).get("installed_userchrome_chunk", USERCHROME_BLOCK)
    else:
        new_uc_text, inserted_uc_chunk = insert_userchrome_block(uc_existing_text, USERCHROME_BLOCK)

    uc_bytes = new_uc_text.encode("utf-8", errors="surrogateescape")

    if ucnt_mstate == "present":
        new_ucnt_text = ucnt_before + USERCONTENT_BLOCK + ucnt_after
        inserted_ucnt_chunk = (ucnt_record or {}).get("installed_usercontent_chunk", USERCONTENT_BLOCK)
    else:
        new_ucnt_text, inserted_ucnt_chunk = insert_userchrome_block(ucnt_existing_text, USERCONTENT_BLOCK)

    ucnt_bytes = new_ucnt_text.encode("utf-8", errors="surrogateescape")

    if ujs_mstate == "present":
        new_ujs_text = ujs_before + new_ujs_block + ujs_after
        inserted_ujs_chunk = (ujs_record or {}).get("installed_userjs_chunk", ujs_inner).replace(ujs_inner, new_ujs_block)
    else:
        new_ujs_text, inserted_ujs_chunk = insert_userjs_block(ujs_existing_text, new_ujs_block)

    ujs_bytes = new_ujs_text.encode("utf-8", errors="surrogateescape")
    pending = {
        "installed_userchrome_block": USERCHROME_BLOCK,
        "installed_userchrome_chunk": inserted_uc_chunk,
        "installed_usercontent_block": USERCONTENT_BLOCK,
        "installed_usercontent_chunk": inserted_ucnt_chunk,
        "installed_userjs_block": new_ujs_block,
        "installed_userjs_chunk": inserted_ujs_chunk,
        "platinum_sums": tree_sums(src_platinum),
        "prefs_snapshot": prefs_snapshot,
    }
    if adoption is not None:
        pending["content_adoption"] = adoption
    if ucnt_mstate == "absent" and ucnt_file.is_file() and not ucnt_managed_before:
        pending["pre_usercontent_sha256"] = sha256_bytes(ucnt_existing_raw)
    stage = chrome_dir / f".macos9-ff-tmp.{secrets.token_hex(12)}"
    for key, backup, insert, block, old_text, new_bytes in (
        ("userchrome", pstate_dir / "backup/chrome/userChrome.css", insert_userchrome_block,
         USERCHROME_BLOCK, uc_existing_text, uc_bytes),
        ("usercontent", content_path, insert_userchrome_block,
         USERCONTENT_BLOCK, ucnt_existing_text, ucnt_bytes),
        ("userjs", pstate_dir / "backup/user.js", insert_userjs_block,
         new_ujs_block, ujs_existing_text, ujs_bytes),
    ):
        original = backup.read_bytes().decode("utf-8", "surrogateescape") if backup.is_file() else ""
        expected, _ = insert(original, block)
        hash_key = f"untouched_{key}_sha256"
        old_hash = sha256_bytes(old_text.encode("utf-8", "surrogateescape"))
        # Older installs normalized line endings. Their recorded hash still
        # identifies the unedited file and its byte-exact original backup.
        untouched = any(r.get(hash_key) == old_hash for r in records)
        if untouched or expected.encode("utf-8", "surrogateescape") == new_bytes:
            pending[hash_key] = sha256_bytes(new_bytes)
    atomic_write_json(jpath, {
        "phase": "installing", "backup_complete": True, "pending": pending, "stage": stage.name,
        "profile_path": str(prof_dir), "profile_real": cur_real,
        "profile_parent_real": cur_parent_real,
    })
    maybe_inject_fault("backup")

    # Stage both directory renames on the profile filesystem.
    chrome_dir.mkdir(parents=True, exist_ok=True)
    stage.mkdir(mode=0o700)
    stage_plat = stage / "new"
    shutil.copytree(src_platinum, stage_plat, symlinks=False, copy_function=shutil.copy2)
    for root, dirs, files in os.walk(str(stage_plat)):
        os.chmod(root, 0o755)
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o755)
        for fn in files:
            os.chmod(os.path.join(root, fn), 0o644)

    if plat_dir.exists():
        os.replace(plat_dir, stage / "old")
        maybe_inject_fault("platinum_swap")
    os.replace(stage_plat, plat_dir)
    shutil.rmtree(stage)
    fsync_dir(chrome_dir)
    maybe_inject_fault("platinum")

    uc_mode = bak_meta.get("userChrome_mode", 0o644)
    atomic_write_bytes(uc_file, uc_bytes, uc_mode)
    maybe_inject_fault("userChrome")

    if ucnt_file.is_file():
        ucnt_mode = stat.S_IMODE(ucnt_file.stat().st_mode)
    atomic_write_bytes(ucnt_file, ucnt_bytes, ucnt_mode)
    maybe_inject_fault("userContent")

    ujs_mode = bak_meta.get("user_js_mode", 0o644)
    atomic_write_bytes(ujs_file, ujs_bytes, ujs_mode)
    maybe_inject_fault("user_js")

    # Step 2d: On upgrade, if an earlier version set a managed pref that is NO LONGER
    # in managed_prefs, restore its original value/absence in prefs.js immediately!
    active_pref_keys = {k for k, _ in managed_prefs}
    retired_keys = {k: v for k, v in prefs_snapshot.items() if k not in active_pref_keys}
    if retired_keys and pjs_file.is_file():
        cur_pjs_text = pjs_file.read_bytes().decode("utf-8", errors="surrogateescape")
        new_pjs_bytes = restore_prefs_in_text(cur_pjs_text, None, retired_keys)
        pjs_mode = stat.S_IMODE(pjs_file.stat().st_mode)
        atomic_write_bytes(pjs_file, new_pjs_bytes, pjs_mode)
        for rk in retired_keys:
            prefs_snapshot.pop(rk, None)

    state_obj = {
        "schema": 1,
        "installed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "firefox_version_at_install": ver_info.get("version"),
        "profile_name": chosen["name"],
        "profile_path": str(prof_dir),
        "profile_real": cur_real,
        "profile_parent_real": cur_parent_real,
        **pending,
        "managed_prefs": managed_prefs,
    }
    atomic_write_json(spath, state_obj)
    atomic_write_json(
        jpath,
        {
            "phase": "installed",
            "backup_complete": True,
            "profile_path": str(prof_dir),
            "profile_real": cur_real,
            "profile_parent_real": cur_parent_real,
        },
    )

    action_word = "Updated" if has_prior_backup else "Installed"
    print(f"{action_word} Platinum for Firefox in profile '{chosen['name']}' ({prof_dir}).")
    print("Restart Firefox to load chrome/userChrome.css and chrome/userContent.css.")
    return 0


# ---------------------------------------------------------------------------
# Uninstall / Byte-for-byte Undo & Conflict Detection
# ---------------------------------------------------------------------------

def plan_marker_removal(
    file_path: pathlib.Path,
    existed_before: bool,
    backup_file: pathlib.Path,
    key: str,
    state: dict,
    pending: dict,
    interrupted: bool,
) -> tuple[str, bytes | None, str]:
    """Validate and plan undo for a marker-delimited file (userChrome.css or user.js).

    Returns (action, new_bytes, err_msg) where action is:
      - "restore_backup": copy backup_file verbatim (byte-for-byte untouched fast path)
      - "delete": unlink file_path (did not exist before, untouched since install)
      - "write": write new_bytes (user added/edited rules outside markers)
      - "noop": file already absent when !existed_before
      - "conflict": markers broken/modified or unexpected file replacement
    """
    if not file_path.exists() and not file_path.is_symlink():
        if not existed_before:
            return ("noop", None, "")
        return ("restore_backup", None, "")

    if file_path.is_symlink() or not file_path.is_file():
        return ("conflict", None, f"{file_path} was replaced by a symlink or folder")

    raw_bytes = file_path.read_bytes()
    text = raw_bytes.decode("utf-8", errors="surrogateescape")
    mstate, before, inner, after = inspect_markers(text)
    if mstate == "corrupt":
        return ("conflict", None, f"{file_path} has corrupted or duplicate macos9-theme-firefox markers")
    if mstate == "absent":
        if interrupted and not state.get(f"installed_{key}_block"):
            if pending.get(f"pre_{key}_sha256") == sha256_bytes(raw_bytes):
                return ("noop", None, "")
            if not state and backup_file.is_file() and raw_bytes == backup_file.read_bytes():
                return ("noop", None, "")
        return (
            "conflict",
            None,
            f"{file_path} was modified and no longer contains macos9-theme-firefox markers; refusing to overwrite",
        )

    recorded = next((r for r in (state, pending) if r.get(f"installed_{key}_block") == inner), None)
    if recorded is None and interrupted and not (state or pending):
        # Recover profiles written by the older installer before it published state.json.
        if key == "userchrome":
            block = USERCHROME_BLOCK
            insert = insert_userchrome_block
        elif key == "usercontent":
            block = USERCONTENT_BLOCK
            insert = insert_userchrome_block
        else:
            block = build_userjs_block(get_managed_prefs())
            insert = insert_userjs_block
        if inner == block:
            original = backup_file.read_bytes().decode("utf-8", "surrogateescape") if existed_before else ""
            _, chunk = insert(original, block)
            recorded = {f"installed_{key}_chunk": chunk}
    if recorded is None:
        return (
            "conflict",
            None,
            f"{file_path} was edited inside the macos9-theme-firefox marker block; refusing to overwrite",
        )

    # Remove only separators added by the installer, even after edits on
    # either side of the block. Older state files already record this chunk.
    if recorded.get(f"untouched_{key}_sha256") == sha256_bytes(raw_bytes):
        return ("restore_backup" if existed_before else "delete", None, "")
    installed_chunk = recorded.get(f"installed_{key}_chunk")
    if installed_chunk and inner in installed_chunk:
        lead, _, tail = installed_chunk.partition(inner)
        if lead and before.endswith(lead):
            before = before[:-len(lead)]
        if tail and after.startswith(tail):
            after = after[len(tail):]
    remainder = before + after
    if not existed_before and remainder == "":
        return ("delete", None, "")

    # If stripping markers yields the exact original backup bytes, use restore_backup!
    rem_bytes = remainder.encode("utf-8", errors="surrogateescape")
    if existed_before and backup_file.is_file() and rem_bytes == backup_file.read_bytes():
        return ("restore_backup", None, "")
    return ("write", rem_bytes, "")


def cmd_uninstall(args: argparse.Namespace, handles: ExitStack) -> int:
    prog = PROG_UNINSTALL
    home = pathlib.Path(args.home)
    config_home = pathlib.Path(args.config_home)
    state_dir = pathlib.Path(args.state_dir)
    state_home = pathlib.Path(args.state_home)
    dry_run = bool(args.dry_run)

    installed = discover_installed_profiles(home, config_home, state_dir)
    if args.list:
        if not installed:
            print("Platinum for Firefox is not installed in any profile.")
            return 0
        print("Installed Firefox profiles:")
        for p in installed:
            print(format_profile_line(p))
        return 0

    if not installed:
        if dry_run:
            print("Dry run: nothing is changed.")
        print("Nothing to remove: Platinum for Firefox is not installed in any profile.")
        return 0

    chosen = select_profile(installed, args.profile, prog, "restore")
    if chosen is None:
        return 1

    prof_dir = pathlib.Path(chosen["path"])
    pkey = chosen["key"]
    pstate_dir = state_dir / "profiles" / pkey
    jpath = pstate_dir / "journal.json"
    spath = pstate_dir / "state.json"

    journal = json.loads(jpath.read_text(encoding="utf-8")) if jpath.is_file() else {}
    state = json.loads(spath.read_text(encoding="utf-8")) if spath.is_file() else {}
    phase = journal.get("phase", "installed")

    # Case 0: Earlier install aborted BEFORE backup completed -> zero profile files touched!
    if phase == "installing" and not journal.get("backup_complete", False):
        if dry_run:
            print("Dry run: nothing is changed.")
            print(f"  would clean up incomplete pre-backup journal in {pstate_dir}")
            return 0
        shutil.rmtree(pstate_dir)
        return 0

    if not check_profile_symlinks(prof_dir, prog):
        return 1
    if not hold_profile_lock(prof_dir, prog, handles):
        return 1

    cur_real = os.path.realpath(str(prof_dir))
    cur_parent_real = real_parent_path(prof_dir)
    rec_real = state.get("profile_real") or journal.get("profile_real")
    rec_parent_real = state.get("profile_parent_real") or journal.get("profile_parent_real")
    if rec_real and rec_real != cur_real:
        return die(
            prog,
            f"{prof_dir} now resolves to {cur_real} (was {rec_real}); "
            "point the directory link back first; nothing was changed",
        )
    if rec_parent_real and rec_parent_real != cur_parent_real:
        return die(
            prog,
            f"parent path of {prof_dir} moved ({cur_parent_real} vs {rec_parent_real}); nothing was changed",
        )

    bak_dir = pstate_dir / "backup"
    if phase == "uninstalling" and not bak_dir.exists() and journal.get("archive_dir"):
        bak_dir = pathlib.Path(journal["archive_dir"]) / "restored-backup"
    ok_bak, bak_meta, bak_err = verify_backup(bak_dir)
    if not ok_bak:
        return die(prog, f"refusing to restore from damaged backup ({bak_err}); nothing was changed")

    completed_steps: list[str] = list(journal.get("completed_steps", [])) if phase == "uninstalling" else []
    interrupted_install = phase == "installing" or journal.get("interrupted_install", False)
    pending = journal.get("pending", {})

    chrome_dir = prof_dir / "chrome"
    plat_dir = chrome_dir / "platinum"
    uc_file = chrome_dir / "userChrome.css"
    ucnt_file = chrome_dir / "userContent.css"
    ujs_file = prof_dir / "user.js"
    pjs_file = prof_dir / "prefs.js"

    adoption = pending.get("content_adoption", state.get("content_adoption"))
    bak_ucnt, ucnt_existed, ucnt_mode = content_backup(pstate_dir, bak_dir, bak_meta, adoption)
    if not valid_adoption(bak_ucnt, adoption):
        return die(prog, "damaged userContent.css upgrade backup")
    usercontent_managed = any("installed_usercontent_block" in r for r in (state, pending))

    # Pre-validate all remaining steps BEFORE mutating anything so a conflict stops cleanly!
    if "platinum" not in completed_steps and plat_dir.exists():
        known = [r["platinum_sums"] for r in (state, pending) if "platinum_sums" in r]
        if interrupted_install and not pending:
            known.append(tree_sums(pathlib.Path(__file__).parent / "chrome/platinum"))
        original = bak_dir / "chrome/platinum"
        if not matches_installed_theme(plat_dir, known):
            may_be_original = phase == "uninstalling" or (interrupted_install and not state)
            if not (may_be_original and original_platinum_matches(plat_dir, original)):
                return die(prog, f"conflict in {plat_dir}; nothing was overwritten")

    # If a rename succeeded just before interruption, its journal update
    # may be missing. Recognize the exact planned result before replaying.
    undo_hashes = journal.get("undo_hashes", {})
    already_written = set()
    for step, path in (("userChrome", uc_file), ("userContent", ucnt_file), ("user_js", ujs_file)):
        if step in undo_hashes and step not in completed_steps:
            current = sha256_file(path) if path.is_file() else None
            if current == undo_hashes[step]:
                already_written.add(step)

    uc_action, uc_new_bytes = ("noop", None)
    if "userChrome" not in completed_steps and "userChrome" not in already_written:
        uc_action, uc_new_bytes, err = plan_marker_removal(
            uc_file, bak_meta["userChrome_existed"], bak_dir / "chrome/userChrome.css",
            "userchrome", state, pending, interrupted_install,
        )
        if err:
            return die(prog, f"conflict: {err}")

    ucnt_action, ucnt_new_bytes = ("noop", None)
    if usercontent_managed and "userContent" not in completed_steps and "userContent" not in already_written:
        ucnt_action, ucnt_new_bytes, err = plan_marker_removal(
            ucnt_file, ucnt_existed, bak_ucnt,
            "usercontent", state, pending, interrupted_install,
        )
        if err:
            return die(prog, f"conflict: {err}")

    ujs_action, ujs_new_bytes = ("noop", None)
    if "user_js" not in completed_steps and "user_js" not in already_written:
        ujs_action, ujs_new_bytes, err = plan_marker_removal(
            ujs_file, bak_meta["user_js_existed"], bak_dir / "user.js",
            "userjs", state, pending, interrupted_install,
        )
        if err:
            return die(prog, f"conflict: {err}")

    if dry_run:
        print("Dry run: nothing is changed.")
        print(f"  target profile: {chosen['name']} ({prof_dir})")
        if "platinum" not in completed_steps:
            print(f"  would remove {plat_dir}/")
            if bak_meta.get("foreign_platinum_existed"):
                print(f"  would restore the original {plat_dir}")
        if "userChrome" not in completed_steps:
            print(f"  would undo {uc_file} ({uc_action})")
        if usercontent_managed and "userContent" not in completed_steps:
            print(f"  would undo {ucnt_file} ({ucnt_action})")
        if "user_js" not in completed_steps:
            print(f"  would undo {ujs_file} ({ujs_action})")
        if "prefs_js" not in completed_steps:
            print(f"  would restore managed prefs in {pjs_file}")
        return 0


    remove_stage(chrome_dir, journal)

    # Save pre-uninstall archive folder (once per uninstall transaction).
    archive_dir_str = journal.get("archive_dir")
    if not archive_dir_str:
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        cand = state_home / f"macos9-theme-firefox-uninstalled-{stamp}"
        idx = 2
        while cand.exists() or cand.is_symlink():
            cand = state_home / f"macos9-theme-firefox-uninstalled-{stamp}-{idx}"
            idx += 1
        cand.mkdir(parents=True, mode=0o700)
        before_snap = cand / "before-uninstall"
        before_snap.mkdir(mode=0o700)
        for rel in ("chrome/userChrome.css", "chrome/userContent.css", "user.js", "prefs.js"):
            fp = prof_dir / rel
            if fp.is_file():
                dst = before_snap / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(fp, dst)
        archive_dir_str = str(cand)

    for step, action, data, backup in (
        ("userChrome", uc_action, uc_new_bytes, bak_dir / "chrome/userChrome.css"),
        ("userContent", ucnt_action, ucnt_new_bytes, bak_ucnt),
        ("user_js", ujs_action, ujs_new_bytes, bak_dir / "user.js"),
    ):
        if action == "write":
            undo_hashes[step] = sha256_bytes(data)
        elif action == "restore_backup":
            undo_hashes[step] = sha256_file(backup)
        elif action == "delete":
            undo_hashes[step] = None

    stage = chrome_dir / f".macos9-ff-tmp.{secrets.token_hex(12)}"

    def save_progress() -> None:
        atomic_write_json(
            jpath,
            {
                "phase": "uninstalling",
                "stage": stage.name,
                "interrupted_install": interrupted_install,
                "pending": pending,
                "backup_complete": True,
                "profile_path": str(prof_dir),
                "profile_real": cur_real,
                "profile_parent_real": cur_parent_real,
                "completed_steps": completed_steps,
                "undo_hashes": undo_hashes,
                "archive_dir": archive_dir_str,
            },
        )

    save_progress()

    # Restore from the verified backup, including backups from older installers.
    if "platinum" not in completed_steps:
        original = bak_dir / "chrome/platinum"
        if plat_dir.exists() or original.exists():
            chrome_dir.mkdir(parents=True, exist_ok=True)
            stage.mkdir(mode=0o700)
            if original.is_dir():
                shutil.copytree(original, stage / "original")
            elif original.is_file():
                shutil.copy2(original, stage / "original")
            if plat_dir.exists():
                os.replace(plat_dir, stage / "installed")
                maybe_inject_fault("uninstall_platinum_swap")
            if original.exists():
                os.replace(stage / "original", plat_dir)
            fsync_dir(chrome_dir)
            shutil.rmtree(stage)
        completed_steps.append("platinum")
        save_progress()
        maybe_inject_fault("uninstall_platinum")

    # Step 2a: Restore or strip marker block in chrome/userChrome.css
    if "userChrome" not in completed_steps:
        bak_uc = bak_dir / "chrome" / "userChrome.css"
        if uc_action == "restore_backup" and bak_uc.is_file():
            chrome_dir.mkdir(parents=True, exist_ok=True)
            tmp = chrome_dir / f".macos9-ff-tmp.{secrets.token_hex(6)}"
            shutil.copy2(bak_uc, tmp)
            os.chmod(str(tmp), bak_meta.get("userChrome_mode", 0o644))
            os.replace(str(tmp), str(uc_file))
            fsync_dir(chrome_dir)
        elif uc_action == "delete":
            if uc_file.exists():
                uc_file.unlink()
                fsync_dir(chrome_dir)
        elif uc_action == "write" and uc_new_bytes is not None:
            cur_mode = stat.S_IMODE(uc_file.stat().st_mode) if uc_file.is_file() else bak_meta.get("userChrome_mode", 0o644)
            atomic_write_bytes(uc_file, uc_new_bytes, cur_mode)

        maybe_inject_fault("userChrome_before_journal")
        completed_steps.append("userChrome")
        save_progress()
        maybe_inject_fault("uninstall_userChrome")

    # Step 2b: Restore or strip marker block in chrome/userContent.css (+ rmdir chrome/ if created by us & empty)
    if "userContent" not in completed_steps:
        if ucnt_action == "restore_backup" and bak_ucnt.is_file():
            chrome_dir.mkdir(parents=True, exist_ok=True)
            tmp = chrome_dir / f".macos9-ff-tmp.{secrets.token_hex(6)}"
            shutil.copy2(bak_ucnt, tmp)
            os.chmod(str(tmp), ucnt_mode)
            os.replace(str(tmp), str(ucnt_file))
            fsync_dir(chrome_dir)
        elif ucnt_action == "delete":
            if ucnt_file.exists():
                ucnt_file.unlink()
                fsync_dir(chrome_dir)
        elif ucnt_action == "write" and ucnt_new_bytes is not None:
            cur_mode = stat.S_IMODE(ucnt_file.stat().st_mode) if ucnt_file.is_file() else ucnt_mode
            atomic_write_bytes(ucnt_file, ucnt_new_bytes, cur_mode)

        if not bak_meta.get("chrome_existed") and chrome_dir.is_dir():
            try:
                chrome_dir.rmdir()
            except OSError:
                pass
        elif bak_meta.get("chrome_existed") and chrome_dir.is_dir():
            os.chmod(str(chrome_dir), bak_meta.get("chrome_mode", 0o755))

        maybe_inject_fault("userContent_before_journal")
        completed_steps.append("userContent")
        save_progress()
        maybe_inject_fault("uninstall_userContent")

    # Step 3: Restore or strip marker block in user.js
    if "user_js" not in completed_steps:
        bak_ujs = bak_dir / "user.js"
        if ujs_action == "restore_backup" and bak_ujs.is_file():
            tmp = prof_dir / f".macos9-ff-tmp.{secrets.token_hex(6)}"
            shutil.copy2(bak_ujs, tmp)
            os.chmod(str(tmp), bak_meta.get("user_js_mode", 0o644))
            os.replace(str(tmp), str(ujs_file))
            fsync_dir(prof_dir)
        elif ujs_action == "delete":
            if ujs_file.exists():
                ujs_file.unlink()
                fsync_dir(prof_dir)
        elif ujs_action == "write" and ujs_new_bytes is not None:
            cur_mode = stat.S_IMODE(ujs_file.stat().st_mode) if ujs_file.is_file() else bak_meta.get("user_js_mode", 0o644)
            atomic_write_bytes(ujs_file, ujs_new_bytes, cur_mode)

        completed_steps.append("user_js")
        save_progress()
        maybe_inject_fault("uninstall_user_js")

    # Step 4: Restore managed prefs in prefs.js directly!
    if "prefs_js" not in completed_steps:
        prefs_snap = pending.get("prefs_snapshot", state.get("prefs_snapshot", bak_meta["prefs_snapshot"]))
        bak_pjs = bak_dir / "prefs.js"
        backup_bytes = bak_pjs.read_bytes() if bak_pjs.is_file() else None
        current = pjs_file.read_bytes() if pjs_file.is_file() else None
        base = current if current is not None else (backup_bytes or b"")
        # A later version may have adopted a preference the user changed after
        # the first install. Only use the original file wholesale if its values
        # agree with the snapshots taken when each preference was adopted.
        compatible = parse_prefs_snapshot(bak_pjs, list(prefs_snap)) == prefs_snap
        restored = restore_prefs_in_text(base.decode("utf-8", "surrogateescape"),
                                         backup_bytes if compatible else None, prefs_snap)
        if backup_bytes is None and not restored:
            if current is not None:
                pjs_file.unlink()
                fsync_dir(prof_dir)
        elif current != restored:
            mode = bak_meta["prefs_js_mode"]
            if current is not None and restored != backup_bytes:
                mode = stat.S_IMODE(pjs_file.stat().st_mode)
            atomic_write_bytes(pjs_file, restored, mode)

        completed_steps.append("prefs_js")
        save_progress()

    # Step 5: Archive backup into $archive_dir/restored-backup and retire $pstate_dir cleanly.
    archive_dir = pathlib.Path(archive_dir_str)
    if adoption is not None and ucnt_existed:
        shutil.copy2(bak_ucnt, archive_dir / "adopted-userContent.css")
    if bak_dir == pstate_dir / "backup":
        os.replace(bak_dir, archive_dir / "restored-backup")
        maybe_inject_fault("archived_backup")
    shutil.rmtree(pstate_dir)

    profs_root = state_dir / "profiles"
    if profs_root.is_dir():
        try:
            profs_root.rmdir()
        except OSError:
            pass

    print(f"Removed Platinum for Firefox from profile '{chosen['name']}' ({prof_dir}).")
    print(f"Backup archive kept in {archive_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="profile_ops.py")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_ins = sub.add_parser("install")
    p_ins.add_argument("--home", required=True)
    p_ins.add_argument("--config-home", required=True)
    p_ins.add_argument("--state-dir", required=True)
    p_ins.add_argument("--repo-firefox-dir", required=True)
    p_ins.add_argument("--profile", default=None)
    p_ins.add_argument("--list", action="store_true")
    p_ins.add_argument("--dry-run", action="store_true")

    p_un = sub.add_parser("uninstall")
    p_un.add_argument("--home", required=True)
    p_un.add_argument("--config-home", required=True)
    p_un.add_argument("--state-dir", required=True)
    p_un.add_argument("--state-home", required=True)
    p_un.add_argument("--profile", default=None)
    p_un.add_argument("--list", action="store_true")
    p_un.add_argument("--dry-run", action="store_true")

    return ap


def main() -> int:
    ap = build_parser()
    args = ap.parse_args()
    with ExitStack() as handles:
        if args.cmd == "install":
            return cmd_install(args, handles)
        if args.cmd == "uninstall":
            return cmd_uninstall(args, handles)
    return 2


if __name__ == "__main__":
    sys.exit(main())
