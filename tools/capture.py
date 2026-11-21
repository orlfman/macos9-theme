#!/usr/bin/env python3
"""Capture the Mac OS 9 VM's screen losslessly at its native resolution.

Talks to QEMU's QMP socket and runs `screendump` (PNG). This is the guest's
own framebuffer, 1x, unscaled, so it is the reference to measure against.

The VM must be started with a QMP socket, e.g.:
    /mnt/storage1/local/VM/mac-os-9/mac9 \
        -qmp unix:$XDG_RUNTIME_DIR/mac9-qmp.sock,server=on,wait=off

Usage:
    tools/capture.py NAME            -> reference/NAME.png (never overwrites)
    tools/capture.py --socket PATH NAME
    tools/capture.py --delay 5 NAME  -> capture after 5 s (pressed states)
    tools/capture.py --check         -> just test the connection

Every capture is appended to reference/INDEX.tsv (time, file, size, sha256),
so docs/REFERENCE.md can cite captures by file name.
"""

import argparse
import hashlib
import json
import os
import re
import socket
import struct
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference"
DEFAULT_SOCK = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp")) / "mac9-qmp.sock"


def qmp(sock_path, command, arguments=None):
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(15)
    s.connect(str(sock_path))
    f = s.makefile("rwb")

    def read():
        while True:
            line = f.readline()
            if not line:
                raise RuntimeError("QMP connection closed")
            msg = json.loads(line)
            if "event" in msg:
                continue
            return msg

    def send(cmd, args=None):
        req = {"execute": cmd}
        if args:
            req["arguments"] = args
        f.write(json.dumps(req).encode() + b"\n")
        f.flush()
        reply = read()
        if "error" in reply:
            raise RuntimeError(f"{cmd}: {reply['error'].get('desc', reply)}")
        return reply.get("return")

    read()  # greeting
    send("qmp_capabilities")
    result = send(command, arguments)
    s.close()
    return result


def png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"{path} is not a PNG")
    return struct.unpack(">II", head[16:24])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("name", nargs="?", help="capture name, e.g. finder-window-active")
    ap.add_argument("--socket", type=Path, default=DEFAULT_SOCK)
    ap.add_argument("--check", action="store_true", help="only test the QMP connection")
    ap.add_argument("--delay", type=float, default=0, metavar="SECONDS",
                    help="wait before capturing, to set up a pressed or "
                         "dragging state in the VM")
    a = ap.parse_args()

    if not a.socket.exists():
        sys.exit(f"no QMP socket at {a.socket}; start the VM with "
                 f"-qmp unix:{a.socket},server=on,wait=off")

    if a.check:
        status = qmp(a.socket, "query-status")
        print(f"QMP ok, VM status: {status.get('status')}")
        return

    if not a.name or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", a.name):
        sys.exit("give a name of lowercase letters, digits, '.', '_' or '-'")

    REF.mkdir(exist_ok=True)
    out = REF / f"{a.name}.png"
    if out.exists():
        sys.exit(f"{out} exists; pick another name (captures are never overwritten)")

    # The screamer QEMU build has no libpng, so dump PPM (lossless, always
    # available) and convert it to PNG here.
    if a.delay > 0:
        for left in range(int(a.delay), 0, -1):
            print(f"capturing in {left} s...", flush=True)
            time.sleep(1)
        time.sleep(a.delay - int(a.delay))
        print("\a", end="", flush=True)

    ppm = REF / f".{a.name}.ppm"
    ppm.unlink(missing_ok=True)
    qmp(a.socket, "screendump", {"filename": str(ppm)})
    for _ in range(50):  # QEMU may finish writing after replying
        if ppm.exists() and ppm.stat().st_size > 0:
            break
        time.sleep(0.1)
    from PIL import Image
    with Image.open(ppm) as im:
        im.load()
        im.save(out, format="PNG", optimize=True)
    with Image.open(ppm) as a_im, Image.open(out) as b_im:
        if a_im.tobytes() != b_im.convert(a_im.mode).tobytes():
            out.unlink()
            sys.exit("PNG does not match the PPM pixel for pixel; nothing saved")
    ppm.unlink()
    w, h = png_size(out)
    digest = hashlib.sha256(out.read_bytes()).hexdigest()

    index = REF / "INDEX.tsv"
    new = not index.exists()
    with open(index, "a") as fh:
        if new:
            fh.write("time\tfile\twidth\theight\tsha256\n")
        fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')}\t{out.name}\t{w}\t{h}\t{digest}\n")
    print(f"{out} {w}x{h}")


if __name__ == "__main__":
    main()
