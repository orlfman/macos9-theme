#!/usr/bin/env python3
"""Checks Firefox theme CSS selectors and Firefox major-version compatibility
against the installed Firefox omni.ja archives and application.ini.

Run before every release and after any Firefox upgrade:
  python3 -I tools/check-firefox-selectors.py

Exit codes:
  0  all referenced #id selectors and ::part(...) names exist in omni.ja, and
     installed Firefox major version is inside firefox/version.json's tested range
  1  one or more selectors are missing from omni.ja (or required files unreadable)
  3  selectors OK, but installed Firefox major version is outside the tested range
     (warning emitted; pass --allow-untested-version to treat as warning only)

SPDX-License-Identifier: BSD-2-Clause
"""

from __future__ import annotations

import argparse
import configparser
import json
import pathlib
import re
import subprocess
import sys


def strip_css_comments(text: str) -> str:
    return re.sub(r"/\*[\s\S]*?\*/", "", text)


def extract_css_ids_and_parts(css_dir: pathlib.Path) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Extract #id selectors (ignoring hex colors in declarations) and ::part() names."""
    id_refs: dict[str, list[str]] = {}
    part_refs: dict[str, list[str]] = {}

    for css_file in sorted(css_dir.rglob("*.css")):
        raw = strip_css_comments(css_file.read_text(encoding="utf-8"))
        # Extract selector tokens by scanning outside declaration value segments:
        # In nested CSS, every selector line/clause appears before '{' and after
        # either start-of-file, '{', '}', or ';'. Property declarations contain ':'
        # followed by a value ending in ';'. Split on '{' and inspect only the
        # prelude after the last ';' or '}' to cleanly separate selectors from values!
        rel = str(css_file.relative_to(css_dir))
        pos = 0
        for m in re.finditer(r"\{", raw):
            chunk = raw[pos : m.start()]
            pos = m.end()
            # Keep only text after the last ';' or '}' in chunk (the actual selector prelude)
            last_sep = max(chunk.rfind(";"), chunk.rfind("}"))
            prelude = chunk[last_sep + 1 :].strip()
            if not prelude or prelude.startswith("@"):
                continue

            for im in re.finditer(r"#([A-Za-z_][A-Za-z0-9_-]*)", prelude):
                ident = im.group(1)
                id_refs.setdefault(ident, []).append(rel)

            for pm in re.finditer(r"::part\(\s*([A-Za-z0-9_-]+)\s*\)", prelude):
                part = pm.group(1)
                part_refs.setdefault(part, []).append(rel)

    return id_refs, part_refs


def scan_omni_ja(ja_paths: list[pathlib.Path]) -> tuple[set[str], set[str], int]:
    """Extract declared element IDs and shadow parts from Firefox MozJar omni.ja archives."""
    found_ids: set[str] = set()
    found_parts: set[str] = set()
    files_scanned = 0

    id_pat = re.compile(r"""(?:(?<![\w:-])id\s*=\s*["']([A-Za-z0-9_-]+)["']|getElementById\(\s*["']([A-Za-z0-9_-]+)["']\s*\)|setAttribute\(\s*["']id["']\s*,\s*["']([A-Za-z0-9_-]+)["']\s*\))""")
    part_pat = re.compile(r"""(?<![\w:-])part\s*=\s*["']([^"']+)["']""")

    for ja in ja_paths:
        if not ja.is_file():
            continue
        # List files inside MozJar (unzip exits 2 on compensated MozJar header while listing cleanly).
        lp = subprocess.run(["unzip", "-l", str(ja)], capture_output=True, text=True)
        if lp.returncode not in (0, 1, 2) or not lp.stdout:
            raise RuntimeError(f"Failed to list {ja} (rc={lp.returncode})")

        targets = []
        for line in lp.stdout.splitlines():
            parts = line.split()
            if len(parts) >= 4:
                name = parts[-1]
                if name.startswith(("chrome/browser/content/", "chrome/toolkit/content/", "chrome/browser/skin/", "chrome/toolkit/skin/", "modules/")) and name.endswith((".xhtml", ".html", ".xml", ".js", ".mjs", ".css")):
                    targets.append(name)

        if not targets:
            continue

        # Stream all relevant chrome/module sources from omni.ja in chunks via unzip -p.
        chunk_size = 200
        for i in range(0, len(targets), chunk_size):
            batch = targets[i : i + chunk_size]
            ep = subprocess.run(["unzip", "-p", str(ja), *batch], capture_output=True, text=True, errors="replace")
            if ep.returncode not in (0, 1, 2):
                raise RuntimeError(f"Failed to extract batch from {ja} (rc={ep.returncode})")
            txt = ep.stdout
            files_scanned += len(batch)
            for m in id_pat.finditer(txt):
                val = m.group(1) or m.group(2) or m.group(3)
                if val:
                    found_ids.add(val)
            for pm in part_pat.finditer(txt):
                for tok in pm.group(1).split():
                    found_parts.add(tok)

    return found_ids, found_parts, files_scanned


