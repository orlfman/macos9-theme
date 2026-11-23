#!/usr/bin/env python3
"""Fast O(N) manifest and checksum operations for install.sh and uninstall.sh.

Preserves format version 4 of $state/installed (`macos9-theme-record\\t4`) while
handling tens of thousands of installed files and symlinks (e.g. WhiteSur
Lavender's 44,619 entries) without per-file shell forks or quadratic scans.

Subcommands:
  load-meta MANIFEST VERSION HOME DATA CONFIG
      Validate MANIFEST header, kinds, and home/data/config lines; print only
      non-sum lines to stdout.
  write-meta MANIFEST
      Read non-sum lines from stdin, preserve existing sum lines from MANIFEST,
      and write MANIFEST atomically.
  record-sums MANIFEST SOURCE TARGET [KEYS_FILE]
      Compute SHA-256 / symlink targets under SOURCE -> TARGET, append any
      missing sum lines to MANIFEST atomically, and optionally write the
      recorded (path, val) lines to KEYS_FILE for prune-sums.
  record-single-sum MANIFEST TARGET VAL
      Ensure `sum\\tTARGET\\tVAL` is in MANIFEST atomically.
  prune-sums MANIFEST TARGET KEYS_FILE
      Drop sum lines under TARGET (exact or prefix TARGET/) whose (path, val)
      is not listed in KEYS_FILE; write MANIFEST atomically.
  prune-single-sum MANIFEST TARGET KEEP_VAL
      Drop sum lines for TARGET whose value != KEEP_VAL; write MANIFEST atomically.
  drop-sums MANIFEST TARGET
      Drop all sum lines for TARGET (exact or prefix TARGET/); write MANIFEST atomically.
  check-file MANIFEST PATH
      Exit 0 iff PATH is a non-symlink regular file matching a sum line.
  check-link MANIFEST PATH
      Exit 0 iff PATH is a symlink whose readlink target matches a sum line.
  check-tree MANIFEST DIR_PATH
      Exit 0 iff every file, symlink, and subdirectory under DIR_PATH matches
      the recorded sum lines (no additions, no edits, no added empty dirs).
  clean-dir MANIFEST DIR_PATH [--dry-run]
      Remove matching installed files/links and empty installed dirs under
      DIR_PATH, keeping user-added or edited items. Prints `REMOVED` or
      `KEPT\\t<count>\\t<preview>`.

SPDX-License-Identifier: BSD-2-Clause
"""
from __future__ import annotations

import hashlib
import os
import stat
import sys
import tempfile
from pathlib import Path

VALID_KINDS = frozenset({"home", "data", "config", "madedir", "file", "dir", "link", "displaced", "temp", "sum"})


def die(msg: str) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(1)


def sha256_file(path: str | Path) -> str:
    with open(path, "rb") as fh:
        return hashlib.file_digest(fh, "sha256").hexdigest()


def atomic_write_lines(manifest: Path, lines: list[str]) -> None:
    manifest.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=".installed.new.", dir=manifest.parent)
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", errors="surrogateescape") as fh:
            for line in lines:
                fh.write(line)
                fh.write("\n")
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, manifest)
    except BaseException:
        try:
            tmp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


def read_manifest_lines(manifest: Path) -> list[str]:
    if not manifest.exists():
        return []
    with open(manifest, "r", encoding="utf-8", errors="surrogateescape") as fh:
        return fh.read().splitlines()


def cmd_load_meta(manifest_arg: str, version: str, home: str, data: str, config: str) -> None:
    manifest = Path(manifest_arg)
    if not os.path.lexists(manifest):
        return
    st = os.lstat(manifest)
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode):
        die(f"{manifest} isn't a regular file")
    lines = read_manifest_lines(manifest)
    if not lines or lines[0] != f"macos9-theme-record\t{version}":
        die(f"{manifest} has a format this version doesn't know; nothing was changed")
    meta: list[str] = [lines[0]]
    for line in lines[1:]:
        kind, sep, value = line.partition("\t")
        if not sep or kind not in VALID_KINDS:
            die(f"{manifest} has an entry this version doesn't know ({kind}); nothing was changed")
        if kind == "home" and value != home:
            die(f"{manifest} was made for the home {value}, not {home}; nothing was changed")
        elif kind == "data" and value != data:
            die(
                f"{manifest} was made with the data folder {value} (XDG_DATA_HOME), not {data}; "
                f"run this again with XDG_DATA_HOME={value}; nothing was changed"
            )
        elif kind == "config" and value != config:
            die(
                f"{manifest} was made with the config folder {value} (XDG_CONFIG_HOME), not {config}; "
                f"run this again with XDG_CONFIG_HOME={value}; nothing was changed"
            )
        if kind != "sum":
            meta.append(line)
    sys.stdout.write("\n".join(meta) + "\n")


