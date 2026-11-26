#!/usr/bin/env python3
"""Adds a Platinum Lavender variant (plus tracked icons/custom/ overrides) to
a disposable WhiteSur export tree, verifies the built themes, publishes it
safely, and reviews upstream updates.

usage:
  whitesur-lavender.py WHITESUR_TREE
  whitesur-lavender.py --print-pin
  whitesur-lavender.py --preflight [CUSTOM_DIR]
  whitesur-lavender.py --validate-custom [CUSTOM_DIR]
  whitesur-lavender.py --check-dest DEST PROJECT UPSTREAM
  whitesur-lavender.py --recover-dest DEST
  whitesur-lavender.py --apply-custom STAGE_DIR [CUSTOM_DIR]
  whitesur-lavender.py --verify STAGE_DIR EXPORT_DIR [CUSTOM_DIR]
  whitesur-lavender.py --publish STAGE_DIR DEST PROJECT UPSTREAM
  whitesur-lavender.py --review-update EXPORT_DIR COMMIT REF PROPOSED_OUT PROJECT UPSTREAM CUSTOM_DIR [OLD_EXPORT_DIR]

Pin data lives in icons/whitesur-pin.json next to this script.

SPDX-License-Identifier: BSD-2-Clause
Note: this license covers this script only. Derived WhiteSur icon artwork
generated from upstream remains GNU GPL v3 only (GPL-3.0-only, per upstream
COPYING and AUTHORS; no later-version grant is evidenced).
"""
from __future__ import annotations

import configparser
import datetime
import difflib
import fcntl
import hashlib
import io
import json
import os
import posixpath
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

SOURCE = "purple"
NAME = "lavender"
THEME_IDS = (
    "WhiteSur-lavender",
    "WhiteSur-lavender-light",
)
CUSTOM_LAYERS = ("all", "light")

# WhiteSur's purple folder paints -> measured Mac OS 9.2.2 Finder folder ramp
# (docs/REFERENCE.md "Finder folder icons", AUDIT.md #107).
COLORS = {
    "#f299ff": "#ddddfe",
    "#e791f3": "#b5b4f9",
    "#c75cd6": "#7e7dd9",
}

ALLOWED_ICON_DIRS = frozenset({
    "actions/16", "actions/22", "actions/24", "actions/32", "actions/symbolic",
    "animations/16", "animations/22", "animations/24",
    "apps/16", "apps/22", "apps/32", "apps/scalable", "apps/symbolic",
    "categories/22", "categories/32", "categories/symbolic",
    "places/symbolic", "places/scalable", "places/16", "places/22", "places/24",
    "mimes/16", "mimes/22", "mimes/scalable", "mimes/symbolic",
    "devices/16", "devices/22", "devices/24", "devices/32", "devices/scalable", "devices/symbolic",
    "emotes/22", "emotes/symbolic",
    "emblems/16", "emblems/22", "emblems/24", "emblems/symbolic",
    "status/16", "status/22", "status/24", "status/32", "status/symbolic",
    "preferences/32",
})

SVG_NS = "{http://www.w3.org/2000/svg}svg"
SVG_ROOT_RE = re.compile(r"<svg(?=\s|>)")

APPLE_PATH_MARKERS = (
    "10.062 3.2488",
    "10.356 286.57",
    "11.82 8.4375",
    "19.302 7.855",
)
KDE_PLASMA_MARKERS = (
    "M 5 2 A 1 1",
    "M 7 3 C 6.4 3",
    "m425.24 489.13",
)

NOTICE_NAME = "LAVENDER-NOTICE.txt"
OWNERSHIP_STAMP = ".macos9-whitesur-lavender-build"
OWNERSHIP_HEADER = "managed-by=macos9-theme/icons/build-whitesur-lavender.sh"
PUBLISH_JOURNAL = ".whitesur-lavender-publish.json"
HERE = Path(__file__).resolve().parent
PIN_FILE = HERE / "whitesur-pin.json"
DEFAULT_CUSTOM_DIR = HERE / "custom"


def fail(msg: str) -> None:
    raise SystemExit(f"whitesur-lavender: {msg}")


def run_preflight(custom_arg: str | None = None) -> None:
    """Verify all tools and Python/GTK modules before lock, fetch, or writes (#118)."""
    missing: list[str] = []
    if sys.version_info < (3, 11):
        missing.append(
            f"python3 >= 3.11 (found {sys.version_info.major}.{sys.version_info.minor}; Arch package: python)"
        )
    for cmd, pkg in (
        ("git", "git"),
        ("tar", "tar"),
        ("xmllint", "libxml2"),
        ("rsvg-convert", "librsvg"),
        ("gtk-update-icon-cache", "gtk-update-icon-cache"),
    ):
        if shutil.which(cmd) is None:
            missing.append(f"{cmd} (Arch package: {pkg})")

    gi_ok = False
    try:
        import gi  # type: ignore[import-untyped]
        gi_ok = True
    except Exception:
        missing.append("Python module 'gi' (Arch package: python-gobject)")

    if gi_ok:
        try:
            gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk  # type: ignore[import-untyped]
            _ = Gtk.IconTheme
        except Exception:
            missing.append("GTK 3 GI typelib Gtk-3.0 (Arch package: gtk3)")

    # Pillow is only required when the custom icon layer contains .png files.
    need_pillow = False
    cdir = resolve_custom_dir(custom_arg) if custom_arg is not None else DEFAULT_CUSTOM_DIR
    if cdir.exists() and cdir.is_dir() and not cdir.is_symlink():
        for layer in CUSTOM_LAYERS:
            ldir = cdir / layer
            if ldir.is_dir() and not ldir.is_symlink():
                for _, _, fnames in os.walk(ldir, followlinks=False):
                    if any(fn.endswith(".png") for fn in fnames):
                        need_pillow = True
                        break
            if need_pillow:
                break
    if need_pillow:
        try:
            from PIL import Image  # type: ignore[import-untyped]
            _ = Image
        except Exception:
            missing.append("Python module 'PIL' for custom PNG validation (Arch package: python-pillow)")

    if missing:
        fail(
            "missing required dependencies: "
            + "; ".join(missing)
            + ". Install the missing Arch package(s) and try again; nothing was changed"
        )


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_pin(pin_path: Path = PIN_FILE) -> dict[str, Any]:
    """Load and validate the reviewed pin file (icons/whitesur-pin.json)."""
    if not os.path.lexists(pin_path):
        fail(f"pin file not found: {pin_path}")
    st = os.lstat(pin_path)
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        fail(f"pin file must be a regular non-symlink file: {pin_path}")
    try:
        pin = json.loads(pin_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        fail(f"invalid pin JSON in {pin_path}: {exc}")
    if not isinstance(pin, dict) or pin.get("schema_version") != 1:
        fail(f"unsupported pin schema in {pin_path}")
    required = (
        "upstream_url",
        "release",
        "commit",
        "artwork_license",
        "installer_sha256",
        "copying_sha256",
        "authors_sha256",
        "status32_start_here_sha256",
        "plasma_launchers",
        "purple_manifest",
        "missing_ns_svgs",
        "symlink_count",
    )
    for key in required:
        if key not in pin:
            fail(f"pin file missing key {key!r}: {pin_path}")
    if not re.fullmatch(r"[0-9a-f]{40}", str(pin["commit"])):
        fail(f"pin commit is not a 40-char SHA-1: {pin['commit']!r}")
    if not isinstance(pin["purple_manifest"], dict) or not pin["purple_manifest"]:
        fail("pin purple_manifest must be a non-empty object")
    if not isinstance(pin["plasma_launchers"], dict) or not pin["plasma_launchers"]:
        fail("pin plasma_launchers must be a non-empty object")
    if not isinstance(pin["missing_ns_svgs"], list):
        fail("pin missing_ns_svgs must be a list")
    return pin


def replace_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"upstream install.sh changed: expected 1 occurrence of {old!r}, found {count}")
    return text.replace(old, new, 1)


def reject_bad_path_chars(raw: str, label: str) -> None:
    if not raw or any(ch in raw for ch in ("\x00", "\t", "\n", "\r")):
        fail(f"{label} must be a non-empty path without tabs or line breaks")


def ensure_no_symlinks_in_existing_chain(path: Path, label: str) -> None:
    """Reject any symlink anywhere in the existing ancestor chain or at path."""
    abs_path = Path(os.path.abspath(str(path)))
    cur = Path("/")
    for part in abs_path.parts[1:]:
        cur = cur / part
        if os.path.lexists(cur):
            if cur.is_symlink():
                fail(f"{label} traverses symbolic link {cur}")
        else:
            break


def ensure_confined_entry(root_real: Path, rel: str, expect_dir: bool) -> Path:
    """Verify every component of root_real/rel is non-symlink and stays in root_real."""
    rel_path = Path(rel)
    if rel_path.is_absolute() or ".." in rel_path.parts:
        fail(f"invalid relative path {rel!r}")
    cur = root_real
    for part in rel_path.parts:
        cur = cur / part
        if not os.path.lexists(cur):
            fail(f"missing expected path: {cur}")
        st = os.lstat(cur)
        if stat.S_ISLNK(st.st_mode):
            fail(f"refusing symlinked input or target: {cur}")
    resolved = cur.resolve(strict=True)
    if not resolved.is_relative_to(root_real):
        fail(f"path escapes export root: {cur}")
    st = os.lstat(cur)
    if expect_dir:
        if not stat.S_ISDIR(st.st_mode):
            fail(f"expected directory: {cur}")
    else:
        if not stat.S_ISREG(st.st_mode):
            fail(f"expected regular file: {cur}")
    return cur


def scan_export_symlinks(root_real: Path) -> tuple[dict[str, str], list[str]]:
    """Return (rel_path -> target, list of absolute/escaping problems)."""
    links: dict[str, str] = {}
    problems: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root_real, followlinks=False):
        dirnames.sort()
        for name in sorted(dirnames + filenames):
            entry = Path(dirpath) / name
            if entry.is_symlink():
                rel = entry.relative_to(root_real).as_posix()
                target = os.readlink(entry)
                links[rel] = target
                if os.path.isabs(target):
                    problems.append(f"absolute symlink: {rel} -> {target}")
                else:
                    norm = Path(os.path.normpath(os.path.join(dirpath, target)))
                    if not norm.is_relative_to(root_real):
                        problems.append(f"escaping symlink: {rel} -> {target}")
    return links, problems


def verify_export_symlinks(root_real: Path) -> None:
    _, problems = scan_export_symlinks(root_real)
    if problems:
        fail(problems[0])


