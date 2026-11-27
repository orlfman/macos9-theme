# SPDX-License-Identifier: BSD-2-Clause
"""Cache the pinned Big Sur archive and track the KDE sound preference."""
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import urllib.request
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from icon_prefs import atomic_write_text, kde_delete_key, kde_key_state, kde_set_key, state_matches

VERSION = "1.0.2"
ARCHIVE = f"bigsur-{VERSION}.zip"
# M9_SOUND_URL is for dev/test-install.sh only (a file:// copy, no network).
URL = os.environ.get(
    "M9_SOUND_URL",
    f"https://github.com/gxanshu/macos-bigsur-sound-theme-linux/releases/download/{VERSION}/bigsur.zip",
)
DIGEST = "074ed200fb8ebd5285f2ca0a8be20c481d41999bf944423371baabf4a83563a9"
# Names and contents of every file in the release's bigsur/ folder.
TREE_DIGEST = "da5ee4833e61118e996dd516f818e144601b2398f4cbe92ba9f514108631ff1f"
GROUP = "Sounds"
KEY = "Theme"
THEME = "bigsur"


def read_tree(root):
    """Return (files, digest) for a folder; ValueError if it has links or odd entries."""
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"{root} must be a regular directory")
    files = {}
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        if path.is_symlink() or not (path.is_file() or path.is_dir()):
            raise ValueError(f"unexpected entry in {root}: {path}")
        if path.is_file():
            name = path.relative_to(root).as_posix()
            content = path.read_bytes()
            files[name] = content
            digest.update(name.encode() + b"\0" + hashlib.sha256(content).digest())
    return files, digest.hexdigest()


def stage_checkout(checkout, stage):
    """Use an upstream clone that holds exactly the pinned release. Returns
    False (and says why) when it holds something else, so the caller can fall
    back to the pinned download instead of failing (an updated clone)."""
    try:
        files, digest = read_tree(checkout)
    except ValueError as error:
        print(f"not using {checkout}: {error}", file=sys.stderr)
        return False
    if digest != TREE_DIGEST:
        print(f"not using {checkout}: it isn't Big Sur {VERSION}", file=sys.stderr)
        return False
    if stage is None:
        print(f"use the local Big Sur {VERSION} checkout at {checkout}")
        return True
    for name, content in files.items():
        dest = stage / "bigsur" / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
    return True


def prepare(project, stage):
    private_copy = project / "reference" / "sounds" / ARCHIVE
    cache = project / "build" / "sound-themes" / ARCHIVE
    source = next((p for p in (private_copy, cache) if os.path.lexists(p)), None)
    checkout = project / "build" / "upstreams" / "macos-bigsur-sound-theme-linux" / "theme" / "bigsur"
    if source is None and os.path.lexists(checkout) and stage_checkout(checkout, stage):
        return
    if source is not None:
        if not source.is_file() or source.is_symlink():
            raise ValueError(f"{source} must be a regular archive file")
        if stage is None:
            print(f"use cached Big Sur {VERSION} archive at {source}")
        data = source.read_bytes()
    elif stage is None:
        print(f"download Big Sur {VERSION} from {URL} to {cache}")
        return
    else:
        with urllib.request.urlopen(URL, timeout=30) as response:
            data = response.read(2 * 1024 * 1024)

    if hashlib.sha256(data).hexdigest() != DIGEST:
        raise ValueError(f"Big Sur {VERSION} checksum mismatch in {source or URL}")
    if stage is None:
        return
    # The checksum pins the full ZIP, including member names and contents.
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        archive.extractall(stage)
    if source is None:
        cache.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=cache.parent) as temp:
            staged = Path(temp) / ARCHIVE
            staged.write_bytes(data)
            os.replace(staged, cache)


def check_installed(target):
    """An existing sounds/bigsur folder must be the pinned release, byte for
    byte. Needs no archive, so dry runs and offline runs can check it first."""
    if not os.path.lexists(target):
        return
    try:
        _, digest = read_tree(target)
    except ValueError:
        digest = None
    if digest != TREE_DIGEST:
        raise ValueError(f"{target} differs from the pinned Big Sur {VERSION} release")


def load_record(marker):
    if not os.path.lexists(marker):
        return {}
    if marker.is_symlink() or not marker.is_file():
        raise ValueError(f"{marker} must be a regular state file")
    return json.loads(marker.read_text())


def save_record(marker, record):
    atomic_write_text(marker, json.dumps(record) + "\n", fsync=True)


def select(config, marker):
    current = kde_key_state(config, GROUP, KEY)
    record = load_record(marker)
    if "previous" not in record or not selected(current):
        save_record(marker, {"previous": current})
    if not selected(current):
        kde_set_key(config, GROUP, KEY, THEME)


def selected(state):
    return state["present"] and state["value"] == THEME


def undo_state(config, record):
    if "undo" in record:
        return record["undo"]
    current = kde_key_state(config, GROUP, KEY)
    return record["previous"] if selected(current) else current


def capture_undo(config, marker):
    record = load_record(marker)
    if record:
        record.pop("undo", None)
        record["undo"] = undo_state(config, record)
        save_record(marker, record)


def add_deleted_marker(config):
    """Put `Theme[$d]` back inside the existing [Sounds] group, or add the
    group at the end when there is none (no second [Sounds] heading)."""
    contents = config.read_text(encoding="utf-8") if config.exists() else ""
    lines = contents.splitlines()
    header = f"[{GROUP}]"
    for index, line in enumerate(lines):
        if line.strip() == header:
            lines.insert(index + 1, f"{KEY}[$d]")
            break
    else:
        if lines and lines[-1].strip():
            lines.append("")
        lines += [header, f"{KEY}[$d]"]
    atomic_write_text(config, "\n".join(lines) + "\n")


def restore(config, marker, dry_run):
    record = load_record(marker)
    if not record:
        return
    previous = undo_state(config, record)
    if dry_run:
        if previous["present"]:
            print(f"set the KDE sound theme to {previous['value']!r}")
        else:
            print("restore the previous KDE sound theme default")
        return
    current = kde_key_state(config, GROUP, KEY)
    if not state_matches(current, previous) or current["deleted_marker"] != previous["deleted_marker"]:
        if previous["present"]:
            kde_set_key(config, GROUP, KEY, previous["value"])
        else:
            kde_delete_key(config, GROUP, KEY, remove_if_empty_file=not previous["file_exists"])
            if previous["deleted_marker"]:
                add_deleted_marker(config)
    marker.unlink()


def main():
    command, *args = sys.argv[1:]
    if command == "prepare":
        first, second = args
        prepare(Path(first), Path(second) if second else None)
        return
    if command == "check-installed":
        (target,) = args
        check_installed(Path(target))
        return
    config, marker = (Path(arg) for arg in args)
    if command == "select":
        select(config, marker)
    elif command == "capture-undo":
        capture_undo(config, marker)
    elif command in ("restore", "preview-restore"):
        restore(config, marker, dry_run=command == "preview-restore")
    else:
        raise ValueError(f"unknown command: {command}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        sys.exit(str(error))
