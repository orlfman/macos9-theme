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


def selected(config: Path, home: Path, backup: Path | None) -> str:
    stores = [
        (config, "config", "gtk-3.0/settings.ini", None),
        (config, "config", "gtk-4.0/settings.ini", None),
        (home, "home", ".gtkrc-2.0", r'gtk-theme-name\s*=\s*"([^"]+)"'),
        (config, "config", "xsettingsd/xsettingsd.conf", r'Net/ThemeName\s+"([^"]+)"'),
    ]
    roots = dict(line.split("\t", 1) for line in (backup / "ROOTS").read_text().splitlines()) if backup else {}
    absent = set((backup / "ABSENT").read_text().splitlines()) if backup else set()
    for parent, base, rel, pattern in stores:
        path = parent / rel
        if backup and roots.get(base) == str(parent) and not path.is_symlink():
            if f"{base}\t{rel}" in absent:
                continue
            if (backup / base / rel).exists():
                path = backup / base / rel
        if not os.path.lexists(path):
            continue
        if not path.is_file():
            raise ValueError(f"unreadable GTK selection: {path}")
        value = ""
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
        if value == "Platinum":
            return rel
    value = subprocess.check_output(["gsettings", "get", "org.gnome.desktop.interface", "gtk-theme"], text=True)
    return "GSettings" if value.strip() == "'Platinum'" else ""


if __name__ == "__main__":
    try:
        if sys.argv[1] == "validate":
            validate(Path(sys.argv[2]))
        elif sys.argv[1] == "self-contain":
            self_contain(Path(sys.argv[2]))
        else:
            print(selected(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]) if len(sys.argv) == 5 else None))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
