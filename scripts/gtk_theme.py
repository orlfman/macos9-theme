"""Validate the GTK 3 and GTK 4 packages, make GTK 4 stand alone, and read
widget-theme selections for uninstall."""
# SPDX-License-Identifier: BSD-2-Clause
import os
from pathlib import Path
import re
import subprocess
import sys


def validate(root: Path) -> None:
    """Every resource the GTK 3 and GTK 4 stylesheets reference must exist inside the package."""
    root = root.resolve()
    files = [root / "index.theme", root / "palette.css"]
    for toolkit in ("gtk-3.0", "gtk-4.0"):
        for css in sorted((root / toolkit).glob("*.css")):
            files.append(css)
            for url in re.findall(r'url\("([^"]+)"\)', css.read_text()):
                if not url.startswith("resource://"):
                    files.append(css.parent / url)
        if not (root / toolkit / "gtk.css").is_file():
            raise ValueError(f"missing GTK theme stylesheet: {root / toolkit / 'gtk.css'}")
    for path in files:
        if not path.is_file() or not path.stat().st_size or not os.access(path, os.R_OK):
            raise ValueError(f"missing or unreadable GTK theme resource: {path}")
        resolved = path.resolve()
        if not resolved.is_relative_to(root) or resolved != Path(os.path.normpath(path)):
            raise ValueError(f"linked GTK theme resource: {path}")
    for toolkit in ("gtk-3.0", "gtk-4.0"):
        if any(p.is_symlink() for p in (root / toolkit).rglob("*")):
            raise ValueError(f"unexpected symlink in the {toolkit} package")


def self_contain(gtk4: Path) -> None:
    """Make an installed gtk-4.0 folder stand alone: copy the GTK 3 artwork and
    palette it references into it and point its stylesheets there."""
    shared = gtk4.parent
    for css in sorted(gtk4.glob("*.css")):
        text = css.read_text()
        for url in sorted(set(re.findall(r'url\("(\.\./[^"]+)"\)', text))):
            source = (css.parent / url).resolve()
            if url == "../palette.css":
                local = "palette.css"
            elif url.startswith("../gtk-3.0/assets/"):
                local = "assets/gtk3/" + url.removeprefix("../gtk-3.0/assets/")
            else:
                raise ValueError(f"unexpected shared GTK 4 resource: {url}")
            if not source.is_relative_to(shared.resolve()) or not source.is_file():
                raise ValueError(f"missing GTK 4 resource: {url}")
            target = gtk4 / local
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
            text = text.replace(f'url("{url}")', f'url("{local}")')
        css.write_text(text)


# The GTK widget-theme setting in each store Plasma's GTK sync writes, besides
# GSettings (which install and undo never copy).
STORES = (
    ("config", "gtk-3.0/settings.ini", None),
    ("config", "gtk-4.0/settings.ini", None),
    ("home", ".gtkrc-2.0", r'gtk-theme-name\s*=\s*"([^"]+)"'),
    ("config", "xsettingsd/xsettingsd.conf", r'Net/ThemeName\s+"([^"]+)"'),
)


def theme_state(path: Path, pattern: str | None) -> str | None:
    """The widget theme a store names, or None when the file or key is absent."""
    if not os.path.lexists(path):
        return None
    if not path.is_file():
        raise ValueError(f"unreadable GTK selection: {path}")
    value = None
    section = ""
    for line in path.read_text().splitlines():
        line = line.strip()
        if pattern:
            match = re.fullmatch(pattern + r"\s*(?:#.*)?", line)
            if match:
                value = match[1]
        elif line.startswith("[") and line.endswith("]"):
            section = line[1:-1]
        elif section == "Settings":
            key, sep, setting = line.partition("=")
            if sep and key.strip() == "gtk-theme-name":
                value = setting.strip()
    return value


def backup_lists(backup: Path) -> tuple[dict[str, str], set[str]]:
    roots = dict(line.split("\t", 1) for line in (backup / "ROOTS").read_text().splitlines())
    absent = set((backup / "ABSENT").read_text().splitlines())
    return roots, absent