def cmd_write_meta(manifest_arg: str) -> None:
    manifest = Path(manifest_arg)
    meta_lines = sys.stdin.read().splitlines()
    existing = read_manifest_lines(manifest)
    sum_lines = [ln for ln in existing[1:] if ln.startswith("sum\t")]
    atomic_write_lines(manifest, meta_lines + sum_lines)


def collect_source_sums(source_arg: str, target_arg: str) -> dict[str, str]:
    source = Path(source_arg)
    target = target_arg.rstrip("/")
    sums: dict[str, str] = {}
    st = os.lstat(source)
    if stat.S_ISREG(st.st_mode):
        sums[target] = sha256_file(source)
        return sums
    if not stat.S_ISDIR(st.st_mode):
        die(f"unexpected source type: {source}")
    src_str = str(source)
    src_prefix_len = len(src_str.rstrip("/")) + 1
    for dirpath, dirnames, filenames in os.walk(src_str, followlinks=False):
        for name in dirnames:
            full = os.path.join(dirpath, name)
            if os.path.islink(full):
                rel = full[src_prefix_len:]
                sums[f"{target}/{rel}"] = "->" + os.readlink(full)
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = full[src_prefix_len:]
            if os.path.islink(full):
                sums[f"{target}/{rel}"] = "->" + os.readlink(full)
            elif os.path.isfile(full):
                sums[f"{target}/{rel}"] = sha256_file(full)
    return sums


def cmd_record_sums(manifest_arg: str, source_arg: str, target_arg: str, keys_file: str | None) -> None:
    manifest = Path(manifest_arg)
    new_sums = collect_source_sums(source_arg, target_arg)
    if keys_file:
        with open(keys_file, "w", encoding="utf-8", errors="surrogateescape") as fh:
            for path, val in new_sums.items():
                fh.write(f"{path}\t{val}\n")
    lines = read_manifest_lines(manifest)
    existing = set(lines)
    added = False
    for path, val in new_sums.items():
        entry = f"sum\t{path}\t{val}"
        if entry not in existing:
            lines.append(entry)
            existing.add(entry)
            added = True
    if added or not manifest.exists():
        atomic_write_lines(manifest, lines)


def cmd_record_single_sum(manifest_arg: str, target_arg: str, val: str) -> None:
    manifest = Path(manifest_arg)
    lines = read_manifest_lines(manifest)
    entry = f"sum\t{target_arg}\t{val}"
    if entry not in set(lines):
        lines.append(entry)
        atomic_write_lines(manifest, lines)


def cmd_prune_sums(manifest_arg: str, target_arg: str, keys_file: str) -> None:
    manifest = Path(manifest_arg)
    keep_pairs: set[str] = set()
    with open(keys_file, "r", encoding="utf-8", errors="surrogateescape") as fh:
        for line in fh:
            keep_pairs.add(line.rstrip("\n"))
    target = target_arg.rstrip("/")
    prefix = target + "/"
    lines = read_manifest_lines(manifest)
    out: list[str] = []
    changed = False
    for line in lines:
        if line.startswith("sum\t"):
            rest = line[4:]
            path, sep, _ = rest.partition("\t")
            if sep and (path == target or path.startswith(prefix)) and rest not in keep_pairs:
                changed = True
                continue
        out.append(line)
    if changed:
        atomic_write_lines(manifest, out)


