#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
"""Switch menu plugins in Plasma's saved layout while its shell is stopped."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
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


def switch_layout(path, direction, check=False):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return 0
    if not stat.S_ISREG(info.st_mode):
        raise ValueError(f"{path} is not a regular layout file")

    lines = path.read_bytes().splitlines(keepends=True)
    changes = replacement_lines(lines, direction)
    if changes and not check:
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
    return len(changes)


def digest(path):
    with open(path, "rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def fingerprint(plugin):
    loader = subprocess.run(["ldd", str(plugin)], check=True, text=True, capture_output=True)
    library_names = ("libPlasma.so.", "libtaskmanager.so.", "libQt6Core.so.",
                     "libQt6Qml.so.", "libQt6Quick.so.", "libQt6Widgets.so.")
    resolved = {}
    for line in loader.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 3 and fields[1] == "=>" and fields[2].startswith("/"):
            for name in library_names:
                if fields[0].startswith(name):
                    resolved[name] = fields[2]
    shell = shutil.which("plasmashell")
    if set(resolved) != set(library_names) or shell is None:
        raise ValueError("couldn't identify the Plasma and Qt libraries for Platinum Global Menu")
    return {
        "plugin": digest(plugin),
        "runtime": {path: digest(path) for path in sorted({shell, *resolved.values()})},
    }


def compatible(plugin, stamp):
    try:
        expected = json.loads(stamp.read_text())
        runtime = expected["runtime"]
        if not isinstance(runtime, dict) or len(runtime) != 7:
            return False
        return digest(plugin) == expected["plugin"] and all(
            Path(path).is_absolute() and digest(path) == checksum
            for path, checksum in runtime.items()
        )
    except (OSError, ValueError, KeyError, TypeError):
        return False


def login(plugin, stamp, layout, lock_path):
    # Use the same lock as install and uninstall. A session starting during
    # either waits until both the plugin and its fingerprint are published.
    with lock_path.open("rb") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if compatible(plugin, stamp):
            return True
        if switch_layout(layout, "restore", check=True):
            reply = subprocess.run(
                ["dbus-send", "--session", "--print-reply", "--reply-timeout=3000",
                 "--dest=org.freedesktop.DBus", "/org/freedesktop/DBus",
                 "org.freedesktop.DBus.NameHasOwner", "string:org.kde.plasmashell"],
                text=True, capture_output=True, timeout=4,
            )
            if reply.returncode == 0 and "boolean false" in reply.stdout:
                switch_layout(layout, "restore")
            else:
                print("Platinum Global Menu: panel recovery requires a fresh Plasma session.", file=sys.stderr)
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout", type=Path)
    parser.add_argument("direction", choices=("migrate", "restore", "fingerprint", "compatible", "login"))
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--plugin", type=Path)
    parser.add_argument("--stamp", type=Path)
    parser.add_argument("--lock", type=Path)
    args = parser.parse_args()
    try:
        if args.direction == "fingerprint":
            print(json.dumps(fingerprint(args.plugin), sort_keys=True))
        elif args.direction == "compatible":
            return 0 if compatible(args.plugin, args.stamp) else 1
        elif args.direction == "login":
            return 0 if login(args.plugin, args.stamp, args.layout, args.lock) else 1
        else:
            print(switch_layout(args.layout, args.direction, args.check))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    sys.exit(main())
