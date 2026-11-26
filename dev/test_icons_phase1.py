#!/usr/bin/env python3
"""Disposable verification suite for the WhiteSur Lavender builder and update
review workflow (#101-#109, #111).

Run with one command:
  /home/pieman/Files/Archive/projects/macos9-theme/dev/test_icons_phase1.py

Uses only fresh disposable directories under /tmp (never writes to
dev/build/icons/, ~/.local/share/icons, or ../WhiteSur-icon-theme).

SPDX-License-Identifier: BSD-2-Clause
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
UPSTREAM = Path(os.environ.get("M9_WHITESUR_UPSTREAM", str(PROJECT.parent / "WhiteSur-icon-theme")))
BUILDER = PROJECT / "icons/build-whitesur-lavender.sh"
GENERATOR = PROJECT / "icons/whitesur-lavender.py"
REVIEWER = PROJECT / "icons/review-whitesur-update.sh"
FETCHER = PROJECT / "icons/fetch-whitesur.sh"
PIN_FILE = PROJECT / "icons/whitesur-pin.json"
THEME_IDS = ("WhiteSur-lavender", "WhiteSur-lavender-light", "WhiteSur-lavender-dark")

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}" + (f" ({detail})" if detail else ""))
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def run(cmd: list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, text=True, capture_output=True)


def make_export(dst: Path, commit: str) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    p1 = subprocess.Popen(
        ["git", "-C", str(UPSTREAM), "archive", "--format=tar", commit],
        stdout=subprocess.PIPE,
    )
    p2 = subprocess.Popen(["tar", "-x", "-C", str(dst)], stdin=p1.stdout)
    assert p1.stdout is not None
    p1.stdout.close()
    assert p2.wait() == 0
    assert p1.wait() == 0


def main() -> None:
    pin = json.loads(PIN_FILE.read_text(encoding="utf-8"))
    pinned_commit = pin["commit"]
    pin_before_bytes = PIN_FILE.read_bytes()

    tmp_root = Path(tempfile.mkdtemp(prefix="ws-phase1-tests-"))
    try:
        # ------------------------------------------------------------------
        # #101: Destination safety & ownership refusals (before any writes)
        # ------------------------------------------------------------------
        unowned_out = tmp_root / "unowned-out"
        marker = unowned_out / "WhiteSur-lavender/KEEP_ME"
        marker.parent.mkdir(parents=True)
        marker.write_text("precious\n")
        r = run([str(BUILDER), str(UPSTREAM), str(unowned_out)])
        check(
            "#101 refuse unowned existing theme dir",
            r.returncode != 0 and marker.exists() and marker.read_text() == "precious\n",
            f"rc={r.returncode}",
        )

        real_target = tmp_root / "real-target"
        real_target.mkdir()
        (real_target / "sentinel").write_text("untouched\n")
        link_dest = tmp_root / "link-dest"
        link_dest.symlink_to(real_target)
        r1 = run([str(BUILDER), str(UPSTREAM), str(link_dest)])
        r2 = run([str(BUILDER), str(UPSTREAM), str(link_dest / "sub")])
        check(
            "#101 refuse symlink destination and symlink parent chain",
            r1.returncode != 0
            and r2.returncode != 0
            and (real_target / "sentinel").read_text() == "untouched\n"
            and not (real_target / "sub").exists(),
            f"rc1={r1.returncode}, rc2={r2.returncode}",
        )

        r1 = run([str(BUILDER), str(UPSTREAM), str(UPSTREAM)])
        r2 = run([str(BUILDER), str(UPSTREAM), str(UPSTREAM / "sub-out")])
        check(
            "#101 refuse writing into upstream tree",
            r1.returncode != 0 and r2.returncode != 0 and not (UPSTREAM / "sub-out").exists(),
            f"rc1={r1.returncode}, rc2={r2.returncode}",
        )

        for label, bad_dest in [
            ("project root", PROJECT),
            ("icons/", PROJECT / "icons"),
            ("icons/sub", PROJECT / "icons/sub"),
            ("reference/sub", PROJECT / "reference/sub"),
            (".git/sub", PROJECT / ".git/sub"),
        ]:
            r = run([str(BUILDER), str(UPSTREAM), str(bad_dest)])
            check(f"#101 refuse trackable/unsafe {label}", r.returncode != 0, f"rc={r.returncode}")

        # ------------------------------------------------------------------
        # #104: Bad inputs
        # ------------------------------------------------------------------
        bad_cases = [
            ("empty upstream", [str(BUILDER), "", str(tmp_root / "b1")]),
            ("empty out", [str(BUILDER), str(UPSTREAM), ""]),
            ("extra 3rd arg", [str(BUILDER), str(UPSTREAM), str(tmp_root / "b2"), "extra"]),
            ("unknown flag", [str(BUILDER), "--bogus"]),
            ("nonexistent upstream", [str(BUILDER), str(tmp_root / "nope"), str(tmp_root / "b3")]),
            ("non-git upstream", [str(BUILDER), str(tmp_root), str(tmp_root / "b4")]),
            ("newline in path", [str(BUILDER), str(UPSTREAM), str(tmp_root) + "/bad\npath"]),
        ]
        for label, cmd in bad_cases:
            r = run(cmd)
            check(f"#104 bad input: {label}", r.returncode != 0, f"rc={r.returncode}")

        # ------------------------------------------------------------------
        # #103: Wrong upstream HEAD commit refused
        # ------------------------------------------------------------------
        wrong_repo = tmp_root / "wrong-upstream"
        r = run(["git", "clone", "--quiet", str(UPSTREAM), str(wrong_repo)])
        assert r.returncode == 0, r.stderr
        r = run(
            [
                "git",
                "-C",
                str(wrong_repo),
                "-c",
                "user.name=Test",
                "-c",
                "user.email=test@example.invalid",
                "commit",
                "--allow-empty",
                "-q",
                "-m",
                "unreviewed bump",
            ]
        )
        assert r.returncode == 0, r.stderr
        r = run([str(BUILDER), str(wrong_repo), str(tmp_root / "wrong-out")])
        check(
            "#103 refuse unpinned upstream commit",
            r.returncode != 0 and not (tmp_root / "wrong-out").exists(),
            f"rc={r.returncode}",
        )

        # ------------------------------------------------------------------
        # #104 + #102: Spaces in OUTPUT_DIR & TMPDIR + poisoned environment
        # ------------------------------------------------------------------
        spaced_tmp = tmp_root / "tmp with spaces"
        spaced_tmp.mkdir()
        spaced_out = tmp_root / "out with spaces" / "icons dir"
        poisoned_env = os.environ.copy()
        poisoned_env.update(
            {
                "TMPDIR": str(spaced_tmp),
                "remove": "true",
                "name": "Hijacked",
                "black": "true",
                "bold": "true",
                "alternative": "true",
                "DESKTOP_SESSION": "/usr/share/xsessions/budgie-desktop",
                "DISPLAY": ":99",
                "WAYLAND_DISPLAY": "wayland-99",
                "DBUS_SESSION_BUS_ADDRESS": "unix:path=/tmp/fake-bus",
                "GIT_DIR": "/tmp/nonexistent-git-dir",
                "GIT_WORK_TREE": "/tmp/nonexistent-work-tree",
                "BASH_ENV": "/tmp/nonexistent-bash-env",
            }
        )
        r = run([str(BUILDER), str(UPSTREAM), str(spaced_out)], env=poisoned_env)
        top_entries = sorted(p.name for p in spaced_out.iterdir()) if spaced_out.exists() else []
        tmp_leftovers = list(spaced_tmp.iterdir())
        dir_mode = stat.S_IMODE(os.lstat(spaced_out / "WhiteSur-lavender").st_mode) if spaced_out.exists() else 0
        check(
            "#102+#104 spaces in OUTPUT_DIR & TMPDIR with poisoned env (remove=true, name=Hijacked, GIT_DIR)",
            r.returncode == 0
            and top_entries == sorted(THEME_IDS)
            and pinned_commit in r.stdout
            and len(tmp_leftovers) == 0
            and (dir_mode & 0o002) == 0,
            f"rc={r.returncode}, entries={top_entries}, tmp_leftovers={len(tmp_leftovers)}, mode={oct(dir_mode)}",
        )

        # ------------------------------------------------------------------
        # #104: Relative OUTPUT_DIR and relative UPSTREAM_CLONE
        # ------------------------------------------------------------------
        rel_cwd = tmp_root / "rel-cwd"
        rel_cwd.mkdir()
        rel_up = os.path.relpath(UPSTREAM, rel_cwd)
        r = run([str(BUILDER), rel_up, "result"], cwd=rel_cwd)
        rel_entries = sorted(p.name for p in (rel_cwd / "result").iterdir()) if (rel_cwd / "result").exists() else []
        check(
            "#104 relative UPSTREAM_CLONE and relative OUTPUT_DIR ('result')",
            r.returncode == 0 and rel_entries == sorted(THEME_IDS),
            f"rc={r.returncode}, entries={rel_entries}",
        )

        # ------------------------------------------------------------------
        # #101: Failed rebuilds, mid-publish rollback, owned rebuild, concurrency
        # ------------------------------------------------------------------
        owned_marker = spaced_out / "WhiteSur-lavender/.test-prev-marker"
        owned_marker.write_text("v1\n")
        r_fail1 = run([str(BUILDER), str(wrong_repo), str(spaced_out)])
        bad_tmp_env = os.environ.copy()
        bad_tmp_env["TMPDIR"] = str(tmp_root / "no-such-tmpdir")
        r_fail2 = run([str(BUILDER), str(UPSTREAM), str(spaced_out)], env=bad_tmp_env)
        check(
            "#101 failed rebuilds leave previous owned output untouched",
            r_fail1.returncode != 0
            and r_fail2.returncode != 0
            and owned_marker.exists()
            and owned_marker.read_text() == "v1\n"
            and sorted(p.name for p in spaced_out.iterdir()) == sorted(THEME_IDS),
            f"rc1={r_fail1.returncode}, rc2={r_fail2.returncode}",
        )

        sys.dont_write_bytecode = True
        spec = importlib.util.spec_from_file_location("ws_mod", GENERATOR)
        assert spec and spec.loader
        ws_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ws_mod)

        rb_stage = tmp_root / "rb-stage"
        rb_dest = tmp_root / "rb-dest"
        shutil.copytree(spaced_out, rb_stage, symlinks=True)
        shutil.copytree(spaced_out, rb_dest, symlinks=True)
        (rb_dest / "WhiteSur-lavender/.rb-sentinel").write_text("original-v1\n")
        (rb_stage / "WhiteSur-lavender/.rb-sentinel").write_text("new-v2\n")
        real_rename = os.rename
        rename_calls = {"n": 0}

        def failing_rename(src, dst):
            rename_calls["n"] += 1
            if rename_calls["n"] == 5:
                raise OSError("simulated mid-publish rename failure")
            return real_rename(src, dst)

        ws_mod.os.rename = failing_rename
        rb_threw = False
        try:
            ws_mod.publish_trio(str(rb_stage), str(rb_dest), str(PROJECT), str(UPSTREAM))
        except OSError:
            rb_threw = True
        finally:
            ws_mod.os.rename = real_rename

        rb_entries = sorted(p.name for p in rb_dest.iterdir())
        check(
            "#101 mid-publish swap failure rolls back all 3 previous themes cleanly",
            rb_threw
            and rb_entries == sorted(THEME_IDS)
            and (rb_dest / "WhiteSur-lavender/.rb-sentinel").read_text() == "original-v1\n",
            f"threw={rb_threw}, entries={rb_entries}",
        )

        r_reb = run([str(BUILDER), str(UPSTREAM), str(spaced_out)])
        check(
            "#101 rebuild over owned output succeeds cleanly",
            r_reb.returncode == 0
            and not owned_marker.exists()
            and sorted(p.name for p in spaced_out.iterdir()) == sorted(THEME_IDS),
            f"rc={r_reb.returncode}",
        )

        conc_out = tmp_root / "concurrent-out"
        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(run, [str(BUILDER), str(UPSTREAM), str(conc_out)])
            f2 = pool.submit(run, [str(BUILDER), str(UPSTREAM), str(conc_out)])
            res1, res2 = f1.result(), f2.result()
        conc_entries = sorted(p.name for p in conc_out.iterdir()) if conc_out.exists() else []
        check(
            "#101 concurrent writers to same destination both succeed cleanly",
            res1.returncode == 0 and res2.returncode == 0 and conc_entries == sorted(THEME_IDS),
            f"rc1={res1.returncode}, rc2={res2.returncode}, entries={conc_entries}",
        )

        # ------------------------------------------------------------------
        # #103, #105, #106: Direct whitesur-lavender.py fault-injection tests
        # ------------------------------------------------------------------
        def test_gen_fault(label: str, mutate) -> None:
            exp = tmp_root / f"exp-{hashlib.sha1(label.encode()).hexdigest()[:8]}"
            make_export(exp, pinned_commit)
            mutate(exp)
            inst_after_mutate = (exp / "install.sh").read_bytes()
            r = run(["python3", "-I", str(GENERATOR), str(exp)])
            no_leftover = not os.path.lexists(exp / "colors/color-lavender")
            inst_untouched = (exp / "install.sh").read_bytes() == inst_after_mutate
            check(
                f"generator rejects {label} without leaving color-lavender",
                r.returncode != 0 and no_leftover and inst_untouched,
                f"rc={r.returncode}, leftover={not no_leftover}",
            )

        test_gen_fault("#105 dropped folder.svg", lambda e: (e / "colors/color-purple/folder.svg").unlink())
        test_gen_fault(
            "#105 extra file in color-purple",
            lambda e: (e / "colors/color-purple/extra.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'/>"),
        )
        test_gen_fault(
            "#105 changed accent in folder-cloud.svg",
            lambda e: (e / "colors/color-purple/folder-cloud.svg").write_text(
                (e / "colors/color-purple/folder-cloud.svg").read_text().replace("#e791f3", "#d65fce")
            ),
        )
        test_gen_fault(
            "#105 truncated folder.svg",
            lambda e: (e / "colors/color-purple/folder.svg").write_text("<svg xmlns='http://www.w3.org/2000/svg'><path"),
        )
        test_gen_fault(
            "#105 changed installer anchor",
            lambda e: (e / "install.sh").write_text((e / "install.sh").read_text().replace("purple)", "violet)")),
        )
        test_gen_fault(
            "#106 inserted variant before pink",
            lambda e: (e / "install.sh").write_text(
                (e / "install.sh").read_text().replace("'-purple' '-pink'", "'-purple' '-mint' '-pink'")
            ),
        )

        def mut_link_svg(e: Path) -> None:
            p = e / "colors/color-purple/folder.svg"
            copy = e / "colors/folder-orig.svg"
            shutil.copy2(p, copy)
            p.unlink()
            p.symlink_to("../folder-orig.svg")

        test_gen_fault("#103 symlinked input SVG", mut_link_svg)

        def mut_link_inst(e: Path) -> None:
            p = e / "install.sh"
            copy = e / "install-orig.sh"
            shutil.copy2(p, copy)
            p.unlink()
            p.symlink_to("install-orig.sh")

        test_gen_fault("#103 symlinked install.sh", mut_link_inst)
        test_gen_fault(
            "#103 escaping symlink in export",
            lambda e: (e / "links/escape.svg").symlink_to("../../../../../../etc/hosts"),
        )

        exp_106 = tmp_root / "exp-106-literal"
        make_export(exp_106, pinned_commit)
        r_p = run(["python3", "-I", str(GENERATOR), str(exp_106)])
        assert r_p.returncode == 0, r_p.stderr
        inst_text = (exp_106 / "install.sh").read_text()
        check(
            "#106 patched install.sh uses literal '-lavender' (not THEME_VARIANTS[9])",
            "themes+=('-lavender')" in inst_text and "THEME_VARIANTS[9]" not in inst_text,
        )
        (exp_106 / "install.sh").write_text(inst_text.replace("'-purple' '-pink'", "'-purple' '-mint' '-pink'"))
        stage_106 = tmp_root / "stage-106"
        stage_106.mkdir()
        r_run106 = run(
            [
                "env",
                "-i",
                "PATH=/usr/local/bin:/usr/bin:/bin",
                "LC_ALL=C",
                f"HOME={tmp_root}",
                "/usr/bin/bash",
                "--noprofile",
                "--norc",
                "./install.sh",
                "-d",
                str(stage_106),
                "-n",
                "WhiteSur",
                "-t",
                "lavender",
                "-p",
            ],
            cwd=exp_106,
        )
        out_106 = sorted(p.name for p in stage_106.iterdir())
        check(
            "#106 shifted THEME_VARIANTS still builds WhiteSur-lavender* (never Nord)",
            r_run106.returncode == 0 and out_106 == sorted(THEME_IDS),
            f"rc={r_run106.returncode}, out={out_106}",
        )

        # ------------------------------------------------------------------
        # #111: SVG XML & namespace check across all physical SVGs
        # ------------------------------------------------------------------
        total_svgs = 0
        missing_ns = 0
        for tid in THEME_IDS:
            for dp, _, fns in os.walk(spaced_out / tid, followlinks=False):
                for fn in fns:
                    if not fn.endswith(".svg"):
                        continue
                    fp = Path(dp) / fn
                    if fp.is_symlink():
                        continue
                    total_svgs += 1
                    root = ET.fromstring(fp.read_bytes())
                    if root.tag != "{http://www.w3.org/2000/svg}svg":
                        missing_ns += 1
        # The pinned upstream build has 20,326 physical SVGs with an empty
        # custom layer. Each tracked custom entry can add, replace, or alias
        # away at most one physical SVG per theme, so the build must stay
        # within that margin (#287: catches a build that drops icons en masse).
        svg_baseline = 20326
        custom_entries = sum(
            1
            for p in (PROJECT / "icons/custom").rglob("*")
            if p.suffix in (".svg", ".png") and (p.is_symlink() or p.is_file())
        )
        svg_margin = custom_entries * len(THEME_IDS)
        check(
            "#111 all physical SVGs in built trio have SVG namespace",
            abs(total_svgs - svg_baseline) <= svg_margin and missing_ns == 0,
            f"total_svgs={total_svgs}, baseline={svg_baseline}±{svg_margin}, missing_ns={missing_ns}",
        )

        empty_custom = tmp_root / "empty-custom"
        empty_custom.mkdir()
        sample_svg = stage_106 / "WhiteSur-lavender/places/16/folder-vbox.svg"
        orig_sample = sample_svg.read_text()
        sample_svg.write_text(orig_sample.replace(' xmlns="http://www.w3.org/2000/svg"', "", 1))
        r_v111 = run(
            ["python3", "-I", str(GENERATOR), "--verify", str(stage_106), str(exp_106), str(empty_custom)]
        )
        check(
            "#111 --verify rejects staged SVG missing SVG namespace",
            r_v111.returncode != 0 and "SVG namespace" in r_v111.stderr,
            f"rc={r_v111.returncode}",
        )

        # ------------------------------------------------------------------
        # #108 & #109: Launcher resolution & license notices
        # ------------------------------------------------------------------
        import gi

        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk

        launcher_ok = True
        for tid in THEME_IDS:
            it = Gtk.IconTheme.new()
            it.set_search_path([str(spaced_out)])
            it.set_custom_theme(tid)
            for sz in (16, 22, 24, 32, 48, 64):
                info = it.lookup_icon("start-here-kde-plasma", sz, 0)
                if not info or not info.get_filename():
                    launcher_ok = False
                    continue
                resolved = Path(info.get_filename()).resolve()
                txt = resolved.read_text()
                has_apple = any(m in txt for m in ("10.062 3.2488", "10.356 286.57", "11.82 8.4375", "19.302 7.855"))
                has_kde = any(m in txt for m in ("M 5 2 A 1 1", "M 7 3 C 6.4 3", "m425.24 489.13"))
                if has_apple or not has_kde:
                    launcher_ok = False
        check("#108 start-here-kde-plasma resolves to KDE Plasma at 16-64 px in all 3 themes", launcher_ok)

        icons_texts = "\n".join(p.read_text() for p in (PROJECT / "icons").iterdir() if p.is_file())
        notices_ok = all(
            (spaced_out / tid / "COPYING").read_bytes() == (UPSTREAM / "COPYING").read_bytes()
            and (spaced_out / tid / "AUTHORS").read_bytes() == (UPSTREAM / "AUTHORS").read_bytes()
            and pinned_commit in (spaced_out / tid / "LAVENDER-NOTICE.txt").read_text()
            and "GPL-3.0-only" in (spaced_out / tid / "LAVENDER-NOTICE.txt").read_text()
            for tid in THEME_IDS
        )
        check(
            "#109 accurate license headers and per-theme notices (COPYING, AUTHORS, LAVENDER-NOTICE.txt)",
            "GPL-3.0-or-later" not in icons_texts and notices_ok,
        )

        # ------------------------------------------------------------------
        # Safe upstream update review workflow (never executes candidate install.sh)
        # ------------------------------------------------------------------
        prop_same = tmp_root / "proposed-same.json"
        r_rev0 = run([str(REVIEWER), pinned_commit, str(UPSTREAM), str(prop_same)])
        check(
            "update review on current pin passes with 0 blockers and writes proposal",
            r_rev0.returncode == 0
            and "READY FOR HUMAN REVIEW" in r_rev0.stdout
            and prop_same.is_file()
            and json.loads(prop_same.read_text())["commit"] == pinned_commit,
            f"rc={r_rev0.returncode}",
        )

        # Refuses overwriting active icons/whitesur-pin.json directly
        r_rev_active = run([str(REVIEWER), pinned_commit, str(UPSTREAM), str(PIN_FILE)])
        check(
            "update review refuses overwriting icons/whitesur-pin.json directly",
            r_rev_active.returncode != 0 and PIN_FILE.read_bytes() == pin_before_bytes,
            f"rc={r_rev_active.returncode}",
        )

        # Simulated upstream release with changes in install.sh (including an exec trap!),
        # color-purple, AUTHORS, symlinks, and missing-xmlns SVGs:
        cand_repo = tmp_root / "candidate-upstream"
        assert run(["git", "clone", "--quiet", str(UPSTREAM), str(cand_repo)]).returncode == 0
        exec_sentinel = tmp_root / "SHOULD_NEVER_EXIST"
        # Add a harmless comment + trap that WOULD create exec_sentinel if install.sh were ever run!
        inst_p = cand_repo / "install.sh"
        inst_p.write_text(
            inst_p.read_text().replace("#!/usr/bin/env bash\n", f"#!/usr/bin/env bash\ntouch '{exec_sentinel}'\n", 1)
        )
        # Fix one missing-xmlns SVG
        first_ns = pin["missing_ns_svgs"][0]
        ns_p = cand_repo / first_ns
        ns_p.write_text(ns_p.read_text().replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1))
        # Modify AUTHORS
        (cand_repo / "AUTHORS").write_text((cand_repo / "AUTHORS").read_text() + "Contributor\n")
        # Add a harmless comment to folder.svg
        fp = cand_repo / "colors/color-purple/folder.svg"
        fp.write_text(fp.read_text() + "\n<!-- test -->\n")
        # Add one relative symlink inside links/
        (cand_repo / "links/places/16/folder-new-test.svg").symlink_to("folder.svg")
        assert run(["git", "-C", str(cand_repo), "add", "-A"]).returncode == 0
        assert (
            run(
                [
                    "git",
                    "-C",
                    str(cand_repo),
                    "-c",
                    "user.name=Test",
                    "-c",
                    "user.email=test@example.invalid",
                    "commit",
                    "-q",
                    "-m",
                    "simulated release",
                ]
            ).returncode
            == 0
        )
        assert run(["git", "-C", str(cand_repo), "tag", "2026-12-01"]).returncode == 0
        cand_commit = run(["git", "-C", str(cand_repo), "rev-parse", "2026-12-01^{commit}"]).stdout.strip()

        prop_cand = tmp_root / "proposed-cand.json"
        r_revc = run([str(REVIEWER), "2026-12-01", str(cand_repo), str(prop_cand)])
        cand_pin = json.loads(prop_cand.read_text()) if prop_cand.is_file() else {}
        check(
            "update review reports all changed categories without executing candidate install.sh",
            r_revc.returncode == 0
            and not exec_sentinel.exists()
            and "CHANGED" in r_revc.stdout
            and "folder.svg" in r_revc.stdout
            and first_ns in r_revc.stdout
            and "AUTHORS" in r_revc.stdout
            and "+1 added" in r_revc.stdout
            and cand_pin.get("commit") == cand_commit
            and len(cand_pin.get("missing_ns_svgs", [])) == len(pin["missing_ns_svgs"]) - 1
            and cand_pin.get("symlink_count") == pin["symlink_count"] + 1
            and PIN_FILE.read_bytes() == pin_before_bytes,
            f"rc={r_revc.returncode}, exec_sentinel={exec_sentinel.exists()}",
        )

        # Builder still refuses candidate commit until icons/whitesur-pin.json is explicitly updated
        r_refuse_cand = run([str(BUILDER), str(cand_repo), str(tmp_root / "cand-out")])
        check(
            "builder refuses unreviewed candidate release until pin is updated",
            r_refuse_cand.returncode != 0 and not (tmp_root / "cand-out").exists(),
            f"rc={r_refuse_cand.returncode}",
        )

        # ------------------------------------------------------------------
        # Tracked custom icon layer (all/, light/, dark/) + update review
        # ------------------------------------------------------------------
        custom_root = tmp_root / "custom-icons"
        for layer in ("all", "light", "dark"):
            (custom_root / layer).mkdir(parents=True)
            (custom_root / layer / ".gitkeep").write_text("")

        svg_all_folder = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" fill="#112233"/></svg>\n'
        svg_light_folder = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" fill="#ddeeff"/></svg>\n'
        svg_all_app = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><circle cx="32" cy="32" r="24" fill="#445566"/></svg>\n'
        svg_dark_app = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><circle cx="32" cy="32" r="24" fill="#111111"/></svg>\n'
        svg_new_app = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="48" height="48" x="8" y="8" fill="#778899"/></svg>\n'

        (custom_root / "all/places/scalable").mkdir(parents=True)
        (custom_root / "all/places/scalable/folder.svg").write_text(svg_all_folder)
        (custom_root / "light/places/scalable").mkdir(parents=True)
        (custom_root / "light/places/scalable/folder.svg").write_text(svg_light_folder)
        (custom_root / "all/apps/scalable").mkdir(parents=True)
        (custom_root / "all/apps/scalable/firefox.svg").write_text(svg_all_app)
        (custom_root / "all/apps/scalable/my-brand-new-app.svg").write_text(svg_new_app)
        (custom_root / "all/apps/scalable/my-brand-new-alias.svg").symlink_to("my-brand-new-app.svg")
        (custom_root / "dark/apps/scalable").mkdir(parents=True)
        (custom_root / "dark/apps/scalable/firefox.svg").write_text(svg_dark_app)

        custom_out = tmp_root / "custom-out"
        custom_env = os.environ.copy()
        custom_env["M9_ICON_CUSTOM_DIR"] = str(custom_root)
        r_cust = run([str(BUILDER), str(UPSTREAM), str(custom_out)], env=custom_env)
        check(
            "custom layer build succeeds with all/light/dark overrides, brand-new icon, and alias",
            r_cust.returncode == 0
            and (custom_out / "WhiteSur-lavender/places/scalable/folder.svg").read_text() == svg_all_folder
            and (custom_out / "WhiteSur-lavender-dark/places/scalable/folder.svg").read_text() == svg_all_folder
            and (custom_out / "WhiteSur-lavender-light/places/scalable/folder.svg").read_text() == svg_light_folder
            and (custom_out / "WhiteSur-lavender/apps/scalable/firefox.svg").read_text() == svg_all_app
            and (custom_out / "WhiteSur-lavender-light/apps/scalable/firefox.svg").read_text() == svg_all_app
            and (custom_out / "WhiteSur-lavender-dark/apps/scalable/firefox.svg").read_text() == svg_dark_app
            and (custom_out / "WhiteSur-lavender/apps/scalable/my-brand-new-app.svg").read_text() == svg_new_app
            and (custom_out / "WhiteSur-lavender/apps/scalable/my-brand-new-alias.svg").is_symlink()
            and os.readlink(custom_out / "WhiteSur-lavender/apps/scalable/my-brand-new-alias.svg") == "my-brand-new-app.svg",
            f"rc={r_cust.returncode}",
        )

        # Removing a custom icon and rebuilding restores the Lavender icon!
        (custom_root / "all/places/scalable/folder.svg").unlink()
        (custom_root / "light/places/scalable/folder.svg").unlink()
        r_cust_rm = run([str(BUILDER), str(UPSTREAM), str(custom_out)], env=custom_env)
        check(
            "removing custom folder.svg and rebuilding restores Lavender folder.svg",
            r_cust_rm.returncode == 0
            and "#b5b4f9" in (custom_out / "WhiteSur-lavender/places/scalable/folder.svg").read_text().lower()
            and "#b5b4f9" in (custom_out / "WhiteSur-lavender-light/places/scalable/folder.svg").read_text().lower(),
            f"rc={r_cust_rm.returncode}",
        )

        # Restore custom folder.svg for review-whitesur-update override reporting test
        (custom_root / "all/places/scalable/folder.svg").write_text(svg_all_folder)
        prop_cust = tmp_root / "proposed-cust.json"
        r_rev_cust = run([str(REVIEWER), "2026-12-01", str(cand_repo), str(prop_cust)], env=custom_env)
        check(
            "review-whitesur-update reports when upstream changed an overridden icon",
            r_rev_cust.returncode == 0
            and "UPSTREAM CHANGED OVERRIDDEN ICON" in r_rev_cust.stdout
            and "all/places/scalable/folder.svg" in r_rev_cust.stdout
            and "brand-new custom" in r_rev_cust.stdout,
            f"rc={r_rev_cust.returncode}",
        )

        # Custom validation rejections (fail before touching destination!)
        def test_bad_custom(label: str, setup_fn) -> None:
            bc = tmp_root / f"bad-cust-{hashlib.sha1(label.encode()).hexdigest()[:8]}"
            for l in ("all", "light", "dark"):
                (bc / l).mkdir(parents=True)
            setup_fn(bc)
            benv = os.environ.copy()
            benv["M9_ICON_CUSTOM_DIR"] = str(bc)
            bout = tmp_root / f"bad-cust-out-{hashlib.sha1(label.encode()).hexdigest()[:8]}"
            r_b = run([str(BUILDER), str(UPSTREAM), str(bout)], env=benv)
            check(f"custom validation rejects {label}", r_b.returncode != 0 and not bout.exists(), f"rc={r_b.returncode}")

        test_bad_custom(
            "malformed SVG",
            lambda c: ((c / "all/apps/scalable").mkdir(parents=True), (c / "all/apps/scalable/bad.svg").write_text("<svg><broken")),
        )
        test_bad_custom(
            "SVG missing xmlns",
            lambda c: ((c / "all/apps/scalable").mkdir(parents=True), (c / "all/apps/scalable/no-ns.svg").write_text('<svg width="64" height="64"/>')),
        )
        test_bad_custom(
            "corrupt PNG",
            lambda c: ((c / "all/apps/16").mkdir(parents=True), (c / "all/apps/16/bad.png").write_bytes(b"not a png")),
        )
        test_bad_custom(
            "escaping symlink alias",
            lambda c: ((c / "all/apps/scalable").mkdir(parents=True), (c / "all/apps/scalable/esc.svg").symlink_to("../../../../etc/hosts.svg")),
        )
        test_bad_custom(
            "unindexed directory",
            lambda c: ((c / "all/bogus/99").mkdir(parents=True), (c / "all/bogus/99/foo.svg").write_text(svg_new_app)),
        )
        test_bad_custom(
            "broken alias target",
            lambda c: ((c / "all/apps/scalable").mkdir(parents=True), (c / "all/apps/scalable/broken-alias.svg").symlink_to("does-not-exist-anywhere.svg")),
        )

        # ------------------------------------------------------------------
        # Automatic WhiteSur bare cache & fetch-whitesur.sh (local file:// remote)
        # ------------------------------------------------------------------
        local_remote = tmp_root / "local-remote.git"
        assert run(["git", "clone", "--bare", "--quiet", str(UPSTREAM), str(local_remote)]).returncode == 0
        assert run(["git", "-C", str(local_remote), "config", "uploadpack.allowAnySHA1InWant", "true"]).returncode == 0
        remote_url = f"file://{local_remote}"

        cache_path = tmp_root / "cache-home/macos9-theme/WhiteSur-icon-theme"
        r_chk = run([str(FETCHER), "--check-only", pinned_commit, str(cache_path), remote_url])
        check(
            "fetch-whitesur --check-only reports NEEDS_FETCH without creating cache dir",
            r_chk.returncode == 0 and r_chk.stdout.strip() == "NEEDS_FETCH" and not cache_path.parent.exists(),
            f"rc={r_chk.returncode}, out={r_chk.stdout.strip()!r}",
        )

        r_fetch = run([str(FETCHER), pinned_commit, str(cache_path), remote_url])
        check(
            "fetch-whitesur fetches exact pinned commit from local remote into bare cache",
            r_fetch.returncode == 0 and r_fetch.stdout.strip() == "FETCHED" and cache_path.is_dir(),
            f"rc={r_fetch.returncode}, out={r_fetch.stdout.strip()!r}",
        )

        # Offline reuse with unreachable remote URL succeeds!
        r_off_hit = run([str(FETCHER), pinned_commit, str(cache_path), "file:///nonexistent-offline-remote"])
        check(
            "fetch-whitesur reuses verified cache offline",
            r_off_hit.returncode == 0 and r_off_hit.stdout.strip() == "CACHED",
            f"rc={r_off_hit.returncode}, out={r_off_hit.stdout.strip()!r}",
        )

        # Builder works directly from the bare cache!
        bare_out = tmp_root / "bare-cache-out"
        r_bare_build = run([str(BUILDER), str(cache_path), str(bare_out)])
        check(
            "builder builds verified trio directly from bare cache",
            r_bare_build.returncode == 0 and sorted(p.name for p in bare_out.iterdir()) == sorted(THEME_IDS),
            f"rc={r_bare_build.returncode}",
        )

        # Offline failure when cache is missing
        miss_cache = tmp_root / "miss-cache/WhiteSur-icon-theme"
        r_off_miss = run([str(FETCHER), pinned_commit, str(miss_cache), "file:///nonexistent-offline-remote"])
        check(
            "fetch-whitesur fails cleanly offline when cache is missing",
            r_off_miss.returncode != 0 and not miss_cache.exists(),
            f"rc={r_off_miss.returncode}",
        )

        # Corrupt cache rejected
        corrupt_cache = tmp_root / "corrupt-cache"
        corrupt_cache.mkdir()
        (corrupt_cache / "garbage").write_text("corrupt")
        r_corrupt = run([str(FETCHER), pinned_commit, str(corrupt_cache), remote_url])
        check(
            "fetch-whitesur rejects corrupt cache",
            r_corrupt.returncode != 0 and "corrupt" in r_corrupt.stderr.lower(),
            f"rc={r_corrupt.returncode}",
        )

        # Wrong-commit cache rejected
        r_wrong_c = run([str(FETCHER), pinned_commit, str(wrong_repo), remote_url])
        check(
            "fetch-whitesur rejects cache at wrong commit",
            r_wrong_c.returncode != 0 and "expected reviewed pin" in r_wrong_c.stderr,
            f"rc={r_wrong_c.returncode}",
        )

        # Symlinked cache rejected
        sym_cache = tmp_root / "sym-cache"
        sym_cache.symlink_to(cache_path)
        r_sym_c = run([str(FETCHER), pinned_commit, str(sym_cache), remote_url])
        check(
            "fetch-whitesur rejects symlinked cache path",
            r_sym_c.returncode != 0 and "symbolic link" in r_sym_c.stderr,
            f"rc={r_sym_c.returncode}",
        )

        # ------------------------------------------------------------------
        # #116: Unrelated .WhiteSur-fetch.mydata preserved + owned pending cleanup
        # ------------------------------------------------------------------
        cache_116_parent = tmp_root / "cache-116"
        unrelated_dir = cache_116_parent / ".WhiteSur-fetch.mydata"
        unrelated_dir.mkdir(parents=True)
        (unrelated_dir / "keep.txt").write_text("do-not-delete\n")
        cache_116 = cache_116_parent / "WhiteSur-icon-theme"
        r_116 = run([str(FETCHER), pinned_commit, str(cache_116), remote_url])
        check(
            "#116 fetch-whitesur preserves unrelated .WhiteSur-fetch.mydata",
            r_116.returncode == 0
            and cache_116.is_dir()
            and (unrelated_dir / "keep.txt").read_text() == "do-not-delete\n",
            f"rc={r_116.returncode}",
        )

        # ------------------------------------------------------------------
        # #121: Full git fsck catches truncated/corrupt blob object in cache
        # ------------------------------------------------------------------
        corrupt_blob_cache = tmp_root / "corrupt-blob-cache"
        shutil.copytree(cache_path, corrupt_blob_cache)
        # Unpack or corrupt an object packfile/loose object inside objects/
        pack_files = sorted((corrupt_blob_cache / "objects/pack").glob("*.pack"))
        if pack_files:
            pf = pack_files[0]
            data = bytearray(pf.read_bytes())
            mid = len(data) // 2
            data[mid] ^= 0xFF
            pf.chmod(0o644)
            pf.write_bytes(bytes(data))
        else:
            loose = [p for p in (corrupt_blob_cache / "objects").rglob("*") if p.is_file() and len(p.parent.name) == 2]
            assert loose, "no git objects found in bare cache"
            loose[0].chmod(0o644)
            loose[0].write_bytes(b"corrupted")
        r_121_chk = run([str(FETCHER), "--check-only", pinned_commit, str(corrupt_blob_cache), remote_url])
        r_121_run = run([str(FETCHER), pinned_commit, str(corrupt_blob_cache), remote_url])
        check(
            "#121 full git fsck catches corrupt blob/pack in --check-only and real fetch",
            r_121_chk.returncode != 0
            and r_121_run.returncode != 0
            and "corrupt" in r_121_chk.stderr.lower()
            and "corrupt" in r_121_run.stderr.lower(),
            f"chk={r_121_chk.returncode}, run={r_121_run.returncode}",
        )

        # ------------------------------------------------------------------
        # #118: Shared preflight checks every tool/module and names Arch package
        # ------------------------------------------------------------------
        def make_masked_path(omit: str) -> Path:
            mdir = tmp_root / f"mask-{omit}"
            mdir.mkdir(exist_ok=True)
            for tool in ("git", "tar", "xmllint", "rsvg-convert", "gtk-update-icon-cache"):
                if tool == omit:
                    continue
                tp = shutil.which(tool)
                if tp:
                    dst = mdir / tool
                    if not dst.exists():
                        dst.symlink_to(tp)
            return mdir

        for missing_tool, arch_pkg in (
            ("xmllint", "libxml2"),
            ("rsvg-convert", "librsvg"),
            ("gtk-update-icon-cache", "gtk-update-icon-cache"),
            ("git", "git"),
        ):
            env_m = os.environ.copy()
            env_m["PATH"] = str(make_masked_path(missing_tool))
            r_pf = run([sys.executable, "-I", str(PROJECT / "icons/whitesur-lavender.py"), "--preflight"], env=env_m)
            check(
                f"#118 preflight detects missing {missing_tool} and names {arch_pkg}",
                r_pf.returncode != 0 and missing_tool in r_pf.stderr and arch_pkg in r_pf.stderr,
                f"rc={r_pf.returncode}, err={r_pf.stderr.strip()!r}",
            )

        # Missing GTK 3 typelib via empty GI_TYPELIB_PATH (note: /usr/lib/girepository-1.0 is default,
        # so also test PIL conditional check with a custom PNG dir and shadow-free PYTHONPATH check).
        png_cust = tmp_root / "png-preflight-custom"
        (png_cust / "all/apps/16").mkdir(parents=True)
        (png_cust / "light").mkdir(parents=True)
        (png_cust / "dark").mkdir(parents=True)
        (png_cust / "all/apps/16/dummy.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        # Pass when PIL is present; block PIL via sys.modules=None in a tiny wrapper to verify message.
        r_pf_ok = run([sys.executable, "-I", str(PROJECT / "icons/whitesur-lavender.py"), "--preflight", str(png_cust)])
        check("#118 preflight passes with all tools and PIL present", r_pf_ok.returncode == 0, f"err={r_pf_ok.stderr.strip()!r}")
        r_pf_nopil = run([
            sys.executable, "-I", "-c",
            "import sys; sys.modules['PIL'] = None; sys.path.insert(0, sys.argv[1]); "
            "import importlib.util; s = importlib.util.spec_from_file_location('wl', sys.argv[2]); "
            "m = importlib.util.module_from_spec(s); s.loader.exec_module(m); m.run_preflight(sys.argv[3])",
            str(PROJECT / "icons"), str(PROJECT / "icons/whitesur-lavender.py"), str(png_cust),
        ])
        check(
            "#118 preflight requires python-pillow when custom PNGs exist",
            r_pf_nopil.returncode != 0 and "python-pillow" in r_pf_nopil.stderr,
            f"rc={r_pf_nopil.returncode}, err={r_pf_nopil.stderr.strip()!r}",
        )
        r_pf_nogi = run([
            sys.executable, "-I", "-c",
            "import sys; sys.modules['gi'] = None; "
            "import importlib.util; s = importlib.util.spec_from_file_location('wl', sys.argv[1]); "
            "m = importlib.util.module_from_spec(s); s.loader.exec_module(m); m.run_preflight()",
            str(PROJECT / "icons/whitesur-lavender.py"),
        ])
        check(
            "#118 preflight detects missing gi and names python-gobject",
            r_pf_nogi.returncode != 0 and "python-gobject" in r_pf_nogi.stderr,
            f"rc={r_pf_nogi.returncode}, err={r_pf_nogi.stderr.strip()!r}",
        )

        # ------------------------------------------------------------------
        # #119: Cross-directory custom alias with light/ and dark/ target overrides
        # ------------------------------------------------------------------
        cust_119 = tmp_root / "custom-119"
        for sub in ("all/apps/scalable", "all/places/scalable", "light/apps/scalable", "dark/apps/scalable"):
            (cust_119 / sub).mkdir(parents=True)
        svg_119_base = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" fill="#111111"/></svg>\n'
        svg_119_light = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" fill="#eeeeee"/></svg>\n'
        svg_119_dark = '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64"><rect width="64" height="64" fill="#333333"/></svg>\n'
        (cust_119 / "all/apps/scalable/m9-xdir-app.svg").write_text(svg_119_base)
        (cust_119 / "all/places/scalable/m9-xdir-alias.svg").symlink_to("../../apps/scalable/m9-xdir-app.svg")
        (cust_119 / "light/apps/scalable/m9-xdir-app.svg").write_text(svg_119_light)
        (cust_119 / "dark/apps/scalable/m9-xdir-app.svg").write_text(svg_119_dark)
        out_119 = tmp_root / "out-119"
        env_119 = os.environ.copy()
        env_119["M9_ICON_CUSTOM_DIR"] = str(cust_119)
        r_119 = run([str(BUILDER), str(UPSTREAM), str(out_119)], env=env_119)
        ok_119_bytes = False
        if r_119.returncode == 0:
            import gi as _gi
            _gi.require_version("Gtk", "3.0")
            from gi.repository import Gtk as _Gtk

            def gtk_read(tid: str, icon_name: str) -> str:
                it = _Gtk.IconTheme.new()
                it.set_search_path([str(out_119)])
                it.set_custom_theme(tid)
                info = it.lookup_icon(icon_name, 64, 0)
                return Path(info.get_filename()).resolve(strict=True).read_text() if info and info.get_filename() else ""

            ok_119_bytes = (
                "#111111" in gtk_read("WhiteSur-lavender", "m9-xdir-alias")
                and "#eeeeee" in gtk_read("WhiteSur-lavender-light", "m9-xdir-alias")
                and "#333333" in gtk_read("WhiteSur-lavender-dark", "m9-xdir-alias")
            )
        check(
            "#119 cross-directory custom alias resolves to exact variant bytes in base, -light, and -dark via GTK3",
            r_119.returncode == 0 and ok_119_bytes,
            f"rc={r_119.returncode}, ok_bytes={ok_119_bytes}",
        )

        # ------------------------------------------------------------------
        # #120: Abrupt exit (os._exit) after first publish rename recovers cleanly
        # ------------------------------------------------------------------
        dest_120 = tmp_root / "dest-120"
        stage_120_v1 = tmp_root / "stage-120-v1"
        stage_120_v2 = tmp_root / "stage-120-v2"
        shutil.copytree(bare_out, stage_120_v1, symlinks=True)
        shutil.copytree(bare_out, stage_120_v2, symlinks=True)
        for tid in THEME_IDS:
            (stage_120_v1 / tid / ".macos9-whitesur-lavender-build").unlink(missing_ok=True)
            (stage_120_v2 / tid / ".macos9-whitesur-lavender-build").unlink(missing_ok=True)
        (stage_120_v1 / "WhiteSur-lavender/marker.txt").write_text("v1\n")
        (stage_120_v2 / "WhiteSur-lavender/marker.txt").write_text("v2\n")
        # Initial clean publish v1
        r_p1 = run([sys.executable, "-I", str(PROJECT / "icons/whitesur-lavender.py"), "--publish", str(stage_120_v1), str(dest_120), str(PROJECT), str(UPSTREAM)])
        # Crash abruptly right after 1st rename during v2 publish
        env_crash = os.environ.copy()
        env_crash["M9_TEST_CRASH_AFTER_FIRST_RENAME"] = "1"
        r_crash = run([sys.executable, "-I", str(PROJECT / "icons/whitesur-lavender.py"), "--publish", str(stage_120_v2), str(dest_120), str(PROJECT), str(UPSTREAM)], env=env_crash)
        crashed_partial = (
            r_crash.returncode == 99
            and (dest_120 / ".whitesur-lavender-publish.json").is_file()
            and not (dest_120 / "WhiteSur-lavender").exists()
        )
        # Explicit --recover-dest restores v1 cleanly with zero leftover dirs
        r_rec = run([sys.executable, "-I", str(PROJECT / "icons/whitesur-lavender.py"), "--recover-dest", str(dest_120)])
        rec_ok = (
            r_rec.returncode == 0
            and sorted(p.name for p in dest_120.iterdir()) == sorted(THEME_IDS)
            and (dest_120 / "WhiteSur-lavender/marker.txt").read_text() == "v1\n"
        )
        # Crash again and verify a subsequent --publish automatically reconciles and publishes v2 with zero leftovers!
        r_crash2 = run([sys.executable, "-I", str(PROJECT / "icons/whitesur-lavender.py"), "--publish", str(stage_120_v2), str(dest_120), str(PROJECT), str(UPSTREAM)], env=env_crash)
        r_p2 = run([sys.executable, "-I", str(PROJECT / "icons/whitesur-lavender.py"), "--publish", str(stage_120_v2), str(dest_120), str(PROJECT), str(UPSTREAM)])
        repub_ok = (
            r_crash2.returncode == 99
            and r_p2.returncode == 0
            and sorted(p.name for p in dest_120.iterdir()) == sorted(THEME_IDS)
            and (dest_120 / "WhiteSur-lavender/marker.txt").read_text() == "v2\n"
        )
        check(
            "#120 abrupt exit mid-publish recovers cleanly via --recover-dest and automatic next --publish",
            r_p1.returncode == 0 and crashed_partial and rec_ok and repub_ok,
            f"p1={r_p1.returncode}, partial={crashed_partial}, rec={rec_ok}, repub={repub_ok}",
        )

        # ------------------------------------------------------------------
        # #132: Interrupting recovery ITSELF during incoming cleanup never deletes restored themes
        # ------------------------------------------------------------------
        dest_132 = tmp_root / "dest-132"
        r_132_p1 = run([sys.executable, "-I", str(PROJECT / "icons/whitesur-lavender.py"), "--publish", str(stage_120_v1), str(dest_132), str(PROJECT), str(UPSTREAM)])
        r_132_c1 = run([sys.executable, "-I", str(PROJECT / "icons/whitesur-lavender.py"), "--publish", str(stage_120_v2), str(dest_132), str(PROJECT), str(UPSTREAM)], env=env_crash)
        env_rec_crash = os.environ.copy()
        env_rec_crash["M9_TEST_CRASH_DURING_RECOVERY_CLEANUP"] = "1"
        r_132_rc1 = run([sys.executable, "-I", str(PROJECT / "icons/whitesur-lavender.py"), "--recover-dest", str(dest_132)], env=env_rec_crash)
        r_132_rc2 = run([sys.executable, "-I", str(PROJECT / "icons/whitesur-lavender.py"), "--recover-dest", str(dest_132)])
        check(
            "#132 interrupted recovery during staging cleanup preserves all 3 restored originals on retry",
            r_132_p1.returncode == 0
            and r_132_c1.returncode == 99
            and r_132_rc1.returncode == 98
            and r_132_rc2.returncode == 0
            and sorted(p.name for p in dest_132.iterdir()) == sorted(THEME_IDS)
            and (dest_132 / "WhiteSur-lavender/marker.txt").read_text() == "v1\n",
            f"p1={r_132_p1.returncode}, c1={r_132_c1.returncode}, rc1={r_132_rc1.returncode}, rc2={r_132_rc2.returncode}",
        )

        # ------------------------------------------------------------------
        # #123 + #134: Extracted source archive works; linked Git worktree STILL enforces tracked-file protection
        # ------------------------------------------------------------------
        archive_proj = tmp_root / "archive-macos9-theme"
        (archive_proj / "icons").mkdir(parents=True)
        for fname in ("build-whitesur-lavender.sh", "whitesur-lavender.py", "whitesur-pin.json"):
            shutil.copy2(PROJECT / "icons" / fname, archive_proj / "icons" / fname)
        shutil.copytree(PROJECT / "icons/custom", archive_proj / "icons/custom")
        r_arch = run([str(archive_proj / "icons/build-whitesur-lavender.sh"), str(UPSTREAM)])
        arch_default_out = archive_proj / "dev/build/icons"
        # Also verify source-archive still rejects publishing into archive/icons!
        r_arch_bad = run([str(archive_proj / "icons/build-whitesur-lavender.sh"), str(UPSTREAM), str(archive_proj / "icons/bad-out")])
        check(
            "#123 standalone builder works with default dev/build/icons from extracted source archive (no .git)",
            r_arch.returncode == 0
            and sorted(p.name for p in arch_default_out.iterdir()) == sorted(THEME_IDS)
            and r_arch_bad.returncode != 0,
            f"arch_rc={r_arch.returncode}, bad_rc={r_arch_bad.returncode}",
        )

        # #134: Linked git worktree must detect git checkout and reject tracked files in dev/build/icons
        wt_main = tmp_root / "wt-main"
        wt_linked = tmp_root / "wt-linked"
        assert run(["git", "init", "--quiet", str(wt_main)]).returncode == 0
        (wt_main / ".gitignore").write_text("dev/build/\n")
        (wt_main / "icons").mkdir()
        for fname in ("build-whitesur-lavender.sh", "whitesur-lavender.py", "whitesur-pin.json"):
            shutil.copy2(PROJECT / "icons" / fname, wt_main / "icons" / fname)
        assert run(["git", "-C", str(wt_main), "add", ".gitignore", "icons"]).returncode == 0
        assert run(["git", "-C", str(wt_main), "-c", "user.name=Test", "-c", "user.email=t@e.invalid", "commit", "-q", "-m", "init"]).returncode == 0
        assert run(["git", "-C", str(wt_main), "worktree", "add", "--quiet", "--detach", str(wt_linked)]).returncode == 0
        # Stage a tracked file inside dev/build/icons/WhiteSur-lavender in the linked worktree
        tracked_marker = wt_linked / "dev/build/icons/WhiteSur-lavender/tracked.txt"
        tracked_marker.parent.mkdir(parents=True)
        tracked_marker.write_text("do-not-delete\n")
        (wt_linked / "dev/build/icons/WhiteSur-lavender/.macos9-whitesur-lavender-build").write_text(
            "managed-by=macos9-theme/icons/build-whitesur-lavender.sh\ntheme=WhiteSur-lavender\n"
        )
        assert run(["git", "-C", str(wt_linked), "add", "-f", "dev/build/icons/WhiteSur-lavender/tracked.txt"]).returncode == 0
        r_wt_bad = run([
            sys.executable, "-I", str(wt_linked / "icons/whitesur-lavender.py"),
            "--check-dest", str(wt_linked / "dev/build/icons"), str(wt_linked), str(UPSTREAM),
        ])
        r_wt_unignored = run([
            sys.executable, "-I", str(wt_linked / "icons/whitesur-lavender.py"),
            "--check-dest", str(wt_linked / "unignored-out"), str(wt_linked), str(UPSTREAM),
        ])
        check(
            "#134 linked Git worktree enforces tracked-file and git-ignore protections",
            r_wt_bad.returncode != 0
            and r_wt_unignored.returncode != 0
            and tracked_marker.read_text() == "do-not-delete\n",
            f"bad_rc={r_wt_bad.returncode}, unign_rc={r_wt_unignored.returncode}",
        )

        # ------------------------------------------------------------------
        # #137: Nonexistent TMPDIR leaves zero cache parent or .WhiteSur-fetch.* behind
        # ------------------------------------------------------------------
        cache_137_parent = tmp_root / "cache-137-parent"
        cache_137 = cache_137_parent / "WhiteSur-icon-theme"
        env_137 = os.environ.copy()
        env_137["TMPDIR"] = str(tmp_root / "nonexistent-tmpdir-137")
        r_137 = run([str(FETCHER), pinned_commit, str(cache_137), remote_url], env=env_137)
        check(
            "#137 nonexistent TMPDIR fails cleanly before creating cache parent or .WhiteSur-fetch.* temp dir",
            r_137.returncode != 0 and not cache_137_parent.exists(),
            f"rc={r_137.returncode}, parent_exists={cache_137_parent.exists()}",
        )

        # ------------------------------------------------------------------
        # #143: User-owned symlinked ~/.cache works; unsafe/foreign paths refused
        # ------------------------------------------------------------------
        real_storage_143 = tmp_root / "storage-143/local/cache"
        real_storage_143.mkdir(parents=True)
        os.chmod(real_storage_143, 0o700)
        home_143 = tmp_root / "home-143"
        home_143.mkdir()
        (home_143 / ".cache").symlink_to(real_storage_143)
        sym_home_cache = home_143 / ".cache/macos9-theme/WhiteSur-icon-theme"

        r_143_chk = run([str(FETCHER), "--check-only", pinned_commit, str(sym_home_cache), remote_url])
        r_143_fetch = run([str(FETCHER), pinned_commit, str(sym_home_cache), remote_url])
        r_143_reuse = run([str(FETCHER), pinned_commit, str(sym_home_cache), "file:///nonexistent-offline"])
        out_143 = tmp_root / "out-143-sym-cache"
        r_143_build = run([str(BUILDER), str(sym_home_cache), str(out_143)])
        check(
            "#143 user-owned symlinked ~/.cache fetches, reuses offline, and builds directly",
            r_143_chk.returncode == 0
            and r_143_chk.stdout.strip() == "NEEDS_FETCH"
            and r_143_fetch.returncode == 0
            and r_143_fetch.stdout.strip() == "FETCHED"
            and r_143_reuse.returncode == 0
            and r_143_reuse.stdout.strip() == "CACHED"
            and (real_storage_143 / "macos9-theme/WhiteSur-icon-theme").is_dir()
            and r_143_build.returncode == 0
            and all((out_143 / tid / "index.theme").is_file() for tid in THEME_IDS),
            f"chk={r_143_chk.returncode}, fetch={r_143_fetch.returncode}, reuse={r_143_reuse.returncode}, build={r_143_build.returncode}",
        )

        # Unsafe/foreign symlinked or non-symlinked cache paths must still be refused:
        dangling_143 = tmp_root / "home-143-dangling"
        dangling_143.mkdir()
        (dangling_143 / ".cache").symlink_to(tmp_root / "does-not-exist-143")
        r_143_dang = run([str(FETCHER), pinned_commit, str(dangling_143 / ".cache/macos9-theme/WhiteSur-icon-theme"), remote_url])
        check(
            "#143 fetch-whitesur refuses dangling symlinked ~/.cache",
            r_143_dang.returncode != 0,
            f"rc={r_143_dang.returncode}, err={r_143_dang.stderr.strip()}",
        )

        loop_143 = tmp_root / "home-143-loop"
        loop_143.mkdir()
        (loop_143 / "a").symlink_to(loop_143 / "b")
        (loop_143 / "b").symlink_to(loop_143 / "a")
        r_143_loop = run([str(FETCHER), pinned_commit, str(loop_143 / "a/macos9-theme/WhiteSur-icon-theme"), remote_url])
        check(
            "#143 fetch-whitesur refuses symlink loop in cache ancestor",
            r_143_loop.returncode != 0,
            f"rc={r_143_loop.returncode}",
        )

        file_link_143 = tmp_root / "home-143-file"
        file_link_143.mkdir()
        (file_link_143 / "regular-file").write_text("not a dir\n")
        (file_link_143 / ".cache").symlink_to(file_link_143 / "regular-file")
        r_143_file = run([str(FETCHER), pinned_commit, str(file_link_143 / ".cache/macos9-theme/WhiteSur-icon-theme"), remote_url])
        check(
            "#143 fetch-whitesur refuses symlinked ~/.cache pointing to non-directory",
            r_143_file.returncode != 0,
            f"rc={r_143_file.returncode}",
        )

        ww_target_143 = tmp_root / "ww-target-143"
        ww_target_143.mkdir()
        os.chmod(ww_target_143, 0o777)
        ww_home_143 = tmp_root / "home-143-ww"
        ww_home_143.mkdir()
        (ww_home_143 / ".cache").symlink_to(ww_target_143)
        r_143_ww = run([str(FETCHER), pinned_commit, str(ww_home_143 / ".cache/macos9-theme/WhiteSur-icon-theme"), remote_url])
        check(
            "#143 fetch-whitesur refuses symlinked ~/.cache pointing to world-writable directory",
            r_143_ww.returncode != 0 and "world-writable" in r_143_ww.stderr,
            f"rc={r_143_ww.returncode}, err={r_143_ww.stderr.strip()}",
        )

        foreign_home_143 = tmp_root / "home-143-foreign"
        foreign_home_143.mkdir()
        (foreign_home_143 / ".cache").symlink_to("/etc")
        r_143_etc = run([str(FETCHER), pinned_commit, str(foreign_home_143 / ".cache/macos9-theme/WhiteSur-icon-theme"), remote_url])
        r_143_tmp = run([str(FETCHER), "--check-only", pinned_commit, "/tmp/macos9-theme-143-test/WhiteSur-icon-theme", remote_url])
        check(
            "#143 fetch-whitesur refuses foreign-owned (/etc) and world-writable (/tmp) cache paths",
            r_143_etc.returncode != 0 and r_143_tmp.returncode != 0,
            f"etc_rc={r_143_etc.returncode}, tmp_rc={r_143_tmp.returncode}",
        )

        # Verify upstream checkout & active pin remained untouched
        up_status = run(["git", "-C", str(UPSTREAM), "status", "--short"]).stdout.strip()
        up_head = run(["git", "-C", str(UPSTREAM), "rev-parse", "HEAD"]).stdout.strip()
        check(
            "upstream checkout and active pin untouched",
            up_status == "" and up_head == pinned_commit and PIN_FILE.read_bytes() == pin_before_bytes,
            f"HEAD={up_head}",
        )
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)

    print(f"\nSUMMARY: {passed} passed, {failed} failed")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