def cmd_prune_single_sum(manifest_arg: str, target_arg: str, keep_val: str) -> None:
    manifest = Path(manifest_arg)
    target = target_arg.rstrip("/")
    prefix = target + "/"
    keep_rest = f"{target}\t{keep_val}"
    lines = read_manifest_lines(manifest)
    out: list[str] = []
    changed = False
    for line in lines:
        if line.startswith("sum\t"):
            rest = line[4:]
            path, sep, _ = rest.partition("\t")
            if sep and (path == target or path.startswith(prefix)) and rest != keep_rest:
                changed = True
                continue
        out.append(line)
    if changed:
        atomic_write_lines(manifest, out)


def cmd_drop_sums(manifest_arg: str, target_arg: str) -> None:
    manifest = Path(manifest_arg)
    if not manifest.exists():
        return
    target = target_arg.rstrip("/")
    prefix = target + "/"
    lines = read_manifest_lines(manifest)
    out: list[str] = []
    changed = False
    for line in lines:
        if line.startswith("sum\t"):
            rest = line[4:]
            path, sep, _ = rest.partition("\t")
            if sep and (path == target or path.startswith(prefix)):
                changed = True
                continue
        out.append(line)
    if changed:
        atomic_write_lines(manifest, out)


def load_target_sums(manifest: Path, target_dir: str) -> tuple[dict[str, set[str]], set[str]]:
    target = target_dir.rstrip("/")
    prefix = target + "/"
    expected: dict[str, set[str]] = {}
    our_dirs: set[str] = set()
    for line in read_manifest_lines(manifest):
        if not line.startswith("sum\t"):
            continue
        rest = line[4:]
        path, sep, val = rest.partition("\t")
        if not sep or not path.startswith(prefix):
            continue
        expected.setdefault(path, set()).add(val)
        parent = os.path.dirname(path)
        while parent.startswith(prefix) and parent not in our_dirs:
            our_dirs.add(parent)
            parent = os.path.dirname(parent)
    return expected, our_dirs


def cmd_check_file(manifest_arg: str, path_arg: str) -> None:
    if os.path.islink(path_arg) or not os.path.isfile(path_arg):
        raise SystemExit(1)
    want = f"sum\t{path_arg}\t{sha256_file(path_arg)}"
    for line in read_manifest_lines(Path(manifest_arg)):
        if line == want:
            return
    raise SystemExit(1)


def cmd_check_link(manifest_arg: str, path_arg: str) -> None:
    if not os.path.islink(path_arg):
        raise SystemExit(1)
    link_target = os.readlink(path_arg)
    if "\n" in link_target:
        # Format 4 lines never contain embedded newlines; an edited link with
        # a newline never matches any recorded entry.
        raise SystemExit(1)
    want = f"sum\t{path_arg}\t->{link_target}"
    for line in read_manifest_lines(Path(manifest_arg)):
        if line == want:
            return
    raise SystemExit(1)


def item_matches(full: str, expected: dict[str, set[str]]) -> bool:
    vals = expected.get(full)
    if not vals:
        return False
    if os.path.islink(full):
        target = os.readlink(full)
        if "\n" in target:
            return False
        return ("->" + target) in vals
    if os.path.isfile(full):
        return sha256_file(full) in vals
    return False


def cmd_check_tree(manifest_arg: str, dir_arg: str) -> None:
    if os.path.islink(dir_arg) or not os.path.isdir(dir_arg):
        raise SystemExit(1)
    target = dir_arg.rstrip("/")
    expected, our_dirs = load_target_sums(Path(manifest_arg), target)
    for dirpath, dirnames, filenames in os.walk(target, followlinks=False):
        for name in list(dirnames):
            full = os.path.join(dirpath, name)
            if os.path.islink(full):
                if not item_matches(full, expected):
                    raise SystemExit(1)
            else:
                if full not in our_dirs:
                    raise SystemExit(1)
        for name in filenames:
            full = os.path.join(dirpath, name)
            if not item_matches(full, expected):
                raise SystemExit(1)


