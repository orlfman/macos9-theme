#!/usr/bin/env python3
"""Check Platinum's palette and Firefox's System appearance in the test session."""

# SPDX-License-Identifier: BSD-2-Clause
from configparser import ConfigParser
import os
from pathlib import Path
import runpy
import socket
import subprocess
import sys
import time


def palette_check(scheme: Path) -> None:
    colors = ConfigParser(interpolation=None)
    with scheme.open() as file:
        colors.read_file(file)
    for group in ("Colors:Window", "Colors:View"):
        rgb = tuple(map(int, colors[group]["BackgroundNormal"].split(",")))
        if len(rgb) != 3 or any(not 0 <= channel <= 255 for channel in rgb):
            raise RuntimeError(f"{group} needs an RGB background: {rgb}")
        red, green, blue = rgb
        gray = (red * 11 + green * 16 + blue * 5) // 32
        print(f"{group}: qGray={gray}")
        if gray < 192:
            raise RuntimeError(f"{group} must keep a light background (qGray >= 192)")


def firefox_check(root: Path, project: Path) -> None:
    marionette = runpy.run_path(str(project / "dev/firefox-m1/probe.py"))["Marionette"]
    profiles = Path(os.environ["HOME"]) / ".mozilla/firefox"
    profiles.mkdir(parents=True, exist_ok=True)
    profile = profiles / "appearance"
    profile.mkdir()
    (profiles / "profiles.ini").write_text(
        "[Profile0]\nName=appearance\nIsRelative=1\nPath=appearance\nDefault=1\n"
    )
    (profile / "prefs.js").touch()
    subprocess.run([str(project / "firefox/install.sh"), "--profile", "appearance"], check=True)

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    with (profile / "user.js").open("a") as prefs:
        prefs.write(
            f'\nuser_pref("marionette.port", {port});\n'
            'user_pref("layout.css.prefers-color-scheme.content-override", 2);\n'
            'user_pref("browser.shell.checkDefaultBrowser", false);\n'
            'user_pref("browser.startup.homepage_override.mstone", "ignore");\n'
            'user_pref("browser.startup.firstrunSkipsHomepage", true);\n'
        )
    page = root / "appearance.html"
    page.write_text("""<!doctype html><meta charset="utf-8"><title>System appearance</title>
<style>
  @media (prefers-color-scheme: light) { body { background: white; color: black } }
  @media (prefers-color-scheme: dark) { body { background: black; color: white } }
</style><p>System appearance</p>
""")

    with (root / "appearance-firefox.log").open("w") as output:
        firefox = subprocess.Popen(
            ["firefox", "--no-remote", "--profile", str(profile), "--marionette", "about:blank"],
            env={**os.environ, "GDK_BACKEND": "wayland", "MOZ_ENABLE_WAYLAND": "1"},
            stdout=output, stderr=subprocess.STDOUT,
        )
        browser = None
        try:
            for _ in range(100):
                if firefox.poll() is not None:
                    raise RuntimeError(f"Firefox exited with status {firefox.returncode}")
                try:
                    browser = marionette(port)
                    break
                except ConnectionRefusedError:
                    time.sleep(0.1)
            if browser is None:
                raise RuntimeError("Firefox Marionette did not start")
            browser.send("WebDriver:NewSession", {"capabilities": {}})
            browser.send("WebDriver:Navigate", {"url": page.as_uri()})
            for scheme, color in (("Platinum", "rgb(255, 255, 255)"),
                                  ("BreezeDark", "rgb(0, 0, 0)"),
                                  ("Platinum", "rgb(255, 255, 255)")):
                subprocess.run(["plasma-apply-colorscheme", scheme], check=True)
                for _ in range(50):
                    rendered = browser.exec_chrome("return getComputedStyle(document.body).backgroundColor;")
                    if rendered == color:
                        print(f"Firefox Website appearance System under {scheme}: {rendered}")
                        break
                    time.sleep(0.1)
                else:
                    raise RuntimeError(f"Firefox under {scheme} rendered {rendered}, expected {color}")
        finally:
            if browser:
                browser.close()
            firefox.terminate()
            try:
                firefox.wait(timeout=10)
            except subprocess.TimeoutExpired:
                firefox.kill()
                firefox.wait()


if __name__ == "__main__":
    if len(sys.argv) == 2:
        palette_check(Path(sys.argv[1]))
    else:
        firefox_check(Path(sys.argv[1]), Path(sys.argv[2]))