def check_svg_xml(data: bytes, label: str, require_svg_ns: bool = True) -> str:
    """Parse XML and return root tag; fail on syntax error or missing namespace."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        fail(f"malformed XML in {label}: {exc}")
    if require_svg_ns and root.tag != SVG_NS:
        fail(f"{label} root tag is {root.tag!r}, expected {SVG_NS!r}")
    return root.tag


def check_svg_external(data: bytes, label: str) -> None:
    """Validate an SVG with xmllint and librsvg (rsvg-convert)."""
    r_xml = subprocess.run(
        ["xmllint", "--nonet", "--noout", "-"],
        input=data,
        capture_output=True,
        check=False,
    )
    if r_xml.returncode != 0:
        err = r_xml.stderr.decode("utf-8", errors="replace").strip()
        fail(f"xmllint failed on {label}: {err}")

    r_rsvg = subprocess.run(
        ["rsvg-convert", "-w", "32", "-h", "32", "-f", "png"],
        input=data,
        capture_output=True,
        check=False,
    )
    if r_rsvg.returncode != 0 or not r_rsvg.stdout.startswith(b"\x89PNG\r\n\x1a\n"):
        err = r_rsvg.stderr.decode("utf-8", errors="replace").strip()
        fail(f"rsvg-convert failed on {label}: {err}")


def check_png_bytes(data: bytes, label: str) -> None:
    """Validate a PNG file with Pillow."""
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        fail(f"invalid PNG signature in {label}")
    from PIL import Image

    try:
        with Image.open(io.BytesIO(data)) as im:
            im.verify()
        with Image.open(io.BytesIO(data)) as im2:
            im2.load()
    except Exception as exc:
        fail(f"corrupt PNG in {label}: {exc}")


# ---------------------------------------------------------------------------
# Tracked custom icon layer (icons/custom/{all,light}/)
# ---------------------------------------------------------------------------

def resolve_custom_dir(custom_arg: str | None) -> Path:
    if custom_arg is None or custom_arg == "":
        return DEFAULT_CUSTOM_DIR
    reject_bad_path_chars(custom_arg, "CUSTOM_DIR")
    return Path(os.path.abspath(custom_arg))


def load_and_validate_custom_layer(custom_dir: Path) -> dict[str, dict[str, tuple[str, bytes | str]]]:
    """Validate icons/custom/{all,light}/ and return per-layer entries.

    Each layer maps `rel_posix` (e.g. 'apps/scalable/my-app.svg') to either
    `('file', bytes)` or `('link', target_str)`.
    """
    result: dict[str, dict[str, tuple[str, bytes | str]]] = {layer: {} for layer in CUSTOM_LAYERS}
    if not os.path.lexists(custom_dir):
        return result
    ensure_no_symlinks_in_existing_chain(custom_dir, "CUSTOM_DIR")
    if custom_dir.is_symlink() or not custom_dir.is_dir():
        fail(f"CUSTOM_DIR must be a non-symlink directory: {custom_dir}")

    # Only allow all/, light/, and README.md at custom root.
    for entry in sorted(custom_dir.iterdir()):
        if entry.name == "README.md":
            if entry.is_symlink() or not entry.is_file():
                fail(f"custom README.md must be a regular file: {entry}")
            continue
        if entry.name not in CUSTOM_LAYERS:
            fail(f"unexpected entry in custom icon directory {custom_dir}: {entry.name!r} (expected all/, light/)")
        if entry.is_symlink() or not entry.is_dir():
            fail(f"custom layer must be a non-symlink directory: {entry}")

    for layer in CUSTOM_LAYERS:
        layer_root = custom_dir / layer
        if not os.path.lexists(layer_root):
            continue
        for dirpath, dirnames, filenames in os.walk(layer_root, followlinks=False):
            dirnames.sort()
            cur_dir = Path(dirpath)
            for dname in list(dirnames):
                dpath = cur_dir / dname
                if dname.startswith("."):
                    fail(f"hidden directory not allowed in custom icons: {dpath}")
                if dpath.is_symlink():
                    fail(f"directory symlink not allowed in custom icons: {dpath}")
            for fname in sorted(filenames):
                fpath = cur_dir / fname
                rel = fpath.relative_to(layer_root)
                rel_posix = rel.as_posix()
                if rel_posix == ".gitkeep":
                    if fpath.is_symlink() or not fpath.is_file():
                        fail(f"custom .gitkeep must be a regular file: {fpath}")
                    continue
                if any(part.startswith(".") for part in rel.parts):
                    fail(f"hidden file not allowed in custom icons: {fpath}")
                parent_posix = rel.parent.as_posix()
                if parent_posix not in ALLOWED_ICON_DIRS:
                    fail(
                        f"custom icon {layer}/{rel_posix} is outside WhiteSur's indexed icon directories "
                        f"(got {parent_posix!r}; expected e.g. apps/scalable, places/scalable, actions/16)"
                    )
                suffix = fpath.suffix.lower()
                if suffix not in (".svg", ".png"):
                    fail(f"unsupported custom icon extension in {layer}/{rel_posix} (expected .svg or .png)")
                st = os.lstat(fpath)
                if stat.S_ISLNK(st.st_mode):
                    target = os.readlink(fpath)
                    if not target or any(ch in target for ch in ("\x00", "\t", "\n", "\r")):
                        fail(f"invalid symlink target in custom icon {layer}/{rel_posix}: {target!r}")
                    if os.path.isabs(target):
                        fail(f"custom icon alias must be a relative symlink: {layer}/{rel_posix} -> {target}")
                    if Path(target).suffix.lower() not in (".svg", ".png"):
                        fail(f"custom icon alias target must end in .svg or .png: {layer}/{rel_posix} -> {target}")
                    # Verify normalized target stays inside the theme root.
                    norm = os.path.normpath(os.path.join(parent_posix, target))
                    if norm == ".." or norm.startswith("../") or os.path.isabs(norm):
                        fail(f"custom icon alias escapes theme root: {layer}/{rel_posix} -> {target}")
                    result[layer][rel_posix] = ("link", target)
                elif stat.S_ISREG(st.st_mode):
                    raw = fpath.read_bytes()
                    if not raw:
                        fail(f"empty custom icon file: {layer}/{rel_posix}")
                    if suffix == ".svg":
                        try:
                            raw.decode("utf-8")
                        except UnicodeDecodeError as exc:
                            fail(f"custom SVG is not valid UTF-8 ({layer}/{rel_posix}): {exc}")
                        check_svg_xml(raw, f"custom {layer}/{rel_posix}", require_svg_ns=True)
                        check_svg_external(raw, f"custom {layer}/{rel_posix}")
                    else:
                        check_png_bytes(raw, f"custom {layer}/{rel_posix}")
                    result[layer][rel_posix] = ("file", raw)
                else:
                    fail(f"unsupported file type in custom icons: {fpath}")
    return result


def effective_custom_for_theme(
    custom: dict[str, dict[str, tuple[str, bytes | str]]], tid: str
) -> dict[str, tuple[str, bytes | str]]:
    eff = dict(custom["all"])
    if tid == "WhiteSur-lavender-light":
        eff.update(custom["light"])
    return eff


def materialize_symlink_dir(theme_dir: Path, rel_dir: str, stage_real: Path) -> Path:
    """Ensure theme_dir/rel_dir is a real directory without mutating symlink targets."""
    cur = theme_dir
    for part in Path(rel_dir).parts:
        cur = cur / part
        if os.path.lexists(cur):
            if cur.is_symlink():
                real_target = cur.resolve(strict=True)
                if not real_target.is_relative_to(stage_real) or not real_target.is_dir():
                    fail(f"unexpected symlinked directory target while materializing {cur} -> {real_target}")
                cur.unlink()
                cur.mkdir(mode=0o755)
                for child in sorted(real_target.iterdir()):
                    rel_link = os.path.relpath(real_target / child.name, cur)
                    (cur / child.name).symlink_to(rel_link)
            elif not cur.is_dir():
                fail(f"expected directory at {cur}")
        else:
            cur.mkdir(mode=0o755)
    return cur


def write_custom_entry(dest_file: Path, kind: str, payload: bytes | str) -> None:
    if os.path.lexists(dest_file):
        if dest_file.is_dir() and not dest_file.is_symlink():
            fail(f"refusing to replace directory with custom icon: {dest_file}")
        dest_file.unlink()
    if kind == "file":
        assert isinstance(payload, bytes)
        atomic_write_bytes(dest_file, payload, mode=0o644)
    else:
        assert isinstance(payload, str)
        dest_file.symlink_to(payload)


def resolve_logical_custom_target(
    eff_custom: dict[str, tuple[str, bytes | str]], rel_posix: str
) -> str:
    """Resolve a custom alias chain purely lexically within a theme (max 16 hops)."""
    cur = rel_posix
    seen: set[str] = {cur}
    for _ in range(16):
        entry = eff_custom.get(cur)
        if entry is None or entry[0] != "link":
            return cur
        target = entry[1]
        assert isinstance(target, str)
        nxt = posixpath.normpath(posixpath.join(posixpath.dirname(cur), target))
        if nxt == "." or nxt.startswith("..") or nxt in seen:
            return nxt
        seen.add(nxt)
        cur = nxt
    return cur


def path_traverses_symlink(theme_dir: Path, rel_parent: Path) -> bool:
    cur = theme_dir
    for part in rel_parent.parts:
        cur = cur / part
        if cur.is_symlink():
            return True
    return False


def apply_custom_layer(stage_arg: str, custom_arg: str | None = None) -> None:
    """Apply validated icons/custom/{all,light}/ onto staged themes & rebuild caches."""
    stage_real = Path(stage_arg).resolve(strict=True)
    custom_dir = resolve_custom_dir(custom_arg)
    custom = load_and_validate_custom_layer(custom_dir)
    total_entries = sum(len(v) for v in custom.values())
    if total_entries == 0:
        return

    base_dir = stage_real / "WhiteSur-lavender"

    light_dir = stage_real / "WhiteSur-lavender-light"
    light_custom = custom["light"]

    # Materialize directories before copying shared overrides. A cross-directory
    # alias also needs its own directory when light has a distinct target (#119).
    for rel_posix in sorted(light_custom):
        rel_parent = Path(rel_posix).parent.as_posix()
        materialize_symlink_dir(light_dir, rel_parent, stage_real)

    eff = effective_custom_for_theme(custom, light_dir.name)
    changed = True
    while changed:
        changed = False
        for rel_posix, (kind, payload) in sorted(eff.items()):
            if kind != "link":
                continue
            rel_parent = Path(rel_posix).parent
            if not path_traverses_symlink(light_dir, rel_parent):
                continue
            logical_rel = resolve_logical_custom_target(eff, rel_posix)
            target_overridden = logical_rel in light_custom
            if not target_overridden:
                # Check if upstream itself gives this variant a distinct file at logical_rel.
                v_cand = light_dir / logical_rel
                b_cand = base_dir / logical_rel
                if os.path.lexists(v_cand) and os.path.lexists(b_cand):
                    try:
                        if v_cand.resolve(strict=True) != b_cand.resolve(strict=True):
                            target_overridden = True
                    except OSError:
                        target_overridden = True
            if target_overridden:
                materialize_symlink_dir(light_dir, rel_parent.as_posix(), stage_real)
                changed = True

    # Shared entries in symlinked light directories come from the base.
    for rel_posix, (kind, payload) in sorted(custom["all"].items()):
        rel_parent = Path(rel_posix).parent
        (base_dir / rel_parent).mkdir(parents=True, exist_ok=True)
        write_custom_entry(base_dir / rel_posix, kind, payload)
        if not path_traverses_symlink(light_dir, rel_parent):
            (light_dir / rel_parent).mkdir(parents=True, exist_ok=True)
            write_custom_entry(light_dir / rel_posix, kind, payload)

    for rel_posix, (kind, payload) in sorted(light_custom.items()):
        write_custom_entry(light_dir / rel_posix, kind, payload)

    # Regenerate icon-theme.cache for both staged themes so new names/aliases index cleanly.
    for tid in THEME_IDS:
        tdir = stage_real / tid
        r = subprocess.run(
            ["gtk-update-icon-cache", "-f", "-t", str(tdir)],
            capture_output=True,
            check=False,
        )
        if r.returncode != 0:
            fail(f"gtk-update-icon-cache failed after custom layer on {tid}: {r.stderr.decode('utf-8', errors='replace').strip()}")


# ---------------------------------------------------------------------------
# Upstream patching
# ---------------------------------------------------------------------------

def without_dark_variant(text: str) -> str:
    text = replace_once(text, "COLOR_VARIANTS=('' '-light' '-dark')", "COLOR_VARIANTS=('' '-light')")
    text, count = re.subn(r"(?ms)^  if \[\[ \$\{color\} == '-dark' \]\]; then\n.*?^  fi\n\n", "", text)
    if count != 1:
        fail(f"upstream install.sh changed: expected one dark variant block, found {count}")
    return text


def patch_installer_text(text: str) -> str:
    """Apply reviewed Lavender, quoting, and license-notice patches to install.sh."""
    text = without_dark_variant(text)
    text = replace_once(
        text,
        "THEME_VARIANTS=('' '-purple' '-pink' '-red' '-orange' '-yellow' '-green' '-grey' '-nord')",
        f"THEME_VARIANTS=('' '-purple' '-pink' '-red' '-orange' '-yellow' '-green' '-grey' '-nord' '-{NAME}')",
    )
    text = replace_once(
        text,
        "green|grey|nord|all]",
        f"green|grey|nord|{NAME}|all]",
    )
    lavender_branch = (
        f"          {NAME})\n"
        f"            themes+=('-{NAME}')\n"
        f"            shift\n"
        f"            ;;\n"
    )
    text = replace_once(
        text,
        "          purple)\n",
        lavender_branch + "          purple)\n",
    )
    text = replace_once(
        text,
        '#  cp -r "${SRC_DIR}"/{COPYING,AUTHORS}                                                       "${THEME_DIR}"',
        f'  cp "${{SRC_DIR}}"{{/COPYING,/AUTHORS,/{NOTICE_NAME}}}                                        "${{THEME_DIR}}/"',
    )
    text = replace_once(
        text,
        "  local THEME_DIR=${dest}/${name}${theme}${color}\n\n  [[ -d \"${THEME_DIR}\" ]] && rm -rf \"${THEME_DIR}\"\n\n  echo \"Installing '${THEME_DIR}'...\"",
        "  local THEME_DIR=\"${dest}/${name}${theme}${color}\"\n\n  [[ -d \"${THEME_DIR}\" ]] && rm -rf \"${THEME_DIR}\"\n\n  echo \"Installing '${THEME_DIR}'...\"",
    )
    text = replace_once(
        text,
        "  local THEME_DIR=${dest}/${name}${theme}${color}\n\n  [[ -d \"${THEME_DIR}\" ]] && rm -rf \"${THEME_DIR}\"\n\n  echo \"Uninstalling '\"${THEME_DIR}\"'...\"",
        "  local THEME_DIR=\"${dest}/${name}${theme}${color}\"\n\n  [[ -d \"${THEME_DIR}\" ]] && rm -rf \"${THEME_DIR}\"\n\n  echo \"Uninstalling '${THEME_DIR}'...\"",
    )
    text = replace_once(
        text,
        '    cp -r ${SRC_DIR}/src/status/{16,22,24,32}                                                "${THEME_DIR}"/status',
        '    cp -r "${SRC_DIR}"/src/status/{16,22,24,32}                                              "${THEME_DIR}"/status',
    )

    old_light_links = "\n".join([
        "    cd ${dest}",
        "    ln -s ../${name}${theme}/actions ${name}${theme}-light/actions",
        "    ln -s ../${name}${theme}/animations ${name}${theme}-light/animations",
        "    ln -s ../${name}${theme}/apps ${name}${theme}-light/apps",
        "    ln -s ../${name}${theme}/categories ${name}${theme}-light/categories",
        "    ln -s ../${name}${theme}/devices ${name}${theme}-light/devices",
        "    ln -s ../${name}${theme}/emotes ${name}${theme}-light/emotes",
        "    ln -s ../${name}${theme}/emblems ${name}${theme}-light/emblems",
        "    ln -s ../${name}${theme}/mimes ${name}${theme}-light/mimes",
        "    ln -s ../${name}${theme}/places ${name}${theme}-light/places",
        "    ln -s ../${name}${theme}/preferences ${name}${theme}-light/preferences",
        "    ln -s ../../${name}${theme}/status/symbolic ${name}${theme}-light/status/symbolic",
    ])
    new_light_links = "\n".join([
        "    (",
        '      cd "${dest}"',
        '      ln -s "../${name}${theme}/actions" "${name}${theme}-light/actions"',
        '      ln -s "../${name}${theme}/animations" "${name}${theme}-light/animations"',
        '      ln -s "../${name}${theme}/apps" "${name}${theme}-light/apps"',
        '      ln -s "../${name}${theme}/categories" "${name}${theme}-light/categories"',
        '      ln -s "../${name}${theme}/devices" "${name}${theme}-light/devices"',
        '      ln -s "../${name}${theme}/emotes" "${name}${theme}-light/emotes"',
        '      ln -s "../${name}${theme}/emblems" "${name}${theme}-light/emblems"',
        '      ln -s "../${name}${theme}/mimes" "${name}${theme}-light/mimes"',
        '      ln -s "../${name}${theme}/places" "${name}${theme}-light/places"',
        '      ln -s "../${name}${theme}/preferences" "${name}${theme}-light/preferences"',
        '      ln -s "../../${name}${theme}/status/symbolic" "${name}${theme}-light/status/symbolic"',
        "    )",
    ])
    text = replace_once(text, old_light_links, new_light_links)

    if "THEME_VARIANTS[9]" in text:
        fail("patched install.sh unexpectedly contains hard-coded THEME_VARIANTS[9]")

    r = subprocess.run(
        ["bash", "-n"],
        input=text.encode("utf-8"),
        capture_output=True,
        check=False,
    )
    if r.returncode != 0:
        fail(f"patched install.sh failed bash -n: {r.stderr.decode('utf-8', errors='replace').strip()}")
    return text


def derive_status32_launcher(plasma24_text: str) -> bytes:
    status32_text = replace_once(plasma24_text, 'width="24" height="24"', 'width="32" height="32"')
    status32_text = replace_once(status32_text, "color:#232629;", "color:#f2f2f2;")
    status32_bytes = status32_text.encode("utf-8")
    check_svg_xml(status32_bytes, "derived src/status/32/start-here.svg", require_svg_ns=True)
    check_svg_external(status32_bytes, "derived src/status/32/start-here.svg")
    if any(m in status32_text for m in APPLE_PATH_MARKERS) or not any(m in status32_text for m in KDE_PLASMA_MARKERS):
        fail("derived src/status/32/start-here.svg did not contain expected KDE Plasma path")
    return status32_bytes


def build_notice_text(pin: dict[str, Any]) -> str:
    today = datetime.date.today().isoformat()
    missing_count = len(pin["missing_ns_svgs"])
    return (
        "WhiteSur Lavender icon theme derivative notice\n"
        "==============================================\n\n"
        f"Upstream project: {pin['upstream_url']}\n"
        "Upstream author:  Vince Liuice (see AUTHORS)\n"
        f"Upstream release: {pin['release']}\n"
        f"Upstream commit:  {pin['commit']}\n"
        f"Artwork license:  GNU General Public License v3 only ({pin['artwork_license']}, see COPYING;\n"
        "                  no later-version grant is evidenced in the reviewed upstream release).\n\n"
        f"Modifications applied on {today} by macos9-theme/icons/whitesur-lavender.py:\n"
        f"  1. Added the Platinum Lavender folder variant ({len(pin['purple_manifest'])} SVGs derived from\n"
        "     colors/color-purple/ using Mac OS 9.2.2 Finder folder measurements:\n"
        "     #f299ff -> #ddddfe, #e791f3 -> #b5b4f9, #c75cd6 -> #7e7dd9).\n"
        "  2. Built with upstream's KDE Plasma launcher option (-p) and derived\n"
        "     status/32/start-here.svg from upstream plasma/places/24/start-here.svg\n"
        "     so start-here-kde-plasma resolves to KDE Plasma artwork at all panel sizes.\n"
        f"  3. Normalized {missing_count} upstream src/ SVGs that omitted xmlns=\"http://www.w3.org/2000/svg\".\n"
        "  4. Applied any tracked project custom icon overrides from icons/custom/{all,light}/.\n"
    )


def atomic_write_bytes(dest: Path, data: bytes, mode: int | None = None) -> None:
    fd, tmp_name = tempfile.mkstemp(prefix=f".{dest.name}.tmp.", dir=dest.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        if mode is not None:
            os.chmod(tmp_path, mode)
        os.replace(tmp_path, dest)
    except BaseException:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def patch_export_tree(tree_arg: str) -> None:
    pin = load_pin()
    reject_bad_path_chars(tree_arg, "WHITESUR_TREE")
    root = Path(tree_arg)
    if not os.path.lexists(root):
        fail(f"export tree does not exist: {root}")
    if root.is_symlink() or not root.is_dir():
        fail(f"export tree must be a non-symlink directory: {root}")
    root_real = root.resolve(strict=True)

    verify_export_symlinks(root_real)

    colors_dir = ensure_confined_entry(root_real, "colors", expect_dir=True)
    source_dir = ensure_confined_entry(root_real, f"colors/color-{SOURCE}", expect_dir=True)
    target_dir = colors_dir / f"color-{NAME}"
    if os.path.lexists(target_dir):
        fail(f"{target_dir} already exists")

    copying_path = ensure_confined_entry(root_real, "COPYING", expect_dir=False)
    if sha256_bytes(copying_path.read_bytes()) != pin["copying_sha256"]:
        fail("upstream COPYING digest does not match pinned commit")
    authors_path = ensure_confined_entry(root_real, "AUTHORS", expect_dir=False)
    if sha256_bytes(authors_path.read_bytes()) != pin["authors_sha256"]:
        fail("upstream AUTHORS digest does not match pinned commit")

    for rel, expected_sha in pin["plasma_launchers"].items():
        p = ensure_confined_entry(root_real, rel, expect_dir=False)
        if sha256_bytes(p.read_bytes()) != expected_sha:
            fail(f"upstream {rel} digest does not match pinned commit")

    status32_path = ensure_confined_entry(root_real, "src/status/32/start-here.svg", expect_dir=False)
    if sha256_bytes(status32_path.read_bytes()) != pin["status32_start_here_sha256"]:
        fail("upstream src/status/32/start-here.svg digest does not match pinned commit")

    plasma24_text = (root_real / "plasma/places/24/start-here.svg").read_text(encoding="utf-8")
    status32_bytes = derive_status32_launcher(plasma24_text)

    purple_manifest: dict[str, dict[str, Any]] = pin["purple_manifest"]
    actual_entries = sorted(p.name for p in source_dir.iterdir())
    expected_entries = sorted(purple_manifest)
    if actual_entries != expected_entries:
        missing = sorted(set(expected_entries) - set(actual_entries))
        extra = sorted(set(actual_entries) - set(expected_entries))
        fail(f"upstream colors/color-{SOURCE} manifest mismatch (missing={missing}, extra={extra})")

    src_pattern = re.compile("|".join(re.escape(k) for k in COLORS), re.I)
    generated_svgs: dict[str, bytes] = {}
    all_seen: set[str] = set()

    for name in expected_entries:
        spec = purple_manifest[name]
        expected_sha = spec["sha256"]
        expected_paints = tuple(sorted(spec["paints"]))
        svg_path = ensure_confined_entry(root_real, f"colors/color-{SOURCE}/{name}", expect_dir=False)
        raw = svg_path.read_bytes()
        actual_sha = sha256_bytes(raw)
        if actual_sha != expected_sha:
            fail(f"upstream {name} digest mismatch: got {actual_sha}, expected {expected_sha}")
        check_svg_xml(raw, f"colors/color-{SOURCE}/{name}", require_svg_ns=True)
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            fail(f"invalid UTF-8 in {name}: {exc}")
        found = tuple(sorted({m.lower() for m in src_pattern.findall(text)}))
        if found != expected_paints:
            fail(f"upstream {name} paints changed: found {found}, expected {expected_paints}")
        all_seen.update(found)

        recolored = src_pattern.sub(lambda m: COLORS[m[0].lower()], text)
        if src_pattern.search(recolored):
            fail(f"unconverted source paint left in {name}")
        for old_hex in expected_paints:
            new_hex = COLORS[old_hex]
            if new_hex not in recolored.lower():
                fail(f"expected target paint {new_hex} missing in {name}")

        out_bytes = recolored.encode("utf-8")
        check_svg_xml(out_bytes, f"generated color-{NAME}/{name}", require_svg_ns=True)
        check_svg_external(out_bytes, f"generated color-{NAME}/{name}")
        generated_svgs[name] = out_bytes

    if all_seen != set(COLORS):
        fail(f"upstream {SOURCE} palette mismatch across manifest: found {sorted(all_seen)}")

    installer_path = ensure_confined_entry(root_real, "install.sh", expect_dir=False)
    installer_raw = installer_path.read_bytes()
    installer_mode = stat.S_IMODE(os.lstat(installer_path).st_mode)
    if sha256_bytes(installer_raw) != pin["installer_sha256"]:
        fail("upstream install.sh digest does not match pinned commit")
    patched_installer = patch_installer_text(installer_raw.decode("utf-8")).encode("utf-8")

    ensure_confined_entry(root_real, "src", expect_dir=True)
    missing_ns_paths: list[str] = []
    normalized_svgs: dict[Path, bytes] = {}
    for dirpath, dirnames, filenames in os.walk(root_real / "src", followlinks=False):
        dirnames.sort()
        for fname in sorted(filenames):
            if not fname.endswith(".svg"):
                continue
            fpath = Path(dirpath) / fname
            if fpath.is_symlink():
                continue
            raw = fpath.read_bytes()
            rel = fpath.relative_to(root_real).as_posix()
            tag = check_svg_xml(raw, rel, require_svg_ns=False)
            if tag == SVG_NS:
                continue
            if tag != "svg":
                fail(f"unexpected root tag {tag!r} in {rel}")
            missing_ns_paths.append(rel)
            txt = raw.decode("utf-8")
            norm_txt, count = SVG_ROOT_RE.subn('<svg xmlns="http://www.w3.org/2000/svg"', txt, count=1)
            if count != 1:
                fail(f"could not insert SVG namespace into {rel}")
            norm_bytes = norm_txt.encode("utf-8")
            check_svg_xml(norm_bytes, f"normalized {rel}", require_svg_ns=True)
            normalized_svgs[fpath] = norm_bytes

    missing_ns_paths.sort()
    expected_missing_ns = sorted(pin["missing_ns_svgs"])
    if missing_ns_paths != expected_missing_ns:
        added = sorted(set(missing_ns_paths) - set(expected_missing_ns))
        removed = sorted(set(expected_missing_ns) - set(missing_ns_paths))
        fail(
            f"upstream missing-xmlns SVG set changed: count={len(missing_ns_paths)} "
            f"(expected {len(expected_missing_ns)}), added={added[:5]}, removed={removed[:5]}"
        )

    notice_bytes = build_notice_text(pin).encode("utf-8")

    stage_color_dir = Path(tempfile.mkdtemp(prefix=f".color-{NAME}-stage.", dir=colors_dir))
    try:
        os.chmod(stage_color_dir, 0o755)
        for name, data in generated_svgs.items():
            (stage_color_dir / name).write_bytes(data)
        os.rename(stage_color_dir, target_dir)
    except BaseException:
        shutil.rmtree(stage_color_dir, ignore_errors=True)
        raise

    atomic_write_bytes(root_real / NOTICE_NAME, notice_bytes, mode=0o644)
    atomic_write_bytes(installer_path, patched_installer, mode=installer_mode)
    atomic_write_bytes(status32_path, status32_bytes, mode=0o644)
    for fpath, norm_bytes in normalized_svgs.items():
        atomic_write_bytes(fpath, norm_bytes, mode=stat.S_IMODE(os.lstat(fpath).st_mode))


# ---------------------------------------------------------------------------
# Destination validation, locking, verification, publishing
# ---------------------------------------------------------------------------

def is_owned_theme_dir(theme_dir: Path, expected_id: str) -> bool:
    if not os.path.lexists(theme_dir):
        return False
    st = os.lstat(theme_dir)
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        return False
    stamp = theme_dir / OWNERSHIP_STAMP
    if not os.path.lexists(stamp):
        return False
    st_stamp = os.lstat(stamp)
    if stat.S_ISLNK(st_stamp.st_mode) or not stat.S_ISREG(st_stamp.st_mode):
        return False
    try:
        lines = stamp.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return False
    return OWNERSHIP_HEADER in lines and f"theme={expected_id}" in lines


def is_git_worktree(project_real: Path) -> bool:
    """Return True iff project_real is a primary OR linked Git worktree (#123, #134)."""
    env = {**os.environ, "GIT_CEILING_DIRECTORIES": str(project_real.parent)}
    r = subprocess.run(
        ["git", "-C", str(project_real), "rev-parse", "--show-toplevel"],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0:
        return False
    top_str = r.stdout.strip()
    if not top_str:
        return False
    return Path(top_str).resolve() == project_real.resolve()


def git_path_is_ignored_and_untracked(project_real: Path, rel_path: Path) -> bool:
    rel_str = rel_path.as_posix()
    env = {**os.environ, "GIT_CEILING_DIRECTORIES": str(project_real.parent)}
    r_ign = subprocess.run(
        ["git", "-C", str(project_real), "check-ignore", "--quiet", "--", rel_str],
        env=env,
        capture_output=True,
        check=False,
    )
    if r_ign.returncode != 0:
        return False
    r_trk = subprocess.run(
        ["git", "-C", str(project_real), "ls-files", "--error-unmatch", "--", rel_str],
        env=env,
        capture_output=True,
        check=False,
    )
    return r_trk.returncode != 0


def validate_destination(dest_arg: str, project_arg: str, upstream_arg: str) -> Path:
    reject_bad_path_chars(dest_arg, "OUTPUT_DIR")
    reject_bad_path_chars(project_arg, "PROJECT_DIR")
    reject_bad_path_chars(upstream_arg, "UPSTREAM_CLONE")

    project_real = Path(project_arg).resolve(strict=True)
    upstream_real = Path(upstream_arg).resolve(strict=True)

    dest_abs = Path(os.path.abspath(dest_arg))
    ensure_no_symlinks_in_existing_chain(dest_abs, "OUTPUT_DIR")

    if os.path.lexists(dest_abs):
        st = os.lstat(dest_abs)
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
            fail(f"OUTPUT_DIR exists and is not a real directory: {dest_abs}")

    dest_real = Path(os.path.realpath(str(dest_abs)))

    if dest_real == upstream_real or dest_real.is_relative_to(upstream_real) or upstream_real.is_relative_to(dest_real):
        fail(f"refusing to publish into or across upstream clone: {dest_real}")

    if dest_real == project_real:
        fail(f"refusing to publish directly into project root: {dest_real}")
    if dest_real.is_relative_to(project_real / ".git"):
        fail(f"refusing to publish inside .git: {dest_real}")
    if dest_real.is_relative_to(project_real / "reference"):
        fail(f"refusing to publish inside reference/: {dest_real}")

    if dest_real.is_relative_to(project_real):
        dest_rel = dest_real.relative_to(project_real)
        if is_git_worktree(project_real):
            samples: list[Path] = [dest_real]
            for tid in THEME_IDS:
                tdir = dest_real / tid
                samples.append(tdir)
                samples.append(tdir / "index.theme")
                if not (tdir / "places").is_symlink():
                    samples.append(tdir / "places/scalable/folder.svg")
                else:
                    samples.append(tdir / "places")
            for sample in samples:
                rel = sample.relative_to(project_real)
                if not git_path_is_ignored_and_untracked(project_real, rel):
                    fail(
                        f"refusing to publish into trackable project path: {dest_real} "
                        f"({rel.as_posix()} is not git-ignored)"
                    )
            env = {**os.environ, "GIT_CEILING_DIRECTORIES": str(project_real.parent)}
            r_any = subprocess.run(
                ["git", "-C", str(project_real), "ls-files", "--", dest_rel.as_posix()],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            if r_any.returncode != 0 or r_any.stdout.strip():
                fail(f"refusing to publish into path containing tracked git files: {dest_real}")
        else:
            # Extracted source archive without .git (#123): only allow dev/build/... inside project_real.
            build_root = project_real / "dev" / "build"
            if not dest_real.is_relative_to(build_root):
                fail(
                    f"refusing to publish into source-archive path outside dev/build/: {dest_real} "
                    "(pass an explicit external OUTPUT_DIR or use dev/build/icons)"
                )

    for tid in THEME_IDS:
        target = dest_real / tid
        if os.path.lexists(target) and not is_owned_theme_dir(target, tid):
            fail(
                f"refusing to overwrite unowned existing path: {target} "
                "(manual-copy adoption belongs in install.sh)"
            )

    return dest_real


def open_dest_lock(dest_real: Path) -> int:
    uid = os.getuid()
    lock_key = sha256_bytes(str(dest_real).encode("utf-8"))
    lock_dir = Path(f"/tmp/macos9-whitesur-locks-{uid}")
    use_tmp = False
    try:
        if not os.path.lexists(lock_dir):
            os.mkdir(lock_dir, 0o700)
        st = os.lstat(lock_dir)
        if stat.S_ISDIR(st.st_mode) and not stat.S_ISLNK(st.st_mode) and st.st_uid == uid:
            os.chmod(lock_dir, 0o700)
            use_tmp = True
    except OSError:
        use_tmp = False

    if use_tmp:
        lock_path = lock_dir / f"{lock_key}.lock"
    else:
        dest_real.mkdir(parents=True, exist_ok=True)
        lock_path = dest_real / ".whitesur-lavender.lock"

    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
    except BaseException:
        os.close(fd)
        raise
    return fd


def verify_staged_build(stage_arg: str, export_arg: str, custom_arg: str | None = None) -> None:
    """Verify the entire staged themes before publishing (including custom icons)."""
    pin = load_pin()
    stage_real = Path(stage_arg).resolve(strict=True)
    export_real = Path(export_arg).resolve(strict=True)
    custom = load_and_validate_custom_layer(resolve_custom_dir(custom_arg))

    actual_top = sorted(p.name for p in stage_real.iterdir())
    expected_top = sorted(THEME_IDS)
    if actual_top != expected_top:
        fail(f"staged output IDs mismatch: got {actual_top}, expected {expected_top}")
    for tid in THEME_IDS:
        tdir = stage_real / tid
        if tdir.is_symlink() or not tdir.is_dir():
            fail(f"staged theme is not a real directory: {tdir}")

    expected_folders = {
        name: (export_real / f"colors/color-{NAME}" / name).read_bytes()
        for name in pin["purple_manifest"]
    }
    expected_copying = (export_real / "COPYING").read_bytes()
    expected_authors = (export_real / "AUTHORS").read_bytes()
    expected_notice = (export_real / NOTICE_NAME).read_bytes()

    dir_sizes: dict[str, int] = {}

    for tid in THEME_IDS:
        tdir = stage_real / tid
        eff_custom = effective_custom_for_theme(custom, tid)

        idx_path = tdir / "index.theme"
        if idx_path.is_symlink() or not idx_path.is_file():
            fail(f"missing index.theme in {tid}")
        cp = configparser.ConfigParser(interpolation=None)
        cp.read(idx_path, encoding="utf-8")
        if "Icon Theme" not in cp:
            fail(f"missing [Icon Theme] in {tid}/index.theme")
        if cp["Icon Theme"].get("Name") != tid:
            fail(f"index Name mismatch in {tid}: {cp['Icon Theme'].get('Name')!r}")
        if cp["Icon Theme"].get("Inherits") != "hicolor,breeze":
            fail(f"unexpected Inherits in {tid}: {cp['Icon Theme'].get('Inherits')!r}")
        for key in ("Directories", "ScaledDirectories"):
            dirs = [d.strip() for d in cp["Icon Theme"].get(key, "").split(",") if d.strip()]
            if not dirs:
                fail(f"empty {key} in {tid}/index.theme")
            for rel_d in dirs:
                if rel_d not in cp:
                    fail(f"missing section [{rel_d}] in {tid}/index.theme")
                if not (tdir / rel_d).is_dir():
                    fail(f"missing directory {rel_d} listed in {tid}/index.theme")
                if key == "Directories" and rel_d not in dir_sizes:
                    dir_sizes[rel_d] = int(cp[rel_d].get("Size", "64"))

        for fname, exp_bytes in (
            ("COPYING", expected_copying),
            ("AUTHORS", expected_authors),
            (NOTICE_NAME, expected_notice),
        ):
            npath = tdir / fname
            if npath.is_symlink() or not npath.is_file():
                fail(f"missing notice file {tid}/{fname}")
            if npath.read_bytes() != exp_bytes:
                fail(f"notice file mismatch: {tid}/{fname}")

        # Verify all 25 Lavender folder assets (respecting explicit custom overrides).
        for fname, exp_bytes in expected_folders.items():
            rel_key = f"places/scalable/{fname}"
            fpath = tdir / rel_key
            if rel_key in eff_custom:
                continue
            if not fpath.is_file():
                fail(f"missing Lavender asset {tid}/{rel_key}")
            if fpath.read_bytes() != exp_bytes:
                fail(f"Lavender asset bytes mismatch: {tid}/{rel_key}")

        # Verify every custom override / new icon / alias matches in this theme (#119).
        for rel_key, (kind, payload) in sorted(eff_custom.items()):
            cpath = tdir / rel_key
            if kind == "file":
                assert isinstance(payload, bytes)
                if not cpath.is_file() or cpath.read_bytes() != payload:
                    fail(f"custom icon bytes mismatch in {tid}/{rel_key}")
            else:
                assert isinstance(payload, str)
                if not cpath.is_symlink():
                    fail(f"custom alias is not a symlink in {tid}/{rel_key}")
                # Note: in -light, symlinked dir inheritance means cpath itself
                # may live in base; readlink on cpath returns the exact relative link target.
                if os.readlink(cpath) != payload:
                    fail(f"custom alias target mismatch in {tid}/{rel_key}: got {os.readlink(cpath)!r}, expected {payload!r}")
                resolved = cpath.resolve(strict=True)
                if not resolved.is_relative_to(stage_real):
                    fail(f"custom alias resolves outside staging: {tid}/{rel_key} -> {resolved}")
                # Verify alias resolves to the exact expected variant target inside tdir (#119).
                logical_rel = resolve_logical_custom_target(eff_custom, rel_key)
                expected_target = (tdir / logical_rel).resolve(strict=True)
                if resolved != expected_target:
                    fail(
                        f"custom alias {tid}/{rel_key} resolved to wrong variant target {resolved} "
                        f"(expected {expected_target})"
                    )
                if resolved.read_bytes() != expected_target.read_bytes():
                    fail(f"custom alias {tid}/{rel_key} bytes differ from expected variant target")

        # Neutral KDE Plasma launcher at panel sizes (unless explicitly custom-overridden).
        launcher_paths = [
            "places/16/start-here-kde-plasma.svg",
            "places/22/start-here-kde-plasma.svg",
            "places/24/start-here-kde-plasma.svg",
            "places/scalable/start-here-kde-plasma.svg",
            "status/32/start-here-kde-plasma.svg",
            "apps/scalable/start-here-kde-plasma.svg",
        ]
        for lrel in launcher_paths:
            if lrel in eff_custom or lrel.replace("start-here-kde-plasma.svg", "start-here.svg") in eff_custom:
                continue
            lpath = tdir / lrel
            resolved = lpath.resolve(strict=True)
            if not resolved.is_relative_to(stage_real):
                fail(f"launcher resolves outside staging: {lpath} -> {resolved}")
            ltext = resolved.read_text(encoding="utf-8")
            if any(m in ltext for m in APPLE_PATH_MARKERS):
                fail(f"Apple logo found in {tid}/{lrel} (-> {resolved})")
            if not any(m in ltext for m in KDE_PLASMA_MARKERS):
                fail(f"expected KDE Plasma artwork missing in {tid}/{lrel} (-> {resolved})")

        r_cache = subprocess.run(
            ["gtk-update-icon-cache", "--validate", str(tdir)],
            capture_output=True,
            check=False,
        )
        if r_cache.returncode != 0:
            err = r_cache.stderr.decode("utf-8", errors="replace").strip()
            fail(f"gtk-update-icon-cache --validate failed for {tid}: {err}")

    # Full walk: 0 broken/absolute/escaping symlinks; 100% XML + SVG namespace.
    svg_count = 0
    for tid in THEME_IDS:
        tdir = stage_real / tid
        for dirpath, dirnames, filenames in os.walk(tdir, followlinks=False):
            for name in dirnames + filenames:
                p = Path(dirpath) / name
                if p.is_symlink():
                    target = os.readlink(p)
                    if os.path.isabs(target):
                        fail(f"absolute symlink in staged build: {p} -> {target}")
                    try:
                        resolved = p.resolve(strict=True)
                    except OSError as exc:
                        fail(f"broken symlink in staged build: {p} -> {target} ({exc})")
                    if not resolved.is_relative_to(stage_real):
                        fail(f"escaping symlink in staged build: {p} -> {resolved}")
                elif name.endswith(".svg"):
                    svg_count += 1
                    raw = p.read_bytes()
                    tag = check_svg_xml(raw, str(p.relative_to(stage_real)), require_svg_ns=False)
                    if tag != SVG_NS:
                        fail(f"staged SVG lacks SVG namespace ({tag!r}): {p.relative_to(stage_real)}")

    if svg_count == 0:
        fail("no SVG files found in staged build")

    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import Gtk

    for tid in THEME_IDS:
        eff_custom = effective_custom_for_theme(custom, tid)
        it = Gtk.IconTheme.new()
        it.set_search_path([str(stage_real)])
        it.set_custom_theme(tid)
        for fname in expected_folders:
            icon_name = fname[:-4]
            info = it.lookup_icon(icon_name, 64, 0)
            if info is None or info.get_filename() is None:
                fail(f"GTK failed to resolve {icon_name} at 64 px in {tid}")
            resolved = Path(info.get_filename()).resolve(strict=True)
            if not resolved.is_relative_to(stage_real):
                fail(f"GTK resolved {icon_name} outside staging in {tid}: {resolved}")
        for rel_key, (kind, payload) in sorted(eff_custom.items()):
            rel_p = Path(rel_key)
            icon_name = rel_p.stem
            sz = dir_sizes.get(rel_p.parent.as_posix(), 64)
            info = it.lookup_icon(icon_name, sz, 0)
            if info is None or info.get_filename() is None:
                fail(f"GTK failed to resolve custom icon {icon_name} ({rel_key}) at {sz} px in {tid}")
            gtk_path = Path(info.get_filename())
            resolved = gtk_path.resolve(strict=True)
            if not resolved.is_relative_to(stage_real):
                fail(f"GTK resolved custom icon {icon_name} outside staging in {tid}: {resolved}")
            # Verify GTK resolved to the exact expected variant bytes (#119).
            expected_path = (stage_real / tid / rel_key).resolve(strict=True)
            if gtk_path.parent.name == rel_p.parent.name and gtk_path.parent.parent.name == rel_p.parent.parent.name:
                if resolved.read_bytes() != expected_path.read_bytes():
                    fail(
                        f"GTK resolved {icon_name} ({rel_key}) in {tid} to {resolved}, "
                        f"whose bytes differ from expected variant file {expected_path}"
                    )
            elif kind == "link":
                logical_rel = resolve_logical_custom_target(eff_custom, rel_key)
                expected_bytes = (stage_real / tid / logical_rel).resolve(strict=True).read_bytes()
                if resolved.read_bytes() != expected_bytes:
                    fail(
                        f"GTK resolved custom alias {icon_name} ({rel_key}) in {tid} to {resolved}, "
                        f"whose bytes differ from expected variant target {logical_rel}"
                    )
        custom_overrode_launcher = any(
            k.endswith("/start-here.svg") or k.endswith("/start-here-kde-plasma.svg") for k in eff_custom
        )
        for sz in (16, 22, 24, 32, 48, 64):
            info = it.lookup_icon("start-here-kde-plasma", sz, 0)
            if info is None or info.get_filename() is None:
                fail(f"GTK failed to resolve start-here-kde-plasma at {sz} px in {tid}")
            resolved = Path(info.get_filename()).resolve(strict=True)
            if not resolved.is_relative_to(stage_real):
                fail(f"GTK resolved start-here-kde-plasma at {sz} px outside staging in {tid}: {resolved}")
            if not custom_overrode_launcher:
                ltext = resolved.read_text(encoding="utf-8")
                if any(m in ltext for m in APPLE_PATH_MARKERS) or not any(m in ltext for m in KDE_PLASMA_MARKERS):
                    fail(f"GTK resolved start-here-kde-plasma at {sz} px in {tid} to non-KDE artwork: {resolved}")


def write_ownership_stamp(theme_dir: Path, tid: str, commit: str) -> None:
    stamp_text = (
        f"{OWNERSHIP_HEADER}\n"
        f"theme={tid}\n"
        f"upstream-commit={commit}\n"
    )
    (theme_dir / OWNERSHIP_STAMP).write_text(stamp_text, encoding="utf-8")


def write_publish_journal(
    dest_real: Path,
    state: str,
    incoming: Path,
    rollback: Path,
    existed_before: dict[str, bool],
) -> None:
    journal = dest_real / PUBLISH_JOURNAL
    payload = json.dumps(
        {
            "version": 2,
            "state": state,
            "incoming": incoming.name,
            "rollback": rollback.name,
            "existed_before": existed_before,
        },
        indent=2,
    ).encode("utf-8") + b"\n"
    fd, tmp_name = tempfile.mkstemp(prefix=".whitesur-journal.tmp.", dir=dest_real)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, journal)
    except BaseException:
        tmp_path.unlink(missing_ok=True)
        raise


def _valid_txn_dirname(name: object, prefix: str) -> bool:
    return (
        isinstance(name, str)
        and "/" not in name
        and name.startswith(prefix)
        and len(name) > len(prefix)
    )


def reconcile_publish_journal(dest_real: Path) -> bool:
    """Recover an interrupted standalone publish under the destination lock (#120, #132).

    Records `rolled_back` BEFORE cleaning private staging directories so even an
    abrupt kill during recovery cleanup never deletes an already-restored theme.
    """
    journal = dest_real / PUBLISH_JOURNAL
    if not os.path.lexists(journal):
        return False
    if journal.is_symlink() or not journal.is_file():
        fail(f"refusing to read non-regular publish journal: {journal}")
    try:
        data = json.loads(journal.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"corrupt publish journal {journal}: {exc}")

    state = data.get("state")
    inc_name = data.get("incoming")
    rb_name = data.get("rollback")
    if state not in ("staging", "switching", "rolling_back", "rolled_back", "committed"):
        fail(f"unknown publish journal state {state!r} in {journal}")
    if not _valid_txn_dirname(inc_name, ".whitesur-lavender-incoming.") or not _valid_txn_dirname(
        rb_name, ".whitesur-lavender-rollback."
    ):
        fail(f"invalid publish journal directory names in {journal}")

    incoming = dest_real / inc_name
    rollback = dest_real / rb_name

    raw_existed = data.get("existed_before")
    # Older journals may still have a third tree to restore.
    legacy_id = "WhiteSur-lavender-dark"
    txn_ids = THEME_IDS
    if isinstance(raw_existed, dict) and legacy_id in raw_existed:
        txn_ids += (legacy_id,)
    existed_before = (
        {tid: bool(raw_existed.get(tid, False)) for tid in txn_ids}
        if isinstance(raw_existed, dict)
        else {tid: os.path.lexists(rollback / tid) for tid in txn_ids}
    )

    if state in ("switching", "rolling_back"):
        all_placed = (
            state == "switching"
            and all(
                is_owned_theme_dir(dest_real / tid, tid) and not os.path.lexists(incoming / tid)
                for tid in txn_ids
            )
        )
        if all_placed:
            write_publish_journal(dest_real, "committed", incoming, rollback, existed_before)
        else:
            if state != "rolling_back":
                write_publish_journal(dest_real, "rolling_back", incoming, rollback, existed_before)
            for tid in reversed(txn_ids):
                target = dest_real / tid
                backed = rollback / tid
                if os.path.lexists(backed):
                    if os.path.lexists(target):
                        if not is_owned_theme_dir(target, tid):
                            fail(f"cannot recover interrupted publish: unowned path at {target}")
                        if os.path.isdir(incoming) and not incoming.is_symlink() and not os.path.lexists(incoming / tid):
                            os.rename(target, incoming / tid)
                        else:
                            shutil.rmtree(target)
                    os.rename(backed, target)
                elif not existed_before.get(tid, False) and os.path.lexists(target) and not os.path.lexists(incoming / tid):
                    # First-time publish interrupted after placing tid (no prior theme existed).
                    if is_owned_theme_dir(target, tid):
                        shutil.rmtree(target)
            # Mark rollback durable BEFORE touching private staging directories (#132).
            write_publish_journal(dest_real, "rolled_back", incoming, rollback, existed_before)

    # For staging, committed, and rolled_back: cleanup only removes private staging.
    crash_during_cleanup = os.environ.get("M9_TEST_CRASH_DURING_RECOVERY_CLEANUP") == "1"
    if os.path.lexists(incoming) and not incoming.is_symlink() and incoming.is_dir():
        if crash_during_cleanup:
            first_inc = incoming / THEME_IDS[0]
            if os.path.lexists(first_inc):
                shutil.rmtree(first_inc, ignore_errors=True)
            os._exit(98)
        shutil.rmtree(incoming, ignore_errors=True)
    if os.path.lexists(rollback) and not rollback.is_symlink() and rollback.is_dir():
        shutil.rmtree(rollback, ignore_errors=True)
    journal.unlink(missing_ok=True)
    return True


def recover_destination(dest_arg: str) -> None:
    """Explicitly recover an interrupted publish in dest_arg under the destination lock (#120, #132)."""
    reject_bad_path_chars(dest_arg, "OUTPUT_DIR")
    dest_abs = Path(os.path.abspath(dest_arg))
    ensure_no_symlinks_in_existing_chain(dest_abs, "OUTPUT_DIR")
    if not os.path.isdir(dest_abs) or dest_abs.is_symlink():
        fail(f"OUTPUT_DIR is not an existing directory: {dest_abs}")
    dest_real = Path(os.path.realpath(str(dest_abs)))
    lock_fd = open_dest_lock(dest_real)
    try:
        reconcile_publish_journal(dest_real)
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)


def publish_themes(stage_arg: str, dest_arg: str, project_arg: str, upstream_arg: str) -> None:
    pin = load_pin()
    stage_real = Path(stage_arg).resolve(strict=True)
    dest_abs = Path(os.path.abspath(dest_arg))
    ensure_no_symlinks_in_existing_chain(dest_abs, "OUTPUT_DIR")
    dest_real = Path(os.path.realpath(str(dest_abs)))

    lock_fd = open_dest_lock(dest_real)
    try:
        # Reconcile any abrupt-exit interrupted publish under lock BEFORE checking targets (#120, #132).
        if os.path.isdir(dest_real) and not dest_real.is_symlink():
            reconcile_publish_journal(dest_real)
        dest_real = validate_destination(str(dest_real), project_arg, upstream_arg)
        dest_real.mkdir(parents=True, exist_ok=True)
        ensure_no_symlinks_in_existing_chain(dest_real, "OUTPUT_DIR")

        existed_before = {tid: os.path.lexists(dest_real / tid) for tid in THEME_IDS}
        incoming = Path(tempfile.mkdtemp(prefix=".whitesur-lavender-incoming.", dir=dest_real))
        rollback = Path(tempfile.mkdtemp(prefix=".whitesur-lavender-rollback.", dir=dest_real))
        os.chmod(incoming, 0o700)
        os.chmod(rollback, 0o700)
        write_publish_journal(dest_real, "staging", incoming, rollback, existed_before)

        moved_old: list[str] = []
        placed_new: list[str] = []
        crash_after_first = os.environ.get("M9_TEST_CRASH_AFTER_FIRST_RENAME") == "1"
        try:
            for tid in THEME_IDS:
                src = stage_real / tid
                dst = incoming / tid
                shutil.copytree(src, dst, symlinks=True)
                write_ownership_stamp(dst, tid, pin["commit"])

            write_publish_journal(dest_real, "switching", incoming, rollback, existed_before)
            rename_count = 0
            for tid in THEME_IDS:
                existing = dest_real / tid
                if os.path.lexists(existing):
                    if not is_owned_theme_dir(existing, tid):
                        fail(f"refusing to overwrite unowned path under lock: {existing}")
                    os.rename(existing, rollback / tid)
                    moved_old.append(tid)
                    rename_count += 1
                    if crash_after_first and rename_count == 1:
                        os._exit(99)

            for tid in THEME_IDS:
                os.rename(incoming / tid, dest_real / tid)
                placed_new.append(tid)
                rename_count += 1
                if crash_after_first and rename_count == 1:
                    os._exit(99)

            write_publish_journal(dest_real, "committed", incoming, rollback, existed_before)
        except BaseException:
            for tid in reversed(placed_new):
                placed = dest_real / tid
                if os.path.lexists(placed):
                    try:
                        os.rename(placed, incoming / tid)
                    except OSError:
                        shutil.rmtree(placed, ignore_errors=True)
            for tid in reversed(moved_old):
                backed = rollback / tid
                if os.path.lexists(backed):
                    os.rename(backed, dest_real / tid)
            write_publish_journal(dest_real, "rolled_back", incoming, rollback, existed_before)
            shutil.rmtree(incoming, ignore_errors=True)
            shutil.rmtree(rollback, ignore_errors=True)
            (dest_real / PUBLISH_JOURNAL).unlink(missing_ok=True)
            raise

        shutil.rmtree(rollback, ignore_errors=True)
        shutil.rmtree(incoming, ignore_errors=True)
        (dest_real / PUBLISH_JOURNAL).unlink(missing_ok=True)
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
        finally:
            os.close(lock_fd)


# ---------------------------------------------------------------------------
# Safe read-only upstream update review
# ---------------------------------------------------------------------------

def validate_proposed_pin_path(out_arg: str, project_arg: str, upstream_arg: str) -> Path:
    reject_bad_path_chars(out_arg, "PROPOSED_PIN_OUT")
    project_real = Path(project_arg).resolve(strict=True)
    upstream_real = Path(upstream_arg).resolve(strict=True)
    out_abs = Path(os.path.abspath(out_arg))
    ensure_no_symlinks_in_existing_chain(out_abs, "PROPOSED_PIN_OUT")
    out_real = Path(os.path.realpath(str(out_abs)))

    if out_real == PIN_FILE.resolve():
        fail("refusing to overwrite active pin icons/whitesur-pin.json directly; review the proposal first")
    if out_real == upstream_real or out_real.is_relative_to(upstream_real):
        fail(f"refusing to write proposal into upstream clone: {out_real}")
    if out_real.is_relative_to(project_real / ".git") or out_real.is_relative_to(project_real / "reference"):
        fail(f"refusing to write proposal inside .git or reference/: {out_real}")
    if out_real.is_relative_to(project_real):
        rel = out_real.relative_to(project_real)
        if is_git_worktree(project_real):
            if not git_path_is_ignored_and_untracked(project_real, rel):
                fail(f"refusing to write proposal into trackable project path: {rel.as_posix()}")
        else:
            if not out_real.is_relative_to(project_real / "dev" / "build"):
                fail(f"refusing to write proposal into source-archive path outside dev/build/: {rel.as_posix()}")
    if os.path.lexists(out_real) and os.path.isdir(out_real):
        fail(f"PROPOSED_PIN_OUT is a directory, expected file path: {out_real}")
    return out_real


def upstream_icon_fingerprint(export_root: Path, rel_posix: str) -> tuple[str, str] | None:
    """Locate an icon in an upstream export and return (source_location, fingerprint)."""
    candidates: list[Path] = []
    if rel_posix.startswith("places/scalable/"):
        candidates.append(export_root / f"colors/color-{SOURCE}" / Path(rel_posix).name)
    candidates.append(export_root / "plasma" / rel_posix)
    candidates.append(export_root / "src" / rel_posix)
    candidates.append(export_root / "links" / rel_posix)
    for cand in candidates:
        if os.path.lexists(cand):
            loc = cand.relative_to(export_root).as_posix()
            if cand.is_symlink():
                return (loc, "->" + os.readlink(cand))
            if cand.is_file():
                return (loc, sha256_bytes(cand.read_bytes()))
    return None


def review_upstream_update(
    export_arg: str,
    target_commit: str,
    target_ref: str,
    proposed_out_arg: str,
    project_arg: str,
    upstream_arg: str,
    custom_arg: str | None = None,
    old_export_arg: str | None = None,
) -> None:
    """Inspect a candidate upstream export without executing its install.sh."""
    pin = load_pin()
    proposed_out = validate_proposed_pin_path(proposed_out_arg, project_arg, upstream_arg)

    root = Path(export_arg)
    if root.is_symlink() or not root.is_dir():
        fail(f"candidate export must be a non-symlink directory: {root}")
    root_real = root.resolve(strict=True)
    old_real = Path(old_export_arg).resolve(strict=True) if old_export_arg else None
    custom_dir = resolve_custom_dir(custom_arg)

    blockers: list[str] = []
    report: list[str] = []

    def add(line: str = "") -> None:
        report.append(line)

    add("WhiteSur Upstream Update Review (read-only; install.sh NOT executed)")
    add("====================================================================")
    add(f"Current pin:    {pin['release']} ({pin['commit']})")
    add(f"Candidate ref:  {target_ref} ({target_commit})")
    add(f"Active pin:     {PIN_FILE} (untouched)")
    add(f"Proposed pin:   {proposed_out}")
    add("")

    # 1. Symlinks
    add("## 1. Symlinks")
    new_links, link_problems = scan_export_symlinks(root_real)
    add(f"Count: {len(new_links)} (pinned: {pin['symlink_count']}, delta: {len(new_links) - pin['symlink_count']:+d})")
    if link_problems:
        for prob in link_problems[:20]:
            blockers.append(f"symlink: {prob}")
            add(f"  BLOCKER: {prob}")
        if len(link_problems) > 20:
            add(f"  ... and {len(link_problems) - 20} more symlink problems")
    else:
        add("Escaping or absolute symlinks: 0")
    if old_real is not None:
        old_links, _ = scan_export_symlinks(old_real)
        added_l = sorted(set(new_links) - set(old_links))
        removed_l = sorted(set(old_links) - set(new_links))
        changed_l = sorted(k for k in set(new_links) & set(old_links) if new_links[k] != old_links[k])
        add(f"Diff vs pinned commit: +{len(added_l)} added, -{len(removed_l)} removed, ~{len(changed_l)} retargeted")
        for k in added_l[:10]:
            add(f"  + {k} -> {new_links[k]}")
        for k in removed_l[:10]:
            add(f"  - {k} -> {old_links[k]}")
        for k in changed_l[:10]:
            add(f"  ~ {k}: {old_links[k]} -> {new_links[k]}")
    add("")

    # 2. Installer (install.sh)
    add("## 2. Installer (install.sh)")
    new_inst_sha = ""
    try:
        inst_path = ensure_confined_entry(root_real, "install.sh", expect_dir=False)
        inst_bytes = inst_path.read_bytes()
        new_inst_sha = sha256_bytes(inst_bytes)
        changed = new_inst_sha != pin["installer_sha256"]
        add(f"SHA-256: {new_inst_sha} ({'CHANGED' if changed else 'unchanged'})")
        try:
            patch_installer_text(inst_bytes.decode("utf-8"))
            add("Patch anchors & bash -n check: PASS (not executed)")
        except SystemExit as exc:
            blockers.append(f"install.sh patch check failed: {exc}")
            add(f"  BLOCKER: {exc}")
        if changed and old_real is not None and (old_real / "install.sh").is_file():
            old_text = (old_real / "install.sh").read_text(encoding="utf-8", errors="replace")
            new_text = inst_bytes.decode("utf-8", errors="replace")
            # Keep the full installer digest in the pin. Report the diff for
            # the code the project builds, excluding the unused dark branch.
            try:
                old_text, new_text = without_dark_variant(old_text), without_dark_variant(new_text)
            except SystemExit:
                pass  # An anchor moved. Show the raw diff for diagnosis.
            old_lines, new_lines = old_text.splitlines(), new_text.splitlines()
            diff = list(difflib.unified_diff(old_lines, new_lines, fromfile="pinned/install.sh", tofile="candidate/install.sh", lineterm=""))
            add(f"Unified diff ({len(diff)} lines):")
            for dl in diff[:80]:
                add(f"  {dl}")
            if len(diff) > 80:
                add(f"  ... ({len(diff) - 80} more diff lines truncated)")
    except SystemExit as exc:
        blockers.append(f"install.sh inspection failed: {exc}")
        add(f"  BLOCKER: {exc}")
    add("")

    # 3. 25 color inputs
    add("## 3. Color inputs (colors/color-purple/)")
    new_purple_manifest: dict[str, dict[str, Any]] = {}
    old_purple = pin["purple_manifest"]
    src_pattern = re.compile("|".join(re.escape(k) for k in COLORS), re.I)
    try:
        purple_dir = ensure_confined_entry(root_real, f"colors/color-{SOURCE}", expect_dir=True)
        entries = sorted(p.name for p in purple_dir.iterdir())
        added_p = sorted(set(entries) - set(old_purple))
        removed_p = sorted(set(old_purple) - set(entries))
        changed_p: list[str] = []
        all_seen: set[str] = set()
        for name in entries:
            try:
                p = ensure_confined_entry(root_real, f"colors/color-{SOURCE}/{name}", expect_dir=False)
                raw = p.read_bytes()
                h = sha256_bytes(raw)
                check_svg_xml(raw, f"colors/color-{SOURCE}/{name}", require_svg_ns=True)
                txt = raw.decode("utf-8")
                paints = sorted({m.lower() for m in src_pattern.findall(txt)})
                if not paints:
                    blockers.append(f"color input {name} contains no expected purple paints")
                all_seen.update(paints)
                recolored = src_pattern.sub(lambda m: COLORS[m[0].lower()], txt).encode("utf-8")
                check_svg_xml(recolored, f"dry-run recolor {name}", require_svg_ns=True)
                check_svg_external(recolored, f"dry-run recolor {name}")
                new_purple_manifest[name] = {"sha256": h, "paints": paints}
                if name in old_purple and (old_purple[name]["sha256"] != h or sorted(old_purple[name]["paints"]) != paints):
                    changed_p.append(name)
            except SystemExit as exc:
                blockers.append(f"color input {name}: {exc}")
                add(f"  BLOCKER ({name}): {exc}")
        if all_seen != set(COLORS):
            blockers.append(f"color-purple palette set is {sorted(all_seen)}, expected {sorted(COLORS)}")
        add(f"Files: {len(entries)} (pinned: {len(old_purple)}), +{len(added_p)} added, -{len(removed_p)} removed, ~{len(changed_p)} changed")
        for n in added_p:
            add(f"  + {n} paints={new_purple_manifest.get(n, {}).get('paints')}")
        for n in removed_p:
            add(f"  - {n}")
        for n in changed_p:
            add(f"  ~ {n} sha256={new_purple_manifest[n]['sha256'][:16]} paints={new_purple_manifest[n]['paints']}")
        if not added_p and not removed_p and not changed_p:
            add("All 25 color-purple inputs unchanged; dry-run recolor/xmllint/rsvg passed.")
    except SystemExit as exc:
        blockers.append(f"colors/color-purple: {exc}")
        add(f"  BLOCKER: {exc}")
    add("")

    # 4. Launcher files
    add("## 4. Launcher files (plasma/ & src/status/32/start-here.svg)")
    new_plasma_launchers: dict[str, str] = {}
    for rel, old_sha in pin["plasma_launchers"].items():
        try:
            p = ensure_confined_entry(root_real, rel, expect_dir=False)
            raw = p.read_bytes()
            h = sha256_bytes(raw)
            new_plasma_launchers[rel] = h
            txt = raw.decode("utf-8")
            has_kde = any(m in txt for m in KDE_PLASMA_MARKERS)
            has_apple = any(m in txt for m in APPLE_PATH_MARKERS)
            status = "CHANGED" if h != old_sha else "unchanged"
            add(f"  {rel}: {status} (kde={has_kde}, apple={has_apple})")
            if has_apple or not has_kde:
                blockers.append(f"launcher {rel} unexpected artwork (kde={has_kde}, apple={has_apple})")
        except SystemExit as exc:
            blockers.append(f"launcher {rel}: {exc}")
            add(f"  BLOCKER ({rel}): {exc}")

    new_status32_sha = ""
    try:
        s32 = ensure_confined_entry(root_real, "src/status/32/start-here.svg", expect_dir=False)
        new_status32_sha = sha256_bytes(s32.read_bytes())
        st_lbl = "CHANGED" if new_status32_sha != pin["status32_start_here_sha256"] else "unchanged"
        add(f"  src/status/32/start-here.svg: {st_lbl}")
        if (root_real / "plasma/places/24/start-here.svg").is_file():
            derive_status32_launcher((root_real / "plasma/places/24/start-here.svg").read_text(encoding="utf-8"))
            add("  32 px KDE Plasma derivation check: PASS")
    except SystemExit as exc:
        blockers.append(f"status/32 launcher: {exc}")
        add(f"  BLOCKER (status/32): {exc}")
    add("")

    # 5. License files
    add("## 5. License & attribution files (COPYING, AUTHORS)")
    new_copying_sha = ""
    new_authors_sha = ""
    for fname, pin_key in (("COPYING", "copying_sha256"), ("AUTHORS", "authors_sha256")):
        try:
            p = ensure_confined_entry(root_real, fname, expect_dir=False)
            raw = p.read_bytes()
            h = sha256_bytes(raw)
            if fname == "COPYING":
                new_copying_sha = h
            else:
                new_authors_sha = h
            changed = h != pin[pin_key]
            add(f"  {fname}: {h} ({'CHANGED - manual license review required' if changed else 'unchanged'})")
            if changed and old_real is not None and (old_real / fname).is_file():
                old_l = (old_real / fname).read_text(encoding="utf-8", errors="replace").splitlines()
                new_l = raw.decode("utf-8", errors="replace").splitlines()
                diff = list(difflib.unified_diff(old_l, new_l, fromfile=f"pinned/{fname}", tofile=f"candidate/{fname}", lineterm=""))
                for dl in diff[:40]:
                    add(f"    {dl}")
        except SystemExit as exc:
            blockers.append(f"license file {fname}: {exc}")
            add(f"  BLOCKER ({fname}): {exc}")
    add("")

    # 6. Namespace exceptions (#111)
    add("## 6. SVG namespace exceptions (src/**/*.svg)")
    new_missing_ns: list[str] = []
    xml_errors: list[str] = []
    for dirpath, dirnames, filenames in os.walk(root_real / "src", followlinks=False):
        dirnames.sort()
        for fname in sorted(filenames):
            if not fname.endswith(".svg"):
                continue
            fpath = Path(dirpath) / fname
            if fpath.is_symlink():
                continue
            rel = fpath.relative_to(root_real).as_posix()
            raw = fpath.read_bytes()
            try:
                root_el = ET.fromstring(raw)
            except ET.ParseError as exc:
                xml_errors.append(f"{rel}: {exc}")
                continue
            if root_el.tag == SVG_NS:
                continue
            if root_el.tag != "svg":
                xml_errors.append(f"{rel}: unexpected root tag {root_el.tag!r}")
                continue
            new_missing_ns.append(rel)
            norm_txt, count = SVG_ROOT_RE.subn('<svg xmlns="http://www.w3.org/2000/svg"', raw.decode("utf-8"), count=1)
            if count != 1:
                xml_errors.append(f"{rel}: could not insert xmlns")
            else:
                try:
                    if ET.fromstring(norm_txt.encode("utf-8")).tag != SVG_NS:
                        xml_errors.append(f"{rel}: normalization failed")
                except ET.ParseError as exc:
                    xml_errors.append(f"{rel}: post-normalization XML error: {exc}")
    new_missing_ns.sort()
    old_missing_ns = sorted(pin["missing_ns_svgs"])
    added_ns = sorted(set(new_missing_ns) - set(old_missing_ns))
    removed_ns = sorted(set(old_missing_ns) - set(new_missing_ns))
    add(f"Count: {len(new_missing_ns)} (pinned: {len(old_missing_ns)}), +{len(added_ns)} added, -{len(removed_ns)} removed")
    for p in added_ns[:20]:
        add(f"  + {p}")
    for p in removed_ns[:20]:
        add(f"  - {p}")
    if xml_errors:
        for xe in xml_errors[:20]:
            blockers.append(f"SVG XML error: {xe}")
            add(f"  BLOCKER: {xe}")
    add("")

    # 7. Custom icon overrides (icons/custom/{all,light}/)
    add(f"## 7. Custom icon overrides ({custom_dir})")
    try:
        custom = load_and_validate_custom_layer(custom_dir)
        all_custom_keys = sorted({k for layer in CUSTOM_LAYERS for k in custom[layer]})
        if not all_custom_keys:
            add("No custom icons present.")
        else:
            changed_overrides = 0
            for layer in CUSTOM_LAYERS:
                for rel_key, (kind, payload) in sorted(custom[layer].items()):
                    cand_fp = upstream_icon_fingerprint(root_real, rel_key)
                    old_fp = upstream_icon_fingerprint(old_real, rel_key) if old_real is not None else None
                    if cand_fp is None and old_fp is None:
                        add(f"  {layer}/{rel_key}: brand-new custom {kind} (not in upstream)")
                    elif old_real is None:
                        if cand_fp is None:
                            add(f"  {layer}/{rel_key}: brand-new custom {kind} (not in candidate upstream)")
                        else:
                            add(f"  {layer}/{rel_key}: overrides upstream {cand_fp[0]} (pinned export unavailable for diff)")
                    elif cand_fp != old_fp:
                        changed_overrides += 1
                        if old_fp is None and cand_fp is not None:
                            add(f"  {layer}/{rel_key}: UPSTREAM ADDED ICON NOW OVERRIDDEN ({cand_fp[0]}: {cand_fp[1][:16]})")
                        elif old_fp is not None and cand_fp is None:
                            add(f"  {layer}/{rel_key}: UPSTREAM REMOVED OVERRIDDEN ICON (was {old_fp[0]})")
                        else:
                            assert old_fp is not None and cand_fp is not None
                            add(f"  {layer}/{rel_key}: UPSTREAM CHANGED OVERRIDDEN ICON ({cand_fp[0]}: {old_fp[1][:16]} -> {cand_fp[1][:16]})")
                    else:
                        assert cand_fp is not None
                        add(f"  {layer}/{rel_key}: overrides upstream {cand_fp[0]} (upstream unchanged)")

                    # Verify custom alias target still exists in custom layer or candidate export.
                    if kind == "link":
                        assert isinstance(payload, str)
                        target_rel = os.path.normpath(os.path.join(Path(rel_key).parent.as_posix(), payload))
                        in_custom = target_rel in custom["all"] or target_rel in custom[layer]
                        in_upstream = upstream_icon_fingerprint(root_real, target_rel) is not None
                        if not in_custom and not in_upstream:
                            blockers.append(f"custom alias {layer}/{rel_key} -> {payload} target {target_rel} missing in candidate upstream")
                            add(f"    BLOCKER: alias target {target_rel} not found in custom layer or candidate upstream")
            add(f"Summary: {sum(len(custom[l]) for l in CUSTOM_LAYERS)} custom entry(ies), {changed_overrides} upstream override change(s).")
    except SystemExit as exc:
        blockers.append(f"custom icon layer validation failed: {exc}")
        add(f"  BLOCKER: {exc}")
    add("")

    proposed_pin = {
        "schema_version": 1,
        "upstream_url": pin["upstream_url"],
        "release": target_ref,
        "commit": target_commit,
        "artwork_license": pin["artwork_license"],
        "installer_sha256": new_inst_sha,
        "copying_sha256": new_copying_sha,
        "authors_sha256": new_authors_sha,
        "status32_start_here_sha256": new_status32_sha,
        "plasma_launchers": new_plasma_launchers,
        "purple_manifest": new_purple_manifest,
        "missing_ns_svgs": new_missing_ns,
        "symlink_count": len(new_links),
    }
    proposed_out.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_bytes(proposed_out, (json.dumps(proposed_pin, indent=2) + "\n").encode("utf-8"), mode=0o644)

    add("## Summary")
    if blockers:
        add(f"STATUS: BLOCKED ({len(blockers)} blocker(s) require code/review changes before adopting)")
        for b in blockers:
            add(f"  - {b}")
    else:
        add("STATUS: READY FOR HUMAN REVIEW (0 blockers; active pin NOT changed)")
        add(f"Next: inspect `diff -u {PIN_FILE} {proposed_out}` and review any install.sh/license/override changes before adopting.")

    print("\n".join(report))
    if blockers:
        raise SystemExit(2)


def main(argv: list[str] | None = None) -> None:
    os.umask(0o022)
    args = sys.argv[1:] if argv is None else argv
    if not args or args[0] in ("-h", "--help"):
        print(__doc__.strip())
        raise SystemExit(0 if args else 2)
    if args == ["--print-pin"]:
        print(load_pin()["commit"])
        return
    if args[0] == "--preflight" and len(args) in (1, 2):
        run_preflight(args[1] if len(args) == 2 else None)
        return
    if args[0] == "--validate-custom" and len(args) in (1, 2):
        cdir = resolve_custom_dir(args[1] if len(args) == 2 else None)
        load_and_validate_custom_layer(cdir)
        return
    if len(args) == 4 and args[0] == "--check-dest":
        dest_real = validate_destination(args[1], args[2], args[3])
        print(str(dest_real))
        return
    if len(args) == 2 and args[0] == "--recover-dest":
        recover_destination(args[1])
        return
    if args[0] == "--apply-custom" and len(args) in (2, 3):
        apply_custom_layer(args[1], args[2] if len(args) == 3 else None)
        return
    if args[0] == "--verify" and len(args) in (3, 4):
        verify_staged_build(args[1], args[2], args[3] if len(args) == 4 else None)
        return
    if len(args) == 5 and args[0] == "--publish":
        publish_themes(args[1], args[2], args[3], args[4])
        return
    if args[0] == "--review-update" and len(args) in (8, 9):
        old_exp = args[8] if len(args) == 9 else None
        review_upstream_update(args[1], args[2], args[3], args[4], args[5], args[6], args[7], old_exp)
        return
    if len(args) == 1 and not args[0].startswith("-"):
        patch_export_tree(args[0])
        return
    fail(f"invalid arguments: {args!r}\n{__doc__.strip()}")


if __name__ == "__main__":
    main()