def cmd_clean_dir(manifest_arg: str, dir_arg: str, dry_run: bool) -> None:
    """Unlink only verified recorded entries and remove directories deepest-first
    with rmdir (never rmtree), so a concurrently saved personal file can never
    be swept up during removal (AUDIT.md #125)."""
    target = dir_arg.rstrip("/")
    prefix_len = len(target) + 1
    expected, our_dirs = load_target_sums(Path(manifest_arg), target)
    kept: list[str] = []
    dirs_to_prune: list[str] = []

    for dirpath, dirnames, filenames in os.walk(target, followlinks=False):
        for name in dirnames:
            full = os.path.join(dirpath, name)
            if os.path.islink(full):
                if item_matches(full, expected):
                    if not dry_run:
                        try:
                            os.unlink(full)
                        except FileNotFoundError:
                            pass
                else:
                    kept.append(full[prefix_len:])
            else:
                if full in our_dirs:
                    dirs_to_prune.append(full)
                else:
                    kept.append(full[prefix_len:] + "/")
        for name in filenames:
            full = os.path.join(dirpath, name)
            if item_matches(full, expected):
                if not dry_run:
                    try:
                        os.unlink(full)
                    except FileNotFoundError:
                        pass
            else:
                kept.append(full[prefix_len:])

    if dry_run:
        if not kept:
            print("REMOVED")
            return
        preview = " ".join(kept[:5])
        if len(kept) > 5:
            preview += " ..."
        print(f"KEPT\t{len(kept)}\t{preview}")
        return

    # Remove recorded subdirectories deepest-first with rmdir only (#125).
    for d in sorted(dirs_to_prune, key=len, reverse=True):
        try:
            os.rmdir(d)
        except OSError:
            pass

    removed_target = False
    try:
        os.rmdir(target)
        removed_target = True
    except FileNotFoundError:
        removed_target = True
    except OSError:
        removed_target = False

    if removed_target:
        print("REMOVED")
        return

    # Target directory is still non-empty (either previously kept items or a
    # personal file saved concurrently during the walk). Report what remains.
    kept_set = set(kept)
    for dirpath, dirnames, filenames in os.walk(target, followlinks=False):
        for name in filenames:
            rel = os.path.join(dirpath, name)[prefix_len:]
            if rel not in kept_set:
                kept.append(rel)
                kept_set.add(rel)
        for name in dirnames:
            full = os.path.join(dirpath, name)
            rel = full[prefix_len:] + ("" if os.path.islink(full) else "/")
            if os.path.islink(full) or full not in our_dirs:
                if rel not in kept_set:
                    kept.append(rel)
                    kept_set.add(rel)
    if not kept:
        kept.append(os.path.basename(target) + "/")
    preview = " ".join(kept[:5])
    if len(kept) > 5:
        preview += " ..."
    print(f"KEPT\t{len(kept)}\t{preview}")


def main() -> None:
    args = sys.argv[1:]
    if not args:
        die("manifest_ops.py: missing subcommand")
    cmd = args[0]
    if cmd == "load-meta" and len(args) == 6:
        cmd_load_meta(args[1], args[2], args[3], args[4], args[5])
    elif cmd == "write-meta" and len(args) == 2:
        cmd_write_meta(args[1])
    elif cmd == "record-sums" and len(args) in (4, 5):
        cmd_record_sums(args[1], args[2], args[3], args[4] if len(args) == 5 else None)
    elif cmd == "record-single-sum" and len(args) == 4:
        cmd_record_single_sum(args[1], args[2], args[3])
    elif cmd == "prune-sums" and len(args) == 4:
        cmd_prune_sums(args[1], args[2], args[3])
    elif cmd == "prune-single-sum" and len(args) == 4:
        cmd_prune_single_sum(args[1], args[2], args[3])
    elif cmd == "drop-sums" and len(args) == 3:
        cmd_drop_sums(args[1], args[2])
    elif cmd == "check-file" and len(args) == 3:
        cmd_check_file(args[1], args[2])
    elif cmd == "check-link" and len(args) == 3:
        cmd_check_link(args[1], args[2])
    elif cmd == "check-tree" and len(args) == 3:
        cmd_check_tree(args[1], args[2])
    elif cmd == "clean-dir" and len(args) in (3, 4):
        dry = len(args) == 4 and args[3] == "--dry-run"
        cmd_clean_dir(args[1], args[2], dry)
    else:
        die(f"manifest_ops.py: invalid arguments: {args!r}")


if __name__ == "__main__":
    main()
