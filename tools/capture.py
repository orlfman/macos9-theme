#!/usr/bin/env python3
"""Capture the Mac OS 9 VM's screen losslessly at its native resolution.

Talks to QEMU's QMP socket and runs `screendump`. This is the guest's own
framebuffer, 1x, unscaled, so it is the reference to measure against. The
screamer QEMU build has no libpng, so QEMU dumps PPM (lossless) and this
script converts it to PNG and checks the PNG pixel for pixel.

The VM must be started with a QMP socket, e.g.:
    /mnt/storage1/local/VM/mac-os-9/mac9 -boot c \
        -qmp unix:$XDG_RUNTIME_DIR/mac9-qmp.sock,server=on,wait=off

Usage:
    tools/capture.py NAME              -> reference/NAME.png (never overwrites)
    tools/capture.py --delay 5 NAME    -> capture after 5 s (pressed states)
    tools/capture.py --burst 15 NAME   -> capture continuously for 15 s and
                                          keep every frame that changed, as
                                          reference/NAME-001.png, -002, ...
                                          (states too short to time by hand,
                                          e.g. a Finder copy's progress bar)
    tools/capture.py --fast --burst 10 NAME
                                       -> same, every 0.01 s (~100 frames/s;
                                          a dump takes ~4 ms at 1920x1080)
    tools/capture.py --check           -> just test the connection
    tools/capture.py --socket PATH ... -> another QMP socket

--delay and --burst combine: the burst starts after the delay.

Every saved capture is appended to reference/INDEX.tsv (time, file, size,
sha256), so docs/REFERENCE.md can cite captures by file name.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import struct
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF = ROOT / "reference"
RUNTIME = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
DEFAULT_SOCK = RUNTIME / "mac9-qmp.sock"


class QMP:
    """One QMP connection, reused for every command (bursts send many)."""

    def __init__(self, sock_path):
        self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.s.settimeout(15)
        self.s.connect(str(sock_path))
        self.f = self.s.makefile("rwb")
        self._read()  # greeting
        self.cmd("qmp_capabilities")

    def _read(self):
        while True:
            line = self.f.readline()
            if not line:
                raise RuntimeError("QMP connection closed")
            msg = json.loads(line)
            if "event" not in msg:
                return msg

    def cmd(self, command, arguments=None):
        req = {"execute": command}
        if arguments:
            req["arguments"] = arguments
        self.f.write(json.dumps(req).encode() + b"\n")
        self.f.flush()
        reply = self._read()
        if "error" in reply:
            raise RuntimeError(f"{command}: {reply['error'].get('desc', reply)}")
        return reply.get("return")

    def dump(self, ppm):
        ppm.unlink(missing_ok=True)
        self.cmd("screendump", {"filename": str(ppm)})
        for _ in range(50):  # QEMU may finish writing after replying
            if ppm.exists() and ppm.stat().st_size > 0:
                return
            time.sleep(0.1)
        raise RuntimeError(f"QEMU did not write {ppm}")

    def close(self):
        self.s.close()


def png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise RuntimeError(f"{path} is not a PNG")
    return struct.unpack(">II", head[16:24])


def save_png(ppm, out):
    """Convert a PPM dump to `out` (never overwriting), verify, and index it."""
    from PIL import Image
    with Image.open(ppm) as im:
        im.load()
        try:
            # "x": fail instead of overwriting if another run saved this name
            # meanwhile (the exists() checks run before --delay/--burst)
            with open(out, "xb") as fh:
                im.save(fh, format="PNG", optimize=True)
        except FileExistsError:
            sys.exit(f"{out} was created by another run meanwhile; nothing saved")
    with Image.open(ppm) as a_im, Image.open(out) as b_im:
        if a_im.tobytes() != b_im.convert(a_im.mode).tobytes():
            out.unlink()
            sys.exit(f"{out.name}: PNG does not match the PPM pixel for pixel; not saved")
    w, h = png_size(out)
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    index = REF / "INDEX.tsv"
    new = not index.exists()
    with open(index, "a") as fh:
        if new:
            fh.write("time\tfile\twidth\theight\tsha256\n")
        fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')}\t{out.name}\t{w}\t{h}\t{digest}\n")
    return w, h


def countdown(seconds):
    for left in range(int(seconds), 0, -1):
        print(f"capturing in {left} s...", flush=True)
        time.sleep(1)
    time.sleep(seconds - int(seconds))


MIN_FREE = 1 << 30  # stop a burst early when the temp dir has < 1 GiB free


def burst(q, name, seconds, interval):
    """Dump frames for `seconds`; save the ones that differ from the last kept."""
    tmp = Path(tempfile.mkdtemp(prefix="mac9-burst-", dir=RUNTIME))
    try:
        frames = []  # (ppm path, capture time)
        last = None
        n = 0
        end = time.monotonic() + seconds
        print(f"bursting for {seconds:g} s (every {interval:g} s)...", flush=True)
        while time.monotonic() < end:
            if n % 25 == 0 and shutil.disk_usage(tmp).free < MIN_FREE:
                print(f"stopping early: less than 1 GiB free in {RUNTIME}", flush=True)
                break
            t0 = time.monotonic()
            ppm = tmp / f"{n:05d}.ppm"
            q.dump(ppm)
            n += 1
            digest = hashlib.sha256(ppm.read_bytes()).digest()
            if digest != last:
                frames.append((ppm, t0))
                last = digest
            else:
                ppm.unlink()
            time.sleep(max(0.0, interval - (time.monotonic() - t0)))
        print("\a", end="", flush=True)
        print(f"{n} frames taken, {len(frames)} different; saving...", flush=True)
        start = frames[0][1] if frames else 0
        for i, (ppm, t) in enumerate(frames, 1):
            out = REF / f"{name}-{i:03d}.png"
            w, h = save_png(ppm, out)
            print(f"{out} {w}x{h} (+{t - start:.1f} s)")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("name", nargs="?", help="capture name, e.g. finder-window-active")
    ap.add_argument("--socket", type=Path, default=DEFAULT_SOCK)
    ap.add_argument("--check", action="store_true", help="only test the QMP connection")
    ap.add_argument("--delay", type=float, default=0, metavar="SECONDS",
                    help="wait before capturing, to set up a pressed or "
                         "dragging state in the VM")
    ap.add_argument("--burst", type=float, default=0, metavar="SECONDS",
                    help="capture continuously for this long and keep every "
                         "frame that changed")
    ap.add_argument("--interval", type=float, default=0.1, metavar="SECONDS",
                    help="time between burst frames (default 0.1)")
    ap.add_argument("--fast", action="store_true",
                    help="burst every 0.01 s (about 100 frames/s); needs --burst")
    a = ap.parse_args()

    if not a.socket.exists():
        sys.exit(f"no QMP socket at {a.socket}; start the VM with "
                 f"-qmp unix:{a.socket},server=on,wait=off")

    if a.check:
        q = QMP(a.socket)
        print(f"QMP ok, VM status: {q.cmd('query-status').get('status')}")
        q.close()
        return

    if not a.name or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", a.name):
        sys.exit("give a name of lowercase letters, digits, '.', '_' or '-'")
    if a.fast:
        if not a.burst:
            sys.exit("--fast needs --burst SECONDS")
        a.interval = 0.01
    if a.burst < 0 or a.burst > 120 or a.interval < 0.005:
        sys.exit("--burst must be 0-120 s and --interval at least 0.005 s")

    REF.mkdir(exist_ok=True)
    if a.burst:
        taken = sorted(REF.glob(f"{a.name}-[0-9][0-9][0-9].png"))
        if taken:
            sys.exit(f"{taken[0]} exists; pick another name (captures are never overwritten)")
    else:
        out = REF / f"{a.name}.png"
        if out.exists():
            sys.exit(f"{out} exists; pick another name (captures are never overwritten)")

    if a.delay > 0:
        countdown(a.delay)
        if not a.burst:
            print("\a", end="", flush=True)

    q = QMP(a.socket)
    try:
        if a.burst:
            burst(q, a.name, a.burst, a.interval)
        else:
            ppm = REF / f".{a.name}.{os.getpid()}.ppm"
            try:
                q.dump(ppm)
                w, h = save_png(ppm, out)
            finally:
                ppm.unlink(missing_ok=True)
            print(f"{out} {w}x{h}")
    finally:
        q.close()


if __name__ == "__main__":
    main()
