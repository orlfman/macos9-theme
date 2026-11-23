#!/usr/bin/env python3
"""Durable KDE + GTK icon-selection transaction and unified dependency checker.

Implements one small durable transaction record ($state/icon-adoption, v3) that
records captured KDE and GTK icon preferences, intended first-install selection
values, and transaction phase (`captured`, `selecting`, `selected`, `skipped`,
`restoring`, `restored`) plus `restore_decision`. Install, retry, and uninstall
all resume or roll back from this single record (AUDIT.md #110, #113, #114,
#115, #117, #124, #126, #127, #128, #129, #130, #131, #133).

Preserves existing file permissions and POSIX ACLs when updating config files
(e.g. 0600 GTK settings remain 0600), and creates new settings files with 0600.

SPDX-License-Identifier: BSD-2-Clause
"""
from __future__ import annotations

import base64
import configparser
import errno
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

MANAGED_ICON_IDS = ("WhiteSur-lavender", "WhiteSur-lavender-light", "WhiteSur-lavender-dark")
ICON_BASE_ID = "WhiteSur-lavender"

GTK2_RE = re.compile(r'^\s*gtk-icon-theme-name\s*=\s*"([^"]*)"\s*$')
XSET_RE = re.compile(r'^\s*Net/IconThemeName\s+"([^"]*)"\s*$')

ACL_XATTRS = ("system.posix_acl_access", "system.posix_acl_default")


def die(msg: str) -> None:
    print(f"icon_prefs: {msg}", file=sys.stderr)
    raise SystemExit(1)


# ---------------------------------------------------------------------------
# Mode & POSIX ACL preservation + atomic fsynced writes (#131)
# ---------------------------------------------------------------------------

def capture_file_perms(path: Path | None) -> tuple[int | None, dict[str, bytes]]:
    """Capture permission bits and POSIX ACL xattrs from an existing regular file."""
    if path is None or not os.path.lexists(path) or path.is_symlink() or not path.is_file():
        return (None, {})
    st = os.lstat(path)
    mode = stat.S_IMODE(st.st_mode)
    acls: dict[str, bytes] = {}
    if hasattr(os, "getxattr"):
        for attr in ACL_XATTRS:
            try:
                acls[attr] = os.getxattr(path, attr, follow_symlinks=False)
            except OSError:
                pass
    return (mode, acls)


def apply_file_perms(path: Path, mode: int | None, acls: dict[str, bytes], default_mode: int = 0o600) -> None:
    os.chmod(path, mode if mode is not None else default_mode)
    if hasattr(os, "setxattr"):
        for attr, val in acls.items():
            try:
                os.setxattr(path, attr, val, follow_symlinks=False)
            except OSError as exc:
                if exc.errno not in (errno.ENOTSUP, errno.EOPNOTSUPP, errno.EPERM):
                    raise
    if not acls and hasattr(os, "removexattr"):
        for attr in ACL_XATTRS:
            try:
                os.removexattr(path, attr, follow_symlinks=False)
            except OSError:
                pass


def serialize_perms(path: Path | None) -> dict[str, Any]:
    mode, acls = capture_file_perms(path)
    return {
        "mode": mode,
        "acls": {k: base64.b64encode(v).decode("ascii") for k, v in acls.items()},
    }


def deserialize_perms(st: dict[str, Any] | None) -> tuple[int | None, dict[str, bytes]]:
    if not isinstance(st, dict):
        return (None, {})
    mode = st.get("mode")
    raw_acls = st.get("acls")
    acls: dict[str, bytes] = {}
    if isinstance(raw_acls, dict):
        for k, v in raw_acls.items():
            if isinstance(k, str) and isinstance(v, str):
                acls[k] = base64.b64decode(v)
    return (int(mode) if mode is not None else None, acls)


def perms_differ(actual: tuple[int | None, dict[str, bytes]], expected: tuple[int | None, dict[str, bytes]]) -> bool:
    if expected[0] is None:
        return False
    return actual[0] != expected[0] or actual[1] != expected[1]


def atomic_write_text(
    dest: Path,
    text: str,
    *,
    default_mode: int = 0o600,
    source_perms: tuple[int | None, dict[str, bytes]] | None = None,
    fsync: bool = False,
) -> None:
    """Atomically write text to dest, preserving existing permissions and ACLs (#131)."""
    if dest.is_symlink():
        die(f"refusing to write through symbolic link: {dest}")
    if source_perms is not None:
        mode, acls = source_perms
    else:
        mode, acls = capture_file_perms(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=f".{dest.name}.tmp.", dir=dest.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            if fsync:
                fh.flush()
                os.fsync(fh.fileno())
        apply_file_perms(tmp_path, mode, acls, default_mode=default_mode)
        os.replace(tmp_path, dest)
    except BaseException:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


# ---------------------------------------------------------------------------
# KDE INI helpers (uses kreadconfig6 / kwriteconfig6, preserving exact key
# presence and existing file modes/ACLs)
# ---------------------------------------------------------------------------

def kde_key_state(path: Path | None, group: str, key: str) -> dict[str, Any]:
    if path is None or not os.path.lexists(path):
        return {"file_exists": False, "present": False, "value": ""}
    if path.is_symlink() or not path.is_file():
        die(f"cannot read non-regular KDE config file: {path}")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        die(f"cannot read {path}: {exc}")

    in_group = False
    present = False
    parsed_val = ""
    hdr = f"[{group}]"
    for raw in lines:
        s = raw.strip()
        if s.startswith("[") and s.endswith("]"):
            in_group = s == hdr
            continue
        if in_group and "=" in raw and not s.startswith("#") and not s.startswith(";"):
            k, _, v = raw.partition("=")
            if k.strip() == key:
                present = True
                parsed_val = v.strip()

    if not shutil.which("kreadconfig6"):
        die("kreadconfig6 is required to read KDE icon settings (Arch package: kconfig)")
    r = subprocess.run(
        ["kreadconfig6", "--file", str(path), "--group", group, "--key", key],
        text=True,
        capture_output=True,
        check=False,
    )
    if r.returncode != 0:
        die(f"kreadconfig6 failed on {path}: {r.stderr.strip()}")
    val = r.stdout.rstrip("\n")
    if present:
        parsed_val = val

    return {"file_exists": True, "present": present, "value": parsed_val}


def kde_set_key(path: Path, group: str, key: str, value: str, *, new_mode: int = 0o600) -> None:
    if path.is_symlink():
        die(f"refusing to write through symbolic link: {path}")
    if not shutil.which("kwriteconfig6"):
        die("kwriteconfig6 is required to update KDE icon settings (Arch package: kconfig)")
    existed = path.is_file()
    perms = capture_file_perms(path) if existed else (None, {})
    path.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        ["kwriteconfig6", "--file", str(path), "--group", group, "--key", key, value],
        text=True,
        capture_output=True,
        check=False,
    )
    if r.returncode != 0:
        die(f"kwriteconfig6 failed on {path}: {r.stderr.strip()}")
    if path.is_file() and not path.is_symlink():
        apply_file_perms(path, perms[0], perms[1], default_mode=new_mode)


