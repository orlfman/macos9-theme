#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
"""Switch menu plugins in Plasma's saved layout while its shell is stopped."""

import argparse
import os
from pathlib import Path
import re
import stat
import tempfile

STOCK = b"org.kde.plasma.appmenu"
PLATINUM = b"platinum.globalmenu"
GROUP = re.compile(rb"\[Containments\]\[(\d+)\](?:\[Applets\]\[(\d+)\])?")


def replacement_lines(lines, direction):
    panels = set()
    applets = []
    group = None
    for index, line in enumerate(lines):
        line = line.rstrip(b"\r\n")
        if line.startswith(b"["):
            group = GROUP.fullmatch(line)
        elif group and line.startswith(b"plugin="):
            containment, applet = group.groups()
            plugin = line.removeprefix(b"plugin=")
            if applet is None and plugin == b"org.kde.panel":
                panels.add(containment)
            elif applet is not None and plugin in (STOCK, PLATINUM):
                applets.append((index, containment, plugin))

    if direction == "restore":
        return {index: STOCK for index, _, plugin in applets if plugin == PLATINUM}
    # The stock and Platinum plugins share the menu service. Convert a single
    # panel instance, leaving a custom multi-menu arrangement to its owner.
    if len(applets) == 1:
        index, containment, plugin = applets[0]
        if plugin == STOCK and containment in panels:
            return {index: PLATINUM}
    return {}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout", type=Path)
    parser.add_argument("direction", choices=("migrate", "restore"))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = args.layout
    try:
        try:
            info = path.lstat()
        except FileNotFoundError:
            print(0)
            return
        if not stat.S_ISREG(info.st_mode):
            raise ValueError(f"{path} is not a regular layout file")

        lines = path.read_bytes().splitlines(keepends=True)
        changes = replacement_lines(lines, args.direction)
        if changes and not args.check:
            for index, plugin in changes.items():
                line = lines[index]
                ending = line[len(line.rstrip(b"\r\n")):]
                lines[index] = b"plugin=" + plugin + ending
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".platinum-menu-", delete=False) as tmp:
                staged = Path(tmp.name)
                try:
                    os.fchmod(tmp.fileno(), stat.S_IMODE(info.st_mode))
                    tmp.writelines(lines)
                    tmp.flush()
                    os.fsync(tmp.fileno())
                    staged.replace(path)
                finally:
                    staged.unlink(missing_ok=True)
        print(len(changes))
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