def store_values(config: Path, home: Path, backup: Path | None):
    """(base, rel, state now, state after undo, later choice?) per store.

    A state is the widget-theme name, or None when the key or file is absent.
    Neither install nor Plasma's GTK sync changes the name (docs/FINDINGS.md),
    so a state that differs from the copy taken before the switch is the
    user's later choice, including removing the key (#249, #251), and undo
    carries it forward. The sync does write the name into a file or key that
    was missing, copying it from the others: a new key with a name the copy
    already held is the sync's, not a choice."""
    parents = {"config": config, "home": home}
    roots, absent = backup_lists(backup) if backup else ({}, set())
    rows = []
    for base, rel, pattern in STORES:
        parent = parents[base]
        path = parent / rel
        now = theme_state(path, pattern)
        restored = now
        if backup and roots.get(base) == str(parent) and not path.is_symlink():
            if f"{base}\t{rel}" in absent:
                restored = None
            elif (backup / base / rel).exists():
                restored = theme_state(backup / base / rel, pattern)
        rows.append((base, rel, now, restored))
    before = {restored for _, _, _, restored in rows if restored is not None}
    for base, rel, now, restored in rows:
        later = now != restored and not (restored is None and now in before)
        yield base, rel, now, now if later else restored, later


def later_choices(config: Path, home: Path, backup: Path) -> str:
    """One line per store the user changed after the switch: base, path and
    the name to keep ("" to keep the key removed)."""
    return "".join(f"{base}\t{rel}\t{now or ''}\n"
                   for base, rel, now, _, later in store_values(config, home, backup) if later)


def carry(config: Path, home: Path, lines: str) -> None:
    """Write each carried widget-theme name back after the config restore,
    leaving the rest of the restored file as it was."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from icon_prefs import ini_delete_key, ini_set_key, line_delete_key, line_set_key  # noqa: E402

    parents = {"config": config, "home": home}
    for line in lines.splitlines():
        if not line:
            continue
        base, rel, value = line.split("\t")
        if (base, rel) not in {(b, r) for b, r, _ in STORES} or not re.fullmatch(r"[^\"\n\t]*", value):
            raise ValueError(f"unexpected GTK theme choice: {line!r}")
        path = parents[base] / rel
        if not value:
            # The user removed the key after the switch: remove it again.
            if rel.endswith("settings.ini"):
                ini_delete_key(path, "Settings", "gtk-theme-name")
            else:
                key = r"^\s*gtk-theme-name\s*=" if rel == ".gtkrc-2.0" else r"^\s*Net/ThemeName\s"
                line_delete_key(path, re.compile(key))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith("settings.ini"):
            ini_set_key(path, "Settings", "gtk-theme-name", value)
        elif rel == ".gtkrc-2.0":
            line_set_key(path, re.compile(r'^\s*gtk-theme-name\s*='), f'gtk-theme-name="{value}"',
                         create_if_missing=True, default_mode=0o644)
        else:
            line_set_key(path, re.compile(r'^\s*Net/ThemeName\s'), f'Net/ThemeName "{value}"',
                         create_if_missing=True, default_mode=0o644)


def selected(config: Path, home: Path, backup: Path | None) -> str:
    """Where Platinum is still the GTK widget theme after undo, or ""."""
    # An exported GTK_THEME overrides every store for that session (#250).
    override = os.environ.get("GTK_THEME", "")
    if override.split(":", 1)[0] == "Platinum":
        return f"GTK_THEME={override}"
    for _, rel, _, after, _ in store_values(config, home, backup):
        if after == "Platinum":
            return rel
    value = subprocess.check_output(["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"], text=True)
    return "GSettings" if value.strip() == "'Platinum'" else ""


if __name__ == "__main__":
    try:
        if sys.argv[1] == "validate":
            validate(Path(sys.argv[2]))
        elif sys.argv[1] == "self-contain":
            self_contain(Path(sys.argv[2]))
        elif sys.argv[1] == "later-choices":
            print(later_choices(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])), end="")
        elif sys.argv[1] == "carry":
            carry(Path(sys.argv[2]), Path(sys.argv[3]), sys.stdin.read())
        else:
            print(selected(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]) if len(sys.argv) == 5 else None))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