def read_firefox_version(ini_path: pathlib.Path | None, default_paths: list[str]) -> tuple[str | None, int | None]:
    candidates = [ini_path] if ini_path else [pathlib.Path(p) for p in default_paths]
    for p in candidates:
        if p and p.is_file():
            cp = configparser.ConfigParser()
            cp.read(p, encoding="utf-8")
            ver = cp.get("App", "Version", fallback=None)
            if ver:
                m = re.match(r"(\d+)", ver.strip())
                return ver.strip(), (int(m.group(1)) if m else None)
    return None, None


def main() -> int:
    project = pathlib.Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description="Verify Firefox Platinum selectors against omni.ja and check Firefox version gate.")
    ap.add_argument("--css-dir", type=pathlib.Path, default=project / "firefox" / "chrome")
    ap.add_argument("--version-json", type=pathlib.Path, default=project / "firefox" / "version.json")
    ap.add_argument("--application-ini", type=pathlib.Path, default=None)
    ap.add_argument("--omni-ja", type=pathlib.Path, action="append", default=None)
    ap.add_argument("--version-only", action="store_true", help="Only run the Firefox major version gate check.")
    ap.add_argument("--allow-untested-version", action="store_true", help="Warn on untested Firefox major versions without returning exit code 3.")
    args = ap.parse_args()

    meta = json.loads(args.version_json.read_text(encoding="utf-8"))
    ver_str, major = read_firefox_version(args.application_ini, meta["application_ini_paths"])
    min_maj = int(meta["tested_major_min"])
    max_maj = int(meta["tested_major_max"])

    version_ok = major is not None and min_maj <= major <= max_maj
    if ver_str is None:
        print("WARN  Firefox application.ini not found; cannot verify installed major version", file=sys.stderr)
    elif version_ok:
        print(f"PASS  firefox-version-gate (installed={ver_str}, tested={min_maj}..{max_maj})")
    else:
        print(
            f"WARN  firefox-version-gate: installed Firefox {ver_str} (major {major}) is outside tested range {min_maj}..{max_maj}; "
            "re-run tools/check-firefox-selectors.py and dev/check-firefox-m4.sh before relying on this theme",
            file=sys.stderr,
        )

    if args.version_only:
        if version_ok or args.allow_untested_version:
            return 0
        return 3

    if not args.css_dir.is_dir():
        print(f"FAIL  CSS directory not found: {args.css_dir}", file=sys.stderr)
        return 1

    id_refs, part_refs = extract_css_ids_and_parts(args.css_dir)
    if not id_refs:
        print(f"FAIL  No #id selectors found under {args.css_dir}", file=sys.stderr)
        return 1

    ja_paths = args.omni_ja if args.omni_ja else [pathlib.Path(p) for p in meta["omni_ja_paths"]]
    existing_jas = [p for p in ja_paths if p.is_file()]
    if len(existing_jas) != len(ja_paths) or not existing_jas:
        print(f"FAIL  Missing required omni.ja archive in {ja_paths}", file=sys.stderr)
        return 1

    found_ids, found_parts, files_scanned = scan_omni_ja(existing_jas)

    missing_ids = sorted(ident for ident in id_refs if ident not in found_ids)
    missing_parts = sorted(part for part in part_refs if part not in found_parts)

    print(f"INFO  scanned {files_scanned} files across {len(existing_jas)} omni.ja archive(s); checked {len(id_refs)} #id selector(s) and {len(part_refs)} ::part() selector(s)")

    failed = False
    if missing_ids:
        failed = True
        for ident in missing_ids:
            files = ", ".join(sorted(set(id_refs[ident])))
            print(f"FAIL  missing #id selector in omni.ja: #{ident} (referenced in {files})", file=sys.stderr)
    else:
        print(f"PASS  all-css-id-selectors-present ({len(id_refs)}/{len(id_refs)})")

    if missing_parts:
        failed = True
        for part in missing_parts:
            files = ", ".join(sorted(set(part_refs[part])))
            print(f"FAIL  missing ::part() in omni.ja: ::part({part}) (referenced in {files})", file=sys.stderr)
    else:
        print(f"PASS  all-css-part-selectors-present ({len(part_refs)}/{len(part_refs)})")

    if failed:
        return 1
    if not version_ok and not args.allow_untested_version:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
