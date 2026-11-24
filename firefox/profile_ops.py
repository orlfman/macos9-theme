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
  - Refuses while the target profile is in use (lock symlink/file or an active
    POSIX fcntl / BSD flock lock on .parentlock) or if any target path/parent
    is a symbolic link or was repointed since installation.
  - Journals and backs up (with SHA-256 verification) the entire pre-existing
    chrome/ folder, user.js, and prefs.js + exact per-pref snapshot BEFORE any
    profile file is modified.
  - Installs chrome/platinum/, prepends one marker-delimited @import block to
    chrome/userChrome.css (after @charset if present, preserving @namespace and
    all user rules below it), and appends one marker-delimited user_pref block
    to user.js.
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
import datetime as dt
import errno
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

# Managed prefs written into user.js (in deterministic order).
# Overrideable via M9_FF_MANAGED_PREFS_JSON in tests to verify upgrade path
# (adding/retiring a managed pref across theme versions).
DEFAULT_MANAGED_PREFS: list[tuple[str, str]] = [
    ("toolkit.legacyUserProfileCustomizations.stylesheets", "true"),
    ("browser.tabs.inTitlebar", "0"),
    ("browser.toolbars.bookmarks.visibility", '"always"'),
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
        os.write(fd, data)
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


def clean_profile_temps(prof_dir: pathlib.Path) -> None:
    for d in (prof_dir, prof_dir / "chrome"):
        if d.is_dir() and not d.is_symlink():
            for child in d.iterdir():
                if child.name.startswith(".macos9-ff-tmp."):
                    if child.is_symlink() or child.is_file():
                        child.unlink()
                    elif child.is_dir():
                        shutil.rmtree(child)


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
    seen_real: set[str] = set()

    for store_name, base_dir in stores:
        ini_path = base_dir / "profiles.ini"
        if not ini_path.is_file() or ini_path.is_symlink():
            continue
        cp = configparser.RawConfigParser()
        cp.read(ini_path, encoding="utf-8")

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
            if not prof_path.exists() and not prof_path.is_symlink():
                continue

            real_str = os.path.realpath(str(prof_path))
            if real_str in seen_real:
                continue
            seen_real.add(real_str)

            name = cp.get(sec, "Name", fallback=prof_path.name).strip() or prof_path.name
            leg_def = cp.get(sec, "Default", fallback="0").strip() == "1"
            inst_def = (real_str in install_default_reals) or (str(prof_path) in install_default_raws)

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


def check_profile_not_in_use(prof_dir: pathlib.Path, prog: str) -> bool:
    """Return True if profile is NOT locked; emit error and return False if locked."""
    lock_link = prof_dir / "lock"
    if os.path.lexists(str(lock_link)):
        target_info = ""
        if lock_link.is_symlink():
            try:
                target_info = f" -> {os.readlink(str(lock_link))}"
            except OSError:
                pass
        die(
            prog,
            f"profile is in use ({lock_link}{target_info} exists). "
            "Close Firefox completely and try again; nothing was changed",
        )
        return False

    plock = prof_dir / ".parentlock"
    if os.path.lexists(str(plock)):
        if plock.is_symlink():
            die(prog, f"{plock} is a symbolic link; refusing to touch profile; nothing was changed")
            return False
        try:
            fd = os.open(str(plock), os.O_RDWR)
        except OSError as e:
            die(prog, f"cannot open {plock} ({e.strerror}); close Firefox and try again; nothing was changed")
            return False
        try:
            # Probe POSIX advisory write lock (Firefox nsProfileLock on Linux)
            # AND BSD flock so both locking mechanisms are caught cleanly while
            # an unlocked leftover 0-byte .parentlock on a closed profile passes.
            try:
                fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.lockf(fd, fcntl.LOCK_UN)
            except OSError as e:
                if e.errno in (errno.EACCES, errno.EAGAIN):
                    die(
                        prog,
                        f"profile is currently in use by a running Firefox process ({plock} is locked). "
                        "Close Firefox completely and try again; nothing was changed",
                    )
                    return False
                raise
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                fcntl.flock(fd, fcntl.LOCK_UN)
            except OSError as e:
                if e.errno in (errno.EACCES, errno.EAGAIN, errno.EWOULDBLOCK):
                    die(
                        prog,
                        f"profile is currently in use ({plock} is flock-locked). "
                        "Close Firefox completely and try again; nothing was changed",
                    )
                    return False
                raise
        finally:
            os.close(fd)
    return True


def check_profile_symlinks(prof_dir: pathlib.Path, prog: str) -> bool:
    """Refuse if profile dir or any managed file/folder (or child of chrome/) is a symlink."""
    if prof_dir.is_symlink():
        die(prog, f"profile path {prof_dir} is a symbolic link; nothing was changed")
        return False
    if not prof_dir.is_dir():
        die(prog, f"profile folder {prof_dir} does not exist; nothing was changed")
        return False

    for rel in ("chrome", "chrome/userChrome.css", "chrome/platinum", "user.js", "prefs.js"):
        p = prof_dir / rel
        if p.is_symlink():
            die(
                prog,
                f"{p} is a symbolic link; {prog} refuses to write through symlinks. "
                "Replace it with a regular file/folder and try again; nothing was changed",
            )
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
                if cand.is_symlink():
                    die(
                        prog,
                        f"{cand} inside {chrome_dir} is a symbolic link; "
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
    sep = "\n" if not existing_text.startswith(("\n", "\r\n")) else ""
    chunk = block + sep
    if m:
        prefix = m.group(1)
        if not prefix.endswith("\n"):
            prefix += "\n"
            rest = existing_text[m.end() :]
        else:
            rest = existing_text[m.end() :]
        return (prefix + chunk + rest, chunk)
    return (chunk + existing_text, chunk)


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

    text = prefs_path.read_text(encoding="utf-8", errors="surrogateescape")
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


def check_platinum_dir_intact(plat_dir: pathlib.Path, recorded_sums: dict[str, str]) -> tuple[bool, str]:
    """Verify chrome/platinum contains no modified or user-added files."""
    if not plat_dir.exists() and not plat_dir.is_symlink():
        return (True, "")
    if plat_dir.is_symlink() or not plat_dir.is_dir():
        return (False, f"{plat_dir} is no longer a regular folder")

    for dirpath, dirnames, filenames in os.walk(str(plat_dir), followlinks=False):
        dp = pathlib.Path(dirpath)
        for d in dirnames:
            if (dp / d).is_symlink():
                return (False, f"symlink added inside {plat_dir}: {dp / d}")
        for fn in filenames:
            fp = dp / fn
            if fp.is_symlink() or not fp.is_file():
                return (False, f"non-regular entry inside {plat_dir}: {fp}")
            rel = str(fp.relative_to(plat_dir))
            if rel not in recorded_sums:
                return (False, f"user file added inside {plat_dir}: {rel}")
            if sha256_file(fp) != recorded_sums[rel]:
                return (False, f"installed file modified inside {plat_dir}: {rel}")
    return (True, "")


def take_initial_backup(prof_dir: pathlib.Path, pstate_dir: pathlib.Path, managed_prefs: list[tuple[str, str]]) -> dict[str, Any]:
    """Create checksummed initial backup of chrome/, user.js, and prefs.js BEFORE any change."""
    bak_tmp = pstate_dir / f".backup-tmp.{secrets.token_hex(6)}"
    bak_final = pstate_dir / "backup"
    if bak_tmp.exists():
        shutil.rmtree(bak_tmp)
    bak_tmp.mkdir(parents=True, mode=0o700)

    chrome_dir = prof_dir / "chrome"
    uc_file = chrome_dir / "userChrome.css"
    plat_dir = chrome_dir / "platinum"
    ujs_file = prof_dir / "user.js"
    pjs_file = prof_dir / "prefs.js"

    meta: dict[str, Any] = {
        "chrome_existed": chrome_dir.exists(),
        "chrome_mode": (stat.S_IMODE(chrome_dir.stat().st_mode) if chrome_dir.exists() else 0o755),
        "userChrome_existed": uc_file.is_file(),
        "userChrome_mode": (stat.S_IMODE(uc_file.stat().st_mode) if uc_file.is_file() else 0o644),
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
    atomic_write_json(bak_tmp / "BACKUP_META.json", {"meta": meta, "sums": sums})

    if bak_final.exists():
        shutil.rmtree(bak_final)
    os.replace(str(bak_tmp), str(bak_final))
    fsync_dir(pstate_dir)
    return meta


def verify_backup(pstate_dir: pathlib.Path) -> tuple[bool, dict[str, Any], str]:
    bak = pstate_dir / "backup"
    meta_file = bak / "BACKUP_META.json"
    if not bak.is_dir() or bak.is_symlink() or not meta_file.is_file() or meta_file.is_symlink():
        return (False, {}, f"backup folder {bak} is missing or incomplete")

    payload = json.loads(meta_file.read_text(encoding="utf-8"))
    recorded_sums: dict[str, str] = payload.get("sums", {})
    actual_sums = tree_sums(bak)
    actual_sums.pop("BACKUP_META.json", None)
    if actual_sums != recorded_sums:
        return (False, {}, f"backup checksum verification failed in {bak}")
    return (True, payload["meta"], "")


# ---------------------------------------------------------------------------
# Install / Reinstall / Upgrade
# ---------------------------------------------------------------------------

def cmd_install(args: argparse.Namespace) -> int:
    prog = PROG_INSTALL
    home = pathlib.Path(args.home)
    config_home = pathlib.Path(args.config_home)
    state_dir = pathlib.Path(args.state_dir)
    repo_ff_dir = pathlib.Path(args.repo_firefox_dir)
    dry_run = bool(args.dry_run)

    src_platinum = repo_ff_dir / "chrome" / "platinum"
    if not src_platinum.is_dir() or not (src_platinum / "platinum.css").is_file():
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
    if not check_profile_not_in_use(prof_dir, prog):
        return 1

    pkey = chosen["key"]
    pstate_dir = state_dir / "profiles" / pkey
    jpath = pstate_dir / "journal.json"
    spath = pstate_dir / "state.json"

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
        ok, bak_meta, err = verify_backup(pstate_dir)
        if not ok:
            return die(prog, f"existing state backup is damaged ({err}); nothing was changed")
        has_prior_backup = True
    elif existing_journal and not existing_journal.get("backup_complete"):
        # Earlier install aborted before backup completed (zero profile mutations happened).
        if not dry_run and pstate_dir.exists():
            shutil.rmtree(pstate_dir)
        existing_journal = None

    # Pre-check existing chrome/platinum, userChrome.css, and user.js for conflicts BEFORE writing!
    chrome_dir = prof_dir / "chrome"
    plat_dir = chrome_dir / "platinum"
    uc_file = chrome_dir / "userChrome.css"
    ujs_file = prof_dir / "user.js"
    pjs_file = prof_dir / "prefs.js"

    if has_prior_backup and existing_state is not None:
        ok_plat, reason = check_platinum_dir_intact(plat_dir, existing_state.get("platinum_sums", {}))
        if not ok_plat:
            return die(
                prog,
                f"conflict in {plat_dir} ({reason}); move your changes out of chrome/platinum/ first; nothing was changed",
            )

    # Inspect userChrome.css markers
    uc_existing_text = uc_file.read_text(encoding="utf-8", errors="surrogateescape") if uc_file.is_file() else ""
    uc_mstate, uc_before, uc_inner, uc_after = inspect_markers(uc_existing_text)
    if uc_mstate == "corrupt":
        return die(prog, f"corrupted {MARKER_BEGIN} markers in {uc_file}; fix them first; nothing was changed")
    if uc_mstate == "present":
        if not has_prior_backup:
            return die(prog, f"{uc_file} already contains macos9-theme-firefox markers without an install record; nothing was changed")
        rec_uc_block = (existing_state or {}).get("installed_userchrome_block", USERCHROME_BLOCK)
        if uc_inner != rec_uc_block:
            return die(prog, f"conflict in {uc_file}: lines inside macos9-theme-firefox markers were edited; nothing was changed")

    # Inspect user.js markers
    ujs_existing_text = ujs_file.read_text(encoding="utf-8", errors="surrogateescape") if ujs_file.is_file() else ""
    ujs_mstate, ujs_before, ujs_inner, ujs_after = inspect_markers(ujs_existing_text)
    if ujs_mstate == "corrupt":
        return die(prog, f"corrupted {MARKER_BEGIN} markers in {ujs_file}; fix them first; nothing was changed")
    if ujs_mstate == "present":
        if not has_prior_backup:
            return die(prog, f"{ujs_file} already contains macos9-theme-firefox markers without an install record; nothing was changed")
        rec_ujs_block = (existing_state or {}).get("installed_userjs_block")
        if rec_ujs_block is not None and ujs_inner != rec_ujs_block:
            return die(prog, f"conflict in {ujs_file}: lines inside macos9-theme-firefox markers were edited; nothing was changed")

    if dry_run:
        print("Dry run: nothing is changed.")
        print(f"  target profile: {chosen['name']} ({prof_dir})")
        if not has_prior_backup:
            print(f"  would back up existing chrome/, user.js, and prefs.js snapshot to {pstate_dir / 'backup'}")
            if plat_dir.exists():
                print(f"  would move existing {plat_dir} aside to {pstate_dir / 'displaced/platinum'}")
        else:
            print(f"  would preserve original pre-install backup in {pstate_dir / 'backup'}")
        print(f"  would install {src_platinum} -> {plat_dir}/")
        print(f"  would write marker-delimited @import block in {uc_file}")
        print(f"  would write marker-delimited user_pref block in {ujs_file}")
        return 0

    clean_profile_temps(prof_dir)
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
        atomic_write_json(
            jpath,
            {
                "phase": "installing",
                "backup_complete": True,
                "profile_path": str(prof_dir),
                "profile_real": cur_real,
                "profile_parent_real": cur_parent_real,
            },
        )
        maybe_inject_fault("backup")
    else:
        prefs_snapshot = dict((existing_state or {}).get("prefs_snapshot") or bak_meta["prefs_snapshot"])
        new_keys = [k for k, _ in managed_prefs if k not in prefs_snapshot]
        if new_keys:
            extra = parse_prefs_snapshot(pjs_file, new_keys)
            prefs_snapshot.update(extra)
        atomic_write_json(
            jpath,
            {
                "phase": "installing",
                "backup_complete": True,
                "profile_path": str(prof_dir),
                "profile_real": cur_real,
                "profile_parent_real": cur_parent_real,
            },
        )

    # Step 2a: Displace pre-existing foreign chrome/platinum (first install only) & stage chrome/platinum/
    chrome_dir.mkdir(parents=True, exist_ok=True)
    displaced_plat = pstate_dir / "displaced" / "platinum"
    if existing_state is None and bak_meta.get("foreign_platinum_existed") and plat_dir.exists() and not displaced_plat.exists():
        displaced_plat.parent.mkdir(parents=True, exist_ok=True)
        os.replace(str(plat_dir), str(displaced_plat))
        fsync_dir(displaced_plat.parent)

    stage_plat = chrome_dir / f".macos9-ff-tmp.{secrets.token_hex(6)}"
    shutil.copytree(src_platinum, stage_plat, symlinks=False, copy_function=shutil.copy2)
    for root, dirs, files in os.walk(str(stage_plat)):
        os.chmod(root, 0o755)
        for d in dirs:
            os.chmod(os.path.join(root, d), 0o755)
        for fn in files:
            os.chmod(os.path.join(root, fn), 0o644)
    new_plat_sums = tree_sums(stage_plat)

    if plat_dir.exists():
        old_plat = chrome_dir / f".macos9-ff-tmp.old.{secrets.token_hex(6)}"
        os.replace(str(plat_dir), str(old_plat))
        os.replace(str(stage_plat), str(plat_dir))
        shutil.rmtree(old_plat)
    else:
        os.replace(str(stage_plat), str(plat_dir))
    fsync_dir(chrome_dir)
    maybe_inject_fault("platinum")

    # Step 2b: Write chrome/userChrome.css atomically (keeping existing user rules below markers).
    if uc_mstate == "present":
        # Replace existing marker block in place, keeping surrounding bytes intact.
        new_uc_text = uc_before + USERCHROME_BLOCK + uc_after
        inserted_uc_chunk = (existing_state or {}).get("installed_userchrome_chunk", USERCHROME_BLOCK)
    else:
        new_uc_text, inserted_uc_chunk = insert_userchrome_block(uc_existing_text, USERCHROME_BLOCK)

    uc_bytes = new_uc_text.encode("utf-8", errors="surrogateescape")
    uc_mode = bak_meta.get("userChrome_mode", 0o644)
    atomic_write_bytes(uc_file, uc_bytes, uc_mode)
    maybe_inject_fault("userChrome")

    # Step 2c: Write user.js atomically (keeping existing user lines outside markers).
    if ujs_mstate == "present":
        new_ujs_text = ujs_before + new_ujs_block + ujs_after
        inserted_ujs_chunk = (existing_state or {}).get("installed_userjs_chunk", new_ujs_block)
    else:
        new_ujs_text, inserted_ujs_chunk = insert_userjs_block(ujs_existing_text, new_ujs_block)

    ujs_bytes = new_ujs_text.encode("utf-8", errors="surrogateescape")
    ujs_mode = bak_meta.get("user_js_mode", 0o644)
    atomic_write_bytes(ujs_file, ujs_bytes, ujs_mode)
    maybe_inject_fault("user_js")

    # Step 2d: On upgrade, if an earlier version set a managed pref that is NO LONGER
    # in managed_prefs, restore its original value/absence in prefs.js immediately!
    active_pref_keys = {k for k, _ in managed_prefs}
    retired_keys = {k: v for k, v in prefs_snapshot.items() if k not in active_pref_keys}
    if retired_keys and pjs_file.is_file():
        cur_pjs_text = pjs_file.read_text(encoding="utf-8", errors="surrogateescape")
        new_pjs_bytes = restore_prefs_in_text(cur_pjs_text, None, retired_keys)
        pjs_mode = stat.S_IMODE(pjs_file.stat().st_mode)
        atomic_write_bytes(pjs_file, new_pjs_bytes, pjs_mode)
        for rk in retired_keys:
            prefs_snapshot.pop(rk, None)

    # Preserve original untouched full-file checksums when upgrading an unedited
    # install, or recompute when reinstalling/upgrading cleanly!
    # Wait: if the user hasn't edited outside markers, removing our new block yields
    # exact backup bytes, so installed_userchrome_sha256 == sha256(uc_bytes) holds
    # whenever userChrome.css has no post-install user edits! Let's check against backup!
    bak_uc = pstate_dir / "backup" / "chrome" / "userChrome.css"
    bak_ujs = pstate_dir / "backup" / "user.js"
    uc_matches_untouched = False
    if not bak_meta.get("userChrome_existed"):
        uc_matches_untouched = uc_bytes == USERCHROME_BLOCK.encode("utf-8")
    elif bak_uc.is_file():
        expected_uc, _ = insert_userchrome_block(
            bak_uc.read_text(encoding="utf-8", errors="surrogateescape"),
            USERCHROME_BLOCK,
        )
        uc_matches_untouched = uc_bytes == expected_uc.encode("utf-8", errors="surrogateescape")

    ujs_matches_untouched = False
    if not bak_meta.get("user_js_existed"):
        ujs_matches_untouched = ujs_bytes == new_ujs_block.encode("utf-8")
    elif bak_ujs.is_file():
        expected_ujs, _ = insert_userjs_block(
            bak_ujs.read_text(encoding="utf-8", errors="surrogateescape"),
            new_ujs_block,
        )
        ujs_matches_untouched = ujs_bytes == expected_ujs.encode("utf-8", errors="surrogateescape")

    state_obj = {
        "schema": 1,
        "installed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "firefox_version_at_install": ver_info.get("version"),
        "profile_name": chosen["name"],
        "profile_path": str(prof_dir),
        "profile_real": cur_real,
        "profile_parent_real": cur_parent_real,
        "platinum_sums": new_plat_sums,
        "installed_userchrome_block": USERCHROME_BLOCK,
        "installed_userchrome_chunk": inserted_uc_chunk,
        "untouched_userchrome_sha256": sha256_bytes(uc_bytes) if uc_matches_untouched else None,
        "installed_userjs_block": new_ujs_block,
        "installed_userjs_chunk": inserted_ujs_chunk,
        "untouched_userjs_sha256": sha256_bytes(ujs_bytes) if ujs_matches_untouched else None,
        "managed_prefs": managed_prefs,
        "prefs_snapshot": prefs_snapshot,
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
    print("Restart Firefox to load chrome/userChrome.css.")
    return 0


# ---------------------------------------------------------------------------
# Uninstall / Byte-for-byte Undo & Conflict Detection
# ---------------------------------------------------------------------------

def plan_marker_removal(
    file_path: pathlib.Path,
    existed_before: bool,
    backup_file: pathlib.Path,
    expected_block: str | None,
    untouched_sha256: str | None,
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
    if untouched_sha256 and sha256_bytes(raw_bytes) == untouched_sha256:
        if existed_before:
            return ("restore_backup", None, "")
        return ("delete", None, "")

    text = raw_bytes.decode("utf-8", errors="surrogateescape")
    mstate, before, inner, after = inspect_markers(text)
    if mstate == "corrupt":
        return ("conflict", None, f"{file_path} has corrupted or duplicate macos9-theme-firefox markers")
    if mstate == "absent":
        return (
            "conflict",
            None,
            f"{file_path} was modified and no longer contains macos9-theme-firefox markers; refusing to overwrite",
        )

    if expected_block is not None and inner != expected_block:
        return (
            "conflict",
            None,
            f"{file_path} was edited inside the macos9-theme-firefox marker block; refusing to overwrite",
        )

    # Cleanly strip the marker block + separator while keeping user edits outside markers!
    if after.startswith("\n") and existed_before and (before == "" or before.lstrip("\ufeff").startswith("@charset")):
        # Strip the single separator newline we added after the top userChrome.css block.
        after_clean = after[1:]
    elif after == "" and before.endswith("\n\n") and existed_before:
        # Strip the extra blank separator newline we added before the bottom user.js block.
        before_clean = before[:-1]
        remainder = before_clean
        rem_bytes = remainder.encode("utf-8", errors="surrogateescape")
        if backup_file.is_file() and rem_bytes == backup_file.read_bytes():
            return ("restore_backup", None, "")
        return ("write", rem_bytes, "")
    else:
        after_clean = after

    remainder = before + after_clean
    if not existed_before and remainder == "":
        return ("delete", None, "")

    # If stripping markers yields the exact original backup bytes, use restore_backup!
    rem_bytes = remainder.encode("utf-8", errors="surrogateescape")
    if existed_before and backup_file.is_file() and rem_bytes == backup_file.read_bytes():
        return ("restore_backup", None, "")
    return ("write", rem_bytes, "")


def cmd_uninstall(args: argparse.Namespace) -> int:
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
    if not check_profile_not_in_use(prof_dir, prog):
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

    ok_bak, bak_meta, bak_err = verify_backup(pstate_dir)
    if not ok_bak:
        return die(prog, f"refusing to restore from damaged backup ({bak_err}); nothing was changed")

    completed_steps: list[str] = list(journal.get("completed_steps", [])) if phase == "uninstalling" else []
    interrupted_install = phase == "installing"

    chrome_dir = prof_dir / "chrome"
    plat_dir = chrome_dir / "platinum"
    uc_file = chrome_dir / "userChrome.css"
    ujs_file = prof_dir / "user.js"
    pjs_file = prof_dir / "prefs.js"
    bak_dir = pstate_dir / "backup"
    displaced_plat = pstate_dir / "displaced" / "platinum"

    # Pre-validate all remaining steps BEFORE mutating anything so a conflict stops cleanly!
    if "platinum" not in completed_steps and not interrupted_install:
        ok_plat, reason = check_platinum_dir_intact(plat_dir, state.get("platinum_sums", {}))
        if not ok_plat:
            return die(prog, f"conflict in {plat_dir} ({reason}); nothing was overwritten")

    uc_action, uc_new_bytes = ("noop", None)
    if "userChrome" not in completed_steps:
        if interrupted_install:
            uc_action = "restore_backup" if bak_meta.get("userChrome_existed") else "delete"
        else:
            uc_action, uc_new_bytes, uc_err = plan_marker_removal(
                uc_file,
                bool(bak_meta.get("userChrome_existed")),
                bak_dir / "chrome" / "userChrome.css",
                state.get("installed_userchrome_block", USERCHROME_BLOCK),
                state.get("untouched_userchrome_sha256"),
            )
            if uc_action == "conflict":
                return die(prog, f"conflict: {uc_err}")

    ujs_action, ujs_new_bytes = ("noop", None)
    if "user_js" not in completed_steps:
        if interrupted_install:
            ujs_action = "restore_backup" if bak_meta.get("user_js_existed") else "delete"
        else:
            ujs_action, ujs_new_bytes, ujs_err = plan_marker_removal(
                ujs_file,
                bool(bak_meta.get("user_js_existed")),
                bak_dir / "user.js",
                state.get("installed_userjs_block"),
                state.get("untouched_userjs_sha256"),
            )
            if ujs_action == "conflict":
                return die(prog, f"conflict: {ujs_err}")

    if dry_run:
        print("Dry run: nothing is changed.")
        print(f"  target profile: {chosen['name']} ({prof_dir})")
        if "platinum" not in completed_steps:
            print(f"  would remove {plat_dir}/")
            if displaced_plat.exists():
                print(f"  would put back displaced {displaced_plat} -> {plat_dir}")
        if "userChrome" not in completed_steps:
            print(f"  would undo {uc_file} ({uc_action})")
        if "user_js" not in completed_steps:
            print(f"  would undo {ujs_file} ({ujs_action})")
        if "prefs_js" not in completed_steps:
            print(f"  would restore managed prefs in {pjs_file}")
        return 0

    clean_profile_temps(prof_dir)

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
        for rel in ("chrome/userChrome.css", "user.js", "prefs.js"):
            fp = prof_dir / rel
            if fp.is_file():
                dst = before_snap / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(fp, dst)
        archive_dir_str = str(cand)

    def save_progress() -> None:
        atomic_write_json(
            jpath,
            {
                "phase": "uninstalling",
                "backup_complete": True,
                "profile_path": str(prof_dir),
                "profile_real": cur_real,
                "profile_parent_real": cur_parent_real,
                "completed_steps": completed_steps,
                "archive_dir": archive_dir_str,
            },
        )

    save_progress()

    # Step 1: Remove chrome/platinum/ & restore any displaced pre-install chrome/platinum
    if "platinum" not in completed_steps:
        if plat_dir.is_dir() and not plat_dir.is_symlink():
            shutil.rmtree(plat_dir)
        elif plat_dir.is_file():
            plat_dir.unlink()
        if displaced_plat.exists():
            chrome_dir.mkdir(parents=True, exist_ok=True)
            os.replace(str(displaced_plat), str(plat_dir))
            fsync_dir(chrome_dir)
        elif interrupted_install and bak_meta.get("foreign_platinum_existed") and (bak_dir / "chrome" / "platinum").exists():
            src_fp = bak_dir / "chrome" / "platinum"
            if src_fp.is_dir():
                shutil.copytree(src_fp, plat_dir, symlinks=False, copy_function=shutil.copy2)
            else:
                shutil.copy2(src_fp, plat_dir)
        completed_steps.append("platinum")
        save_progress()
        maybe_inject_fault("uninstall_platinum")

    # Step 2: Restore or strip marker block in chrome/userChrome.css (+ rmdir chrome/ if created by us & empty)
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

        if not bak_meta.get("chrome_existed") and chrome_dir.is_dir():
            try:
                chrome_dir.rmdir()
            except OSError:
                pass
        elif bak_meta.get("chrome_existed") and chrome_dir.is_dir():
            os.chmod(str(chrome_dir), bak_meta.get("chrome_mode", 0o755))

        completed_steps.append("userChrome")
        save_progress()
        maybe_inject_fault("uninstall_userChrome")

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
        prefs_snap = state.get("prefs_snapshot") or bak_meta.get("prefs_snapshot") or {}
        bak_pjs = bak_dir / "prefs.js"
        if pjs_file.is_file():
            pre_sha = bak_meta.get("prefs_js_sha256")
            if pre_sha and sha256_file(pjs_file) == pre_sha:
                # prefs.js was never touched (e.g. Firefox was not launched while installed):
                # leave it completely untouched so mtime, permissions, and bytes are preserved!
                pass
            elif not bak_meta.get("prefs_js_existed"):
                cur_text = pjs_file.read_text(encoding="utf-8", errors="surrogateescape")
                restored_bytes = restore_prefs_in_text(cur_text, None, prefs_snap)
                cur_mode = stat.S_IMODE(pjs_file.stat().st_mode)
                atomic_write_bytes(pjs_file, restored_bytes, cur_mode)
            else:
                bak_bytes = bak_pjs.read_bytes() if bak_pjs.is_file() else None
                cur_text = pjs_file.read_text(encoding="utf-8", errors="surrogateescape")
                restored_bytes = restore_prefs_in_text(cur_text, bak_bytes, prefs_snap)
                if bak_bytes is not None and restored_bytes == bak_bytes and bak_pjs.is_file():
                    tmp = prof_dir / f".macos9-ff-tmp.{secrets.token_hex(6)}"
                    shutil.copy2(bak_pjs, tmp)
                    os.chmod(str(tmp), bak_meta.get("prefs_js_mode", 0o600))
                    os.replace(str(tmp), str(pjs_file))
                    fsync_dir(prof_dir)
                else:
                    cur_mode = stat.S_IMODE(pjs_file.stat().st_mode)
                    atomic_write_bytes(pjs_file, restored_bytes, cur_mode)
        elif bak_meta.get("prefs_js_existed") and bak_pjs.is_file():
            tmp = prof_dir / f".macos9-ff-tmp.{secrets.token_hex(6)}"
            shutil.copy2(bak_pjs, tmp)
            os.chmod(str(tmp), bak_meta.get("prefs_js_mode", 0o600))
            os.replace(str(tmp), str(pjs_file))
            fsync_dir(prof_dir)

        completed_steps.append("prefs_js")
        save_progress()

    # Step 5: Archive backup into $archive_dir/restored-backup and retire $pstate_dir cleanly.
    archive_dir = pathlib.Path(archive_dir_str)
    if bak_dir.is_dir():
        shutil.move(str(bak_dir), str(archive_dir / "restored-backup"))
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
    if args.cmd == "install":
        return cmd_install(args)
    if args.cmd == "uninstall":
        return cmd_uninstall(args)
    return 2


if __name__ == "__main__":
    sys.exit(main())
