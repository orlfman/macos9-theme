#!/usr/bin/env python3
"""Comprehensive throwaway-HOME test suite for firefox/install.sh and
firefox/uninstall.sh (docs/FIREFOX-PLAN.md Milestone 6).

Covers:
  1. Fresh profile (no chrome/, no user.js, existing 0600 prefs.js + unlocked
     0-byte .parentlock): --list, --dry-run, real PTY interactive selection,
     simulated Firefox pref copy, --dry-run undo, interactive undo -> exact
     byte-for-byte + mode restoration, idempotent second uninstall.
  2. Pre-customized profile (existing @charset + @namespace + custom rules in
     chrome/userChrome.css, chrome/userContent.css, chrome/img/dot.bin,
     pre-existing foreign chrome/platinum/ user folder, existing user.js,
     existing prefs.js with prior values & absence):
       a) untouched byte-for-byte undo (including restoring displaced foreign
          chrome/platinum/!)
       b) post-install user edits outside markers in both userChrome.css and
          user.js + new unrelated browsing prefs in prefs.js -> keeps user edits
          and new browsing prefs while removing marker blocks and restoring
          managed prefs' original values/absence.
  3. Conflict & safety guards (never overwrite user changes):
       - edited inside userChrome.css marker block -> refused, file untouched
       - corrupted/unclosed marker in user.js -> refused, file untouched
       - modified file & added user file inside chrome/platinum/ -> refused
       - symlinked userChrome.css, symlink inside chrome/, symlinked state_dir,
         and repointed parent symlink -> refused with zero mutations
  4. Reinstall & Upgrade:
       - reinstall preserves original pre-v1 backup
       - upgrade (M9_FF_MANAGED_PREFS_JSON retiring one pref and adding a new
         pref) immediately restores the retired pref in prefs.js, updates
         user.js, and subsequent uninstall restores byte-for-byte to pre-v1.
  5. Interrupted Install & Interrupted Undo (crash injection at every step):
       - M9_FF_FAULT_AFTER = backup, platinum, userChrome, user_js:
         both immediate uninstall rollback AND install resume -> uninstall
         restore byte-for-byte to pre-install!
       - M9_FF_FAULT_AFTER = uninstall_platinum, uninstall_userChrome,
         uninstall_user_js: install refuses during unfinished uninstall, and
         rerun uninstall completes byte-for-byte without redoing finished steps.
  6. Profile-in-use & concurrency locks:
       - exited loopback PID permits install and undo, while live, remote,
         and unrecognized lock targets are refused
       - active POSIX fcntl.lockf lock on .parentlock -> refused
       - concurrent state flock held -> refused
  7. Two profiles + [Install*] Default= precedence over [Profile*] Default=1:
       - [Install*] Default= ranked [1] (default) ahead of [Profile*] Default=1
       - non-interactive run without --profile refuses cleanly
       - installing into Profile 1 leaves Profile 2 100% untouched
       - installing into both, then uninstalling Profile 1 leaves Profile 2 intact
  8. XDG-only profile (~/.mozilla absent) + untested Firefox major warning gate
     + live Firefox 160.0.1 nested KWin Wayland cold-launch & full undo check!

SPDX-License-Identifier: BSD-2-Clause
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import pathlib
import pty
import select
import runpy
from contextlib import ExitStack
import shutil
import stat
import subprocess
import sys
import time
import tempfile
from typing import Any
from PIL import Image


class Suite:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def check(self, name: str, cond: bool, detail: str = "") -> None:
        if cond:
            self.passed += 1
            print(f"PASS  {name}" + (f" ({detail})" if detail else ""))
        else:
            self.failed += 1
            print(f"FAIL  {name}" + (f" ({detail})" if detail else ""))


def snapshot_tree(root: pathlib.Path) -> dict[str, tuple[str, Any, int]]:
    """Capture complete byte-for-byte + file/dir mode snapshot of a directory tree."""
    snap: dict[str, tuple[str, Any, int]] = {}
    if not root.exists() and not root.is_symlink():
        return snap
    for dirpath, dirnames, filenames in os.walk(str(root), followlinks=False):
        dirnames.sort()
        filenames.sort()
        dp = pathlib.Path(dirpath)
        rel_d = "." if dp == root else str(dp.relative_to(root))
        st_d = dp.lstat()
        snap[rel_d] = ("dir", None, stat.S_IMODE(st_d.st_mode))
        for fn in filenames + [d for d in dirnames if (dp / d).is_symlink()]:
            fp = dp / fn
            rel_f = str(fp.relative_to(root))
            st_f = fp.lstat()
            if stat.S_ISLNK(st_f.st_mode):
                snap[rel_f] = ("link", os.readlink(str(fp)), 0)
            elif stat.S_ISREG(st_f.st_mode):
                snap[rel_f] = ("file", fp.read_bytes(), stat.S_IMODE(st_f.st_mode))
    return snap


def make_env(home: pathlib.Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "XDG_CONFIG_HOME": str(home / ".config"),
        "XDG_DATA_HOME": str(home / ".local/share"),
        "XDG_STATE_HOME": str(home / ".local/state"),
        "XDG_CACHE_HOME": str(home / ".cache"),
        "LC_ALL": "C.UTF-8",
    }
    if extra:
        env.update(extra)
    return env


def run_cmd(
    cmd: list[str],
    home: pathlib.Path,
    extra_env: dict[str, str] | None = None,
    stdin_data: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        env=make_env(home, extra_env),
        input=stdin_data,
        text=True,
        capture_output=True,
    )


def run_pty(
    cmd: list[str],
    home: pathlib.Path,
    reply: str = "\n",
    extra_env: dict[str, str] | None = None,
) -> tuple[int, str]:
    """Run command attached to a genuine pseudo-terminal (isatty(0) == True)."""
    master_fd, slave_fd = pty.openpty()
    proc = subprocess.Popen(
        cmd,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        env=make_env(home, extra_env),
        close_fds=True,
    )
    os.close(slave_fd)
    chunks: list[bytes] = []
    sent = False
    try:
        while True:
            rlist, _, _ = select.select([master_fd], [], [], 0.1)
            if rlist:
                try:
                    data = os.read(master_fd, 4096)
                except OSError:
                    break
                if not data:
                    break
                chunks.append(data)
                combined = b"".join(chunks)
                if not sent and b"Select profile" in combined:
                    os.write(master_fd, reply.encode("utf-8"))
                    sent = True
            elif proc.poll() is not None:
                break
        proc.wait(timeout=10)
    finally:
        os.close(master_fd)
    return (proc.returncode, b"".join(chunks).decode("utf-8", errors="replace"))


def make_xdg_single_profile(home: pathlib.Path, folder: str = "abcd1234.default-release", name: str = "default-release") -> pathlib.Path:
    ff_base = home / ".config/mozilla/firefox"
    prof = ff_base / folder
    prof.mkdir(parents=True)
    (ff_base / "profiles.ini").write_text(
        f"[Install4F96D1932A9F858E]\nDefault={folder}\nLocked=1\n\n"
        f"[Profile0]\nName={name}\nIsRelative=1\nPath={folder}\n\n"
        "[General]\nStartWithLastProfile=1\nVersion=2\n",
        encoding="utf-8",
    )
    return prof


def main() -> int:
    repo = pathlib.Path(sys.argv[1])
    work = pathlib.Path(sys.argv[2])
    install_sh = str(repo / "firefox/install.sh")
    uninstall_sh = str(repo / "firefox/uninstall.sh")

    real_home = pathlib.Path(os.path.expanduser("~"))
    host_before = {
        "dot_mozilla": (real_home / ".mozilla").exists(),
        "ff_state": (real_home / ".local/state/macos9-theme-firefox").exists(),
        "xdg_ini_sha": hashlib.sha256((real_home / ".config/mozilla/firefox/profiles.ini").read_bytes()).hexdigest()
        if (real_home / ".config/mozilla/firefox/profiles.ini").is_file()
        else None,
    }

    s = Suite()

    # =========================================================================
    shortcut_home = work / "root-shortcuts"
    profile = make_xdg_single_profile(shortcut_home, name="Test Profile")
    original = snapshot_tree(profile)
    options = ["--firefox", "--profile", "Test Profile"]
    install = [str(repo / "install.sh"), *options]
    undo = [str(repo / "uninstall.sh"), *options]
    preview = run_cmd([*install, "--dry-run"], shortcut_home)
    s.check("root-firefox-preview", preview.returncode == 0 and snapshot_tree(profile) == original)
    installed = run_cmd(install, shortcut_home)
    s.check("root-firefox-install", installed.returncode == 0 and (profile / "chrome/platinum/platinum.css").is_file())
    removed = run_cmd(undo, shortcut_home)
    s.check("root-firefox-undo", removed.returncode == 0 and snapshot_tree(profile) == original
            and not (shortcut_home / ".local/state/macos9-theme").exists())

    # 1. Fresh profile + unlocked 0-byte .parentlock + dry-run + PTY prompt + undo
    # =========================================================================
    h1 = work / "case1-fresh"
    p1 = make_xdg_single_profile(h1)
    orig_prefs_1 = (
        "// Mozilla User Preferences\n"
        'user_pref("app.normandy.first_run", false);\n'
        'user_pref("browser.startup.page", 3);\n'
    ).encode("utf-8")
    (p1 / "prefs.js").write_bytes(orig_prefs_1)
    os.chmod(p1 / "prefs.js", 0o600)
    # Unlocked 0-byte .parentlock left behind by a cleanly closed Firefox session:
    (p1 / ".parentlock").write_bytes(b"")
    snap1_before = snapshot_tree(p1)

    r_list = run_cmd([install_sh, "--list"], h1)
    s.check("c1-list-shows-default-xdg", r_list.returncode == 0 and "(xdg, default)" in r_list.stdout)

    r_dry = run_cmd([install_sh, "--profile", "1", "--dry-run"], h1)
    s.check(
        "c1-install-dry-run-mutates-nothing",
        r_dry.returncode == 0
        and snapshot_tree(p1) == snap1_before
        and not (h1 / ".local/state/macos9-theme-firefox").exists(),
    )

    rc_pty_i, out_pty_i = run_pty([install_sh], h1, "\n")
    s.check(
        "c1-pty-interactive-install-succeeds",
        rc_pty_i == 0
        and (p1 / "chrome/platinum/platinum.css").is_file()
        and (p1 / "chrome/platinum/content.css").is_file()
        and '@import url("platinum/platinum.css");' in (p1 / "chrome/userChrome.css").read_text(encoding="utf-8")
        and '@import url("platinum/content.css");' in (p1 / "chrome/userContent.css").read_text(encoding="utf-8")
        and 'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);' in (p1 / "user.js").read_text(encoding="utf-8"),
    )

    # Simulate Firefox copying user.js prefs into prefs.js during a session:
    (p1 / "prefs.js").write_bytes(
        orig_prefs_1
        + b'user_pref("browser.tabs.inTitlebar", 0);\n'
        + b'user_pref("browser.toolbars.bookmarks.visibility", "always");\n'
        + b'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);\n'
    )
    os.chmod(p1 / "prefs.js", 0o600)

    snap1_installed = snapshot_tree(p1)
    r_udry = run_cmd([uninstall_sh, "--profile", "1", "--dry-run"], h1)
    s.check("c1-uninstall-dry-run-mutates-nothing", r_udry.returncode == 0 and snapshot_tree(p1) == snap1_installed)

    rc_pty_u, _ = run_pty([uninstall_sh], h1, "\n")
    s.check(
        "c1-fresh-profile-restored-byte-for-byte-and-modes",
        rc_pty_u == 0
        and snapshot_tree(p1) == snap1_before
        and not (p1 / "chrome").exists()
        and not (p1 / "user.js").exists(),
    )

    r_u2 = run_cmd([uninstall_sh], h1)
    s.check("c1-second-uninstall-clean-noop", r_u2.returncode == 0 and "Nothing to remove" in r_u2.stdout)

    # =========================================================================
    # 2. Pre-customized profile (existing userChrome.css, foreign chrome/platinum,
    #    user.js, prefs.js): untouched byte-for-byte undo AND post-install user edits
    # =========================================================================
    def setup_customized_home(name: str) -> tuple[pathlib.Path, pathlib.Path]:
        h = work / name
        p = make_xdg_single_profile(h)
        (p / "chrome/img").mkdir(parents=True)
        (p / "chrome/platinum").mkdir(parents=True)
        (p / "chrome/platinum/my-prior-theme.css").write_bytes(b"/* pre-existing foreign platinum dir */\n")
        (p / "chrome/img/dot.bin").write_bytes(b"\x89PNG\r\n\x1a\n\x00\x01\x02")
        (p / "chrome/userContent.css").write_bytes(b"body { background: #fafafa; }\n")
        # Include UTF-8 @charset + @namespace + custom CSS with custom mode 0640:
        orig_uc = (
            '@charset "UTF-8";\n'
            '@namespace url("http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul");\n'
            "#PersonalToolbar { border-inline: 0; }\n"
        ).encode("utf-8")
        (p / "chrome/userChrome.css").write_bytes(orig_uc)
        os.chmod(p / "chrome/userChrome.css", 0o640)

        # Existing user.js WITHOUT trailing newline:
        (p / "user.js").write_bytes(b'user_pref("privacy.resistFingerprinting", false);')
        os.chmod(p / "user.js", 0o640)

        # Existing prefs.js with inTitlebar=1 (present) and stylesheets (absent):
        (p / "prefs.js").write_bytes(
            b'// Mozilla User Preferences\n'
            b'user_pref("browser.tabs.inTitlebar", 1);\n'
            b'user_pref("general.smoothScroll", true);\n'
        )
        os.chmod(p / "prefs.js", 0o600)
        return h, p

    # 2a. Untouched byte-for-byte restoration (including displaced foreign chrome/platinum!)
    h2a, p2a = setup_customized_home("case2a-custom-untouched")
    snap2a_before = snapshot_tree(p2a)
    r2a_i = run_cmd([install_sh, "--profile", "1"], h2a)
    uc2a_txt = (p2a / "chrome/userChrome.css").read_text(encoding="utf-8")
    ucnt2a_txt = (p2a / "chrome/userContent.css").read_text(encoding="utf-8")
    # Verify @charset stays first, @import comes BEFORE @namespace, and user rules stay after!
    s.check(
        "c2a-charset-first-import-before-namespace-and-user-rules-kept",
        r2a_i.returncode == 0
        and uc2a_txt.startswith('@charset "UTF-8";\n')
        and uc2a_txt.index('@import url("platinum/platinum.css");') < uc2a_txt.index("@namespace")
        and "#PersonalToolbar { border-inline: 0; }" in uc2a_txt
        and '@import url("platinum/content.css");' in ucnt2a_txt
        and ucnt2a_txt.index('@import url("platinum/content.css");') < ucnt2a_txt.index("body { background: #fafafa; }")
        and (p2a / "chrome/img/dot.bin").is_file(),
    )
    # Simulate Firefox applying user.js into prefs.js:
    (p2a / "prefs.js").write_bytes(
        b'// Mozilla User Preferences\n'
        b'user_pref("browser.tabs.inTitlebar", 0);\n'
        b'user_pref("browser.toolbars.bookmarks.visibility", "always");\n'
        b'user_pref("general.smoothScroll", true);\n'
        b'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);\n'
    )
    os.chmod(p2a / "prefs.js", 0o600)
    r2a_u = run_cmd([uninstall_sh, "--profile", "1"], h2a)
    s.check(
        "c2a-customized-profile-and-displaced-platinum-restored-byte-for-byte",
        r2a_u.returncode == 0 and snapshot_tree(p2a) == snap2a_before,
    )

    # 2b. Later user edits outside markers + new unrelated prefs in prefs.js
    h2b, p2b = setup_customized_home("case2b-custom-edited")
    run_cmd([install_sh, "--profile", "1"], h2b)
    with (p2b / "chrome/userChrome.css").open("ab") as f:
        f.write(b"\n/* user post-install tweak */\n#statuspanel { opacity: 0.95; }\n")
    with (p2b / "chrome/userContent.css").open("ab") as f:
        f.write(b"\n/* user content tweak */\na { text-decoration-thickness: 2px; }\n")
    with (p2b / "user.js").open("ab") as f:
        f.write(b'\nuser_pref("my.later.user.pref", 777);\n')
    (p2b / "prefs.js").write_bytes(
        b'// Mozilla User Preferences\n'
        b'user_pref("browser.startup.homepage_override.mstone", "160.0.1");\n'
        b'user_pref("browser.tabs.inTitlebar", 0);\n'
        b'user_pref("browser.toolbars.bookmarks.visibility", "always");\n'
        b'user_pref("general.smoothScroll", true);\n'
        b'user_pref("my.later.user.pref", 777);\n'
        b'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);\n'
    )
    os.chmod(p2b / "prefs.js", 0o600)

    r2b_u = run_cmd([uninstall_sh, "--profile", "1"], h2b)
    uc2b_after = (p2b / "chrome/userChrome.css").read_text(encoding="utf-8")
    ucnt2b_after = (p2b / "chrome/userContent.css").read_text(encoding="utf-8")
    ujs2b_after = (p2b / "user.js").read_text(encoding="utf-8")
    pjs2b_after = (p2b / "prefs.js").read_text(encoding="utf-8")
    s.check(
        "c2b-keeps-later-user-edits-and-restores-managed-prefs-only",
        r2b_u.returncode == 0
        and "macos9-theme-firefox" not in uc2b_after
        and uc2b_after.startswith('@charset "UTF-8";\n@namespace')
        and "#PersonalToolbar { border-inline: 0; }" in uc2b_after
        and "#statuspanel { opacity: 0.95; }" in uc2b_after
        and "macos9-theme-firefox" not in ucnt2b_after
        and "body { background: #fafafa; }" in ucnt2b_after
        and "a { text-decoration-thickness: 2px; }" in ucnt2b_after
        and "macos9-theme-firefox" not in ujs2b_after
        and 'user_pref("privacy.resistFingerprinting", false);' in ujs2b_after
        and 'user_pref("my.later.user.pref", 777);' in ujs2b_after
        and 'user_pref("browser.tabs.inTitlebar", 1);' in pjs2b_after
        and "toolkit.legacyUserProfileCustomizations.stylesheets" not in pjs2b_after
        and "browser.toolbars.bookmarks.visibility" not in pjs2b_after
        and 'user_pref("browser.startup.homepage_override.mstone", "160.0.1");' in pjs2b_after
        and (p2b / "chrome/platinum/my-prior-theme.css").is_file(),
    )

    # =========================================================================
    # 3. Conflict & Symlink Safety Guards (never overwrite user edits)
    # =========================================================================
    h3, p3 = setup_customized_home("case3-conflicts")
    run_cmd([install_sh, "--profile", "1"], h3)

    # 3a. Edit inside userChrome.css marker block
    uc_good = (p3 / "chrome/userChrome.css").read_bytes()
    uc_edited_inside = uc_good.replace(
        b'@import url("platinum/platinum.css");',
        b'@import url("platinum/platinum.css");\n* { color: magenta !important; }',
    )
    (p3 / "chrome/userChrome.css").write_bytes(uc_edited_inside)
    r3_uc = run_cmd([uninstall_sh, "--profile", "1"], h3)
    s.check(
        "c3a-conflict-inside-userchrome-markers-refused-and-preserved",
        r3_uc.returncode == 1 and (p3 / "chrome/userChrome.css").read_bytes() == uc_edited_inside,
    )
    (p3 / "chrome/userChrome.css").write_bytes(uc_good)

    # 3a2. Edit inside userContent.css marker block
    ucnt_good = (p3 / "chrome/userContent.css").read_bytes()
    ucnt_edited_inside = ucnt_good.replace(
        b'@import url("platinum/content.css");',
        b'@import url("platinum/content.css");\nbody { color: lime; }',
    )
    (p3 / "chrome/userContent.css").write_bytes(ucnt_edited_inside)
    r3_ucnt = run_cmd([uninstall_sh, "--profile", "1"], h3)
    s.check(
        "c3a2-conflict-inside-usercontent-markers-refused-and-preserved",
        r3_ucnt.returncode == 1 and (p3 / "chrome/userContent.css").read_bytes() == ucnt_edited_inside,
    )
    (p3 / "chrome/userContent.css").write_bytes(ucnt_good)

    # 3b. Corrupted/unclosed marker in user.js
    ujs_good = (p3 / "user.js").read_bytes()
    ujs_corrupt = ujs_good.replace(b"/* <<< macos9-theme-firefox end <<< */", b"")
    (p3 / "user.js").write_bytes(ujs_corrupt)
    r3_ujs = run_cmd([uninstall_sh, "--profile", "1"], h3)
    s.check(
        "c3b-corrupt-userjs-markers-refused-and-preserved",
        r3_ujs.returncode == 1 and (p3 / "user.js").read_bytes() == ujs_corrupt,
    )
    (p3 / "user.js").write_bytes(ujs_good)

    js_file = p3 / "user.js"
    saved = js_file.read_bytes()
    js_file.write_bytes(b"// replacement preferences\n")
    before = snapshot_tree(p3)
    refused = run_cmd([install_sh, "--profile", "1"], h3)
    s.check("reinstall-refuses-replaced-user-js", refused.returncode == 1 and snapshot_tree(p3) == before)
    js_file.write_bytes(saved)

    # 3c. User added a file inside chrome/platinum/
    extra_css = p3 / "chrome/platinum/user-added.css"
    extra_css.write_bytes(b"/* user file */\n")
    r3_plat_u = run_cmd([uninstall_sh, "--profile", "1"], h3)
    r3_plat_i = run_cmd([install_sh, "--profile", "1"], h3)
    s.check(
        "c3c-modified-platinum-dir-refused-by-uninstall-and-reinstall",
        r3_plat_u.returncode == 1 and r3_plat_i.returncode == 1 and extra_css.is_file(),
    )
    extra_css.unlink()
    r3_ok = run_cmd([uninstall_sh, "--profile", "1"], h3)
    s.check("c3d-uninstall-succeeds-once-conflicts-resolved", r3_ok.returncode == 0)

    # 3e. Symlink safety refusal
    h3s = work / "case3e-symlinks"
    p3s = make_xdg_single_profile(h3s)
    outside_target = work / "outside-secret.js"
    outside_target.write_bytes(b"// outside\n")
    os.symlink(outside_target, p3s / "user.js")
    r3_sym = run_cmd([install_sh, "--profile", "1"], h3s)
    s.check(
        "c3e-refuses-symlinked-userjs-without-touching-target",
        r3_sym.returncode == 1 and outside_target.read_bytes() == b"// outside\n" and not (p3s / "chrome").exists(),
    )

    # =========================================================================
    # 4. Reinstall & Upgrade (adding & retiring managed prefs, preserving backup)
    # =========================================================================
    h4, p4 = setup_customized_home("case4-reinstall-upgrade")
    snap4_before = snapshot_tree(p4)
    r4_1 = run_cmd([install_sh, "--profile", "1"], h4)
    # Reinstall same version:
    r4_2 = run_cmd([install_sh, "--profile", "1"], h4)
    s.check("c4a-reinstall-succeeds", r4_1.returncode == 0 and r4_2.returncode == 0)

    # Simulate Firefox copying v1 prefs into prefs.js:
    (p4 / "prefs.js").write_bytes(
        b'// Mozilla User Preferences\n'
        b'user_pref("browser.tabs.inTitlebar", 0);\n'
        b'user_pref("browser.toolbars.bookmarks.visibility", "always");\n'
        b'user_pref("general.smoothScroll", true);\n'
        b'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);\n'
    )
    os.chmod(p4 / "prefs.js", 0o600)

    # Upgrade to simulated v2: retires bookmarks.visibility and adds layout.css.devPixelsPerPx
    v2_prefs = json.dumps(
        [
            ["toolkit.legacyUserProfileCustomizations.stylesheets", "true"],
            ["browser.tabs.inTitlebar", "0"],
            ["layout.css.devPixelsPerPx", '"-1.0"'],
        ]
    )
    r4_up = run_cmd([install_sh, "--profile", "1"], h4, {"M9_FF_MANAGED_PREFS_JSON": v2_prefs})
    ujs4_v2 = (p4 / "user.js").read_text(encoding="utf-8")
    pjs4_v2 = (p4 / "prefs.js").read_text(encoding="utf-8")
    s.check(
        "c4b-upgrade-retires-old-pref-and-adds-new-pref",
        r4_up.returncode == 0
        and "layout.css.devPixelsPerPx" in ujs4_v2
        and "browser.toolbars.bookmarks.visibility" not in ujs4_v2
        and "browser.toolbars.bookmarks.visibility" not in pjs4_v2,
    )
    # Simulate Firefox applying v2's new pref into prefs.js, then uninstall:
    (p4 / "prefs.js").write_bytes(pjs4_v2.encode("utf-8") + b'user_pref("layout.css.devPixelsPerPx", "-1.0");\n')
    os.chmod(p4 / "prefs.js", 0o600)
    r4_u = run_cmd([uninstall_sh, "--profile", "1"], h4)
    s.check(
        "c4c-uninstall-after-reinstall-and-upgrade-restores-pre-v1-byte-for-byte",
        r4_u.returncode == 0 and snapshot_tree(p4) == snap4_before,
    )

    # 4d. Legacy install (before userContent.css management) upgrades, rolls back mid-upgrade,
    #     and uninstalls cleanly whether or not chrome/userContent.css existed pre-install!
    def simulate_legacy_pre_usercontent(home: pathlib.Path, prof: pathlib.Path, orig_ucnt: bytes | None) -> None:
        state_file = next((home / ".local/state/macos9-theme-firefox/profiles").glob("*/state.json"))
        st = json.loads(state_file.read_text(encoding="utf-8"))
        for k in ("installed_usercontent_block", "installed_usercontent_chunk", "untouched_usercontent_sha256"):
            st.pop(k, None)
        state_file.write_text(json.dumps(st, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        bak_meta_f = state_file.parent / "backup/BACKUP_META.json"
        bm = json.loads(bak_meta_f.read_text(encoding="utf-8"))
        bm["meta"].pop("userContent_existed", None)
        bm["meta"].pop("userContent_mode", None)
        bak_meta_f.write_text(json.dumps(bm, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        ucnt_f = prof / "chrome/userContent.css"
        if orig_ucnt is None:
            if ucnt_f.exists():
                ucnt_f.unlink()
        else:
            ucnt_f.write_bytes(orig_ucnt)

    h4d, p4d = setup_customized_home("case4d-legacy-usercontent-upgrade")
    snap4d_before = snapshot_tree(p4d)
    orig_ucnt_4d = (p4d / "chrome/userContent.css").read_bytes()
    run_cmd([install_sh, "--profile", "1"], h4d)
    simulate_legacy_pre_usercontent(h4d, p4d, orig_ucnt_4d)
    # Interrupted upgrade crashing right before writing userContent.css -> immediate uninstall must roll back cleanly!
    r4d_crash = run_cmd([install_sh, "--profile", "1"], h4d, {"M9_FF_FAULT_AFTER": "userChrome"})
    r4d_rb = run_cmd([uninstall_sh, "--profile", "1"], h4d)
    s.check(
        "c4d-legacy-upgrade-interrupted-before-usercontent-rolls-back-byte-for-byte",
        r4d_crash.returncode == 99 and r4d_rb.returncode == 0 and snapshot_tree(p4d) == snap4d_before,
    )
    # Full legacy upgrade -> installs userContent.css cleanly -> later undo restores byte-for-byte!
    run_cmd([install_sh, "--profile", "1"], h4d)
    simulate_legacy_pre_usercontent(h4d, p4d, orig_ucnt_4d)
    r4d_up = run_cmd([install_sh, "--profile", "1"], h4d)
    has_ucnt_imp = '@import url("platinum/content.css");' in (p4d / "chrome/userContent.css").read_text(encoding="utf-8")
    r4d_u = run_cmd([uninstall_sh, "--profile", "1"], h4d)
    s.check(
        "c4e-legacy-pre-usercontent-upgrade-and-undo-byte-for-byte",
        r4d_up.returncode == 0 and has_ucnt_imp and r4d_u.returncode == 0 and snapshot_tree(p4d) == snap4d_before,
    )
    # Uninstalling a legacy install directly (without upgrading first) leaves unmarked userContent.css alone!
    run_cmd([install_sh, "--profile", "1"], h4d)
    simulate_legacy_pre_usercontent(h4d, p4d, orig_ucnt_4d)
    r4d_direct_u = run_cmd([uninstall_sh, "--profile", "1"], h4d)
    s.check(
        "c4f-legacy-pre-usercontent-direct-uninstall-byte-for-byte",
        r4d_direct_u.returncode == 0 and snapshot_tree(p4d) == snap4d_before,
    )

    # =========================================================================
    for scenario, initial, adopted in (("created", None, b""), ("deleted", b"old", None),
                                       ("edited", b"old", b"/* newer */\r\n")):
        home, profile = setup_customized_home(f"content-adoption-{scenario}")
        css = profile / "chrome/userContent.css"
        if initial is None:
            css.unlink()
        else:
            css.write_bytes(initial)
        run_cmd([install_sh, "--profile", "1"], home)
        simulate_legacy_pre_usercontent(home, profile, adopted)
        if adopted is not None:
            css.chmod(0o600)
        crash = run_cmd([install_sh, "--profile", "1"], home, {"M9_FF_FAULT_AFTER": "userContent"})
        resume = run_cmd([install_sh, "--profile", "1"], home)
        undo = run_cmd([uninstall_sh, "--profile", "1"], home)
        restored = (not css.exists() if adopted is None else
                    css.is_file() and css.read_bytes() == adopted and stat.S_IMODE(css.stat().st_mode) == 0o600)
        s.check(f"content-adoption-{scenario}", crash.returncode == 99 and resume.returncode == undo.returncode == 0 and restored)

    home, profile = setup_customized_home("content-adoption-conflict")
    css = profile / "chrome/userContent.css"
    original = css.read_bytes()
    run_cmd([install_sh, "--profile", "1"], home)
    simulate_legacy_pre_usercontent(home, profile, original)
    crash = run_cmd([install_sh, "--profile", "1"], home, {"M9_FF_FAULT_AFTER": "userContent"})
    css.write_bytes(b"/* replacement after the interruption */")
    before = snapshot_tree(profile)
    retry = run_cmd([install_sh, "--profile", "1"], home)
    s.check("interrupted-adoption-preserves-replacement", crash.returncode == 99
            and retry.returncode == 1 and snapshot_tree(profile) == before)

    hb, pb = setup_customized_home("case-backup-directory-integrity")
    (pb / "chrome/platinum/empty").mkdir()
    run_cmd([install_sh, "--profile", "1"], hb)
    saved = next((hb / ".local/state/macos9-theme-firefox/profiles").glob("*/backup"))
    (saved / "chrome/platinum/empty").rmdir()
    before = snapshot_tree(pb)
    refused = run_cmd([uninstall_sh, "--profile", "1"], hb)
    s.check("damaged-empty-backup-directory-refused", refused.returncode == 1 and snapshot_tree(pb) == before)
    record = saved.parent
    (record / "journal.json").unlink()
    (record / "state.json").unlink()
    # Without the marker checks as a fallback, the orphan backup still survives.
    (pb / "chrome/userChrome.css").unlink()
    (pb / "chrome/userContent.css").unlink()
    (pb / "user.js").unlink()
    before_backup = snapshot_tree(saved)
    refused = run_cmd([install_sh, "--profile", "1"], hb)
    s.check("orphan-backup-preserved", refused.returncode == 1 and snapshot_tree(saved) == before_backup)

    hd = work / "case-duplicate-store-default"
    pa = make_xdg_single_profile(hd, "first", "first")
    (pa.parent / "second").mkdir()
    with (pa.parent / "profiles.ini").open("w") as ini:
        ini.write("[Profile0]\nPath=first\nDefault=1\n[Profile1]\nPath=second\n")
    legacy = hd / ".mozilla/firefox"
    legacy.mkdir(parents=True)
    second = pa.parent / "second"
    (legacy / "profiles.ini").write_text(f"[InstallABC]\nDefault={second}\n[Profile0]\nPath={second}\nIsRelative=0\n")
    listed = run_cmd([install_sh, "--list"], hd)
    s.check("duplicate-profile-retains-install-default", "[1] second (xdg, default)" in listed.stdout)

    installed = run_cmd([install_sh, "--profile", "second"], hd)
    (pa.parent / "profiles.ini").write_bytes(b"[broken")
    undone = run_cmd([uninstall_sh, "--profile", str(second)], hd)
    s.check("undo-works-with-damaged-profile-registry", installed.returncode == 0 and undone.returncode == 0
            and not (second / "user.js").exists())

    for idx, simulated in enumerate((b'', b'user_pref("new.key", false);\n', None)):
        hu = work / f"case-upgrade-snapshot-{idx}"
        pu = make_xdg_single_profile(hu)
        prefs = pu / "prefs.js"
        prefs.write_bytes(b"")
        first = run_cmd([install_sh, "--profile", "1"], hu)
        mine = b'user_pref("new.key", true);\n'
        prefs.write_bytes(mine)
        upgrade = run_cmd([install_sh, "--profile", "1"], hu,
                          {"M9_FF_MANAGED_PREFS_JSON": json.dumps([["new.key", "false"]])})
        if simulated is None:
            prefs.unlink()
        else:
            prefs.write_bytes(simulated)
        undo = run_cmd([uninstall_sh, "--profile", "1"], hu)
        s.check(f"upgrade-restores-value-at-adoption-{hu.name}",
                all(r.returncode == 0 for r in (first, upgrade, undo)) and prefs.read_bytes() == mine)

    # 5. Interrupted Install & Interrupted Undo (Fault Injection at Every Step)
    # =========================================================================
    for fault_step in ("backup", "platinum_swap", "platinum", "userChrome", "userContent", "user_js"):
        # 5a. Interrupted install -> immediate uninstall rolls back byte-for-byte
        hf_a, pf_a = setup_customized_home(f"case5-int-ins-undo-{fault_step}")
        snap_fa = snapshot_tree(pf_a)
        rf_crash = run_cmd([install_sh, "--profile", "1"], hf_a, {"M9_FF_FAULT_AFTER": fault_step})
        rf_rb = run_cmd([uninstall_sh, "--profile", "1"], hf_a)
        s.check(
            f"c5a-interrupted-install-{fault_step}-rollback-byte-for-byte",
            rf_crash.returncode == 99 and rf_rb.returncode == 0 and snapshot_tree(pf_a) == snap_fa,
        )

        # 5b. Interrupted install -> rerun install resumes -> later uninstall restores byte-for-byte
        hf_b, pf_b = setup_customized_home(f"case5-int-ins-resume-{fault_step}")
        snap_fb = snapshot_tree(pf_b)
        run_cmd([install_sh, "--profile", "1"], hf_b, {"M9_FF_FAULT_AFTER": fault_step})
        rf_res = run_cmd([install_sh, "--profile", "1"], hf_b)
        rf_u = run_cmd([uninstall_sh, "--profile", "1"], hf_b)
        s.check(
            f"c5b-interrupted-install-{fault_step}-resume-then-undo-byte-for-byte",
            rf_res.returncode == 0 and rf_u.returncode == 0 and snapshot_tree(pf_b) == snap_fb,
        )

    for u_fault in (
        "uninstall_platinum_swap",
        "uninstall_platinum",
        "userChrome_before_journal",
        "uninstall_userChrome",
        "userContent_before_journal",
        "uninstall_userContent",
        "uninstall_user_js",
        "archived_backup",
    ):
        hu, pu = setup_customized_home(f"case5-int-{u_fault}")
        snap_u = snapshot_tree(pu)
        run_cmd([install_sh, "--profile", "1"], hu)
        ru_crash = run_cmd([uninstall_sh, "--profile", "1"], hu, {"M9_FF_FAULT_AFTER": u_fault})
        # Install MUST refuse while uninstall is unfinished!
        ri_blocked = run_cmd([install_sh, "--profile", "1"], hu)
        ru_resume = run_cmd([uninstall_sh, "--profile", "1"], hu)
        s.check(
            f"c5c-interrupted-{u_fault}-blocks-install-and-resumes-byte-for-byte",
            ru_crash.returncode == 99
            and ri_blocked.returncode == 1
            and ru_resume.returncode == 0
            and snapshot_tree(pu) == snap_u,
        )

    # 5d. Post-crash edit inside user.js markers BEFORE resuming install MUST be caught (#191)
    #     and a profile with no pre-existing prefs.js unlinks empty prefs.js cleanly on undo!
    h5d = work / "case5d-no-prefsjs-and-postcrash-conflict"
    p5d = make_xdg_single_profile(h5d)
    run_cmd([install_sh, "--profile", "1"], h5d, {"M9_FF_FAULT_AFTER": "user_js"})
    ujs5d_orig = (p5d / "user.js").read_bytes()
    (p5d / "user.js").write_bytes(
        ujs5d_orig.replace(b'user_pref("browser.tabs.inTitlebar", 0);', b'user_pref("browser.tabs.inTitlebar", 2);')
    )
    r5d_conflict = run_cmd([install_sh, "--profile", "1"], h5d)
    edited = snapshot_tree(p5d)
    rollback = run_cmd([uninstall_sh, "--profile", "1"], h5d)
    s.check("postcrash-undo-preserves-conflicting-edit", rollback.returncode == 1 and snapshot_tree(p5d) == edited)
    (p5d / "user.js").write_bytes(ujs5d_orig)
    r5d_res = run_cmd([install_sh, "--profile", "1"], h5d)
    # Simulate prefs.js created solely with managed prefs (no other lines) -> unlinked cleanly on undo:
    (p5d / "prefs.js").write_bytes(b'user_pref("browser.tabs.inTitlebar", 0);\n')
    r5d_u = run_cmd([uninstall_sh, "--profile", "1"], h5d)
    s.check(
        "c5d-postcrash-marker-edit-caught-and-empty-new-prefsjs-unlinked",
        r5d_conflict.returncode == 1
        and r5d_res.returncode == 0
        and r5d_u.returncode == 0
        and not (p5d / "prefs.js").exists(),
    )
    # Outside edits and installer-looking filenames belong to the user.
    for fault in (None, "user_js"):
        hb, pb = setup_customized_home(f"case-bytes-{fault}")
        css = pb / "chrome/userChrome.css"
        js = pb / "user.js"
        prefs = pb / "prefs.js"
        keep = pb / ".macos9-ff-tmp.personal"
        keep.write_bytes(b"keep")
        css_original = b"\xef\xbb\xbf/* my rules */\r\n#nav-bar { color: red; }\r\n"
        js_original = b'// my preferences\r\nuser_pref("test.mine", true);'
        prefs_original = b'// mine\r\nuser_pref("test.mine", true);\r\n'
        css.write_bytes(css_original)
        js.write_bytes(js_original)
        prefs.write_bytes(prefs_original)
        installed = run_cmd([install_sh, "--profile", "1"], hb)
        css_edit = b"/* later */\r\n"
        js_edit = b'\r\nuser_pref("test.later", 1);\r\n'
        css.write_bytes(css.read_bytes() + css_edit)
        js.write_bytes(js.read_bytes() + js_edit)
        prefs.write_bytes(prefs_original + js_edit + b'user_pref("browser.tabs.inTitlebar", 0);\n')
        updated = run_cmd([install_sh, "--profile", "1"], hb, {"M9_FF_FAULT_AFTER": fault} if fault else {})
        has_bom = css.read_bytes().startswith(b"\xef\xbb\xbf")
        undone = run_cmd([uninstall_sh, "--profile", "1"], hb)
        s.check(f"profile-bytes-after-reinstall-{fault or 'complete'}",
                installed.returncode == 0 and updated.returncode == (99 if fault else 0)
                and undone.returncode == 0 and has_bom and css.read_bytes() == css_original + css_edit
                and js.read_bytes() == js_original + js_edit and prefs.read_bytes() == prefs_original + js_edit
                and keep.is_file() and keep.read_bytes() == b"keep")

    # Simulate an unedited install made by the earlier LF-normalizing version.
    hl, pl = setup_customized_home("case-legacy-newlines")
    legacy_js = pl / "user.js"
    legacy_original = legacy_js.read_bytes().replace(b"\n", b"\r\n")
    legacy_js.write_bytes(legacy_original)
    run_cmd([install_sh, "--profile", "1"], hl)
    normalized = legacy_js.read_bytes().replace(b"\r\n", b"\n")
    legacy_js.write_bytes(normalized)
    state_file = next((hl / ".local/state/macos9-theme-firefox/profiles").glob("*/state.json"))
    legacy_state = json.loads(state_file.read_text())
    legacy_state["untouched_userjs_sha256"] = hashlib.sha256(normalized).hexdigest()
    state_file.write_text(json.dumps(legacy_state))
    updated = run_cmd([install_sh, "--profile", "1"], hl)
    undone = run_cmd([uninstall_sh, "--profile", "1"], hl)
    s.check("upgrade-of-legacy-install-restores-original-crlf",
            updated.returncode == 0 and undone.returncode == 0 and legacy_js.read_bytes() == legacy_original)

    # A pre-existing Platinum folder can live on a different mount from XDG state.
    if pathlib.Path("/dev/shm").is_dir() and work.stat().st_dev != os.stat("/dev/shm").st_dev:
        hx, px = setup_customized_home("case-separate-state-filesystem")
        before = snapshot_tree(px)
        with tempfile.TemporaryDirectory(dir="/dev/shm") as state_home:
            env = {"XDG_STATE_HOME": state_home}
            installed = run_cmd([install_sh, "--profile", "1"], hx, env)
            undone = run_cmd([uninstall_sh, "--profile", "1"], hx, env)
            s.check("separate-filesystems-restore-original-theme", installed.returncode == 0
                    and undone.returncode == 0 and snapshot_tree(px) == before)

    htypes, ptypes = setup_customized_home("case-invalid-managed-type")
    (ptypes / "user.js").unlink()
    (ptypes / "user.js").mkdir()
    original = snapshot_tree(ptypes)
    refused = run_cmd([install_sh, "--profile", "1"], htypes)
    s.check("directory-at-user-js-refused-before-writing",
            refused.returncode == 1 and snapshot_tree(ptypes) == original)

    h6 = work / "case6-locks"
    p6 = make_xdg_single_profile(h6)
    snap6 = snapshot_tree(p6)

    # Use a reaped child to obtain a dead PID in Firefox's loopback format.
    exited = subprocess.Popen([sys.executable, "-I", "-c", "pass"])
    exited.wait(timeout=5)
    lock = p6 / "lock"
    stale_target = f"127.0.1.1:+{exited.pid}"
    lock.symlink_to(stale_target)
    before = snapshot_tree(p6)
    refused = run_cmd([install_sh, "--profile", "1"], h6)
    s.check("stale-link-needs-advisory-lock-file", refused.returncode == 1 and snapshot_tree(p6) == before)
    plock6 = p6 / ".parentlock"
    os.mkfifo(plock6)
    refused = run_cmd([install_sh, "--profile", "1"], h6)
    s.check("stale-link-rejects-fifo", refused.returncode == 1 and not (p6 / "chrome").exists())
    plock6.unlink()
    plock6.touch()
    installed = run_cmd([install_sh, "--profile", "1"], h6)
    removed = run_cmd([uninstall_sh, "--profile", "1"], h6)
    s.check("c6a-stale-loopback-lock-allows-install-and-undo",
            installed.returncode == removed.returncode == 0 and os.readlink(lock) == stale_target)
    lock.unlink()
    plock6.unlink()
    s.check("c6a-stale-loopback-profile-restored", snapshot_tree(p6) == snap6)

    for target in (f"127.0.1.1:+{os.getpid()}", f"192.0.2.1:+{exited.pid}", "unrecognized"):
        lock.symlink_to(target)
        before = snapshot_tree(p6)
        refused = run_cmd([install_sh, "--profile", "1"], h6)
        s.check(f"c6a-blocks-lock-{target}", refused.returncode == 1 and snapshot_tree(p6) == before)
        lock.unlink()

    # 6b. Separate child process holding POSIX fcntl.lockf(LOCK_EX) on .parentlock
    plock6 = p6 / ".parentlock"
    plock6.write_bytes(b"")
    holder = subprocess.Popen(
        [
            sys.executable,
            "-I",
            "-c",
            "import fcntl, sys, time; f=open(sys.argv[1],'r+b'); "
            "fcntl.lockf(f.fileno(), fcntl.LOCK_EX|fcntl.LOCK_NB); "
            "sys.stdout.write('LOCKED\\n'); sys.stdout.flush(); time.sleep(30)",
            str(plock6),
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert holder.stdout is not None
        assert holder.stdout.readline().strip() == "LOCKED"
        lock.symlink_to(stale_target)
        r6_fcntl = run_cmd([install_sh, "--profile", "1"], h6)
        lock.unlink()
    finally:
        holder.terminate()
        holder.wait(timeout=5)
    s.check("c6b-refuses-live-fcntl-locked-parentlock", r6_fcntl.returncode == 1 and not (p6 / "chrome").exists())

    # A second process must see contention throughout the command's scope.
    hold = runpy.run_path(str(repo / "firefox/profile_ops.py"))["hold_profile_lock"]
    probe = """import fcntl, sys
