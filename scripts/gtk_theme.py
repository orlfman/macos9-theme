"""Validate the GTK 3 package and read widget-theme selections for uninstall."""
# SPDX-License-Identifier: BSD-2-Clause
import os
from pathlib import Path
import re
import subprocess
import sys


def validate(root: Path) -> None:
    root = root.resolve()
    css = root / "gtk-3.0/gtk.css"
    files = [root / "index.theme", root / "palette.css", css]
    for url in re.findall(r'url\("([^"]+)"\)', css.read_text()):
        files.append(css.parent / url)
    for path in files:
        if not path.is_file() or not path.stat().st_size or not os.access(path, os.R_OK):
            raise ValueError(f"missing or unreadable GTK theme resource: {path}")
        resolved = path.resolve()
        if not resolved.is_relative_to(root) or resolved != Path(os.path.normpath(path)):
            raise ValueError(f"linked GTK theme resource: {path}")
    if any(p.is_symlink() for p in (root / "gtk-3.0").rglob("*")):
        raise ValueError("unexpected symlink in GTK 3 package")


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
        else:
            print(selected(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]) if len(sys.argv) == 5 else None))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