def kde_delete_key(path: Path, group: str, key: str, *, remove_if_empty_file: bool = False) -> None:
    if not os.path.lexists(path):
        return
    if path.is_symlink() or not path.is_file():
        return
    if not shutil.which("kwriteconfig6"):
        die("kwriteconfig6 is required to update KDE icon settings (Arch package: kconfig)")
    perms = capture_file_perms(path)
    r = subprocess.run(
        ["kwriteconfig6", "--file", str(path), "--group", group, "--key", key, "--delete"],
        text=True,
        capture_output=True,
        check=False,
    )
    if r.returncode != 0:
        die(f"kwriteconfig6 --delete failed on {path}: {r.stderr.strip()}")
    if path.is_file() and not path.is_symlink():
        if remove_if_empty_file:
            nonempty = [ln.strip() for ln in path.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
            if not nonempty:
                path.unlink(missing_ok=True)
                return
        apply_file_perms(path, perms[0], perms[1], default_mode=0o600)


# ---------------------------------------------------------------------------
# Line-preserving GTK INI / gtkrc-2.0 / xsettingsd editors (mode-preserving)
# ---------------------------------------------------------------------------

def ini_read_key(path: Path | None, section: str, key: str) -> dict[str, Any]:
    if path is None or not os.path.lexists(path) or path.is_symlink() or not path.is_file():
        return {"file_exists": False, "present": False, "value": ""}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    in_sec = False
    present = False
    val = ""
    hdr = f"[{section}]"
    for raw in lines:
        s = raw.strip()
        if s.startswith("[") and s.endswith("]"):
            in_sec = s == hdr
            continue
        if in_sec and "=" in raw and not s.startswith("#") and not s.startswith(";"):
            k, _, v = raw.partition("=")
            if k.strip() == key:
                present = True
                val = v.strip()
    return {"file_exists": True, "present": present, "value": val}


def ini_set_key(path: Path, section: str, key: str, value: str, *, default_mode: int = 0o600) -> None:
    if path.is_symlink():
        die(f"refusing to write through symbolic link: {path}")
    hdr = f"[{section}]"
    new_line = f"{key}={value}"
    if not path.is_file():
        atomic_write_text(path, f"{hdr}\n{new_line}\n", default_mode=default_mode)
        return
    perms = capture_file_perms(path)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    out: list[str] = []
    in_sec = False
    found_sec = False
    replaced = False
    for raw in lines:
        s = raw.strip()
        if s.startswith("[") and s.endswith("]"):
            if in_sec and not replaced:
                out.append(new_line)
                replaced = True
            in_sec = s == hdr
            if in_sec:
                found_sec = True
            out.append(raw)
            continue
        if in_sec and "=" in raw and not s.startswith("#") and not s.startswith(";"):
            k, _, _ = raw.partition("=")
            if k.strip() == key:
                if not replaced:
                    out.append(new_line)
                    replaced = True
                continue
        out.append(raw)
    if in_sec and not replaced:
        out.append(new_line)
    elif not found_sec:
        if out and out[-1] != "":
            out.append("")
        out.append(hdr)
        out.append(new_line)
    atomic_write_text(path, "\n".join(out) + "\n", default_mode=default_mode, source_perms=perms)


def ini_delete_key(path: Path, section: str, key: str, *, remove_if_empty_section: bool = False) -> bool:
    """Delete key from INI file. Returns True if the file itself was unlinked."""
    if not os.path.lexists(path) or path.is_symlink() or not path.is_file():
        return False
    perms = capture_file_perms(path)
    hdr = f"[{section}]"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    out: list[str] = []
    in_sec = False
    for raw in lines:
        s = raw.strip()
        if s.startswith("[") and s.endswith("]"):
            in_sec = s == hdr
            out.append(raw)
            continue
        if in_sec and "=" in raw and not s.startswith("#") and not s.startswith(";"):
            k, _, _ = raw.partition("=")
            if k.strip() == key:
                continue
        out.append(raw)
    if remove_if_empty_section:
        nonempty = [ln.strip() for ln in out if ln.strip()]
        if not nonempty or nonempty == [hdr]:
            path.unlink(missing_ok=True)
            return True
    atomic_write_text(path, "\n".join(out) + "\n", source_perms=perms)
    return False


def line_read_key(path: Path | None, pattern: re.Pattern[str]) -> dict[str, Any]:
    if path is None or not os.path.lexists(path) or path.is_symlink() or not path.is_file():
        return {"file_exists": False, "present": False, "value": ""}
    present = False
    val = ""
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = pattern.match(raw)
        if m:
            present = True
            val = m.group(1)
    return {"file_exists": True, "present": present, "value": val}


def line_set_key(
    path: Path,
    pattern: re.Pattern[str],
    formatted: str,
    *,
    create_if_missing: bool = False,
    default_mode: int = 0o600,
) -> None:
    if path.is_symlink():
        die(f"refusing to write through symbolic link: {path}")
    if not path.is_file():
        if not create_if_missing:
            return
        atomic_write_text(path, formatted + "\n", default_mode=default_mode)
        return
    perms = capture_file_perms(path)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    out: list[str] = []
    replaced = False
    for raw in lines:
        if pattern.match(raw):
            if not replaced:
                out.append(formatted)
                replaced = True
            continue
        out.append(raw)
    if not replaced:
        out.append(formatted)
    atomic_write_text(path, "\n".join(out) + "\n", default_mode=default_mode, source_perms=perms)


def line_delete_key(path: Path, pattern: re.Pattern[str], *, remove_if_empty: bool = False) -> bool:
    """Delete matching line. Returns True if file itself was unlinked."""
    if not os.path.lexists(path) or path.is_symlink() or not path.is_file():
        return False
    perms = capture_file_perms(path)
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    out = [raw for raw in lines if not pattern.match(raw)]
    if remove_if_empty and not [ln for ln in out if ln.strip()]:
        path.unlink(missing_ok=True)
        return True
    atomic_write_text(path, "\n".join(out) + "\n", source_perms=perms)
    return False


# ---------------------------------------------------------------------------
# Unified theme dependency & independence checker (#115, #126, #127)
# ---------------------------------------------------------------------------

def required_ids_for(theme: str) -> list[str]:
    if theme == ICON_BASE_ID:
        return [ICON_BASE_ID]
    if theme in ("WhiteSur-lavender-light", "WhiteSur-lavender-dark"):
        return [theme, ICON_BASE_ID]
    return [theme]


def path_resolves_inside_any(p: Path, forbidden_roots: list[Path]) -> bool:
    try:
        resolved = p.resolve(strict=True)
    except OSError:
        return True
    for root in forbidden_roots:
        if resolved == root or resolved.is_relative_to(root):
            return True
    return False


def _index_directories(idx_path: Path) -> tuple[list[str], list[str]] | None:
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        cp.read(idx_path, encoding="utf-8")
    except (OSError, configparser.Error):
        return None
    if "Icon Theme" not in cp:
        return None
    dirs: list[str] = []
    scaled: list[str] = []
    seen: set[str] = set()
    for part in cp["Icon Theme"].get("Directories", "").split(","):
        rel_d = part.strip().strip("/")
        if rel_d and rel_d not in seen:
            seen.add(rel_d)
            dirs.append(rel_d)
    for part in cp["Icon Theme"].get("ScaledDirectories", "").split(","):
        rel_d = part.strip().strip("/")
        if rel_d and rel_d not in seen:
            seen.add(rel_d)
            scaled.append(rel_d)
    return (dirs, scaled)


def cand_is_independent_and_complete(
    cand: Path,
    forbidden_roots: list[Path],
    *,
    require_complete_artwork: bool = False,
    reference_index: Path | None = None,
) -> bool:
    """Return True iff candidate theme dir, its index.theme, advertised
    directories, and icon symlinks exist and do not resolve inside any
    forbidden_roots (#127).

    When `require_complete_artwork=True` (authorizing deletion of managed
    packages), every directory in `Directories` (plus every directory in
    `reference_index`'s `Directories` when given) MUST actually exist, resolve
    outside `forbidden_roots`, and supply readable .svg/.png artwork resolving
    outside `forbidden_roots`.
    """
    idx = cand / "index.theme"
    if not os.path.lexists(cand) or not os.path.lexists(idx):
        return False
    if path_resolves_inside_any(cand, forbidden_roots) or path_resolves_inside_any(idx, forbidden_roots):
        return False
    if not cand.is_dir() or not idx.is_file() or not os.access(idx, os.R_OK):
        return False

    # If no forbidden roots exist and strict completeness isn't requested, index readability suffices.
    if not forbidden_roots and not require_complete_artwork:
        return True

    parsed = _index_directories(idx)
    if parsed is None:
        return False
    req_dirs, scaled_dirs = parsed
    if require_complete_artwork and not req_dirs:
        return False

    # Also require every directory advertised by the managed package being replaced (#127).
    extra_req_dirs: list[str] = []
    if require_complete_artwork and reference_index is not None and reference_index.is_file():
        ref_parsed = _index_directories(reference_index)
        if ref_parsed is not None:
            req_set = set(req_dirs)
            for rd in ref_parsed[0]:
                if rd not in req_set:
                    extra_req_dirs.append(rd)

    all_required = req_dirs + extra_req_dirs
    advertised: list[str] = list(all_required) + list(scaled_dirs)
    seen_dirs = set(advertised)
    for extra in ("places", "status/32"):
        if extra not in seen_dirs and os.path.lexists(cand / extra):
            advertised.append(extra)
    required_set = set(all_required)

    checked_prefixes: set[Path] = set()
    for rel_d in advertised:
        # Check every prefix component of cand / rel_d (e.g. apps, apps/scalable).
        cur = cand
        for part in Path(rel_d).parts:
            cur = cur / part
            if cur in checked_prefixes:
                continue
            checked_prefixes.add(cur)
            if os.path.lexists(cur):
                if path_resolves_inside_any(cur, forbidden_roots):
                    return False
        dpath = cand / rel_d
        if not os.path.lexists(dpath) or not dpath.is_dir():
            if require_complete_artwork and rel_d in required_set:
                return False
            continue
        has_valid_artwork = False
        try:
            with os.scandir(dpath) as it:
                for entry in it:
                    is_icon_name = entry.name.lower().endswith((".svg", ".png"))
                    if entry.is_symlink():
                        try:
                            target = os.readlink(entry.path)
                        except OSError:
                            return False
                        if "/" in target or target in (".", ".."):
                            try:
                                resolved = Path(entry.path).resolve(strict=True)
                            except OSError:
                                continue
                            if any(resolved == r or resolved.is_relative_to(r) for r in forbidden_roots):
                                return False
                            if is_icon_name and resolved.is_file() and os.access(resolved, os.R_OK):
                                has_valid_artwork = True
                        elif is_icon_name and not has_valid_artwork:
                            try:
                                resolved = Path(entry.path).resolve(strict=True)
                            except OSError:
                                continue
                            if (
                                not any(resolved == r or resolved.is_relative_to(r) for r in forbidden_roots)
                                and resolved.is_file()
                                and os.access(resolved, os.R_OK)
                            ):
                                has_valid_artwork = True
                    elif is_icon_name and entry.is_file(follow_symlinks=False):
                        if os.access(entry.path, os.R_OK):
                            has_valid_artwork = True
        except OSError:
            return False
        if require_complete_artwork and rel_d in required_set and not has_valid_artwork:
            return False
    return True


def icon_search_dirs(home: Path, data_icons: Path, xdg_data_dirs: str, *, include_data_icons: bool) -> list[Path]:
    dirs: list[Path] = []
    data_icons_real = Path(os.path.realpath(str(data_icons)))
    if include_data_icons:
        dirs.append(data_icons)
    if (home / ".icons").is_dir():
        dirs.append(home / ".icons")
    for d in (xdg_data_dirs or "/usr/local/share:/usr/share").split(":"):
        if d:
            p = Path(d) / "icons"
            if p.is_dir():
                dirs.append(p)
    if not include_data_icons:
        dirs = [p for p in dirs if Path(os.path.realpath(str(p))) != data_icons_real]
    return dirs


def theme_is_usable(
    theme: str,
    home: Path,
    data_icons: Path,
    xdg_data_dirs: str,
    restorable_ids: set[str],
    removing_ids: set[str],
    *,
    outside_only: bool = False,
) -> bool:
    """Single dependency check used by BOTH restore and removal (#126, #127).

    Returns True iff every required ID of `theme` will survive removal either
    by being restored from $displaced (`restorable_ids`) or by resolving to a
    complete, independent copy outside all `removing_ids` (excluding
    `restorable_ids`). When `outside_only=True`, `$data/icons` itself is not
    counted (used when deciding whether an independent outside copy authorizes
    removing managed directories).
    """
    if not theme:
        return False
    forbidden_roots = [
        Path(os.path.realpath(str(data_icons / tid)))
        for tid in removing_ids
        if tid not in restorable_ids
    ]
    search_dirs = icon_search_dirs(home, data_icons, xdg_data_dirs, include_data_icons=not outside_only)
    for req in required_ids_for(theme):
        if not outside_only and req in restorable_ids:
            continue
        found_req = False
        ref_idx = (data_icons / req / "index.theme") if (outside_only and req in MANAGED_ICON_IDS) else None
        for sdir in search_dirs:
            cand = sdir / req
            if cand_is_independent_and_complete(
                cand,
                forbidden_roots,
                require_complete_artwork=outside_only,
                reference_index=ref_idx,
            ):
                found_req = True
                break
        if not found_req:
            return False
    return True


def fallback_usable_theme(
    home: Path, data_icons: Path, xdg_data_dirs: str, restorable_ids: set[str], removing_ids: set[str]
) -> str:
    for cand in ("breeze", "Adwaita", "hicolor"):
        if theme_is_usable(cand, home, data_icons, xdg_data_dirs, restorable_ids, removing_ids):
            return cand
    return ""


# ---------------------------------------------------------------------------
# Durable transaction loading / saving (v3 JSON; reads v1 & v2 cleanly)
# ---------------------------------------------------------------------------

def load_adoption(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    if raw.lstrip().startswith("{"):
        data = json.loads(raw)
        if data.get("version") == 3:
            return data
        # Upgrade v2 in memory
        auto_sel = bool(data.get("auto_selected"))
        return {
            "version": 3,
            "phase": "selected" if auto_sel else "skipped",
            "backup_predated": bool(data.get("backup_predated")),
            "restore_decision": "none",
            "intended": None,
            "captured": {
                "kde": data.get("kde", {}),
                "gtk": data.get("gtk"),
            },
            "preexisting": data.get("preexisting", {}),
        }
    # Upgrade v1 tab-separated in memory
    kv: dict[str, str] = {}
    pre: dict[str, str] = {}
    for line in raw.splitlines():
        parts = line.split("\t")
        if len(parts) == 2:
            kv[parts[0]] = parts[1]
        elif len(parts) == 3 and parts[0] == "preexisting":
            pre[parts[1]] = parts[2]
    kg_val = kv.get("kdeglobals_theme", "")
    kd_val = kv.get("kdedefaults_theme", "")
    return {
        "version": 3,
        "phase": "skipped",
        "backup_predated": kv.get("backup_predated") == "1",
        "restore_decision": "none",
        "intended": None,
        "captured": {
            "kde": {
                "effective_source": kv.get("effective_source", "none"),
                "effective_theme": kv.get("effective_theme", ""),
                "kdeglobals": {"file_exists": bool(kg_val), "present": bool(kg_val), "value": kg_val},
                "kdedefaults": {"file_exists": bool(kd_val), "present": bool(kd_val), "value": kd_val},
            },
            "gtk": None,
        },
        "preexisting": pre,
    }


def save_adoption(path: Path, data: dict[str, Any]) -> None:
    atomic_write_text(path, json.dumps(data, indent=2) + "\n", default_mode=0o600, fsync=True)


def make_intended_spec(theme: str) -> dict[str, Any]:
    return {
        "theme": theme,
        "kde": {
            "kdeglobals": {"present": False, "value": ""},
            "kdedefaults": {"present": True, "value": theme},
        },
        "gtk": {
            "gtk3": {"present": True, "value": theme, "only_if_exists": False},
            "gtk4": {"present": True, "value": theme, "only_if_exists": False},
            "gtk2": {"present": True, "value": theme, "only_if_exists": True},
            "xsettingsd": {"present": True, "value": theme, "only_if_exists": True},
        },
    }


def read_all_current_prefs(config_home: Path, home: Path) -> dict[str, Any]:
    kg_path = config_home / "kdeglobals"
    kd_path = config_home / "kdedefaults/kdeglobals"
    gtk3_path = config_home / "gtk-3.0/settings.ini"
    gtk4_path = config_home / "gtk-4.0/settings.ini"
    gtk2_path = home / ".gtkrc-2.0"
    xset_path = config_home / "xsettingsd/xsettingsd.conf"

    kg = {**kde_key_state(kg_path, "Icons", "Theme"), **serialize_perms(kg_path)}
    kd = {**kde_key_state(kd_path, "Icons", "Theme"), **serialize_perms(kd_path)}
    if kg["present"] and kg["value"]:
        eff_src, eff_theme = "kdeglobals", kg["value"]
    elif kd["present"] and kd["value"]:
        eff_src, eff_theme = "kdedefaults", kd["value"]
    else:
        eff_src, eff_theme = "none", ""
    return {
        "kde": {
            "effective_source": eff_src,
            "effective_theme": eff_theme,
            "kdeglobals": kg,
            "kdedefaults": kd,
        },
        "gtk": {
            "gtk3": {**ini_read_key(gtk3_path, "Settings", "gtk-icon-theme-name"), **serialize_perms(gtk3_path)},
            "gtk4": {**ini_read_key(gtk4_path, "Settings", "gtk-icon-theme-name"), **serialize_perms(gtk4_path)},
            "gtk2": {**line_read_key(gtk2_path, GTK2_RE), **serialize_perms(gtk2_path)},
            "xsettingsd": {**line_read_key(xset_path, XSET_RE), **serialize_perms(xset_path)},
        },
    }


def state_matches(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    return bool(actual.get("present")) == bool(expected.get("present")) and str(actual.get("value", "")) == str(
        expected.get("value", "")
    )


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_effective_kde(kg_arg: str, kd_arg: str) -> None:
    kg_path = Path(kg_arg) if kg_arg else None
    kd_path = (Path(kd_arg) / "kdeglobals") if kd_arg else None
    kg = kde_key_state(kg_path, "Icons", "Theme")
    if kg["present"] and kg["value"]:
        print(f"kdeglobals\t{kg['value']}")
        return
    kd = kde_key_state(kd_path, "Icons", "Theme")
    if kd["present"] and kd["value"]:
        print(f"kdedefaults\t{kd['value']}")
        return
    print("none\t")


def cmd_capture(args: list[str]) -> None:
    config_home = Path(args[0])
    home = Path(args[1])
    out_json = Path(args[2])
    backup_predated = args[3] == "1"
    intend_theme = args[4]
    pre_states = {
        "WhiteSur-lavender": args[5],
        "WhiteSur-lavender-light": args[6],
        "WhiteSur-lavender-dark": args[7],
    }

    captured = read_all_current_prefs(config_home, home)
    data: dict[str, Any] = {
        "version": 3,
        "phase": "captured" if intend_theme else "skipped",
        "backup_predated": backup_predated,
        "restore_decision": "none",
        "intended": make_intended_spec(intend_theme) if intend_theme else None,
        "captured": captured,
        "preexisting": pre_states,
    }
    save_adoption(out_json, data)


def cmd_apply_tx(args: list[str]) -> None:
    config_home = Path(args[0])
    home = Path(args[1])
    adoption_path = Path(args[2])
    dry_run = False
    active_lnf: str | None = None
    lnf_id: str | None = None
    i = 3
    while i < len(args):
        if args[i] == "--dry-run":
            dry_run = True
            i += 1
        elif args[i] == "--active-lnf":
            active_lnf = args[i + 1]
            i += 2
        elif args[i] == "--lnf-id":
            lnf_id = args[i + 1]
            i += 2
        else:
            die(f"unknown apply-tx flag: {args[i]}")

    if not os.path.lexists(adoption_path):
        return
    data = load_adoption(adoption_path)
    phase = data.get("phase")
    intended = data.get("intended")
    if phase not in ("captured", "selecting") or not isinstance(intended, dict):
        return
    theme = str(intended.get("theme", ""))
    if not theme:
        return

    # #141: Re-evaluate the active global theme before resuming a pending selection.
    # If the user switched away from Platinum while the selection was pending, cancel
    # the stale intent, roll back only transaction-owned partial writes (preserving any
    # later user choices), and mark phase="skipped".
    if active_lnf is not None and lnf_id is not None and active_lnf != lnf_id:
        if dry_run:
            print("PLAN\tcancel stale pending icon selection (Platinum is no longer the active global theme)")
            return
        kd_dir = config_home / "kdedefaults"
        kd_file = kd_dir / "kdeglobals"
        kg_file = config_home / "kdeglobals"
        gtk3_file = config_home / "gtk-3.0/settings.ini"
        gtk4_file = config_home / "gtk-4.0/settings.ini"
        gtk2_file = home / ".gtkrc-2.0"
        xset_file = config_home / "xsettingsd/xsettingsd.conf"
        if phase == "selecting":
            cap = data.get("captured", {})
            cap_kde = cap.get("kde", {})
            cap_gtk = cap.get("gtk") or {}
            int_kde = intended["kde"]
            int_gtk = intended["gtk"]

            # Roll back KDE ONLY if currently still holding our partial intended WhiteSur-lavender.
            if not kg_file.is_symlink() and not kd_dir.is_symlink() and not kd_file.is_symlink():
                cur_kg = kde_key_state(kg_file, "Icons", "Theme")
                cur_kd = kde_key_state(kd_file, "Icons", "Theme")
                kg_cap = cap_kde.get("kdeglobals", {"file_exists": False, "present": False, "value": ""})
                kd_cap = cap_kde.get("kdedefaults", {"file_exists": False, "present": False, "value": ""})
                if state_matches(cur_kd, int_kde["kdedefaults"]) and (
                    state_matches(cur_kg, int_kde["kdeglobals"]) or state_matches(cur_kg, kg_cap)
                ):
                    if kg_cap.get("present"):
                        kde_set_key(kg_file, "Icons", "Theme", str(kg_cap.get("value", "")), new_mode=0o600)
                        apply_file_perms(kg_file, *deserialize_perms(kg_cap))
                    if kd_cap.get("present"):
                        kde_set_key(kd_file, "Icons", "Theme", str(kd_cap.get("value", "")), new_mode=0o600)
                        apply_file_perms(kd_file, *deserialize_perms(kd_cap))
                    else:
                        kde_delete_key(kd_file, "Icons", "Theme", remove_if_empty_file=not kd_cap.get("file_exists"))

            # Roll back each GTK key ONLY if still at our partial intended value.
            for gkey, gpath in (("gtk3", gtk3_file), ("gtk4", gtk4_file)):
                if gpath.is_symlink():
                    continue
                cur_g = ini_read_key(gpath, "Settings", "gtk-icon-theme-name")
                if state_matches(cur_g, int_gtk[gkey]):
                    g_cap = cap_gtk.get(gkey, {"file_exists": False, "present": False, "value": ""})
                    if g_cap.get("present"):
                        ini_set_key(gpath, "Settings", "gtk-icon-theme-name", str(g_cap.get("value", "")), default_mode=0o600)
                        apply_file_perms(gpath, *deserialize_perms(g_cap))
                    else:
                        ini_delete_key(gpath, "Settings", "gtk-icon-theme-name", remove_if_empty_section=not g_cap.get("file_exists"))

            for gkey, gpath, pat, fmt_fn in (
                ("gtk2", gtk2_file, GTK2_RE, lambda v: f'gtk-icon-theme-name="{v}"'),
                ("xsettingsd", xset_file, XSET_RE, lambda v: f'Net/IconThemeName "{v}"'),
            ):
                if not gpath.is_file() or gpath.is_symlink():
                    continue
                cur_l = line_read_key(gpath, pat)
                if state_matches(cur_l, int_gtk[gkey]):
                    g_cap = cap_gtk.get(gkey, {"file_exists": False, "present": False, "value": ""})
                    if g_cap.get("present"):
                        line_set_key(gpath, pat, fmt_fn(str(g_cap.get("value", ""))), create_if_missing=False, default_mode=0o600)
                        apply_file_perms(gpath, *deserialize_perms(g_cap))
                    else:
                        line_delete_key(gpath, pat, remove_if_empty=not g_cap.get("file_exists"))

        data["phase"] = "skipped"
        data["intended"] = None
        save_adoption(adoption_path, data)
        return

    if dry_run:
        print(f"PLAN\tselect {theme} icons for KDE and GTK (Platinum is active; other settings unchanged)")
        return

    # Validate non-symlink targets before touching any file.
    kd_dir = config_home / "kdedefaults"
    kd_file = kd_dir / "kdeglobals"
    kg_file = config_home / "kdeglobals"
    gtk3_file = config_home / "gtk-3.0/settings.ini"
    gtk4_file = config_home / "gtk-4.0/settings.ini"
    gtk2_file = home / ".gtkrc-2.0"
    xset_file = config_home / "xsettingsd/xsettingsd.conf"
    for p in (kd_dir, kd_file, kg_file, gtk3_file, gtk4_file, gtk2_file, xset_file):
        if p.is_symlink():
            die(f"refusing to write through symbolic link: {p}")

    # Persist phase="selecting" before the first write (#128).
    if phase != "selecting":
        data["phase"] = "selecting"
        save_adoption(adoption_path, data)

    cap = data.get("captured", {})
    cap_kde = cap.get("kde", {})
    cap_gtk = cap.get("gtk") or {}
    int_kde = intended["kde"]
    int_gtk = intended["gtk"]

    # 1. KDE keys: apply if currently at captured (or partially transitioned), preserve if user switched elsewhere.
    cur_kg = kde_key_state(kg_file, "Icons", "Theme")
    cur_kd = kde_key_state(kd_file, "Icons", "Theme")
    kg_cap = cap_kde.get("kdeglobals", {"present": False, "value": ""})
    kd_cap = cap_kde.get("kdedefaults", {"present": False, "value": ""})
    kg_int = int_kde["kdeglobals"]
    kd_int = int_kde["kdedefaults"]

    kg_ok_to_finish = state_matches(cur_kg, kg_cap) or state_matches(cur_kg, kg_int)
    kd_ok_to_finish = state_matches(cur_kd, kd_cap) or state_matches(cur_kd, kd_int)
    if kg_ok_to_finish and kd_ok_to_finish:
        if not state_matches(cur_kd, kd_int):
            kde_set_key(kd_file, "Icons", "Theme", kd_int["value"], new_mode=0o600)
        if not state_matches(cur_kg, kg_int):
            kde_delete_key(kg_file, "Icons", "Theme")

    # 2. GTK 3 & GTK 4 (per-key comparison against captured & intended, preserving existing modes/ACLs #131).
    for gkey, gpath in (("gtk3", gtk3_file), ("gtk4", gtk4_file)):
        cur_g = ini_read_key(gpath, "Settings", "gtk-icon-theme-name")
        g_cap = cap_gtk.get(gkey, {"present": False, "value": ""})
        g_int = int_gtk[gkey]
        if state_matches(cur_g, g_int):
            continue
        if state_matches(cur_g, g_cap):
            ini_set_key(gpath, "Settings", "gtk-icon-theme-name", g_int["value"], default_mode=0o600)

    # 3. GTK 2 & xsettingsd (update only if file exists).
    if gtk2_file.is_file():
        cur2 = line_read_key(gtk2_file, GTK2_RE)
        g2_cap = cap_gtk.get("gtk2", {"present": False, "value": ""})
        g2_int = int_gtk["gtk2"]
        if not state_matches(cur2, g2_int) and state_matches(cur2, g2_cap):
            line_set_key(
                gtk2_file,
                GTK2_RE,
                f'gtk-icon-theme-name="{g2_int["value"]}"',
                create_if_missing=False,
                default_mode=0o600,
            )

    if xset_file.is_file():
        curx = line_read_key(xset_file, XSET_RE)
        gx_cap = cap_gtk.get("xsettingsd", {"present": False, "value": ""})
        gx_int = int_gtk["xsettingsd"]
        if not state_matches(curx, gx_int) and state_matches(curx, gx_cap):
            line_set_key(
                xset_file,
                XSET_RE,
                f'Net/IconThemeName "{gx_int["value"]}"',
                create_if_missing=False,
                default_mode=0o600,
            )

    # Mark complete ONLY after every write succeeded (#128).
    data["phase"] = "selected"
    save_adoption(adoption_path, data)
    print(f"SAY\tSelected {theme} icons for KDE and GTK (other Platinum settings unchanged)")


def cmd_read_restore_decision(adoption_path: Path) -> None:
    if not os.path.lexists(adoption_path) or adoption_path.is_symlink():
        print("none")
        return
    data = load_adoption(adoption_path)
    print(str(data.get("restore_decision", "none")))


def cmd_read_tx_status(adoption_path: Path) -> None:
    """Print `<phase>\t<restore_decision>` for install.sh unfinished-undo guard (#140)."""
    if not os.path.lexists(adoption_path) or adoption_path.is_symlink():
        print("none\tnone")
        return
    data = load_adoption(adoption_path)
    print(f"{data.get('phase', 'none')}\t{data.get('restore_decision', 'none')}")


def cmd_begin_restore(adoption_path: Path) -> None:
    if not os.path.lexists(adoption_path) or adoption_path.is_symlink():
        return
    data = load_adoption(adoption_path)
    data["phase"] = "restoring"
    data["restore_decision"] = "restore_backup"
    save_adoption(adoption_path, data)


def cmd_finish_restore(adoption_path: Path) -> None:
    if not os.path.lexists(adoption_path) or adoption_path.is_symlink():
        return
    data = load_adoption(adoption_path)
    data["phase"] = "restored"
    save_adoption(adoption_path, data)


# ---------------------------------------------------------------------------
# Staged backup merge for undo (#124, #129, #130, #131, #133)
# ---------------------------------------------------------------------------

def load_backup_absent(backup_dir: Path | None) -> set[tuple[str, str]]:
    if backup_dir is None:
        return set()
    abs_file = backup_dir / "ABSENT"
    if not abs_file.is_file():
        return set()
    out: set[tuple[str, str]] = set()
    for line in abs_file.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = line.split("\t", 1)
        if len(parts) == 2:
            out.add((parts[0], parts[1]))
    return out


def backup_source_for(
    base: str,
    rel: str,
    live_path: Path,
    backup_dir: Path | None,
    absent_set: set[tuple[str, str]],
) -> Path | None:
    """Return the file/dir path that restoring $backup alone would produce, or None if absent (#133)."""
    if backup_dir is None:
        return live_path if os.path.lexists(live_path) else None
    if (base, rel) in absent_set:
        return None
    bp = backup_dir / base / rel
    if os.path.lexists(bp):
        return bp
    return live_path if os.path.lexists(live_path) else None


def copy_with_perms(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir() and not src.is_symlink():
        shutil.copytree(src, dst, symlinks=True)
        # Preserve directory mode too.
        st = os.lstat(src)
        os.chmod(dst, stat.S_IMODE(st.st_mode))
    else:
        shutil.copy2(src, dst)
        mode, acls = capture_file_perms(src)
        apply_file_perms(dst, mode, acls, default_mode=0o600)


def cmd_prepare_restore(args: list[str]) -> None:
    config_home = Path(args[0])
    home = Path(args[1])
    backup_dir = Path(args[2]) if args[2] else None
    data_icons = Path(args[3])
    xdg_data_dirs = args[4]

    adoption_path: Path | None = None
    stage_dir: Path | None = None
    dry_run = False
    restorable_ids: set[str] = set()
    removing_ids: set[str] = set()

    i = 5
    while i < len(args):
        if args[i] == "--adoption":
            adoption_path = Path(args[i + 1]) if args[i + 1] else None
            i += 2
        elif args[i] == "--stage-dir":
            stage_dir = Path(args[i + 1]) if args[i + 1] else None
            i += 2
        elif args[i] == "--dry-run":
            dry_run = True
            i += 1
        elif args[i] == "--restorable":
            restorable_ids.add(args[i + 1])
            i += 2
        elif args[i] == "--managed-removing":
            removing_ids.add(args[i + 1])
            i += 2
        else:
            die(f"unknown prepare-restore flag: {args[i]}")

    if not dry_run and stage_dir is None:
        die("prepare-restore requires --stage-dir when not in --dry-run")

    absent_set = load_backup_absent(backup_dir)
    data = load_adoption(adoption_path) if (adoption_path and os.path.lexists(adoption_path)) else None
    backup_predated = bool(data.get("backup_predated")) if data else False

    # Inspect what $backup alone would produce (using None for absent files/dirs #133).
    src_kg = backup_source_for("config", "kdeglobals", config_home / "kdeglobals", backup_dir, absent_set)
    src_kd_dir = backup_source_for("config", "kdedefaults", config_home / "kdedefaults", backup_dir, absent_set)
    src_kd_file = (src_kd_dir / "kdeglobals") if (src_kd_dir is not None and (src_kd_dir / "kdeglobals").is_file()) else None

    cur_kg = kde_key_state(src_kg, "Icons", "Theme")
    cur_kd = kde_key_state(src_kd_file, "Icons", "Theme")

    overlay: dict[tuple[str, str], str] = {}  # (base, rel) -> "file" | "dir" | "absent"

    def stage_path(base: str, rel: str) -> Path:
        assert stage_dir is not None
        return stage_dir / base / rel

    def ensure_staged(base: str, rel: str, src: Path | None) -> Path:
        dst = stage_path(base, rel)
        if not os.path.lexists(dst) and src is not None and os.path.lexists(src):
            copy_with_perms(src, dst)
        return dst

    def resolve_usable(val: str, label: str, *, allow_fallback: bool = True) -> tuple[bool, str]:
        if not val:
            return (False, "")
        if theme_is_usable(val, home, data_icons, xdg_data_dirs, restorable_ids, removing_ids):
            return (True, val)
        if not allow_fallback:
            return (False, "")
        fb = fallback_usable_theme(home, data_icons, xdg_data_dirs, restorable_ids, removing_ids)
        print(f"WARN\tpre-adoption {label} icon theme '{val}' is not installed; falling back to '{fb or 'default'}'")
        return (bool(fb), fb)

    if backup_predated and data is not None:
        cap = data.get("captured", {})
        ad_kde = cap.get("kde", {})
        ad_kg = ad_kde.get("kdeglobals", {"file_exists": False, "present": False, "value": ""})
        ad_kd = ad_kde.get("kdedefaults", {"file_exists": False, "present": False, "value": ""})
        ad_src = ad_kde.get("effective_source", "none")

        # #129: Compute desired presence/value for BOTH KDE layers independently!
        # Explicit kdeglobals layer:
        if ad_kg.get("present"):
            ok_kg, val_kg = resolve_usable(str(ad_kg.get("value", "")), "KDE")
            want_kg_present = ok_kg
            want_kg_val = val_kg
        else:
            want_kg_present = False
            want_kg_val = ""

        # Inherited kdedefaults/kdeglobals layer:
        if ad_kd.get("present"):
            # If kdedefaults was the effective source, fall back to a usable theme if missing;
            # if kdeglobals was explicit and kdedefaults held an unusable theme (e.g. old Platinum WhiteSur),
            # drop the unusable inherited key rather than exposing a missing fallback.
            ok_kd, val_kd = resolve_usable(
                str(ad_kd.get("value", "")),
                "inherited KDE",
                allow_fallback=(ad_src == "kdedefaults" or not want_kg_present),
            )
            want_kd_present = ok_kd
            want_kd_val = val_kd
        else:
            want_kd_present = False
            want_kd_val = ""

        # If explicit kdeglobals had a missing theme and fell back to fb, keep fb inherited if
        # there was no explicit usable fallback desired (Wait: keep explicit if pre-adoption was explicit,
        # unless fallback was needed — if pre-adoption explicit theme was missing, put fallback in kdedefaults
        # or kdeglobals? Actually putting fallback in kdeglobals or kdedefaults both work; keeping kdedefaults
        # clean avoids leaving a broken override, and let's ensure want_kg/want_kd match clearly).
        if ad_kg.get("present") and not theme_is_usable(
            str(ad_kg.get("value", "")), home, data_icons, xdg_data_dirs, restorable_ids, removing_ids
        ):
            want_kg_present = False
            want_kg_val = ""
            if not want_kd_present:
                fb = fallback_usable_theme(home, data_icons, xdg_data_dirs, restorable_ids, removing_ids)
                want_kd_present = bool(fb)
                want_kd_val = fb

        def apply_captured_perms_if_needed(
            base: str,
            rel: str,
            src_p: Path | None,
            st_dict: dict[str, Any],
            *,
            in_dir_rel: str | None = None,
            dir_src: Path | None = None,
        ) -> None:
            """Apply captured pre-adoption mode & POSIX ACLs to the staged copy,
            including when the backed-up icon key already matches (#131)."""
            if dry_run or not st_dict.get("file_exists"):
                return
            cap_perms = deserialize_perms(st_dict)
            if cap_perms[0] is None:
                return
            if in_dir_rel is not None:
                ov_key = (base, in_dir_rel)
                if ov_key in overlay:
                    if overlay[ov_key] == "absent":
                        return
                    target_f = stage_path(base, rel)
                    if target_f.is_file() and not target_f.is_symlink():
                        apply_file_perms(target_f, cap_perms[0], cap_perms[1], default_mode=0o600)
                elif src_p is not None and src_p.is_file() and not src_p.is_symlink():
                    if perms_differ(capture_file_perms(src_p), cap_perms):
                        skd_dir = ensure_staged(base, in_dir_rel, dir_src)
                        target_f = stage_path(base, rel)
                        if target_f.is_file() and not target_f.is_symlink():
                            apply_file_perms(target_f, cap_perms[0], cap_perms[1], default_mode=0o600)
                            overlay[ov_key] = "dir"
            else:
                ov_key = (base, rel)
                if ov_key in overlay:
                    if overlay[ov_key] == "absent":
                        return
                    target_f = stage_path(base, rel)
                    if target_f.is_file() and not target_f.is_symlink():
                        apply_file_perms(target_f, cap_perms[0], cap_perms[1], default_mode=0o600)
                elif src_p is not None and src_p.is_file() and not src_p.is_symlink():
                    if perms_differ(capture_file_perms(src_p), cap_perms):
                        sp = ensure_staged(base, rel, src_p)
                        apply_file_perms(sp, cap_perms[0], cap_perms[1], default_mode=0o600)
                        overlay[ov_key] = "file"

        # Stage merged kdeglobals if it differs from $backup's kdeglobals (or perms differ #131)
        kg_live = config_home / "kdeglobals"
        if not kg_live.is_symlink():
            if want_kg_present:
                if not cur_kg["present"] or cur_kg["value"] != want_kg_val:
                    print(f"PLAN\trestore explicit KDE icon theme ({want_kg_val}) in {kg_live}")
                    if not dry_run:
                        skg = ensure_staged("config", "kdeglobals", src_kg)
                        kde_set_key(skg, "Icons", "Theme", want_kg_val, new_mode=0o600)
                        overlay[("config", "kdeglobals")] = "file"
                        print(f"SAY\tRestored your earlier KDE icon theme ({want_kg_val})")
            else:
                if cur_kg["present"]:
                    print(f"PLAN\tremove explicit KDE icon theme override in {kg_live} (was inherited)")
                    if not dry_run:
                        skg = ensure_staged("config", "kdeglobals", src_kg)
                        kde_delete_key(skg, "Icons", "Theme")
                        overlay[("config", "kdeglobals")] = "file"
            apply_captured_perms_if_needed("config", "kdeglobals", src_kg, ad_kg)

        # Stage merged kdedefaults/ if kdedefaults/kdeglobals differs from $backup's kdedefaults (#129, #131)
        kd_live_dir = config_home / "kdedefaults"
        kd_live_file = kd_live_dir / "kdeglobals"
        if not kd_live_dir.is_symlink() and not kd_live_file.is_symlink():
            if want_kd_present:
                if not cur_kd["present"] or cur_kd["value"] != want_kd_val:
                    print(f"PLAN\trestore inherited KDE icon theme ({want_kd_val}) in {kd_live_file}")
                    if not dry_run:
                        skd_dir = ensure_staged("config", "kdedefaults", src_kd_dir)
                        skd_dir.mkdir(parents=True, exist_ok=True)
                        kde_set_key(skd_dir / "kdeglobals", "Icons", "Theme", want_kd_val, new_mode=0o600)
                        overlay[("config", "kdedefaults")] = "dir"
                        if not want_kg_present:
                            print(f"SAY\tRestored your earlier inherited KDE icon theme ({want_kd_val})")
            else:
                if cur_kd["present"]:
                    print(f"PLAN\tremove stale inherited KDE icon theme ({cur_kd['value']}) in {kd_live_file}")
                    if not dry_run:
                        skd_dir = ensure_staged("config", "kdedefaults", src_kd_dir)
                        kde_delete_key(
                            skd_dir / "kdeglobals",
                            "Icons",
                            "Theme",
                            remove_if_empty_file=(not ad_kd.get("file_exists")),
                        )
                        if skd_dir.is_dir() and not any(skd_dir.iterdir()) and src_kd_dir is None:
                            shutil.rmtree(skd_dir)
                            overlay[("config", "kdedefaults")] = "absent"
                        else:
                            overlay[("config", "kdedefaults")] = "dir"
            apply_captured_perms_if_needed(
                "config", "kdedefaults/kdeglobals", src_kd_file, ad_kd, in_dir_rel="kdedefaults", dir_src=src_kd_dir
            )

        # Stage merged GTK 3, GTK 4, GTK 2, and xsettingsd (#117, #124, #131)
        ad_gtk = cap.get("gtk")
        if isinstance(ad_gtk, dict):
            for gtk_key, rel_ini in (("gtk3", "gtk-3.0/settings.ini"), ("gtk4", "gtk-4.0/settings.ini")):
                st = ad_gtk.get(gtk_key, {})
                live_p = config_home / rel_ini
                if live_p.is_symlink():
                    continue
                src_p = backup_source_for("config", rel_ini, live_p, backup_dir, absent_set)
                cur_g = ini_read_key(src_p, "Settings", "gtk-icon-theme-name")
                if st.get("present"):
                    ok_v, want_v = resolve_usable(str(st.get("value", "")), gtk_key)
                    if ok_v:
                        if not cur_g["present"] or cur_g["value"] != want_v:
                            print(f"PLAN\trestore {gtk_key} icon theme ({want_v}) in {live_p}")
                            if not dry_run:
                                sp = ensure_staged("config", rel_ini, src_p)
                                ini_set_key(sp, "Settings", "gtk-icon-theme-name", want_v, default_mode=0o600)
                                overlay[("config", rel_ini)] = "file"
                    elif cur_g["present"]:
                        print(f"PLAN\tremove missing {gtk_key} icon theme in {live_p}")
                        if not dry_run:
                            sp = ensure_staged("config", rel_ini, src_p)
                            unlinked = ini_delete_key(
                                sp, "Settings", "gtk-icon-theme-name", remove_if_empty_section=not st.get("file_exists")
                            )
                            overlay[("config", rel_ini)] = "absent" if unlinked else "file"
                elif cur_g["present"]:
                    print(f"PLAN\tremove stale {gtk_key} icon theme ({cur_g['value']}) from {live_p} (was unset before adoption)")
                    if not dry_run:
                        sp = ensure_staged("config", rel_ini, src_p)
                        unlinked = ini_delete_key(
                            sp, "Settings", "gtk-icon-theme-name", remove_if_empty_section=not st.get("file_exists")
                        )
                        overlay[("config", rel_ini)] = "absent" if unlinked else "file"
                apply_captured_perms_if_needed("config", rel_ini, src_p, st)

            # GTK 2 (.gtkrc-2.0) and XSettingsd
            for gkey, base, rel, pat, fmt_fn in (
                ("gtk2", "home", ".gtkrc-2.0", GTK2_RE, lambda v: f'gtk-icon-theme-name="{v}"'),
                ("xsettingsd", "config", "xsettingsd/xsettingsd.conf", XSET_RE, lambda v: f'Net/IconThemeName "{v}"'),
            ):
                st = ad_gtk.get(gkey, {})
                live_p = (home / rel) if base == "home" else (config_home / rel)
                if live_p.is_symlink():
                    continue
                src_p = backup_source_for(base, rel, live_p, backup_dir, absent_set)
                cur_l = line_read_key(src_p, pat)
                if st.get("present"):
                    ok_v, want_v = resolve_usable(str(st.get("value", "")), gkey)
                    if ok_v:
                        if not cur_l["present"] or cur_l["value"] != want_v:
                            print(f"PLAN\trestore {gkey} icon theme ({want_v}) in {live_p}")
                            if not dry_run:
                                sp = ensure_staged(base, rel, src_p)
                                line_set_key(sp, pat, fmt_fn(want_v), create_if_missing=True, default_mode=0o600)
                                overlay[(base, rel)] = "file"
                    elif cur_l["present"]:
                        print(f"PLAN\tremove missing {gkey} icon theme in {live_p}")
                        if not dry_run:
                            sp = ensure_staged(base, rel, src_p)
                            unlinked = line_delete_key(sp, pat, remove_if_empty=not st.get("file_exists"))
                            overlay[(base, rel)] = "absent" if unlinked else "file"
                elif cur_l["present"]:
                    print(f"PLAN\tremove stale {gkey} icon theme ({cur_l['value']}) from {live_p}")
                    if not dry_run:
                        sp = ensure_staged(base, rel, src_p)
                        unlinked = line_delete_key(sp, pat, remove_if_empty=not st.get("file_exists"))
                        overlay[(base, rel)] = "absent" if unlinked else "file"
                apply_captured_perms_if_needed(base, rel, src_p, st)
    else:
        # Even when backup did NOT predate adoption, ensure restored KDE/GTK configs
        # do not point at a missing non-managed theme (leave valid or managed-retained themes intact).
        surv_src = "kdeglobals" if (cur_kg["present"] and cur_kg["value"]) else (
            "kdedefaults" if (cur_kd["present"] and cur_kd["value"]) else "none"
        )
        surv_theme = cur_kg["value"] if surv_src == "kdeglobals" else (cur_kd["value"] if surv_src == "kdedefaults" else "")
        if surv_theme and surv_theme not in MANAGED_ICON_IDS:
            if not theme_is_usable(surv_theme, home, data_icons, xdg_data_dirs, restorable_ids, removing_ids):
                fb = fallback_usable_theme(home, data_icons, xdg_data_dirs, restorable_ids, removing_ids)
                print(f"WARN\trestored KDE icon theme '{surv_theme}' is not installed; falling back to '{fb or 'default'}'")
                if not dry_run:
                    if surv_src == "kdeglobals" and not (config_home / "kdeglobals").is_symlink():
                        skg = ensure_staged("config", "kdeglobals", src_kg)
                        if fb:
                            kde_set_key(skg, "Icons", "Theme", fb, new_mode=0o600)
                        else:
                            kde_delete_key(skg, "Icons", "Theme")
                        overlay[("config", "kdeglobals")] = "file"
                    elif surv_src == "kdedefaults" and not (config_home / "kdedefaults").is_symlink():
                        skd_dir = ensure_staged("config", "kdedefaults", src_kd_dir)
                        skd_dir.mkdir(parents=True, exist_ok=True)
                        if fb:
                            kde_set_key(skd_dir / "kdeglobals", "Icons", "Theme", fb, new_mode=0o600)
                        else:
                            kde_delete_key(skd_dir / "kdeglobals", "Icons", "Theme")
                        overlay[("config", "kdedefaults")] = "dir"

    if not dry_run and stage_dir is not None:
        stage_dir.mkdir(parents=True, exist_ok=True)
        lines = [f"{base}\t{rel}\t{kind}" for (base, rel), kind in sorted(overlay.items())]
        atomic_write_text(stage_dir / "OVERLAY", ("\n".join(lines) + "\n") if lines else "", default_mode=0o600)


# ---------------------------------------------------------------------------
# Unified surviving KDE + GTK selection guard for removal (#126, #127)
# ---------------------------------------------------------------------------

def cmd_check_surviving(args: list[str]) -> None:
    config_home = Path(args[0])
    home = Path(args[1])
    data_icons = Path(args[2])
    xdg_data_dirs = args[3]

    dry_run = False
    restored = False
    backup_dir: Path | None = None
    adoption_path: Path | None = None
    restorable_ids: set[str] = set()
    managed_ids: set[str] = set()

    i = 4
    while i < len(args):
        if args[i] == "--dry-run":
            dry_run = True
            i += 1
        elif args[i] == "--restored":
            restored = True
            i += 1
        elif args[i] == "--backup-dir":
            backup_dir = Path(args[i + 1]) if args[i + 1] else None
            i += 2
        elif args[i] == "--adoption":
            adoption_path = Path(args[i + 1]) if args[i + 1] else None
            i += 2
        elif args[i] == "--restorable":
            restorable_ids.add(args[i + 1])
            i += 2
        elif args[i] == "--managed":
            managed_ids.add(args[i + 1])
            i += 2
        else:
            die(f"unknown check-surviving flag: {args[i]}")

    absent_set = load_backup_absent(backup_dir) if (dry_run and restored) else set()
    ad_data = load_adoption(adoption_path) if (adoption_path and os.path.lexists(adoption_path)) else None
    backup_predated = bool(ad_data.get("backup_predated")) if ad_data else False

    def planned_path(base: str, rel: str) -> Path | None:
        live_p = (home / rel) if base == "home" else (config_home / rel)
        if dry_run and restored and backup_dir is not None:
            return backup_source_for(base, rel, live_p, backup_dir, absent_set)
        return live_p if os.path.lexists(live_p) else None

    # Determine surviving KDE & GTK selections (exact on-disk after restore, or exact planned in --dry-run).
    selections: list[tuple[str, str]] = []  # (source_label, theme_name)
    if dry_run and restored and backup_predated and ad_data is not None:
        cap = ad_data.get("captured", {})
        ad_kde = cap.get("kde", {})
        eff_t = str(ad_kde.get("effective_theme", ""))
        if eff_t and theme_is_usable(eff_t, home, data_icons, xdg_data_dirs, restorable_ids, managed_ids):
            selections.append(("KDE", eff_t))
        ad_gtk = cap.get("gtk") or {}
        for gkey, label in (("gtk3", "GTK 3"), ("gtk4", "GTK 4"), ("gtk2", "GTK 2"), ("xsettingsd", "xsettingsd")):
            st = ad_gtk.get(gkey, {})
            if st.get("present") and st.get("value"):
                v = str(st["value"])
                if theme_is_usable(v, home, data_icons, xdg_data_dirs, restorable_ids, managed_ids):
                    selections.append((label, v))
    else:
        kg_p = planned_path("config", "kdeglobals")
        kd_dir = planned_path("config", "kdedefaults")
        kd_p = (kd_dir / "kdeglobals") if (kd_dir is not None and (kd_dir / "kdeglobals").is_file()) else None
        kg_st = kde_key_state(kg_p, "Icons", "Theme")
        kd_st = kde_key_state(kd_p, "Icons", "Theme")
        kde_eff = kg_st["value"] if (kg_st["present"] and kg_st["value"]) else (kd_st["value"] if (kd_st["present"] and kd_st["value"]) else "")
        if kde_eff:
            selections.append(("KDE", kde_eff))
        for rel, label in (("gtk-3.0/settings.ini", "GTK 3"), ("gtk-4.0/settings.ini", "GTK 4")):
            g_st = ini_read_key(planned_path("config", rel), "Settings", "gtk-icon-theme-name")
            if g_st["present"] and g_st["value"]:
                selections.append((label, g_st["value"]))
        g2_st = line_read_key(planned_path("home", ".gtkrc-2.0"), GTK2_RE)
        if g2_st["present"] and g2_st["value"]:
            selections.append(("GTK 2", g2_st["value"]))
        gx_st = line_read_key(planned_path("config", "xsettingsd/xsettingsd.conf"), XSET_RE)
        if gx_st["present"] and gx_st["value"]:
            selections.append(("xsettingsd", gx_st["value"]))

    keep_reasons: dict[str, list[tuple[str, str]]] = {}  # req_id -> [(source, sel_theme), ...]
    for src_label, sel_theme in selections:
        if sel_theme not in MANAGED_ICON_IDS:
            continue
        # If there is a complete independent outside copy (#127), removal of managed dirs is safe.
        if theme_is_usable(sel_theme, home, data_icons, xdg_data_dirs, set(), managed_ids, outside_only=True):
            continue
        req_ids = required_ids_for(sel_theme)
        # Check if removing managed_ids (while restoring restorable_ids) would make sel_theme unusable.
        lose_usable = False
        for req_id in req_ids:
            if req_id in managed_ids:
                if req_id not in restorable_ids:
                    lose_usable = True
            else:
                cand = data_icons / req_id
                if not cand_is_independent_and_complete(
                    cand,
                    [Path(os.path.realpath(str(data_icons / m))) for m in managed_ids if m not in restorable_ids],
                ):
                    lose_usable = True
        if lose_usable:
            for req_id in req_ids:
                if req_id in managed_ids:
                    keep_reasons.setdefault(req_id, []).append((src_label, sel_theme))

    for req_id in MANAGED_ICON_IDS:
        if req_id in keep_reasons:
            srcs = sorted({s for s, _ in keep_reasons[req_id]})
            sels = sorted({t for _, t in keep_reasons[req_id]})
            print(f"KEEP\t{req_id}\t{', '.join(srcs)}\t{', '.join(sels)}")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        die("missing subcommand")
    cmd = args[0]
    if cmd == "effective-kde" and len(args) == 3:
        cmd_effective_kde(args[1], args[2])
    elif cmd == "capture" and len(args) == 9:
        cmd_capture(args[1:])
    elif cmd == "apply-tx" and len(args) >= 4:
        cmd_apply_tx(args[1:])
    elif cmd == "read-restore-decision" and len(args) == 2:
        cmd_read_restore_decision(Path(args[1]))
    elif cmd == "read-tx-status" and len(args) == 2:
        cmd_read_tx_status(Path(args[1]))
    elif cmd == "begin-restore" and len(args) == 2:
        cmd_begin_restore(Path(args[1]))
    elif cmd == "finish-restore" and len(args) == 2:
        cmd_finish_restore(Path(args[1]))
    elif cmd == "prepare-restore" and len(args) >= 6:
        cmd_prepare_restore(args[1:])
    elif cmd == "check-surviving" and len(args) >= 5:
        cmd_check_surviving(args[1:])
    elif cmd == "has-outside-copy" and len(args) >= 6:
        ok = theme_is_usable(args[1], Path(args[2]), Path(args[3]), args[4], set(), set(args[5:]), outside_only=True)
        raise SystemExit(0 if ok else 1)
    else:
        die(f"invalid arguments: {args!r}")


if __name__ == "__main__":
    main()
