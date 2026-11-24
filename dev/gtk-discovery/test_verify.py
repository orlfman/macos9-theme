#!/usr/bin/env python3
"""Negative-control and positive-control test suite for GTK Milestone 1 harness.

Verifies AUDIT.md #153-#156:
  - #153: missing preference step trace, inert GTK 3/4 watchers, missing
          return-to-baseline, missing Adw accent assertion, absent prefer_dark
  - #154: failed plasma-apply-lookandfeel (LNF_APPLY_RC=1), missing post-reapply
          snapshots, lost user gtk-4.0/gtk.css rule, wrong active LnF package,
          unexpected GTK symlink, clobbered store
  - #155: substituted 340x260 stock-gtk3.png for ffmpeg-plasma.png, wrong
          1024x768 image without FFmpeg pixels, missing/mismatched KWin window
          metadata, wrong active GTK theme at launch
  - #156: incomplete session exiting 0 without `$root/complete` must exit
          nonzero from `dev/gtk-discovery.sh`

SPDX-License-Identifier: BSD-2-Clause
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
DEV_DIR = HERE.parent
VERIFY = HERE / "verify.py"
LAUNCHER = DEV_DIR / "gtk-discovery.sh"


def run_verify(evidence: Path, mode: str, shots: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-I", "-W", "error", str(VERIFY), str(evidence), mode, str(shots)],
        capture_output=True,
        text=True,
        check=False,
    )


def choose_baseline(mode: str, explicit: Path | None, build: Path, shots: Path) -> Path:
    if explicit is not None:
        candidates = [explicit]
    else:
        candidates = sorted(build.glob(f"gtk-discovery-{mode}.*"), key=lambda p: p.stat().st_mtime, reverse=True)
    expected = "PASS" if mode == "plasma" else "PARTIAL_BROADWAY_ONLY"
    for path in candidates:
        marker = path / "complete"
        if not marker.is_file() or marker.stat().st_size == 0:
            continue
        result = run_verify(path, mode, shots)
        if result.returncode == 0 and f"VERDICT={expected} " in result.stdout:
            print(f"{mode} baseline: {path}")
            return path
    source = str(explicit) if explicit is not None else str(build)
    raise ValueError(f"No passing {mode} evidence in {source}. Run dev/gtk-discovery.sh {mode}.")


def main() -> int:
    passed = 0
    failed = 0

    def expect(name: str, cond: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"PASS  {name}")
        else:
            failed += 1
            print(f"FAIL  {name}: {detail}")

    parser = argparse.ArgumentParser(description="Validate discovery evidence and run regression controls.")
    parser.add_argument("--broadway", type=Path, help="Use this completed Broadway evidence directory")
    parser.add_argument("--plasma", type=Path, help="Use this completed Wayland evidence directory")
    args = parser.parse_args()
    build = DEV_DIR / "build"
    build.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="gtk-m1-negtest-", dir=DEV_DIR / "build") as td_str:
        td = Path(td_str)
        shots = td / "shots"
        shots.mkdir()

        try:
            b_ref = choose_baseline("broadway", args.broadway, build, shots)
            p_ref = choose_baseline("plasma", args.plasma, build, shots)
        except ValueError as error:
            print(error, file=sys.stderr)
            return 2

        # 1. Positive control: real post-fix broadway evidence
        b_ok = td / "b-ok"
        shutil.copytree(b_ref, b_ok)
        res = run_verify(b_ok, "broadway", shots)
        expect("positive-broadway", res.returncode == 0 and "VERDICT=PARTIAL_BROADWAY_ONLY" in res.stdout and "fail=0" in res.stdout, res.stdout)

        # 2. Positive control: real post-fix plasma evidence
        p_ok = td / "p-ok"
        shutil.copytree(p_ref, p_ok)
        res = run_verify(p_ok, "plasma", shots)
        expect("positive-plasma", res.returncode == 0 and "VERDICT=PASS" in res.stdout and "fail=0 blocked=0" in res.stdout, res.stdout)

        def mut_plasma(case: str, fn, expect_fail_token: str) -> None:
            d = td / f"neg-{case}"
            shutil.copytree(p_ok, d)
            fn(d)
            r = run_verify(d, "plasma", shots)
            ok = r.returncode == 1 and "VERDICT=FAIL" in r.stdout and expect_fail_token in r.stdout
            expect(f"neg-{case}", ok, f"rc={r.returncode} token={expect_fail_token!r}\n{r.stdout}")

        # --- #153 negative controls ---
        mut_plasma(
            "153-missing-portal-trace",
            lambda d: (d / "portal-trace.log").unlink(),
            "FAIL    portal  preference-step-trace",
        )
        mut_plasma(
            "153-inert-gtk3-gtk4-watchers",
            lambda d: (
                (d / "watch-plasma-gtk3.log").write_text(
                    ((d / "watch-plasma-gtk3.log").read_text().splitlines()[0] + "\n") * 2, encoding="utf-8"
                ),
                (d / "watch-plasma-gtk4.log").write_text(
                    ((d / "watch-plasma-gtk4.log").read_text().splitlines()[0] + "\n") * 2, encoding="utf-8"
                ),
            ),
            "FAIL    gtk3    live-watch-plasma",
        )
        mut_plasma(
            "153-inert-gtk4-watcher-only",
            lambda d: (d / "watch-plasma-gtk4.log").write_text(
                ((d / "watch-plasma-gtk4.log").read_text().splitlines()[0] + "\n") * 2, encoding="utf-8"
            ),
            "FAIL    gtk4    live-watch-plasma",
        )
        mut_plasma(
            "153-missing-gtk3-prefer-dark-key",
            lambda d: (d / "watch-plasma-gtk3.log").write_text(
                (d / "watch-plasma-gtk3.log").read_text().replace(" prefer_dark=0", ""), encoding="utf-8"
            ),
            "missing-prefer_dark-field",
        )
        mut_plasma(
            "153-wrong-adw-accent",
            lambda d: (d / "watch-plasma-adw.log").write_text(
                (d / "watch-plasma-adw.log").read_text().replace("adw_accent_enum=7 adw_accent_nick=purple adw_accent_rgba=rgb(145,65,172)", "adw_accent_enum=0 adw_accent_nick=blue adw_accent_rgba=rgb(53,132,228)"),
                encoding="utf-8",
            ),
            "FAIL    adw     live-portal-color-scheme-and-accent",
        )
        mut_plasma(
            "153-no-return-to-baseline-dark",
            lambda d: (d / "watch-plasma-adw.log").write_text(
                "\n".join(
                    ln.replace("adw_dark=0", "adw_dark=1") if i >= 6 else ln
                    for i, ln in enumerate((d / "watch-plasma-adw.log").read_text().splitlines())
                )
                + "\n",
                encoding="utf-8",
            ),
            "FAIL    adw     live-portal-color-scheme-and-accent",
        )

        # --- #154 negative controls ---
        mut_plasma(
            "154-lnf-apply-rc1-and-missing-reapply-snaps",
            lambda d: (
                (d / "lnf-apply.log").write_text("LNF_APPLY_RC=1\n", encoding="utf-8"),
                (d / "kde-files-reapplied.log").unlink(),
                (d / "kde-files-reapplied-with-user-gtk4.log").unlink(),
            ),
            "FAIL    kde     platinum-lnf-reapply",
        )
        mut_plasma(
            "154-lnf-reapply2-rc1",
            lambda d: (d / "lnf-reapply2.log").write_text("LNF_REAPPLY2_RC=1\n", encoding="utf-8"),
            "FAIL    kde     platinum-lnf-reapply-user-gtk4",
        )
        mut_plasma(
            "154-user-gtk4-rule-lost",
            lambda d: (d / "kde-files-reapplied-with-user-gtk4.log").write_text(
                (d / "kde-files-reapplied-with-user-gtk4.log").read_text().replace("#ind-user { color: #aa4499; }", ""),
                encoding="utf-8",
            ),
            "gtk-4.0/gtk.css:user-rule-lost",
        )
        mut_plasma(
            "154-wrong-active-lnf-package",
            lambda d: (d / "kde-files-reapplied.log").write_text(
                (d / "kde-files-reapplied.log").read_text().replace("kreadconfig_lnf=platinum.desktop", "kreadconfig_lnf=org.kde.breeze.desktop"),
                encoding="utf-8",
            ),
            "kreadconfig_lnf=org.kde.breeze.desktop!=platinum.desktop",
        )
        mut_plasma(
            "154-unexpected-gtk-symlink",
            lambda d: (d / "kde-files-reapplied.log").write_text(
                (d / "kde-files-reapplied.log").read_text().replace(
                    "=== PATHS AND SYMLINKS ===\n",
                    "=== PATHS AND SYMLINKS ===\nl 777 /tmp/gtk-4.0/gtk.css -> /tmp/other\n",
                ),
                encoding="utf-8",
            ),
            "unexpected-symlink",
        )

        # --- #155 negative controls ---
        mut_plasma(
            "155-substituted-stock-gtk3-png",
            lambda d: shutil.copy2(d / "stock-gtk3.png", d / "ffmpeg-plasma.png"),
            "wrong-size(340x260!=1024x768)",
        )
        mut_plasma(
            "155-wrong-1024x768-non-ffmpeg-image",
            lambda d: Image.linear_gradient("L").resize((1024, 768)).convert("RGB").save(d / "ffmpeg-plasma.png"),
            "missing-rendered-purple-accent",
        )
        mut_plasma(
            "155-missing-ffmpeg-window-log",
            lambda d: (d / "ffmpeg-window.log").unlink(),
            "missing-ffmpeg-window.log",
        )
        ff_pid_actual = next(
            ln.split("=", 1)[1].strip()
            for ln in (p_ok / "ffmpeg.log").read_text(encoding="utf-8").splitlines()
            if ln.startswith("FFMPEG_PID=")
        )
        mut_plasma(
            "155-wrong-pid-in-ffmpeg-window-log",
            lambda d: (d / "ffmpeg-window.log").write_text(
                (d / "ffmpeg-window.log").read_text().replace(ff_pid_actual, "99999"), encoding="utf-8"
            ),
            f"no-kwin-window-for-pid({ff_pid_actual})",
        )
        mut_plasma(
            "155-wrong-active-gtk-theme-at-ffmpeg-launch",
            lambda d: (d / "ffmpeg.log").write_text(
                (d / "ffmpeg.log").read_text().replace("'DiscoveryKde'", "'DiscoveryGSettingsLive'"), encoding="utf-8"
            ),
            "active-theme='DiscoveryGSettingsLive'!='DiscoveryKde'",
        )

        def replace(path: Path, old: str, new: str) -> None:
            content = path.read_text()
            assert old in content, f"fixture missing {old}"
            path.write_text(content.replace(old, new))

        def reverse_steps(d: Path) -> None:
            path = d / "portal-trace.log"
            steps = path.read_text().split("=== STEP ")[1:]
            path.write_text("".join("=== STEP " + step for step in reversed(steps)))

        def swap_poll_groups(d: Path) -> None:
            path = d / "watch-plasma-gtk4.log"
            lines = path.read_text().splitlines(keepends=True)
            ends = [i + 1 for i, line in enumerate(lines) if line.startswith("tag=poll ")]
            path.write_text("".join(lines[:1] + lines[ends[1]:ends[3]] + lines[1:ends[1]] + lines[ends[3]:]))

        def unrelated_canvas(d: Path) -> None:
            im = Image.new("RGB", (1024, 768), "#fafafb")
            im.paste("#c69ed3", (200, 200, 301, 251))
            im.save(d / "ffmpeg-plasma.png")

        snap = "kde-files-reapplied-with-user-gtk4.log"
        mut_plasma("159-reversed-trace", reverse_steps, "FAIL    portal  preference-step-trace")
        mut_plasma("159-misordered-polls", swap_poll_groups, "wrong-step-polls")
        mut_plasma("159-missing-backend-accent", lambda d: replace(d / "portal-trace.log",
                   "kde_backend_accent=v (ddd) 0.239216", "kde_backend_accent=missing"), "STEP 1:missing")
        mut_plasma("159-rc-prefix", lambda d: replace(d / "portal-trace.log",
                   "STEP1_APPLY_RC=0", "STEP1_APPLY_RC=01"), "STEP 1:missing")
        mut_plasma("160-css-comment", lambda d: replace(d / snap, "#ind-user { color: #aa4499; }",
                   "/* #ind-user { color: #aa4499; } */"), "user-rule-lost")
        mut_plasma("160-wrong-ini", lambda d: replace(d / snap, "gtk-theme-name=DiscoveryKde",
                   "gtk-theme-name=DiscoveryKdeBroken"), "settings.ini:missing")
        mut_plasma("160-missing-cold-launch", lambda d: replace(d / "results.log",
                   "trial=kde-reapplied-user", "trial=other"), "user-rule-or-import-inactive")
        mut_plasma("161-wrong-canvas", unrelated_canvas, "active-capture-content-mismatch")
        mut_plasma("161-missing-active", lambda d: (d / "ffmpeg-active.png").unlink(), "missing-active-capture")
        mut_plasma("161-wrong-launch-contrast", lambda d: replace(d / "ffmpeg.log",
                   "ACTIVE_CONTRAST=v v u 0", "ACTIVE_CONTRAST=v v u 1"), "incorrect-launch-setting")

        # A newer failed run must never supply a positive control.
        candidates = td / "candidate-runs"
        candidates.mkdir()
        good = candidates / "gtk-discovery-plasma.good"
        bad = candidates / "gtk-discovery-plasma.bad"
        good.symlink_to(p_ok, target_is_directory=True)
        bad.mkdir()
        (bad / "complete").write_text("finished\n")
        os.utime(bad, (good.stat().st_mtime + 2,) * 2)
        expect("162-skip-failed-run", choose_baseline("plasma", None, candidates, shots) == good)
        try:
            choose_baseline("plasma", bad, candidates, shots)
        except ValueError:
            expect("162-reject-explicit-failed-run", True)
        else:
            expect("162-reject-explicit-failed-run", False)

        # --- Broadway negative control ---
        b_neg = td / "neg-broadway-missing-trace"
        shutil.copytree(b_ok, b_neg)
        (b_neg / "broadway-trace.log").unlink()
        rb = run_verify(b_neg, "broadway", shots)
        expect(
            "neg-broadway-missing-trace",
            rb.returncode == 1 and "FAIL    session broadway-gsettings-step-trace" in rb.stdout,
            rb.stdout,
        )

        # --- #156 negative control: real dev/gtk-discovery.sh incomplete-session branch ---
        stub_proj = td / "stub-proj"
        (stub_proj / "dev" / "gtk-discovery").mkdir(parents=True)
        shutil.copy2(LAUNCHER, stub_proj / "dev" / "gtk-discovery.sh")
        shutil.copy2(HERE / "fixture.c", stub_proj / "dev" / "gtk-discovery" / "fixture.c")
        shutil.copy2(VERIFY, stub_proj / "dev" / "gtk-discovery" / "verify.py")
        # Stub session.sh exits 0 immediately with empty log and NO complete file
        stub_sess = stub_proj / "dev" / "gtk-discovery" / "session.sh"
        stub_sess.write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
        os.chmod(stub_sess, 0o755)
        r156 = subprocess.run(
            ["bash", str(stub_proj / "dev" / "gtk-discovery.sh"), "broadway"],
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        expect(
            "neg-156-incomplete-session-rc0-exits-nonzero",
            r156.returncode == 1 and "Session did not complete (rc=0)" in r156.stderr,
            f"rc={r156.returncode} stdout={r156.stdout!r} stderr={r156.stderr!r}",
        )

    print(f"\nSUMMARY: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