with open(sys.argv[1], "r+b") as lockfile:
    try:
        getattr(fcntl, sys.argv[2])(lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.exit(3)
"""
    def probe_locks():
        return [subprocess.run([sys.executable, "-I", "-c", probe, str(plock6), method]).returncode
                for method in ("lockf", "flock")]

    with ExitStack() as handles:
        s.check("profile-locks-held-during-command", hold(p6, "test", handles) and probe_locks() == [3, 3])
    s.check("profile-locks-released-after-command", probe_locks() == [0, 0])

    # 6c. Concurrent state flock held
    st_lock = h6 / ".local/state/macos9-theme-firefox/lock"
    st_lock.parent.mkdir(parents=True, exist_ok=True)
    lfd = os.open(str(st_lock), os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(lfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        r6_flock = run_cmd([install_sh, "--profile", "1"], h6)
    finally:
        fcntl.flock(lfd, fcntl.LOCK_UN)
        os.close(lfd)
    s.check("c6c-refuses-concurrent-state-flock", r6_flock.returncode == 1 and "another" in r6_flock.stderr)
    st_lock.unlink()
    st_lock.symlink_to(outside_target)
    refused = run_cmd([install_sh, "--profile", "1"], h6)
    s.check("refuse-symlinked-state-lock", refused.returncode == 1 and outside_target.read_bytes() == b"// outside\n")
    st_lock.unlink()

    # =========================================================================
    # 7. Two Profiles + [Install*] Default= Precedence over [Profile*] Default=1
    # =========================================================================
    h7 = work / "case7-two-profiles"
    xdg_ff7 = h7 / ".config/mozilla/firefox"
    leg_ff7 = h7 / ".mozilla/firefox"
    prof_leg_def = xdg_ff7 / "1111aaaa.default"
    prof_inst_def = xdg_ff7 / "2222bbbb.default-release"
    prof_dotmoz = leg_ff7 / "3333cccc.old"
    for p in (prof_leg_def, prof_inst_def, prof_dotmoz):
        p.mkdir(parents=True)
        (p / "prefs.js").write_bytes(b'// prefs\n')

    # Mirror the exact CachyOS host profiles.ini layout: [Profile0] has Default=1,
    # while [Install4F96D1932A9F858E] points Default= to 2222bbbb.default-release!
    (xdg_ff7 / "profiles.ini").write_text(
        "[Install4F96D1932A9F858E]\nDefault=2222bbbb.default-release\nLocked=1\n\n"
        "[Profile0]\nName=default\nIsRelative=1\nPath=1111aaaa.default\nDefault=1\n\n"
        "[Profile1]\nName=default-release\nIsRelative=1\nPath=2222bbbb.default-release\n\n",
        encoding="utf-8",
    )
    (leg_ff7 / "profiles.ini").write_text(
        "[Profile0]\nName=old-legacy\nIsRelative=1\nPath=3333cccc.old\nDefault=1\n",
        encoding="utf-8",
    )

    snap_leg_def = snapshot_tree(prof_leg_def)
    snap_inst_def = snapshot_tree(prof_inst_def)
    snap_dotmoz = snapshot_tree(prof_dotmoz)

    r7_list = run_cmd([install_sh, "--list"], h7)
    lines7 = [ln.strip() for ln in r7_list.stdout.splitlines() if ln.strip().startswith("[")]
    s.check(
        "c7a-install-section-default-outranks-profile-default1-and-legacy",
        len(lines7) == 3
        and lines7[0].startswith("[1] default-release (xdg, default)")
        and "2222bbbb.default-release" in lines7[0],
        lines7[0] if lines7 else "no lines",
    )

    # Non-interactive without --profile MUST refuse without touching any profile!
    r7_nonint = run_cmd([install_sh], h7, stdin_data="")
    s.check(
        "c7b-noninteractive-without-profile-refuses-cleanly",
        r7_nonint.returncode == 1
        and snapshot_tree(prof_leg_def) == snap_leg_def
        and snapshot_tree(prof_inst_def) == snap_inst_def
        and snapshot_tree(prof_dotmoz) == snap_dotmoz,
    )

    # Install into [1] (default-release) only; verify the other two profiles are 100% untouched!
    r7_i1 = run_cmd([install_sh, "--profile", "1"], h7)
    s.check(
        "c7c-install-touches-only-chosen-profile",
        r7_i1.returncode == 0
        and (prof_inst_def / "chrome/platinum/platinum.css").is_file()
        and snapshot_tree(prof_leg_def) == snap_leg_def
        and snapshot_tree(prof_dotmoz) == snap_dotmoz,
    )

    # Also install into old-legacy, then verify non-interactive uninstall without --profile refuses,
    # and uninstalling [1] leaves old-legacy's install completely intact!
    run_cmd([install_sh, "--profile", "old-legacy"], h7)
    r7_unon = run_cmd([uninstall_sh], h7, stdin_data="")
    r7_u1 = run_cmd([uninstall_sh, "--profile", "default-release"], h7)
    s.check(
        "c7d-uninstall-touches-only-chosen-profile",
        r7_unon.returncode == 1
        and r7_u1.returncode == 0
        and snapshot_tree(prof_inst_def) == snap_inst_def
        and (prof_dotmoz / "chrome/platinum/platinum.css").is_file(),
    )
    r7_u2 = run_cmd([uninstall_sh, "--profile", "old-legacy"], h7)
    s.check("c7e-second-profile-uninstalled-byte-for-byte", r7_u2.returncode == 0 and snapshot_tree(prof_dotmoz) == snap_dotmoz)

    # =========================================================================
    # 8. XDG-Only Profile (~/.mozilla absent) + Untested Version Warning Gate
    #    + Live Firefox 160.0.1 Nested Wayland Cold-Launch & Undo Smoke Check!
    # =========================================================================
    h8 = work / "case8-xdg-live"
    p8 = make_xdg_single_profile(h8, "xdgonly.default-release", "default-release")
    # Seed p8 with offline test settings so live Firefox never touches network:
    page8 = work / "live-m6.html"
    page8.write_text(
        "<!doctype html><meta charset=utf-8><title>Milestone 6 Installed Profile</title>"
        "<style>html,body{background:#fff;color:#000;min-height:2400px;margin:24px;}</style>"
        "<h1>M6 Installed</h1>\n",
        encoding="utf-8",
    )
    (p8 / "prefs.js").write_text(
        'user_pref("widget.non-native-theme.scrollbar.size.override", 21);\n'
        'user_pref("widget.gtk.theme-scrollbar-colors.enabled", false);\n'
        'user_pref("browser.shell.checkDefaultBrowser", false);\n'
        'user_pref("browser.tabs.inTitlebar", 1);\n'
        'user_pref("datareporting.policy.dataSubmissionPolicyBypassNotification", true);\n'
        'user_pref("browser.aboutwelcome.enabled", false);\n'
        'user_pref("browser.startup.homepage_override.mstone", "ignore");\n'
        'user_pref("network.proxy.type", 1);\n'
        'user_pref("network.proxy.http", "127.0.0.1");\n'
        'user_pref("network.proxy.http_port", 9);\n'
        'user_pref("network.proxy.ssl", "127.0.0.1");\n'
        'user_pref("network.proxy.ssl_port", 9);\n',
        encoding="utf-8",
    )
    os.chmod(p8 / "prefs.js", 0o600)

    fake_ini = work / "fake-app-999.ini"
    fake_ini.write_text("[App]\nVersion=999.0.1\n", encoding="utf-8")
    r8_i = run_cmd([install_sh, "--profile", "default-release"], h8, {"M9_FIREFOX_APP_INI": str(fake_ini)})
    s.check(
        "c8a-xdg-only-profile-and-untested-version-warning",
        r8_i.returncode == 0
        and "outside tested major range" in r8_i.stderr
        and not (h8 / ".mozilla").exists()
        and (p8 / "chrome/platinum/platinum.css").is_file(),
    )

    # Capture this run in its own evidence directory so a stale screenshot
    # cannot satisfy the installed-profile smoke check.
    shot8 = work / "installed-live.png"
    live_sh = work / "run-live-p8.sh"
    sess_sh = work / "sess-p8.sh"
    sess_sh.write_text(
        f"""#!/bin/bash
set -euo pipefail
dbus-update-activation-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP QT_QPA_PLATFORM >/dev/null 2>&1 || true
gsettings set org.gnome.desktop.interface gtk-theme Platinum >/dev/null 2>&1 || true
gsettings set org.gnome.desktop.interface color-scheme 'default' >/dev/null 2>&1 || true
env MOZ_ENABLE_WAYLAND=1 MOZ_NO_REMOTE=1 MOZ_CRASHREPORTER_DISABLE=1 \\
  firefox --no-remote --profile {str(p8)!r} --width 1120 --height 760 {page8.as_uri()!r} >"{str(work / 'ff.log')}" 2>&1 &
ff_pid=$!
sleep 5
spectacle -b -n -f -o {str(shot8)!r}
sleep 0.3
kill -TERM "$ff_pid" 2>/dev/null || true
wait "$ff_pid" 2>/dev/null || true
for _ in $(seq 1 30); do
  grep -q 'toolkit.legacyUserProfileCustomizations.stylesheets' {str(p8 / 'prefs.js')!r} 2>/dev/null && break
  sleep 0.2
done
sleep 0.4
echo "done" > {str(work / 'live-complete')!r}
""",
        encoding="utf-8",
    )
    os.chmod(sess_sh, 0o755)
    live_sh.write_text(
        f"""#!/bin/bash
set -euo pipefail
rt=$(mktemp -d /tmp/m9-ffm6-rt.XXXXXX)
chmod 700 "$rt"
trap 'fusermount3 -uz "$rt/doc" 2>/dev/null || true; rm -rf --one-file-system "$rt" 2>/dev/null || true' EXIT
mkdir -p "{h8}/.config/gtk-3.0" "{h8}/.local/share/themes" "{h8}/.local/state" "{h8}/.cache"
cp "{repo}/colors/Platinum.colors" "{h8}/.config/kdeglobals"
if [[ -d "{repo}/gtk/Platinum" ]]; then
  cp -R "{repo}/gtk/Platinum" "{h8}/.local/share/themes/Platinum"
fi
cat > "{h8}/.config/gtk-3.0/settings.ini" <<'GTK'
[Settings]
gtk-theme-name=Platinum
gtk-application-prefer-dark-theme=0
GTK
cat > "{h8}/.config/kwinrc" <<'KWIN'
[org.kde.kdecoration2]
library=platinum
theme=
ButtonsOnLeft=X
ButtonsOnRight=AI
KWIN
env -i \\
  PATH="/usr/local/bin:/usr/bin:/bin" \\
  HOME={str(h8)!r} \\
  USER="${{USER:-$(id -un)}}" \\
  LANG=C.UTF-8 \\
  XDG_CONFIG_HOME={str(h8 / '.config')!r} \\
  XDG_DATA_HOME={str(h8 / '.local/share')!r} \\
  XDG_STATE_HOME={str(h8 / '.local/state')!r} \\
  XDG_CACHE_HOME={str(h8 / '.cache')!r} \\
  XDG_CONFIG_DIRS=/etc/xdg \\
  XDG_DATA_DIRS=/usr/local/share:/usr/share \\
  XDG_RUNTIME_DIR="$rt" \\
  XDG_CURRENT_DESKTOP=KDE \\
  XDG_SESSION_TYPE=wayland \\
  KDE_FULL_SESSION=true \\
  KDE_SESSION_VERSION=6 \\
  QT_QPA_PLATFORM=wayland \\
  QT_QPA_PLATFORMTHEME=kde \\
  QT_STYLE_OVERRIDE=Platinum \\
  QT_PLUGIN_PATH="{repo}/style/build/plugins:{repo}/decoration/build/plugins" \\
  GDK_BACKEND=wayland \\
  timeout 90 dbus-run-session -- \\
  kwin_wayland --virtual --width 1280 --height 900 \\
  --no-lockscreen --no-global-shortcuts --no-kactivities \\
  --socket m9ffm6 --exit-with-session {str(sess_sh)!r} >"{str(work / 'kwin.log')}" 2>&1
""",
        encoding="utf-8",
    )
    os.chmod(live_sh, 0o755)
    r8_live = subprocess.run([str(live_sh)], capture_output=True, text=True)
    lav_px = 0
    lav_scroll_px = 0
    if shot8.is_file():
        im8 = Image.open(shot8).convert("RGB")
        raw8 = im8.tobytes()
        lav_px = sum(1 for i in range(0, len(raw8), 3) if raw8[i] == 0x1B and raw8[i + 1] == 0x1B and raw8[i + 2] == 0x52)
        # Check for #9999FF Lavender scrollbar thumb pixels inside the viewport band (y >= 220)
        w8, h8_img = im8.size
        crop_vp = im8.crop((w8 // 2, 220, w8, h8_img)).tobytes()
        lav_scroll_px = sum(1 for i in range(0, len(crop_vp), 3) if crop_vp[i] == 0x99 and crop_vp[i + 1] == 0x99 and crop_vp[i + 2] == 0xFF)

    if r8_live.returncode == 0 and shot8.is_file():
        shutil.copy2(shot8, repo / "dev/shots/firefox-m6-installed-live.png")

    pjs8_during = (p8 / "prefs.js").read_text(encoding="utf-8", errors="replace")
    s.check(
        "c8b-real-firefox-loads-installed-profile-and-renders-lavender-band",
        r8_live.returncode == 0 and (work / "live-complete").is_file()
        and shot8.is_file()
        and lav_px > 1000
        and lav_scroll_px > 500
        and 'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);' in pjs8_during,
        f"rc={r8_live.returncode} #1B1B52_px={lav_px} #9999FF_scroll_px={lav_scroll_px}",
    )

    user8 = (p8 / "user.js").read_text(encoding="utf-8")
    scroll_prefs = {
        "browser.theme.dark-private-windows": "false",
        "widget.gtk.overlay-scrollbars.enabled": "false",
        "widget.non-native-theme.scrollbar.style": "4",
        "widget.non-native-theme.scrollbar.size.override": "16",
        "widget.gtk.theme-scrollbar-colors.enabled": "true",
    }
    s.check("c8-scrollbar-and-private-prefs-applied", all(
        f'user_pref("{key}", {value});' in user8 for key, value in scroll_prefs.items()
    ) and all(f'user_pref("{key}", {value});' in pjs8_during for key, value in scroll_prefs.items()
              if key != "widget.gtk.theme-scrollbar-colors.enabled")
      and 'user_pref("widget.gtk.theme-scrollbar-colors.enabled", false);' not in pjs8_during)

    # Now run real firefox/uninstall.sh on p8 AFTER real Firefox closed!
    r8_u = run_cmd([uninstall_sh, "--profile", "default-release"], h8)
    pjs8_after = (p8 / "prefs.js").read_text(encoding="utf-8", errors="replace")
    s.check(
        "c8c-real-firefox-profile-cleanly-uninstalled-and-prefs-restored",
        r8_u.returncode == 0
        and not (p8 / "chrome").exists()
        and not (p8 / "user.js").exists()
        and not (h8 / ".mozilla").exists()
        and 'user_pref("browser.tabs.inTitlebar", 1);' in pjs8_after
        and "toolkit.legacyUserProfileCustomizations.stylesheets" not in pjs8_after
        and "browser.toolbars.bookmarks.visibility" not in pjs8_after
        and "browser.theme.dark-private-windows" not in pjs8_after
        and "widget.gtk.overlay-scrollbars.enabled" not in pjs8_after
        and "widget.non-native-theme.scrollbar.style" not in pjs8_after
        and 'user_pref("widget.non-native-theme.scrollbar.size.override", 21);' in pjs8_after
        and 'user_pref("widget.gtk.theme-scrollbar-colors.enabled", false);' in pjs8_after,
    )

    # =========================================================================
    # 9. Verify Host Home Untouched
    # =========================================================================
    host_after = {
        "dot_mozilla": (real_home / ".mozilla").exists(),
        "ff_state": (real_home / ".local/state/macos9-theme-firefox").exists(),
        "xdg_ini_sha": hashlib.sha256((real_home / ".config/mozilla/firefox/profiles.ini").read_bytes()).hexdigest()
        if (real_home / ".config/mozilla/firefox/profiles.ini").is_file()
        else None,
    }
    s.check("c9-host-home-and-firefox-profiles-untouched", host_before == host_after, str(host_after))

    total = s.passed + s.failed
    print(f"\nFirefox Milestone 6 summary: {s.passed}/{total} passed, {s.failed} failed")
    return 0 if s.failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
