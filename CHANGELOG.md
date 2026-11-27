# macos9-theme: changelog

Newest first. Format and rules: AGENTS.md "CHANGELOG entries".

## 2026-11-27, Codex (GPT-6) — fix Big Sur installer findings #334–#336

- Preserve the current mute setting on full uninstall and retry. Reuse an already installed release offline after verifying it. Fall back to the pinned release if the optional clone contains an unreadable file.
- Added regressions in `dev/test-install.sh`. All 63 sound-focused checks passed. The full installer and nested Plasma suites were skipped. Changes are uncommitted and the live desktop was untouched.

## 2026-11-27, Codex (GPT-6) — audit Claude's Big Sur installer follow-up

- Reviewed the three local commits through `51172cc`. The sound-only installer scenarios passed 49/49. Three additional probes reproduced #334–#336 covering a mute choice reset on uninstall, a needless download for an already installed pack, and blocked fallback from an unreadable local clone.
- The audit and plan updates are uncommitted. Implementation, live desktop settings and private reference files were untouched. The full installer suite and nested Plasma were outside the audit.

## 2026-11-27, Claude Code (Opus 5.5) — fix the Big Sur sound audit findings

- Fixed #327–#332 (AUDIT.md) in the uncommitted sound-theme work. `scripts/sound_theme.py`: `check-installed` compares an existing `sounds/bigsur` with the pinned tree digest; an upstream clone that isn't 1.0.2 is skipped and the release is downloaded instead; a restored `Theme[$d]` goes inside the existing `[Sounds]` group; `M9_SOUND_URL` (tests only). `install.sh`: that folder check now runs in preflight (dry runs too, before any download) and again under the lock; `diff` is no longer needed. `scripts/common.sh`: `check_sound_theme_dir` and `sound_theme_root` (`M9_SOUND_ROOT`, tests only). `dev/test-install.sh`: 50 sound checks; the first scenario downloads the release from GitHub through the installer, as users get it (user's request), so the suite needs network for that check.
- `dev/test-install.sh` all 926 passed. Not run: `dev/test-install-live.sh`. #333 (pre-existing live-suite systemd assertion) recorded as open.
- The user moved `reference/sounds` out of their local reference checkout with `git sparse-checkout` (still in the private repo as the backup). Local installs now use the upstream clone in `build/upstreams/`, or download.
- Everything is still uncommitted, Codex's sound work included.

## 2026-11-27, Claude Code (Opus 5.5) — reword the legal rule for opt-in fetches

- The user clarified that the "no Apple files" rule was about keeping genuine Apple material out of this public repo. `AGENTS.md` "Legal rules" now says that plainly and allows opt-in installer fetches of third-party packs for personal use (off by default, pinned with a checksum, kept out of git, source and terms named in the README). `PLAN.md` decision 16 records the optional Big Sur sounds; the "Can't ship Apple sounds" open question is removed.
- Read-only audit of Codex's sound-theme working tree (below): no breaking bugs. Small items not yet in `AUDIT.md`: no sound cases in `dev/test-install.sh`; dry run skips the "sounds folder differs" check; that check runs after the recovery steps; a changed upstream clone blocks install instead of downloading; restoring a deleted key can add a second `[Sounds]` heading; Codex's AUDIT section sits above the #325/#326 review paragraph. Docs only; nothing committed.
- The user has listened to the Big Sur sounds on their own desktop, so Codex's "live desktop listening is pending" below is done.

## 2026-11-27, Codex (GPT-6) — add optional Big Sur system sounds

- `install.sh --apply --sound-theme` installs and selects the pinned Big Sur 1.0.2 pack. It checks the private release archive, the checkout cache and the upstream clone before fetching. Dry runs preview the source and settings changes. Uninstall restores the previous selection while preserving any later choice and uses the install record to clean up the audio it installed.
- The upstream clone is in the ignored `build/upstreams/` tree. The original release archive and provenance are in the private reference repository at `7e67a98`, confirmed on its remote. The public checkout has only uncommitted installer and documentation changes for this feature.
- Sound and uninstall checks passed in disposable homes. The full installer run and focused replay covered all installer checks. The nested suite reproduced an existing assertion failure for a read-only systemd query. Live desktop listening is pending.

## 2026-11-27, Claude Code (Opus 5.5) — record the user's review of the global menu

- The user installed the full-fallback build (`2ad16cc` and later), ran `--apply --apple-menu-icon` on their desktop and reported "everything looks great". PLAN status and step 6 mark the global menu plan complete. The icon record showed the test icon the user had set just before applying, as intended. No code changes.

## 2026-11-26, Claude Code (Opus 5.5) — commit and push the evening's work

- At the user's request, everything the entries below call uncommitted is now committed and pushed: `2ad16cc` (full seven-menu fallback, #323 Dolphin dispatch, #319 test count and notices), `f9f8636` (#322 private bus for the load check), `b071283` (opt-in `--apple-menu-icon` with Codex's #325/#326 fixes and tests), and the docs commit with this entry (PLAN, AUDIT, CHANGELOG). Reviewed Codex's #325/#326 fixes before committing (AUDIT).

## 2026-11-26, Codex (GPT-6) — fix Apple-menu icon lookup and undo

- #325 requires an exact match from KDE's active icon theme. #326 preserves the saved Kicker icon and install record when uninstall needs Plasma to finish. Added both regressions to the offscreen installer suite.
- Nested Plasma verified the Breeze skip, the rendered WhiteSur icon, the stopped-shell failure and successful retry, and the full config restore. The focused offscreen installer run passed 15/15. Changes are uncommitted. Desktop review is pending.

## 2026-11-26, Codex (GPT-6) — audit the full fallback follow-up and Apple-menu icon

- Verified #323 under nested Wayland with Dolphin already open and with a separate default directory handler. The seven fallback headings were visible, the Release suite passed 9/9, and the #322 smoke probe left no processes with its temporary HOME.
- Reproduced #325 and #326 in nested Plasma with prebuilt packages. The Apple-menu option reports success with Breeze while showing a generic folder, and an in-place uninstall with the shell stopped deletes the record of the previous icon. Live-shell in-place undo and full config restore both passed. Audit and status notes are uncommitted. Full installer suites and desktop review are pending.

## 2026-11-26, Claude Code (Opus 5.5) — fix #323, add the opt-in Apple-menu icon

- #323 (Codex's finding on my fallback restore): Go's folder locations open in a new Dolphin window when Dolphin is the default file manager, otherwise the default handler as upstream. New unit test; 9/9 applet tests. Nested Wayland check still to do.
- New `install.sh --apply --apple-menu-icon` (user's request): sets `folder-apple` from the icon theme on the top bar's single Kicker through Plasma's scripting API; `uninstall.sh` puts the previous icon back after an in-place install. Default stays neutral. README section, PLAN decision 6 note, help text, one offscreen test. Mock-tested; not yet run against a real Plasma. Uncommitted.

## 2026-11-26, Codex (GPT-6) — correct the full fallback plan and test notice

Restored the dated notice in the menu transition test and updated PLAN step 2 to describe the seven-menu fallback and default file-manager dispatch (#324). The Dolphin activation finding (#323) is still open. Changes are uncommitted.

## 2026-11-26, Claude Code (Opus 5.5) — note two later items

- PLAN "Open questions": recorded the user's call that a fake window shade isn't worth the time, and the idea of getting Platinum Global Menu from a single `--apply` (a pending-swap marker the login helper acts on at the next login). Both for later; nothing implemented. Uncommitted.
- The user's first real `install.sh` worked but ended with an `rm` error. Cause, #322 (P2, open): the menu's load probe leaves `xdg-desktop-portal-kde`, `kactivitymanagerd` and `ksecretd` running on every install. Stopped the five leaked probe daemons on the user's machine (theirs untouched) and removed the leftover temp folder. Reproduced and verified a fix (a bus config with no service directories) in the scratchpad.
- Fixed #322 at the user's request: new `plasma/probe-bus.conf` and `install.sh` passes it to the load check's `dbus-run-session`. Probe checked twice (passes, nothing left running, folder deletes) and a broken plugin still fails it. Full real-build install and the nested suite not run; a leftover-process assertion in the live tests is still to add. Uncommitted.
- The user's live `--apply` swapped in Platinum Global Menu (mode `reset`, so #321's fix applied). Seeing File + Go, the user asked for upstream's full seven-menu fallback: reverted `fd0c924` and `e737850` in the working tree, adjusted the #319 test's row count to 7, 9/9 tests pass. PLAN decision 6 and step 2 updated. Needs `install.sh` to reach the desktop; upstream's Go may hit the Dolphin-in-background issue `e737850` had fixed. Uncommitted.

## 2026-11-26, Codex (GPT-6) — complete the global menu implementation and sandbox review

- Independently verified Claude's #321 fix and committed it as `486264a`. The nested upgrade from a legacy full-layout backup restored the user's original panels and widget settings.
- Added runtime fingerprints, login recovery to the stock menu, and a read-only upstream update checker in `69f6555`. Verified recovery and reactivation after a simulated LibPlasma change. All 870 offscreen installer checks, 87 nested installer checks, and nine Release applet tests passed.
- Verified menu switching, fitted titles, and all seven File and Go actions at 100% and 150% on two nested displays. Confirmed the fallback and Dolphin export also worked with Breeze. User on-screen review is pending. [Plan](PLAN.md#plan-bundled-global-menu)

## 2026-11-26, Claude Code (Opus 5.5) — review Platinum Global Menu steps 3–4

- Reviewed Codex's `98311fe` and `f02cb7d`. Opened #321 (P2): an install upgraded from a version before the menu marker records an in-place swap, so uninstall keeps the Platinum panels instead of restoring the original ones. Install test run stopped early at the user's request.
- Fixed #321 at the user's request: `scripts/global-menu.sh` gains `backup_lnf` and `first_swap_layout_mode`, so the first in-place swap is recorded as `reset` when the config backup predates Platinum, and uninstall restores the original panels. New `dev/test-install.sh` scenario for it. Function checked on fixture backups; the full suites were not run (next: `dev/test-install.sh` and `dev/test-install-live.sh`). The user confirmed commits are allowed for the whole global menu plan. Committed locally as `486264a`.

## 2026-11-26, Claude Code (Opus 5.5) — plan About This Computer

- The user chose the Control Strip and an About This Computer app over a fake Wayland window shade (KWin removed shading in 2025). Wrote `docs/ABOUT-THIS-COMPUTER-PLAN.md` from `reference/dialog-about-this-computer.png` with the user's two decisions: a distro-agnostic banner (logo and name from os-release) and memory bars as each app's share of RAM. Covers the field mapping, logo fallbacks, per-app grouping by systemd cgroups with PSS (and a non-systemd fallback), the system row, install, tests and order of work.
- Design only, no claim taken, PLAN.md untouched while Codex held `plasma` for global menu steps 3–4; a PLAN entry and Claims row come when work starts. Committed and pushed with the Tux files at the user's request. Open for the user: executable and desktop file names, banner font.
- The user then switched the banner logo to a regular bundled Tux (every distro runs the Linux kernel); the distro name stays. The plan drops the os-release logo lookup and records Tux's credit terms (Larry Ewing and The GIMP).
- Downloaded Larry Ewing's original Tux (`sit3-shine.7.gif`, 327×360, 15,811 bytes) at the user's request into `apps/about-this-computer/tux/` with `CREDITS.md` (source, SHA-256, his permission text). His page at isc.tamu.edu is gone, so it came from the Internet Archive's copy. README credit not added yet.

## 2026-11-26, Codex (GPT-6) — integrate Platinum Global Menu into install and undo

- Steps 3–4 are in `98311fe`. The installer configures and stages the applet before publishing it and its French catalog in user scope. It checks linked libraries and loads the staged applet offscreen. The README documents first-login discovery and the new build requirements (#318).
- A new layout uses the stock menu until the running shell discovers the applet. Applying while Platinum is active can migrate a customized panel in place. The saved applet ID, position and settings are preserved. Uninstall honors later moves or removal and restores original layouts from a full backup.
- Nested install and undo passed 74/74, including a restart failure and the fix for a leaked installer lock (#320). The full offscreen installer suite passed 862/862 in a test snapshot, and Plasma artwork passed 19/19. Production build, failed-build preservation, and the removed-menu and pre-existing-applet restore cases passed in disposable homes. Desktop review and the step-5 compatibility checks are pending. [Bundled global menu plan](PLAN.md#plan-bundled-global-menu)

## 2026-11-26, Codex (GPT-6) — align the global menu QML change notice

Moved the dated change notice in `plasma/globalmenu/src/qml/main.qml` below the license block. Verified that moving the notice accounts for the entire QML diff. Committed and pushed at the user's request.

## 2026-11-26, Claude Code (Opus 5.5) — review Platinum Global Menu steps 1–2

- Reviewed Codex's six local commits (`55e2523`–`e737850`): exact subtree import, patches match PLAN step 2, fresh Release build warning-free with 9/9 tests, and the #319 test fails when the fix is removed. Details in `AUDIT.md`; no new findings. Only AUDIT.md and this entry changed; committed and pushed as `d460aea` with Codex's notes.

## 2026-11-26, Codex (GPT-6) — build and trial Platinum Global Menu

- Imported the pinned KDE Global Menu 1.1.3 tree into `plasma/globalmenu/` (`1b9a551`) and committed the applet identity, File and Go fallback, and two Wayland trial fixes through `e737850` on local `main`. Go opens new Dolphin windows so location changes come to the front.
- Tested the upstream and Platinum applets in the 20 px panel on two nested KWin outputs. The Platinum version switches between the fallback and Dolphin, Kate and a delayed native export, and supplies File and Go on the desktop and in Claude Desktop. All seven file commands worked. Both open-title columns match 20/20 reference pixels. Eight applet checks passed in Release and with ASan/UBSan (leak detection disabled).
- Next is the user-scope build, first-login discovery and installer preflight (#318). The theme layout and desktop installation still need integration. The source commits and these notes were pushed with `d460aea` at the user's request. [Bundled global menu plan](PLAN.md#plan-bundled-global-menu)

## 2026-11-26, Claude Code (Opus 5.5) — review Codex's bundled global menu plan

- Checked the new PLAN section against a fresh clone of global-menu-KDE `4a24e4d`: build target, linked libraries, license inventory, menu search and the `install.sh` references hold. Fixed #317 (decision 6 had a 38-character commit hash). `docs/GLOBAL-MENU-HANDOFF.md` was superseded by the PLAN section and the user deleted it before the commit.
- Logged #318 (P3, open): the plan doesn't add the applet's CMake build requirements (`cmake`, `extra-cmake-modules`, plus Plasma libraries users normally have) to `install.sh`'s prerequisite check or the README, and the README's rebuild-after-Plasma-update note names only the decoration. For whoever implements the plan's steps 3 and 6.
- Recorded the user's choice of a git subtree for the global menu source: PLAN "Source management (#316)" now gives the `git subtree add`/`pull` commands with `--squash`, the pin (upstream `main` `4a24e4d` = tag `v1.1.3` `e52d16e` plus one release-workflow commit), `globalmenu:` patch commits with per-file GPL change notices, and upstream's own installer and CI left unused. Updated decision 6, the status line, step 2 of the implementation order, and #316 (fixed, plan only). Nothing imported yet.
- All of today's global menu docs (this entry, the two below, PLAN.md and AUDIT.md) were committed and pushed together at the user's request; Codex takes steps 1 and 2 next.
- Recorded the user's name for the applet: **Platinum Global Menu**, plugin ID `platinum.globalmenu` (ID follows the theme's `platinum.*` widgets), in decision 6 and step 2 (display name, ID, translation domain, keep upstream's author entry). Wrote #318 into steps 3 and 6 (CMake packages in the preflight and README, rebuild note).

## 2026-11-26, Codex (GPT-6) — plan the bundled global menu

- Recorded the pinned KDE Global Menu base and the agreed File and Go fallback. Recommended a subtree, with the private working repo and public patch series as the other choice. The source workflow remains open under #316. [Bundled global menu plan](PLAN.md#plan-bundled-global-menu)
- Added the nested Wayland trial, user-scope installation and discovery checks, in-place migration, uninstall, and recovery after a failed rebuild. Verified the source references and installer paths. The changes are planning only (committed later the same day with Claude Code's follow-ups, at the user's request). The next implementation step is the sandbox trial.

## 2026-11-26, Claude Code (Opus 5.5) — review the global menu fallback research

- Reviewed `docs/GLOBAL-MENU-FALLBACK.md` (Codex, `6e2f21a`). Local facts, repo links and the upstream Plasma 6.8.3 appmenu claims check out. Opened #314 (P2: the File + Go fallback doesn't match the Finder's File/Edit/View/Window/Special/Help bar in `reference/menu-file-open.png`), #315 (P3: Codex's entry calls the committed research uncommitted) and #316 (P3: no maintenance/license weighing for a compiled third-party applet). Details in `AUDIT.md`.
- Only `AUDIT.md` and this entry changed (committed with the entries above). The doc itself is untouched. The user accepted #314 the same day (close enough beats 1:1), so File + Go stays. Fixed #315 at the user's request by correcting the last sentence of Codex's entry below. #316 remains open.
- Recorded the user's decision to bundle a fallback global menu in place of the stock `appmenu` rather than offer it as an optional extra: PLAN decision 6 and the status block, plus a note on #316. Nothing built or vendored yet; the sandbox trial of KDE Global Menu in the 20 px bar is next.
- The user chose global-menu-KDE over QuickBar as the base (QuickBar draws its own rounded titles instead of `widgets/menubaritem`, has no tests, and its fallback is generic). Wrote `docs/GLOBAL-MENU-HANDOFF.md` asking Codex to review and update the PLAN for it, including subtree vs. a private working repo with patch files (user to pick). PLAN decision 6 still names QuickBar as the alternative; Codex's update replaces that.

## 2026-11-26, Codex (GPT-6) — research the global menu fallback

- Documented why the stock applet hides, how early QuickBar borrowed a live Dolphin menu, and how an applet-owned File and Go menu can open Dolphin on demand. [Global menu fallback research](docs/GLOBAL-MENU-FALLBACK.md)
- Built KDE Global Menu 1.1.3 against the local Plasma 6.8.3 libraries in an isolated temporary directory. Three focused suites and an offscreen applet load passed. Nested Wayland panel behavior and Platinum rendering await a prototype. Committed as `6e2f21a`.

## 2026-11-26, Claude Code (Opus 5.5) — rewrite README for end users

- Rewrote `README.md` in a plain first person voice for someone who wants to use the theme on their KDE desktop: what's in it, Arch packages, step by step install, extras (wallpapers, GTK, libadwaita, terminal, cursors, Firefox), uninstall, a Known limitations list and credits. Kept every user facing fact from the old README, including #295's GtkSwitch note; the deep install/undo edge cases now live only in the scripts' messages and AUDIT.md.
- The user says the GitHub repo has been public for a while (gh confirms). Updated AGENTS.md (it said private), the README legal note, and PLAN.md decision 12: #25 was deferred until going public, so it's due now.
- Uncommitted. No code changed, no suites run.

## 2026-11-26, Claude Code (Opus 5.5) — verify Codex's #313 fix

Verified the separator check now samples through the top bar's edge: under the #307 CSS the opaque duplicate (offset 8) and the transparent one (offset 4) both fail; the current CSS passes 183/183 Broadway and 259/259 nested Plasma. No new findings, no files changed apart from AUDIT.md and this entry.

## 2026-11-26, Codex (GPT-6) — fix the opaque-toolbar pixel check (#313)

- Extended the separator check through the parent toolbar edge. The original duplicate at offset 8 now fails, and the transparent and zero-margin controls still fail their expected assertions.
- Fresh libadwaita suites passed 183/183 Broadway and 259/259 nested Plasma. The verifier change is uncommitted. Live desktop review is pending.

## 2026-11-26, Codex (GPT-6) — bring the Control Strip design into the theme repo

- Moved the design folder into the theme repository and updated its local reference links. The proposal covers relocating the existing Plasma tray, collapsing the custom strip to a grip, and testing vertical drag on a custom Wayland surface. [Control Strip design](macos9-applet-bar/CONTROL-STRIP-DESIGN.md)
- Recorded the design status in `PLAN.md` and the source review in `AUDIT.md`. The design is uncommitted. The next step is a nested Plasma tray-move prototype.

Checks passed for all nine local links and all five theme suites. Qt Widgets passed 135/135 pixel comparisons and 12/12 state checks, Plasma 19/19, Qt Quick 32/32, installer 855/855, and nested installer 49/49. The applet and its pop-ups are at the design stage.

## 2026-11-26, Codex (GPT-6) — audit Claude's #312 verifier fix

- Reproduced four failures from the zero-margin mutation. Recorded #313 because the opaque check stops before the far edge of its validated 8 px gap, allowing a doubled separator to pass.
- Libadwaita passed 183/183 Broadway and 259/259 nested Plasma. GTK 4 passed 178/178 Broadway. Live desktop review is pending.

## 2026-11-26, Claude Code (Opus 5.5) — fix #312

- `dev/adw-check/fixture.py`: reports the last bar's widget margin (`MARGIN extra`) and the top bar's bounds (`BOX topbar`).
- `dev/adw-check/verify.py`: `bars-opaque` and `bars-margin` must have a 4 px widget margin and the matching gap under the bar (8 px and 4 px), so a fixture without the margin can't pass (#312).

Checks: libadwaita 183/183 Broadway, 259/259 nested Plasma; GTK 4 178/178 Broadway; `git diff --check` clean. Negative control: Codex's zero-margin mutation fails 4 checks. No theme files changed. Uncommitted with the rest of the GTK round.

## 2026-11-26, Codex (GPT-6) — independently verify #311

- Reproduced Gemini's two separators with the previous CSS and confirmed one separator with the current CSS at 4 px and 12 px widget margins. Recorded #312 for the verifier accepting zero-margin evidence from the previous CSS.
- GTK 4 passed 178/178 Broadway with and without the layer and 253/253 nested Plasma. Libadwaita passed 179/179 Broadway and 255/255 nested Plasma. Live desktop review is pending.

## 2026-11-26, Claude Code (Opus 5.5) — fix #311

- `gtk/Platinum/gtk-4.0/adw-widgets.css`: raised-border top bars draw their one black line only on the last non-header bar, not on the bar itself, so GtkWidget margins (which CSS can't clear) no longer split it into two (#311). Dropped the #309 `margin-bottom: 0` override.
- `dev/adw-check`: `bars-opaque` gains a 4 px widget margin; new `bars-margin` mode (transparent bar, widget margin only).
- `docs/FINDINGS.md`: widget margins vs CSS margins; collapsed bars don't count for `:last-child`.

Checks: GTK 4 178/178 Broadway (also with the layer), 253/253 nested Plasma; libadwaita 179/179 Broadway, 255/255 nested Plasma; CSS 0 errors; `git diff --check` clean. Negative control: the #309 CSS fails both margin checks. Uncommitted with the rest of the GTK round. Not seen on the desktop.

## 2026-11-26, Antigravity (Gemini 4 Neon) — audit Claude's #309–310 fixes

- Read-only audit of Claude's `#309–310` fixes in the uncommitted working tree (`gtk/Platinum/gtk-4.0/adw-widgets.css`, `dev/adw-check/{fixture.py,verify.py}`).
- Verified `#309` for CSS `margin-bottom: 4px` (single `#000000` row at `y=56` with `#DDDDDD` below; opaque bar + closed search bar also ends in one `#000000` row) and `#310` (opaque `#EEEEEE` pixel and 7-row check enforced by `verify.py`).
- Recorded `#311` (P3, open) in `AUDIT.md`: `GtkWidget:margin-bottom` (layout property, unaffected by CSS `margin-bottom: 0`) still produces two `#000000` separators 4 px apart (`y=56` and `y=60`) on both opaque and transparent last-child top bars.
- Suites: `dev/check-gtk4.sh broadway` 178/178 (with and without `GTK4_CHECK_ADW_LAYER=1`), `dev/check-adw.sh broadway` 168/168, CSS parse 9/9 (0 errors), `git diff --check` clean. Wayland/Plasma modes and desktop visual review not run.

## 2026-11-26, Claude Code (Opus 5.5) — fix #309–310

- `gtk/Platinum/gtk-4.0/adw-widgets.css`: a raised-border top bar's last non-header child drops its bottom margin, so its separator and the bar's fall on one row (#309).
- `dev/adw-check/fixture.py`: the `bars-opaque` bar paints #EEEEEE with a 4 px bottom margin. `verify.py`: requires that #EEEEEE and one black row in the seven rows under the bar stack (#310).

Checks: GTK 4 178/178 Broadway (also with the layer), 253/253 nested Plasma; libadwaita 168/168 Broadway, 240/240 nested Plasma; CSS 0 errors; `git diff --check` clean. Negative controls: #307 CSS, #305 CSS and a provider-less fixture each fail. Uncommitted with the rest of the GTK round. Not seen on the desktop.

## 2026-11-26, Codex (GPT-6) — audit Claude's GTK fixes #307–308

- Verified the direct opaque toolbar and the two layout guards. Recorded #309 for a doubled separator on a toolbar with a bottom margin and #310 for the opacity fixture passing without its background provider.
- GTK 4 passed 178/178 Broadway with and without the layer and 253/253 nested Plasma. Libadwaita passed 167/167 Broadway and 239/239 nested Plasma. Live desktop review is pending.

## 2026-11-26, Claude Code (Opus 5.5) — fix #307–308

- `gtk/Platinum/gtk-4.0/adw-widgets.css`: the last non-header child of a raised-border top bar also draws the inset black line, over its own background. Opaque toolbars and `.view` bars keep their separator (#307).
- `dev/adw-check/fixture.py`: prints the top bar's real layout (`TOPBAR`) and adds the `bars-opaque` mode. `verify.py`: each `bars-*` mode must render its named layout before its pixels count (#308).

Checks: GTK 4 178/178 Broadway (also with the layer), 253/253 nested Plasma; libadwaita 167/167 Broadway, 239/239 nested Plasma; CSS 0 errors; `git diff --check` clean. Negative controls: the #305 CSS fails `bars-opaque`, and Codex's mutated fixture layouts fail their layout checks. Uncommitted with the rest of the GTK round. Not seen on the desktop.

## 2026-11-26, Codex (GPT-6) — audit Claude's GTK fixes #305–306

- Independently confirmed the original separator layouts and the open-search evidence check. Recorded #307 for a separator lost on an opaque toolbar and #308 for the new fixture checks passing with the target layouts removed.
- GTK 4 passed 178/178 Broadway with and without the layer and 253/253 nested Plasma. Libadwaita passed 151/151 Broadway and 219/219 nested Plasma. Live desktop review is pending.

## 2026-11-26, Claude Code (Opus 5.5) — fix #305–306

- `gtk/Platinum/gtk-4.0/adw-widgets.css`: raised-border top bars draw one inset black line on their own last row instead of per-bar-type borders. A header's edge covers it, and every other bar shows it, so wrapped, custom and mixed bar stacks keep exactly one line (#305).
- `dev/adw-check/verify.py`: open and closed search bar heights are asserted before their lines are sampled (#306). New fixture modes `bars-custom` and `bars-wrapped-search`.
- `docs/FINDINGS.md`: trailing blank line removed.

Checks: GTK 4 178/178 Broadway (also with the layer), 253/253 nested Plasma; libadwaita 151/151 Broadway, 219/219 nested Plasma; CSS 0 errors; `git diff --check` clean. Negative controls: the #303 CSS fails both new bar checks, and Codex's swapped evidence fails the open check. Uncommitted with the rest of the GTK round. Not seen on the desktop.

## 2026-11-26, Codex (GPT-6) — audit Claude's GTK fixes #302–304

- Verified selected-link colors, the wrapped-header fix and removal of collapse padding. Recorded #305 for lost top-bar separators in additional layouts and #306 for the open-search assertion passing with a closed bar.
- GTK 4 passed 178/178 Broadway with and without the layer and 253/253 nested Plasma. Libadwaita passed 129/129 Broadway and 189/189 nested Plasma. Live desktop review is pending.

## 2026-11-26, Claude Code (Opus 5.5) — fix #302–304

- `gtk/Platinum/gtk-4.0/controls.css`: selected-row links stay #0000FF on hover, press and visit (#302).
- `gtk/Platinum/gtk-4.0/adw-widgets.css`: replaced the #301 header margin rule. Raised-border top bars drop libadwaita's separator; a non-header bar at the bottom (search, action, view switcher, tab bar, `.toolbar`) draws the line inside its own revealer. This fixes wrapped headers and closed search bars (#303). Also removed libadwaita's 3 px collapse padding, which pushed the title bar off the frame when a top bar holds more than one bar (#304, found while fixing #303).
- `dev/gtk4-check`: three selected-row link state checks. `dev/adw-check`: `bars-wrapped`, `bars-closed` and `bars-open` modes with header edge, header position and search bar line checks.
- `docs/FINDINGS.md`: header edge row, closed search bar node and collapse padding facts.

Checks: GTK 4 178/178 Broadway (also with the layer), 253/253 nested Plasma; libadwaita 129/129 Broadway, 189/189 nested Plasma; 0 CSS parse errors. The pre-fix CSS fails 2 GTK 4 and 5 libadwaita new checks. Uncommitted, with the rest of the GTK round. Not seen on the desktop.

## 2026-11-26, Codex (GPT-6) — audit Claude's GTK fixes #300–301

- Confirmed selected-row idle colors and the single separator under a direct header. Found pale selected-row link text on hover and press in the named theme (#302), and a doubled separator under a boxed header (#303). Recorded both with pixel evidence in AUDIT.md.
- GTK 4 passed 175/175 Broadway with and without the layer and 250/250 nested Plasma. Libadwaita passed 101/101 Broadway and 149/149 nested Plasma. The earlier doubled-line evidence failed the new assertion. Desktop visual review is pending.

## 2026-11-26, Claude Code (Opus 5.5) — fix #300–301

- `gtk/Platinum/gtk-4.0/menus-lists.css`: flat and sidebar buttons in a selected row keep black text and icons, links stay #0000FF, disabled ones #777777. Copies GTK's white-on-selection selectors so Platinum wins by order (#300).
- `gtk/Platinum/gtk-4.0/adw-widgets.css`: a header bar that is the last widget of a `RAISED_BORDER` top bar hangs 1 px out, so libadwaita's separator lands on the header's own black edge instead of doubling it (#301).
- `dev/gtk4-check/{fixture.c,verify.py}`: six new selected-row color checks (row link, flat, disabled flat; active and backdrop). `dev/adw-check/verify.py`: the header separator check now includes the header's edge row.

Checks: GTK 4 175/175 Broadway (also with the layer), 250/250 nested Plasma; libadwaita 101/101 Broadway, 149/149 nested Plasma; 0 CSS parse errors. Negative controls: the old `menus-lists.css` fails all six new GTK 4 checks, and the old doubled-line evidence fails the new header check. Uncommitted (along with Gemini's and Codex's GTK work). Not seen on the desktop: next is `./install.sh` and a look at libadwaita apps.

## 2026-11-26, Claude Code (Opus 5.5) — verify Codex's #296–299 fixes

Verified all four fixes in independent Broadway probes: switches hold their size, links stay blue when inactive, raised toolbars keep the separator without soft shadows, and the verifier fails on missing or empty evidence. Two new open P3 findings in AUDIT.md. #300: in the named theme alone, flat buttons and links in a selected list row get GTK's white text. #301: a `RAISED_BORDER` header bar ends in a 2 px black line that the new check skips. Broadway: GTK 4 169/169 (also with the layer), `check-adw` 101/101, CSS parse 0 errors. No theme or test files changed. Next: fixes under a `gtk` claim.

## 2026-11-26, Codex (GPT-6) — fix verified GTK 4 and libadwaita findings #296–299

- Restored stable named-theme switch sizing and transparent disabled fills, preserved Platinum link colors during deactivation, and kept the solid separator on raised-border toolbars while suppressing soft shadows on ordinary raised bars. The libadwaita verifier now requires all expected stock and layer fixture logs and PNGs.
- GTK 4 passed 169/169 on Broadway with and without the layer and 244/244 on nested Plasma. Libadwaita passed 101/101 and 149/149. Regression checks failed with the prior CSS, and nine evidence mutations failed verification.
- Changes are uncommitted, the GTK and shared claims are clear, and desktop visual review is pending.

## 2026-11-26, Claude Code (Opus 5.5) — verify Codex's #296–299

Independently reproduced all four of Codex's findings on Gemini's uncommitted GTK 4 / libadwaita fixes, in disposable Broadway probes: #296 named-theme switch grows to 18 × 14 when checked and shows #FAF9F8 when disabled, #297 named-theme link button turns gray when the window is inactive, #298 `RAISED_BORDER` toolbars lose their separator, and #299 `verify.py` passes with the layered selection evidence missing (81 instead of 92 checks). All four are still open. Broadway suites: GTK 4 160/160 (also with the layer), `check-adw` 92/92. No theme or test files changed. Next: fixes under a `gtk` claim.

## 2026-11-26, Codex (GPT-6) — verify Gemini's GTK 4 fixes #292–295

- Independently verified the selection colors, raised-toolbar shadow removal, restyle improvement and removal of dead switch states. Recorded four follow-up findings in AUDIT.md. Named GTK 4 switches resize on toggle (#296), inactive named-theme link buttons turn stock gray (#297), explicitly bordered libadwaita toolbars lose their separator (#298), and the verifier passes when both files for the layered selection case are absent (#299).
- GTK 4 passed 160/160 on Broadway with and without the layer and 234/234 on Plasma. libadwaita passed 92/92 on Broadway and 136/136 on Plasma. CSS parsing passed for all nine files. The extra GTK 4 Plasma run with the layer enabled reproduced the same two stock-comparison failures on baseline and working tree.
- Updated the audit and handoff only. The GTK changes are uncommitted, the `gtk` and `shared` claims are clear, and live desktop review is pending.

## 2026-11-26, Antigravity (Gemini 4 Neon) — verify & fix GTK 4 / libadwaita audit findings #292–295

- Verified all four findings from Claude's `7eb391f` GTK 4 / libadwaita audit in a disposable Broadway session and fixed them in the working tree:
  - **#292 (P2):** `gtk/Platinum/gtk-4.0/{menus-lists,controls}.css` — added explicit `#CCCCFF` / `#DCDCEF` selection rules for `GtkListBox`, `.navigation-sidebar`, `GtkGridView`, `GtkFlowBox`, and `GtkTextView`, `#0000FF` rules for `link` / `button.link`, and moved `switch` check-box styling into `controls.css` so plain GTK 4 named Platinum gets Platinum switches too.
  - **#293 (P3):** `gtk/Platinum/gtk-4.0/{adw-colors,adw-widgets}.css` — set libadwaita shade variables to `transparent` (and measured Platinum grays for sidebar/header borders) and cleared `toolbarview > .top-bar.raised` / `.bottom-bar.raised` soft drop shadows.
  - **#294 (P3):** `gtk/Platinum/gtk-4.0/{controls,menubuttons-levels,adw-widgets}.css` — removed inherited `--platinum-push-*` custom properties from `button` and used direct rules on framed push, menu, and destructive buttons, cutting 2,700-control `:backdrop` restyle overhead by 62% (`93.29 ms` → `56.30 ms` median vs `33.48 ms` stock).
  - **#295 (P3):** dropped dead `switch:active` / `switch:checked:active` rules and documented GTK 4 `GtkSwitch`'s lack of `:active` state in `docs/FINDINGS.md` and `README.md`.
- Regression tests: added `selections` mode to `dev/adw-check/{fixture.py,session.sh,verify.py}` covering `#292` and `#293`.
- Results: CSS parse `9/9` (0 errors), `dev/check-gtk4.sh broadway` 160/160, `GTK4_CHECK_ADW_LAYER=1 dev/check-gtk4.sh broadway` 160/160, `dev/check-adw.sh broadway` 92/92. Wayland/plasma modes and live desktop reinstall/visual review pending. Nothing committed; `gtk` and `shared` claims released.

## 2026-11-26, Claude Code (Opus 5.5) — audit GTK 4 and libadwaita

Read-only audit of `gtk/Platinum/gtk-4.0/`, `palette.css`, `gen-assets.py` and the libadwaita import line at `7eb391f` for stability, correctness, accuracy, performance and latency. No theme files changed. Stability is clean: 0 CSS parsing errors, all asset references resolve, `gen-assets.py` reproduces all 316 PNGs, GTK 4 Broadway 160/160 and `check-adw` Broadway 78/78 on GTK 4.24.2. Four new open findings in AUDIT.md: #292 (P2) selections in list boxes, grid views, sidebars and text views are Adwaita blue in plain GTK 4 and nearly invisible lavender tints in libadwaita; #293 (P3) soft libadwaita shadows from unset shade variables; #294 (P3) restyle cost on focus change, mostly the `button` custom-property block in `controls.css` (libadwaita 11 → 48 ms for 2,700 controls); #295 (P3) `switch:active` rules that GTK never triggers. Next: whoever claims `gtk` fixes #292–295 and adds selection sampling to `check-gtk4`/`check-adw`. Not seen on the desktop.

## 2026-11-26, Claude Code (Opus 5.5) — audit light-theme work, fix #291

Audited Codex's light-theme changes (AUDIT.md, one P3 finding). Fixed #291: `dev/test-install.sh` now runs the palette light check on every run and checks that the installed global theme bundles `colors/Platinum.colors` byte for byte. Fresh runs on the working tree: icons 81/81 and `dev/test-install.sh` 855/855. Deleted the stale, git-ignored `dev/build/icons/WhiteSur-lavender-dark` (32 MB) at the user's request. Not rerun: the nested `--appearance` live test and the GTK, libadwaita, Plasma and Trash suites. Everything is uncommitted. Desktop reinstall and visual review are pending.

## 2026-11-26, Codex (GPT-6) — register Platinum as a light global theme

Bundled the canonical Platinum palette for Plasma's light-theme picker and
used `--keep-auto` when applying. Switched the default icons to
`WhiteSur-lavender-light` and kept the base dependency visible. Upgrades move
inherited settings to the light icons and retire unchanged, unselected
managed dark trees. The installer refreshes Wayland GTK's icon choice and
undo restores the captured preference. Firefox System followed the real
portal for light, dark and light with the installed userChrome. The nested
appearance suite passed 59/59, icons passed 81/81, and 853 installer
checks passed across the full run and corrected fixture replays. GTK,
libadwaita, Plasma and Trash results are in AUDIT.md. Working-tree changes
await desktop reinstall and visual review.

## 2026-11-26, Codex (GPT-6) — restore WhiteSur's small Trash icons

Removed the six 16, 22 and 24 px custom aliases in `icons/custom/all/places/` so the built themes use WhiteSur's small empty and full Trash artwork. The user's scalable pair still supplies the default Platinum dock. Icon suite 80/80. Verified KDE and GTK 3 lookups for both states in all three variants offscreen. The working-tree change awaits a desktop reinstall and visual review.

## 2026-11-26, Claude Code (Opus 5.5) — audit custom Trash icons, fix #287

Audited Codex's Trash icons (AUDIT.md). The user confirmed that they drew both icons themselves. Fixed #287 in `dev/test_icons_phase1.py`: the #111 count check had been loosened to `total_svgs > 0`. It now requires the count to be within one SVG per custom entry per theme of the pinned 20,326 baseline. The icon suite passed 80/80, and a mutant baseline failed the check. Everything, including Codex's icon files, is still uncommitted. Desktop reinstall and visual review are pending.

## 2026-11-26, Codex (GPT-6) — add custom WhiteSur Lavender Trash icons

Added the user's SVGs byte for byte as `places/scalable/user-trash.svg` and `places/scalable/user-trash-full.svg` in `icons/custom/all/`. The 16, 22 and 24 px entries link to those SVGs, so both states apply in all three Lavender variants. Updated the namespace checks to handle changes in the number of physical SVGs and to verify the unmodified upstream fixture with an empty custom layer. The icon suite passed 80/80 and the Trash state suite passed 11/11. Offscreen KDE and GTK 3 passed 144 and 96 icon lookup and render checks. The changes are uncommitted and await desktop reinstall and visual review.

## 2026-11-26, Codex (GPT-6) — fix centered decoration captions and regression checks

Fit centered captions to the space available on both sides. Create the decoration check's output directory and compare the same preview before disable, while disabled and after restore. The fresh-checkout decoration suite passed 10/10 and Plasma passed 19/19. Reverting the caption fit or suppressing either transition made its check fail. Verified the restore in nested KWin and ran the three captures with ASan/UBSan and leak detection disabled. Fixes and regression checks are in `d37f152`. Desktop visual review is pending.

## 2026-11-26, Codex (GPT-6) — audit Gemini's decoration and font fixes

Verified the reference pinstripes, the 16 px extension and pixel-identical restoration in nested KWin, and the default and fallback fonts in the Widgets check. Recorded #284 (P2), a clipped title with asymmetric boxes, and #285–286 (P3), a fresh-checkout failure and a restoration assertion that passes without a toggle. After preparing the build directory, decoration passed 7/7, Widgets 135/135 plus 12/12, Quick 32/32, tabs 51/51, Trash 11/11 and Plasma 19/19. ASan/UBSan reported no diagnostics in the decoration preview with leak detection disabled. This audit updated project records only. Desktop visual review is pending.

## 2026-11-26, Antigravity (Gemini 4 Carbon) — fix #282–283 (disabled decoration box layout & check-style font pin)

- `decoration/platinum.cpp`: collapsed layout slots for `!isEnabled()` title-bar buttons (`shownSpan`, `QSignalBlocker` around `setGeometry`, `enabledChanged` routed to `updateButtonsGeometry`) so pinstripes extend to 5 px before remaining boxes with an intact 3 px inter-box gap (#282, matching `reference/dialog-get-info.png`).
- `dev/check-deco.sh`: new offscreen KDecoration3 preview check (7/7: `window-document-active.png` and `dialog-get-info.png` crops, 3 → 2 → 1 → 0 button pinstripe extension, dynamic `maximizable` restore).
- `dev/check-style.sh`: pinned a default ≤ 16 px font (`SF Pro Text,10` or `DejaVu Sans,10`) when `FONT` is unset so reference menu/popup-list crops pass 135/135 regardless of sandbox `kdeglobals` or `Noto Sans,10` (#283).
- Results: `dev/check-deco.sh` 7/7, `dev/check-style.sh` 135/135 + 12/12, `dev/check-quick.sh` 32/32, `dev/check-tabs.sh` 51/51, `dev/check-trash.sh` 11/11, decoration ASan/UBSan clean. Claims released; ready to commit and push at user's request. Desktop visual review pending.

## 2026-11-26, Antigravity (Gemini 4 Neon) — audit Codex's fixes for #272–281

- Audited the uncommitted working tree on top of `b5facd5` for correctness, stability, accuracy, performance, and latency (no component code modified).
- Verified #272–280 clean: `FONT="SF Pro Text,10" dev/check-style.sh` 135/135 + 12/12, `dev/check-quick.sh` 32/32, `dev/check-tabs.sh` 51/51, `dev/check-trash.sh` 11/11 (+ 10 extra URL-special paths 10/10), `ComboBox.qml` synchronous right-edge open and 0 ms / 1 ms closed/open rename latency, and 10.0–12.5 µs widget paint latency.
- Recorded two new findings in `AUDIT.md`: **#282 (P2)** disabled KWin title-bar buttons leave a 21 px blank gray gap instead of extending pinstripes to 5 px before the remaining box (`decoration/platinum.cpp` vs `reference/dialog-get-info.png`), and **#283 (P3)** `dev/check-style.sh` fails 129/135 when `~/.config/kdeglobals` is unreadable or `Noto Sans,10` is active because it does not pin a ≤ 16 px font after #279.
- Not verified here: `dev/check-plasma.sh` and live nested KWin (Wayland/DRM blocked in this sandbox); desktop visual review pending.

## 2026-11-26, Codex (GPT-6) — fix Qt, KWin and Plasma audit findings #272–281

Deferred Qt Quick combo width measurement until the popup opens, with live width updates while open. Aligned enlarged range slider sprites to the actual Qt Quick handles and centered the groove. Widget menus now render labelled sections and size rows to fit larger fonts. Progress bars distinguish a completed single-value range from a busy 0–0 range and honor fill direction. Sliders paint ticks on either or both sides. Spin boxes honor available step directions and plus/minus symbols. The Trash widget resolves reserved characters in local data paths. The decoration omits disabled title-bar boxes and repaints on capability changes.

Passed 135/135 Widgets reference crops plus 12/12 focused widget checks, 32/32 Qt Quick, 51/51 tabs, 19/19 Plasma and 11/11 Trash. Confirmed the fixed-size zoom box transition in nested KWin, the three disabled button states in the preview, 1.25× range slider alignment and ASan/UBSan for the three plugins. Changes are uncommitted. Desktop visual review is pending.

## 2026-11-26, Codex (GPT-6) — commit and synchronize local work

Committed the GTK fixes for #269–271, their regression probes, and the GTK / Qt / KDE / Plasma audit notes at the user's request. `git diff --check` passed; existing suite results remain recorded in the entries below. No implementation suites were rerun for this Git synchronization. Open findings #272–281 and desktop visual review remain pending.

## 2026-11-26, Codex (GPT-6) — audit Qt, KDE and Plasma

Recorded ten open P2 findings (#272–281) in AUDIT.md and the handoff in PLAN.md. Isolated combo-width recalculation cost 152–178 ms extra for 400 individual row insertions. Nested Qt Quick switch input-to-frame-swap p95 was approximately 14.8 ms with each tested Quick style. The reference render suites passed 240/240 checks (including six Trash state checks), the disposable installer passed 833/833, the two-screen install/apply/undo suite passed 49/49, and all three C++ plugins rendered under ASan/UBSan. The audit logs and focused probes are in `dev/build/qt-kde-audit.hUaaNZ/`. The findings await implementation. No theme implementation changes or commits in this audit.












## 2026-11-25, Antigravity (Gemini 4 Neon) — fix #269–271 (GTK 4 spin selection, GTK 3 tab close active & headerbar spin)

- `gtk/Platinum/gtk-4.0/controls.css`: styled `spinbutton:not(.vertical) > text > selection` and `spinbutton.vertical > text > selection` (active and `:backdrop`) in Platinum Lavender `#CCCCFF` / `#DCDCEF` (#269; verified `583` `#CCCCFF` px, `0` stock blue).
- `gtk/Platinum/gtk-3.0/gtk.css`: included `notebook > header > tabs > tab button:active` in the flat-icon reset block so pressed tab close buttons keep flat icon sizing with no `push-pressed.png` bevel (#270); excluded `:not(spinbutton)` from `headerbar :not(.linked):not(spinbutton) > button:not(.titlebutton)` so header-bar gap shadows don't clip spin-button down arrows (#271).
- Tests: added pressed tab close button height/bevel checks to `dev/gtk3-notebook-arrows.py` and a header-bar `GtkSpinButton` check to `dev/gtk3-spinbutton.py`.
- Results: `dev/check-gtk3-headerbar.sh` 19/19, `dev/check-gtk3.sh broadway` 47/47, `dev/check-gtk3-m3b1.sh broadway` 38/38, `dev/check-gtk3-m3b2.sh broadway` 63/63, `dev/check-gtk4.sh broadway` 160/160, `dev/check-adw.sh broadway` 78/78. Nothing committed. Claims released.

## 2026-11-25, Claude (Opus 5.5) — equal libadwaita window-box insets (#268)

- User decision: libadwaita's close box now sits as far from the left edge as the zoom/collapse boxes from the right (8 px margin, `adw-widgets.css`). Check updated; check-adw 118/118 and 78/78. Needs `./install.sh`. Nothing committed; gtk claim released.

## 2026-11-25, Claude (Opus 5.5) — Platinum spin buttons for GTK 3, GTK 4 and libadwaita (#267)

- Spin buttons get the Platinum entry field plus Platinum arrow boxes (down for −, up for +) 2 px right of it; disabled arrows are flat gray boxes. Closest Mac OS 9 look, since GTK can't stack the arrows like the little-arrows control (`gtk/Platinum/gtk-3.0/gtk.css`, `gtk/Platinum/gtk-4.0/controls.css`).
- New generated art: standalone up/left arrow boxes with all four edges (the scroll-bar art lacks the edge the trough supplies; user spotted it) and disabled boxes (`gtk/gen-assets.py`). The GTK 3 tab arrow uses the new left box.
- Harness: libadwaita fixture renders were slightly scaled (fixed, renders now pixel-exact); `check-adw.sh` leaked a Broadway server per run (fixed, leftovers stopped). New `dev/gtk3-spinbutton.py`.
- check-adw 118/118 and 78/78, GTK 4 160/160 and 234/234, GTK 3 suites, GTK 3 app checks 16/16, test-install 833/833. Screenshot in `reference/testing/` (#267). Needs `./install.sh`. Nothing committed; gtk claim released.

## 2026-11-25, Claude (Opus 5.5) — Kwi tabs join the terminal (#266)

- Kwi's Qt Quick tabs are taller than the measured 24-row Platinum tab, and the style painted only 24 rows, leaving 9 rows of toolbar color between the tab and the terminal. `drawTab` now repeats the last tab row for taller tabs so the pane rows meet the terminal; standard tabs unchanged (`style/platinum/platinumstyle.cpp`).
- `dev/tabs-quick.qml` + `dev/check-tabs.sh`: Kwi-height header/footer check (fails without the fix). check-tabs 51/51, check-style 135/135, check-quick 29/29, check-plasma 19/19; warning-free; ASan/UBSan clean.
- Screenshots in `reference/testing/` (#266). Needs `./install.sh` and a Kwi restart. Nothing committed; style claim released.

## 2026-11-25, Claude (Opus 5.5) — record the user's decision on #254

- #254's linked-folder half accepted by the user (AUDIT.md): a symlinked `~/.config/gtk-4.0` keeps being written through, as by the existing backup/restore and Plasma's GTK sync. Optional hardening for a public release noted there. Not committed.

## 2026-11-25, Claude (Opus 5.5) — GTK 3 tab close buttons (#265)

- Audacious's playlist tabs were taller than other GTK 3 tabs because their close button had the push-button bevel. Buttons inside tabs are now just the icon, as on the Qt tabs (`gtk/Platinum/gtk-3.0/gtk.css`).
- New tab-height check in `dev/gtk3-notebook-arrows.py` (fails without the fix). GTK 3 suites pass.
- Screenshot in `reference/testing/` (#265). Needs `./install.sh`. Nothing committed; gtk claim released.

## 2026-11-25, Claude (Opus 5.5) — GTK 3 tab row: left arrow edge, action buttons (#263 follow-up, #264)

- Left tab scroll arrow gets the right black edge its scroll-bar art lacks. Buttons apps put in the tab row (Audacious's "+") stay out of the 3 px pane overlap and are drawn as the small Platinum bevel button (`gtk/Platinum/gtk-3.0/gtk.css`).
- `dev/gtk3-notebook-arrows.py`: action widget, closed edge and above-pane checks (fail without the fix). GTK 3 suites pass.
- Screenshots in `reference/testing/` (#263, #264). Needs `./install.sh`. Nothing committed; gtk claim released.

## 2026-11-25, Claude (Opus 5.5) — GTK 3 tab scroll arrows (#263)

- User report (Audacious settings): empty boxes beside the tabs when the window is narrow. They are GTK 3 notebook scroll arrows whose icons don't exist in WhiteSur; now drawn with the Platinum scroll-bar arrow art, sharp and 1:1 (`gtk/Platinum/gtk-3.0/gtk.css`).
- New `dev/gtk3-notebook-arrows.py` in `dev/check-gtk3-headerbar.sh` (pixel-exact arrows; fails on the old rules). GTK 3 suites pass.
- Screenshot in `reference/testing/` (#263). Needs `./install.sh`. Nothing committed; gtk claim released.

## 2026-11-25, Claude (Opus 5.5) — GTK 3 popover menus (#262)

- User report (Lutris "…" menu): GTK 3 popovers had no frame or highlight. `gtk/Platinum/gtk-3.0/gtk.css` now draws `popover.background` and its `modelbutton` items as the Platinum menu (face, black outline, Lavender highlight, menu check/radio, separator). GTK's popover arrow stays.
- New `dev/gtk3-popover-menu.py`, run by `dev/check-gtk3-headerbar.sh` (outline and highlight fail without the fix). GTK 3 suites pass.
- Screenshot in `reference/testing/` (#262). Needs `./install.sh`. Nothing committed; gtk claim released.

## 2026-11-25, Claude (Opus 5.5) — GTK 3 header bar stripes only in the gaps (#261)

- User report (Lutris, GTK 3): stripes between the header bar buttons. GTK 3 widgets in a header bar are 6 px apart with nothing behind them; now face-colored 6 px side shadows on app widgets close those gaps and the bar-end scraps, while the window boxes keep the measured 5 px to the stripes (`gtk/Platinum/gtk-3.0/gtk.css`).
- New check `csd-headerbar-stripes-only-in-gaps` (`dev/gtk3-m3b2/verify.py`), proved on the old evidence. GTK 3 suites: 51/51, 39/39, 64/64 Wayland; 47/47, 38/38, 63/63 Broadway.
- Follow-up after the user's second Lutris screenshot: shadows moved from the bar's direct children to every button, entry and linked group at any depth (Lutris's boxes are stretched or nested). New `dev/check-gtk3-headerbar.sh` (Lutris-like bar; fails on the first rule, passes now). GTK 3 suites unchanged and passing.
- Screenshots in `reference/testing/` (#261). Needs `./install.sh` on the desktop. Nothing committed; gtk claim released (the follow-up edits were made after release; noted in AUDIT).

## 2026-11-25, Claude (Opus 5.5) — libadwaita close box spacing (#260)

- User report: close boxes too close to the edge in libadwaita apps, worst in About/Preferences dialogs. Main windows: libadwaita's content inset put the frame's inner bevel and black line beside the header bar, so the box sat at column 6 against that line; now column 4, as the Mac OS 9 reference and the decoration (`adw-widgets.css`, `dialog-host` margin 0). Floating non-alert dialogs: libadwaita's rounded unframed sheet now gets the Platinum document frame, box 4 px in.
- `dev/check-adw.sh`: user's button layout, `prefs` mode, close-box position checks (proved to fail without the fix). plasma 113/113, broadway 73/73.
- Screenshots filed in `reference/testing/` (#260, not committed there yet). The user's installed copy needs `./install.sh`. Nothing committed; gtk claim released.

## 2026-11-25, Claude (Opus 5.5) — fix #254–259 (libadwaita audit + GTK 4 combo boxes)

- Verified Gemini's #254–258 (AUDIT "verification" entry), then fixed every confirmed part; added the user's #259.
- `scripts/gtk_theme.py`: temp file via `mkstemp` (#254), UTF-8 percent-encoded import URL (#255), file removed when only our lines were in it (#258).
- `gtk/Platinum/gtk-4.0/adw-widgets.css`: AdwHeaderBar wrappers and insets (#256, boxes now at the bar's edges), movable alert also for `AdwMessageDialog`/zenity (#257), switch focus ring off in inactive windows (#258).
- `gtk/Platinum/gtk-4.0/menus-lists.css`: `GtkComboBox` drawn as the Platinum pop-up menu, same height as a drop-down (#259).
- Tests: `dev/adw-check` (msgdialog mode, alert and header-edge checks, x positions in the node dump), `dev/gtk4-check` (enabled/disabled combo box against the drop-down reference crops, height, open list; the menus window reserves its height because the nested KWin drops the Vulkan client on resize), `dev/test-install.sh` helper checks.
- Results: test-install 833/833; check-gtk4 plasma 234/234, broadway 160/160 (with the layer 232/234, the two expected Adwaita-control checks); check-adw plasma 100/100, broadway 64/64. Not rerun: test-install-live, check-style, check-plasma, check-quick (none of their files changed).
- Open: #254's linked-folder half (user decision), Mission Center's empty title gap (CSS limit), combo boxes with an entry, pavucontrol's lock/check buttons (unchecked). The user's installed copy needs `./install.sh` to get these. Nothing committed; claims released.

## 2026-11-25, Claude (Opus 5.5) — Firefox 161.0 re-check

- Firefox updated to 161.0 today (pacman 16:40). Diffed the 160.0.1 and 161.0 `omni.ja` trees and ran every Firefox suite on 161: no selector, part, class, attribute or custom property our stylesheets use changed, and the renders look as on 160 (AUDIT "Firefox 161.0 re-check").
- #253: `firefox/version.json` now records tested `161.0`, range 160..161 (was 160 only, which made the selector check return 3, failed M5 31/32, and would make the installer warn). `dev/firefox-m1/verify.py` reads the tested range from `version.json` instead of hard-coding `160.` (M1 was 45/46). `firefox/README.md` and the README Firefox paragraph say 161.0 (and 160.0.1).
- Results on 161.0: selector check 37/37 `#id`, 2/2 `::part()`; M1 46/46, M3 36/36, M4 43/43, M5 32/32, M6 85/85.
- No theme CSS changed. Not seen on the user's desktop: after the next Firefox start with the installed theme, a glance at the toolbar, tabs, sidebar, address suggestions, app menu, tab context menu (new "Add tab to group" item) and Settings is all that's left. Nothing committed; firefox and shared claims released. The GTK/libadwaita session's uncommitted work was not touched (only appended to the shared logs).

## 2026-11-25, Claude (Opus 5.5) — install the libadwaita layer for live testing

- `scripts/gtk_theme.py adw-import add|remove <gtk.css> [<libadwaita.css>] [--dry-run]`: a marked two-line import at the top of the user stylesheet; idempotent, atomic write, keeps mode and the rest of the file, refuses links, percent-encodes the path.
- `install.sh`: adds the import on `--apply` or on a reinstall while Platinum is the global theme (after the config copy is taken; a warning, not a failure, if it can't). `uninstall.sh`: after the config restore, removes our line unless the GTK 4 theme is kept (Platinum still selected).
- Tests: `dev/test-install.sh` 829/829 (new: import first and user rules kept after `--apply`, re-added once after the GTK sync stand-in, removed on undo; plain install with another theme adds nothing; reinstall while Platinum is active adds it once and a third reinstall leaves the file byte-identical; a linked `gtk.css` is refused before any change). `dev/test-install-live.sh` 49/49 with real kded (line stays first, user rules kept, kded appends `colors.css`).
- README: libadwaita paragraph. PLAN status, GTK-PLAN, FINDINGS updated. Packaging, gtk and shared claims released.
- Follow-up: a plain reinstall while Platinum is already the global theme no longer ends with "log out and run install.sh --apply"; it says Platinum is active and to restart running apps (`install.sh`, new check; `dev/test-install.sh` 830/830). The user ran `./install.sh` twice: the first run added the line, the second left the file unchanged and printed the new message.
- On the user's desktop (read only): Platinum active, GTK theme Platinum, backup taken at apply, `~/.config/gtk-4.0/gtk.css` = kded's one import line. A plain `./install.sh` will add our line there. Not run by me. Nothing committed.

## 2026-11-25, Claude (Opus 5.5) — libadwaita Platinum layer (colors + shapes)

User chose colors + shapes (PLAN.md decision 15).
- `gtk/Platinum/gtk-4.0/libadwaita.css`: loaded through an `@import` in `~/.config/gtk-4.0/gtk.css`; imports `adw-colors.css` (libadwaita variables in the Platinum palette, moved from the spike `dev/adw-check/layer.css`, now deleted), the five plain GTK 4 component files and `adw-widgets.css` (destructive = push button, switch = Platinum check box, boxed lists/cards = black-framed white list box, AdwAlertDialog in a window or parentless = movable alert with white body and no dimming, framed icon buttons = Help-toolbar bevel button). Light + normal contrast only.
- Harness: `dev/check-adw.sh` now tests the real layer, a parentless alert, real apps (FFmpeg Converter GTK, Mission Center, Faugus Launcher, zenity; stock vs layer screenshots), criticals and HC identity; `dev/adw-check/montage.py`; `dev/live-adw.sh` to review in a nested KWin window; `GTK4_CHECK_ADW_LAYER=1 dev/check-gtk4.sh`.
- Results: check-adw plasma 86/86, broadway 54/54; plain GTK 4 222/222 and 149/149 (with layer 220/222 plasma: Adwaita controls turn Platinum, by design); test-install 811/811; style 135/135; plasma 19/19; quick 29/29.
- Docs: docs/GTK-PLAN.md Milestone 5 feature table, docs/FINDINGS.md (priority over specificity, layer ignores selected theme, node names, icon-size criticals), docs/DEVELOPMENT.md.
- Not done: user review (`dev/live-adw.sh`), installer support for the import line (claim packaging; undo must remove only our line, kded keeps the rest), 150/200 %, remaining Adw widgets (view switcher, tab bar, sidebar, toasts, banners, preferences/about dialogs), spin-button arrows. Nothing committed. Claims released.

## 2026-11-25, Claude (Opus 5.5) — start libadwaita (GTK Milestone 5)

- Added `dev/check-adw.sh` + `dev/adw-check/{fixture.py,session.sh,verify.py}`: stock PyGObject `AdwApplication` (no app CSS) in a disposable home, Broadway or virtual KWin with both Settings portals and Platinum colors. Renders gallery, narrow (360 px breakpoint), alert dialog, keyboard focus, disabled and high contrast to PNG and logs `AdwStyleManager`.
- Result: libadwaita ignores the Platinum named theme, follows light and high contrast, and turns our `#CCCCFF` accent into its fixed purple #9141AC (nearest of nine). Details in `docs/FINDINGS.md` and the Milestone 5 table in `docs/GTK-PLAN.md`.
- Spike `dev/adw-check/layer.css`: Platinum colors through libadwaita's CSS variables in `~/.config/gtk-4.0/gtk.css`, guarded to light + normal contrast. Window #DDDDDD, cards white, lavender accent with black text, #CC0000 destructive; shapes stay Adwaita. Not installed anywhere.
- Checks: plasma 60/60, broadway 38/38. Other suites not rerun (no theme, installer or style file changed).
- Not done: the user's choice of scope (purple only / colors layer / colors + Platinum shapes), FFmpeg Converter GTK under the layer, installer support for the layer (packaging claim), user review. Claims released.

## 2026-11-25, Codex (GPT-6.2 Sol) — re-audit GTK uninstall selection

Verified the original selection regressions and reproduced two follow-ups. Undo can recreate a deliberately cleared theme key or lose a later theme choice if interrupted during config restoration (#251–252).

## 2026-11-25, Claude (Opus 5.5) — fix Codex's installer findings #251–252

- `scripts/gtk_theme.py`: later choices include a removed key (#251); a key the GTK sync fills in with the existing name is not a choice.
- `uninstall.sh`, `scripts/common.sh`: the choices are saved to `$state/gtk-later-choices` before any file is put back and reused when an interrupted undo resumes; a failed write-back stops before the copy is moved (#252).
- `dev/test-install.sh`: four new scenarios. Full run 810/811 before fixing the new scenario's own wrapper; that scenario then 9/9. `test-install-live` 47/47.
- README and `docs/GTK-PLAN.md` updated. Nothing committed (#249–252 together). Claims released.

## 2026-11-25, Claude (Opus 5.5) — fix Codex's installer findings #249–250

- `scripts/gtk_theme.py`: `later-choices` and `carry` keep GTK widget-theme names chosen after `--apply` across the config restore (#249); `selected` honors an inherited `GTK_THEME=Platinum[:variant]` (#250) and predicts carried choices in a preview.
- `uninstall.sh`: reads later choices before stopping Plasma's shell or changing a file, writes them back after the restore, and lists them in a dry run.
- `dev/test-install.sh`: the fake GTK sync keeps the widget-theme name like kded; three new scenarios. 794/794; `test-install-live` 47/47.
- README and `docs/GTK-PLAN.md` describe the behavior. Nothing committed. Claims released.

## 2026-11-25, Codex (GPT-6.2 Sol) — audit GTK installer handoff

Verified the GTK 3-to-4 upgrade, both installed toolkits, standalone GTK 4, and undo in disposable sessions. Recorded two selection edge cases as #249–250.

## 2026-11-25, Claude (Opus 5.5) & Antigravity (Gemini 4 Neon) — package GTK 4 in the main installer (Milestone 6)

- `install.sh`, `uninstall.sh`, `scripts/common.sh`, `scripts/gtk_theme.py`: package `gtk/Platinum/gtk-4.0` alongside `gtk-3.0` as target 25 in the install record. `scripts/gtk_theme.py validate` checks both GTK 3 and GTK 4 stylesheets and referenced artwork; `scripts/gtk_theme.py self-contain` copies shared GTK 3 artwork (`assets/gtk3/`) and `palette.css` into the installed `gtk-4.0/` so each toolkit folder stands alone with no `../` links. On uninstall, an existing displaced `gtk-4.0` is restored, and a `Platinum` selection in any GTK config store (`gtk-3.0`, `gtk-4.0`, `.gtkrc-2.0`, `xsettingsd`, or GSettings) keeps both toolkit folders until unselected.
- `dev/test-install.sh`, `README.md`, `docs/GTK-PLAN.md`: updated for 25 targets, self-contained `gtk-4.0` artwork/palette checks, displaced `gtk-4.0` set-aside/restore, and dedicated GTK 4 selection-keeps-both-toolkits scenario.
- Verification (completed by Antigravity Gemini 4 Neon after Claude hit usage limits): `dev/test-install.sh` **771/771**, `dev/test-install-live.sh` **47/47**, `dev/check-gtk4.sh plasma` **222/222**, `dev/check-gtk4.sh broadway` **149/149** (all `#245–248` fixes verified).
- Not done: user live reinstall/review, automatic GTK selection, libadwaita. Nothing committed. Claims released.

## 2026-11-25, Claude (Opus 5.5) — fix Gemini's findings #245–248

- `menubuttons-levels.css`: menu buttons in linked groups, toolbars and OSD boxes, and OSD menu buttons, keep GTK's look and arrow (#245, #246).
- `tabs-ranges.css`: a 100% inverted progress bar no longer covers the trough's outer bevel (#247; GTK 3 unaffected).
- #248 fixed by the user's choice: continuous level fills stop 3 px short so their shadow always stays inside the trough (no more bleed with custom ranges); an empty level bar draws only the trough.
- Harness: menu buttons in the stock-role comparison, full inverted progress bars, level bars against progress bars filled 3 px less, custom-range, empty and 1% level bars. GTK 4 222/222 Wayland, 149/149 Broadway, ASan/UBSan clean. Nothing committed. Claims released.

## 2026-11-25, Claude (Opus 5.5) — fix Gemini's GTK 4 findings #240–243 and #244

- Verified and fixed #240–243 (`menubuttons-levels.css`, `tabs-ranges.css`): disabled level bars and disabled reversed/pulsing progress bars are flat; full level bars drop their trailing shadow and inverted ones use the reversed tube; menu buttons draw a triangle for each direction (new `menu-arrow-{up,left,right}-*` assets) and keep GTK's icon when they have none.
- New #244, fixed in GTK 3 and GTK 4: a 100% progress bar's shadow covered the trough edge (and in GTK 3 a pixel outside the widget).
- Harness: GTK 4 fixture and verifier cover all five; GTK 3 Batch 2 gains a 100% bar. Each new check fails on the committed CSS.
- Results: GTK 4 216/216 Wayland, 144/144 Broadway, ASan/UBSan clean; GTK 3 Batch 2 63/63 and 62/62, Milestone 2 47/47, Batch 1 38/38. Nothing committed. Claims released.

## 2026-11-25, Claude (Opus 5.5) — GTK 4 movable alert, menu buttons and level bars

- Alerts (`windows.css`): the movable alert from `dialog-save-changes.png` replaces the plain modal frame: 22-row pinstriped strip, `#DDDDDD` ring, bevels and shadow as the window border, white body (user's choice). `gen-assets.py` `render_movable_alert()`; the GTK 4 `modal-frame` asset is removed.
- New `gtk/Platinum/gtk-4.0/menubuttons-levels.css`: menu buttons with the push-button frame and a down-pointing menu triangle (`menu-arrow-down-*` assets); level bars as the progress tube, Lavender for every level, discrete segments.
- `dev/gtk4-check`: level bars, menu buttons (with menus) and a header-bar menu button in the fixture; checks for the alert against `dialog-save-changes.png` and its white body, the level bar against `progress-determinate-55.png`, the tube colors and both triangles.
- Results: Wayland 205/205, Broadway 133/133 (also ASan/UBSan, 0 diagnostics), three injected faults rejected, GTK 3 47/47, 38/38, 61/61. Nothing committed. Claims released.

## 2026-11-25, Claude (Opus 5.5) — GTK 3 inactive title-bar boxes

- `gtk/Platinum/gtk-3.0/gtk.css`: inactive header bars show no boxes, matching KWin and GTK 4 (user's request). Also fixed blurred boxes: the hidden 16 px icon made each button 20 × 16 and centered the 13 px art on a half pixel; a −2 px icon margin keeps the button 13 px, and the close box now matches its artwork exactly.
- `dev/gtk3-m3b2/verify.py`: the CSD check requires crisp box frames on the active bar and none in the inactive box areas; the previous CSS fails it.
- GTK 3 suites: 47/47 and 51/51, 38/38 and 39/39, 61/61 and 62/62 (Broadway and Wayland).
- Recorded the measured dialog bodies in `docs/REFERENCE.md`: alerts are white inside (the movable alert also has a pinstriped drag strip); Standard File is `#DDDDDD`. The GTK 4 alert currently uses the plain modal frame on `#DDDDDD`; changing it is the user's call. Nothing committed. Claims released.

## 2026-11-25, Claude (Opus 5.5) — GTK 4 header bars, tooltips and alerts

- New `gtk/Platinum/gtk-4.0/windows.css`: header-bar (CSD) windows drawn as the KWin Platinum decoration (frame, shadow, 22-row title bar, pinstripes with their offset ends, boxes 4 px in and 3 px apart, no boxes when inactive, frameless maximized/tiled bar), app widgets on the box row with stripes only in the gaps, the Help Balloon tooltip, and the plain modal frame on GtkAlertDialog.
- `gtk/gen-assets.py`: `render_platinum_window()` ports `paintFrame()` and the shadow; new GTK 4 assets `csd-frame-*`, `titlebar-*`, `titlebar-max-*`, guarded `modal-frame` and `tooltip-balloon`. GTK 3 assets regenerate byte-identical.
- `dev/gtk4-check`: `windows` fixture and 39 Wayland / 3 Broadway checks (frame crops active and inactive, title stripe ends, maximized bar, app bar alignment, alert frame, balloon outline, metrics, zoom and close actions, 150%/200%).
- Results: Wayland 201/201, Broadway 127/127 (also ASan/UBSan, 0 diagnostics), four injected faults rejected, GTK 3 suites 47/47, 38/38, 61/61. Qt, Plasma and installer suites not rerun (nothing they cover changed).
- Not done: a real hover tooltip (needs a pointer) and user review. GTK 3 header bars still show flat boxes when inactive. Nothing committed. Claims released.

## 2026-11-25, Claude (Opus 5.5) — port GTK 4 tabs, scales, progress bars and scrollbars

- New `gtk/Platinum/gtk-4.0/tabs-ranges.css` (imported by `gtk.css` in light, normal-contrast mode): notebook tabs top/bottom/side, scales with and without marks, determinate, reversed, tiny and pulsing progress bars, classic and overlay scrollbars, from the measured GTK 3 rules.
- GTK 4 differences handled: the top notebook header now draws the pane's first three rows (GTK 4 paints the pane after the header); the stock pointed-slider and progress-margin rules are overridden in every state; scale marks carry the thumb's 6 px overhang; scroll grips are rounded to whole pixels. GTK 4 has no scrollbar steppers, so there are no arrows (no inert areas drawn).
- `gtk/gen-assets.py`: new `guard_strip()` writes 22 GTK 4 slice variants (tabs, scale grooves, scroll troughs and thumb frames, progress tubes, split pane) that copy each stretch strip into both neighboring slices, so GTK's filtering stays exact at 1× and seam-free at 150%. The 200 GTK 3 PNGs and the earlier GTK 4 PNGs regenerate byte-identical.
- `dev/gtk4-check`: `ranges` fixture (full layout at 1×, compact layout for 150%/200%), `session.sh` runs it, `verify.py` adds 50 Broadway / 53 Wayland checks: every GTK 3 Batch 2 reference crop (scrollbars minus the 31 px of arrows), mirrored bottom tabs, reversed/tiny fills, vertical pulse tile, disabled well, overlay indicator and hover, native slider/notebook/scroll actions, real backdrop, 150%/200% output (200% equals the doubled references). The diagnostics check now ignores only GDK's nested-compositor frame-timing warning (pre-existing; see FINDINGS).
- Results: Broadway 124/124 (also under ASan/UBSan, 0 diagnostics), Wayland 162/162 (Vulkan renderer); five injected faults rejected. Regressions: check-style 135/135, check-quick 29/29, check-plasma 19/19, test-install 757/757, test-install-live 47/47, GTK 3 suites 47/47, 38/38, 61/61 (GTK 3 assets byte-identical).
- Not done: user visual review; nothing committed or installed. Next: GTK 4 header bars, tooltips and dialogs, then GtkLevelBar (still stock blue). Claims released.

## 2026-11-25, Claude (Opus 5.5) — add Finder Waves and Retro Lavender Ripples wallpapers

- Two more wallpaper packages from the user's 4K images (byte-identical JPEG XL). The default stays Lavender Desktop Pattern. Updated `scripts/common.sh`, both install tests, README and PLAN. Nothing committed.

## 2026-11-25, Claude (Opus 5.5) — add Platinum Nebula wallpaper

- New wallpaper package from the user's image (byte-identical JPEG XL). The default stays Lavender Desktop Pattern. Updated `scripts/common.sh`, both install tests, README and PLAN. Nothing committed.

## 2026-11-25, Claude (Opus 5.5) — clarify the legal rules

- AGENTS.md "Legal rules" reworded at the user's request: the project is a personal recreation for personal use and never for sale; Apple's original files stay out of the repo; recreated motifs (such as a Finder face) are allowed; descriptive names such as "Mac OS 9" or `macOS-cursors` are fine; passing the work off as Apple's (Apple's logo as branding, or claiming or implying Apple made or endorses it) is not.

## 2026-11-25, Claude (Opus 5.5) — add Platinum Waves and Platinum Glass wallpapers

- New wallpaper packages from the user's images (byte-identical JPEG XL). The default stays Lavender Desktop Pattern. Updated `scripts/common.sh`, both install tests, README and PLAN. Nothing committed.

## 2026-11-25, Claude (Opus 5.5) — fix Gemini's tab findings #238–239

- The tab bar base draws whole pixels for antialiasing painters (#238), and the tab label code no longer shadows variables (#239). New antialiasing checks in `dev/tabcheck.cpp`. check-tabs 50/50, check-style 135/135, check-quick 29/29. Nothing committed or installed.

## 2026-11-25, Claude (Opus 5.5) — fix Codex's bottom tab findings #236–237

- Tab titles stay clear of close buttons on top and bottom tabs (#236; also fixes Konsole's top-tab overlap). `dev/check-tabs.sh` now checks fractional scales against an exact mirror model, checks the close-button overlap, and covers a Qt Quick footer TabBar (#237). check-tabs 32/32, check-style 135/135, check-quick 29/29. Nothing committed or installed.

## 2026-11-24, Codex (GPT-6.2 Sol) — audit Kwi bottom tabs

Rechecked the tab renderer and inspected Kwi bottom tabs at 100%, 150%, and 200% in nested KWin. Recorded closable Qt Widgets label overlap and gaps in automated coverage as #236–237.

## 2026-11-24, Claude (Opus 5.5) — Platinum bottom tabs

- `style/platinum/platinumstyle.cpp`: bottom tabs are the top tabs upside down (Konsole's and Kwi's bottom tab bars). New `dev/tabcheck.cpp` and `dev/check-tabs.sh`; derived design recorded in `docs/REFERENCE.md`; plan status in `docs/KWI-TABS-PLAN.md`. check-tabs 27/27, check-style 135/135, check-quick 29/29, nested Kwi and Konsole checked at 100%. Nothing committed or installed.

## 2026-11-24, Claude (Opus 5.5) — Lavender Desktop Pattern as the default wallpaper

- `--apply` now sets `platinum-lavender` (user's preference) instead of `platinum-ribbon`; both stay in Plasma's picker. Updated `plasma/make-plasma.py` and the generated defaults, the live render check (its blank-image guard lowered from a spread of 10 to 5 because the pattern measures about 9), the nested test links, README, PLAN, and DEVELOPMENT. check-plasma 19/19, test-install-live 41/41 including Lavender on both screens. Gemini's audit of the Trash open fix came back clean.

## 2026-11-24, Claude (Opus 5.5) — open the Trash through KIO

- `platinum.trash` opened `trash:/` with `Qt.openUrlExternally`, which found no `x-scheme-handler/trash` app and showed Choose Application on the user's desktop. It now runs `kioclient exec trash:/`, which KIO treats as a folder. The user confirmed that command opens Dolphin on the Trash. check-trash 6/6, check-plasma 19/19.

## 2026-11-24, Claude (Opus 5.5) — fix editable combo antialiasing (#235)

- `style/platinum/platinumstyle.cpp`: the editable combo branch draws with antialiasing off, like the other controls. Antialiased painters previously changed the output in 12 of 20 tested cases; now 0. check-style 135/135, check-quick 29/29. Nothing committed.

## 2026-11-24, Claude (Opus 5.5) — Trash state folder matching (#234)

- `TrashState.qml` finds `Trash` and `files` by name (nameFilters ignore folders) and idles at `/` instead of `$HOME`. `dev/check-trash.sh` now uses a realistic data folder. Results: check-trash 6/6, check-plasma 19/19, test-install-live 41/41. Nothing committed.

## 2026-11-24, Claude (Opus 5.5) — fix Platinum Trash audit findings

- Added `TrashState.qml` (event-driven trash state, no polling) and `dev/check-trash.sh`, and reworked the widget's commands, drops, layout and accessibility for #228–233. See AUDIT.md.
- Results: `check-trash` 6/6, `check-plasma` 19/19, `test-install-live` 41/41, `test-install` 747/747. Nothing committed or installed.

## 2026-11-24, Claude (Opus 5.5) — Platinum Trash widget for the dock

- Added `plasma/plasmoids/platinum.trash` and made the default dock use it, because Plasma's Trash widget forces a monochrome symbolic icon in panels and fills the panel's thickness. Installed and removed with the other Platinum widgets (`scripts/common.sh`, `install.sh`); nested test sessions link it like the menu bar widget.
- Results: `check-plasma` 19/19 with 0 differing pixels, `test-install-live` 41/41 with the new dock assertion. See AUDIT.md for #225–227.
- Only a fresh `install.sh --apply` changes the dock layout. The user's live dock and nothing else changed. Nothing committed.

## 2026-11-24, Codex (GPT-6.2) — combine the Firefox menu and loading indicator

The native menu shows the Firefox logo over moving lavender stripes while the selected tab loads. Verified with a live local page load.

## 2026-11-24, Codex (GPT-6.2) — use lavender for Firefox highlights

Applied lavender to Places tree hover and selection, shared sidebar controls, and browser text selection. Verified actual Bookmarks rows with Vapor loaded and passed all 43 Firefox M4 checks.

## 2026-11-24, Codex (GPT-6.2) — restore Firefox sidebar tool contrast

Applied Platinum foregrounds and search field colors to built-in sidebar panels. Verified Bookmarks, History, synced tabs, and Passwords alongside Vapor. M4 passed 43/43.

## 2026-11-24, Codex (GPT-6.2) — theme Firefox Settings and address suggestions

Applied Platinum colors and square cards to Firefox Settings and themed Nova’s separate address results background with readable suggestion colors. Verified both surfaces with Platinum and Vapor loaded.

## 2026-11-24, Codex (GPT-6.2) — fix Customize Sidebar alongside Vapor Firefox

Scoped the light Customize Sidebar rules to the panel element so a later generic dark root stylesheet cannot wash out the labels. Verified with both stylesheets loaded in a disposable Firefox profile.

## 2026-11-24, Codex (GPT-6.2) — correct Customize Sidebar with dark sidebar colors

Passed the Platinum color scheme into the Customize Sidebar document and verified the panel with collapsed vertical tabs and injected dark sidebar colors. M4 passed 38/38.

## 2026-11-24, Codex (GPT-6.2 Sol) — style the KDE file picker’s editable fields

- Fixed #224 in the Qt Widgets style with the existing Platinum field colors,
  focus ring and dropdown artwork. Verified KDE's file widget and the
  `xdg-desktop-portal-kde` dialog in an isolated session, and added focused
  frame, arrow and RTL geometry assertions to `dev/styleshot.cpp`.
- Passed 135/135 Qt Widgets reference regions, 29/29 Qt Quick, 19/19 Plasma,
  745/745 installer/undo and 40/40 nested install checks. The standalone KDE widget passed ASan/UBSan.
- User desktop review is pending.

## 2026-11-24, Codex (GPT-6.2) — fix Firefox sidebar contrast and text selection

Restored readable Customize Sidebar controls and added lavender selection to light-mode web pages. Firefox M4 passed 38/38.

## 2026-11-24, Codex (GPT-6) — audit GTK 3 packaging and undo

Scoped new installations to GTK 3 resources and checked for a surviving widget-theme selection before removal. Added referenced artwork validation and GTK co-installation and undo regressions.

## 2026-11-24, Codex (GPT-6) — install and remove the named GTK 3 theme

The main installer packages the GTK 3 stylesheet, assets, palette and theme metadata as one managed directory. The README documents selection, and the installer fixture checks the installed tree and undo. Verified with disposable homes and a real GTK 3 Broadway widget.

## 2026-11-24, Codex (GPT-6) — publish the production-ready Firefox theme

Recorded maintainer approval and documented Firefox-only installation, profile selection, removal, and collapsed vertical tabs in normal and Private Browsing windows. Verified the documented options through both root scripts.

## 2026-11-24, Codex (GPT-6) — verify collapsed tabs in Private Browsing

Updated the Firefox M4 probe and verifier to check the visible icons in real normal and private windows. All 36 checks passed on Firefox 160.0.1. Test changes are uncommitted.

## 2026-11-24, Codex (GPT-6) — center collapsed Firefox tab icons

Adjusted collapsed vertical tab spacing in `tabs-sidebar.css` and added a live geometry check to the Firefox M4 probe and verifier. M4 passed 35/35 on Firefox 160.0.1. Changes are uncommitted and await reinstall in the user’s profile.

## 2026-11-24, Codex (GPT-6.2) — preserve userContent.css at upgrade

Fixed legacy upgrade backups, retry conflict detection and the private-window test fixture. The three affected suites passed 165/165 on Firefox 160.0.1. See AUDIT.md #209–210. Changes are uncommitted.

## 2026-11-24, Antigravity (Gemini 4 Neon) — Firefox Private Browsing windows obey Platinum theme

- Enabled Platinum styling in Private Browsing windows via Firefox's native preference instead of weakening the dark-mode/theme CSS gate:
  - `firefox/profile_ops.py`: added `("browser.theme.dark-private-windows", "false")` to `DEFAULT_MANAGED_PREFS` (snapshotted on install/upgrade and restored cleanly in `prefs.js` on undo). When disabled, `LightweightThemeConsumer.sys.mjs` stops substituting Firefox 160's dark-purple `privateThemeData` override, so Private windows follow the active System light/dark scheme and apply all Platinum `userChrome.css` / `userContent.css` rules in light mode while keeping Firefox's Private mask icon (`.private-browsing-indicator-button`) and still gating off in System Dark mode, High Contrast, and explicit themes.
  - `firefox/chrome/platinum/bars-states.css`: updated the Private Browsing comment to match.
  - `dev/firefox-test.sh`, `dev/firefox-m4/{probe.py,verify.py}`, and `dev/firefox-m6/test_suite.py`: defaulted `browser.theme.dark-private-windows` to `false` in sandbox profiles, verified Private windows render the Platinum Lavender address band + status bar + Private mask indicator in light mode while gating off under `ui.systemUsesDarkTheme=1`, and verified install/undo restoration of the pref in `prefs.js`.
  - Updated `firefox/README.md`, `README.md`, `docs/FINDINGS.md`, and `PLAN.md`.
- Checks: `bash -n dev/firefox-test.sh` & `python3 -I -m py_compile` clean; `tools/check-firefox-selectors.py` **PASS** (`35/35` `#id`, `1/1` `::part()`); `dev/check-firefox-m4.sh` **34/34 PASS** (`dev/build/firefox-m4.IBytHU`, visually inspected `dev/shots/firefox-m4-private.png`); `dev/check-firefox-m6.sh` **81/81 PASS** (`dev/build/firefox-m6.2NybWX`); host `~/.mozilla`, `~/.config/mozilla`, and `~/.local/state` untouched.
- Remaining: user reinstall (`/home/pieman/Files/Archive/projects/macos9-theme/install.sh --firefox` with Firefox closed) and live on-screen review; uncommitted; cleared `firefox` and `shared` claims (`nobody`).

## 2026-11-24, Antigravity (Gemini 4 Neon) — Firefox Lavender scrollbars via `userContent.css`

- Added Mac OS 9 Platinum Lavender (`#9999FF` thumb on `#CCCCCC` track) scrollbar styling for both web pages and Firefox browser chrome:
  - `firefox/chrome/platinum/content.css` & `firefox/chrome/userContent.css`: added `scrollbar-color: #9999FF #CCCCCC;` on `:root` gated on `@media (prefers-color-scheme: light) and (not (prefers-contrast)) and (not (forced-colors))` without `!important` so dark-mode and custom-scrollbar web apps keep their own styling.
  - `firefox/chrome/platinum/{palette.css,tabs-sidebar.css}`: applied matching `scrollbar-color: var(--m9-lav-light) var(--m9-surface-mid)` to browser chrome (including `#sidebar-container` / vertical tabs) inside the System-light-only `:root:not([lwtheme])` gate.
  - `firefox/profile_ops.py`: extended install, upgrade, conflict detection, symlink/type validation, backup metadata (backward-compatible with pre-`userContent.css` installs lacking `userContent_existed` / `installed_usercontent_block`), crash-safe journaling (`undo_hashes`, `before-uninstall`, `pre_usercontent_sha256`), and byte-for-byte undo to manage a marker-delimited `@import url("platinum/content.css");` block in `chrome/userContent.css`, deferring empty `chrome/` removal until after both `userChrome.css` and `userContent.css` undo finish.
  - `dev/firefox-m6/test_suite.py`: added coverage for `userContent.css` installation, `@import` ordering, post-install user-edit preservation, inner-marker conflict refusal, legacy pre-`userContent.css` upgrade / mid-upgrade rollback / direct undo, fault injection (`userContent`, `userContent_before_journal`, `uninstall_userContent`), and live `#9999FF` scrollbar pixel verification (`1,952` px in `dev/shots/firefox-m6-installed-live.png`).
  - Updated `firefox/README.md`, `README.md`, `docs/FINDINGS.md`, and `PLAN.md`.
- Checks: `python3 -I -m py_compile` clean; `tools/check-firefox-selectors.py` **PASS** (`35/35` `#id`, `1/1` `::part()`); `dev/check-firefox-m3.sh` **36/36 PASS** (`dev/build/firefox-m3.PJK7Dk`); `dev/check-firefox-m4.sh` **34/34 PASS** (`dev/build/firefox-m4.4TwSLt`); `dev/check-firefox-m5.sh` **32/32 PASS** (`dev/build/firefox-m5.WQPaxX`); `dev/check-firefox-m6.sh` **81/81 PASS** (`dev/build/firefox-m6.vB3b1T`); visually inspected `dev/shots/firefox-m6-installed-live.png`; host `~/.mozilla`, `~/.config/mozilla`, and `~/.local/state` untouched.
- Remaining: user reinstall (`/home/pieman/Files/Archive/projects/macos9-theme/install.sh --firefox` with Firefox closed) and live on-screen review; uncommitted; cleared `firefox` and `shared` claims (`nobody`).

## 2026-11-24, Codex (GPT-6.2) — audit Firefox desktop polish

Restricted sandbox cleanup to one filesystem and strengthened browser tests for the Go button, packaged logo and scrollbar preference restoration. All four affected suites passed (175 checks). See AUDIT.md #207–208. Changes are uncommitted.

## 2026-11-24, Antigravity (Gemini 4 Neon) — Firefox live-review polish (Go button, idle Firefox logo, classic 16 px scrollbars)

- Applied user desktop review refinements (keeping toolbar left-aligned per IE5):
  - `firefox/chrome/platinum/top-bands.css` & `bars-states.css`: unhid and styled Firefox's real clickable `.urlbar-go-button` as an IE5-inspired `▸ go` button (48×24 px, crisp original inline SVG, hover/pressed bevels, muted inactive state, RTL-safe logical positioning) in the right end of the Deep Lavender address band (`padding-inline: 68px 52px`, `#urlbar[open]` `width: calc(100% - 120px)`).
  - `firefox/chrome/platinum/status-activity.css`: replaced the idle activity orb with Firefox's built-in vector logo (`url("chrome://branding/content/about-logo.svg")`, centered `18px × 18px` inside the 24×24 sunken Platinum well; zero Mozilla artwork shipped in repo), keeping the animated Platinum Lavender barber-pole when loading (`:has(.tabbrowser-tab[selected][busy])`).
  - `firefox/profile_ops.py`: added classic 16 px full-width square non-overlay scrollbar prefs (`widget.gtk.overlay-scrollbars.enabled=false`, `widget.non-native-theme.scrollbar.style=4`, `widget.non-native-theme.scrollbar.size.override=16`, `widget.gtk.theme-scrollbar-colors.enabled=true`) to `DEFAULT_MANAGED_PREFS` (snapshotted on upgrade/install and restored in `prefs.js` on undo).
  - `dev/firefox-m3/{probe.py,verify.py}`, `dev/firefox-m4/{probe.py,verify.py}`, and `dev/firefox-m6/test_suite.py`: added automated checks for `.urlbar-go-button`, `about-logo.svg`, and scrollbar pref restoration, and unmounted `$rt/doc` FUSE mount in `run-live-p8.sh`'s exit trap (`fusermount3 -uz`).
  - Updated `firefox/README.md`, `docs/FINDINGS.md`, and `PLAN.md`.
- Checks: `tools/check-firefox-selectors.py` **PASS** (`35/35` `#id`, `1/1` `::part()`); `dev/check-firefox-m3.sh` **35/35 PASS** (`dev/build/firefox-m3.FtZmBb`); `dev/check-firefox-m4.sh` **34/34 PASS** (`dev/build/firefox-m4.wNy6RK`); `dev/check-firefox-m5.sh` **32/32 PASS**; `dev/check-firefox-m6.sh` **72/72 PASS** (`dev/build/firefox-m6.mNECuc`); visually inspected `dev/shots/firefox-polish-scroll-style4-btn.png`, `dev/shots/firefox-m3-cold.png`, and `dev/shots/firefox-m4-cold-1a.png`.
- Remaining: user reinstall (`/home/pieman/Files/Archive/projects/macos9-theme/install.sh --firefox` with Firefox closed) and on-screen check; uncommitted; cleared `firefox` and `shared` claims (`nobody`).

## 2026-11-24, Codex (GPT-6.2) — hold Firefox profile locks during install and undo

The stale-link exception requires a regular advisory lock file. Both advisory locks stay held through command completion. Installer suite 72/72, see audit #206.

## 2026-11-24, Codex (GPT-6) — accept stale local Firefox profile locks

Install and undo now proceed past a leftover loopback Firefox lock when its PID has exited and the advisory checks pass. Milestone 6 passed 68/68. See #205 in AUDIT.md.

## 2026-11-24, Codex (GPT-6) — add Firefox-only installer shortcuts

The root install and uninstall scripts accept `--firefox` as the first argument and forward the remaining options to the profile tools. Updated both READMEs and command help. The install/undo suite passed 64/64. Changes are uncommitted.

## 2026-11-24, Codex (GPT-6) — second Firefox audit

- Fixed RTL address-band layout, preference restoration across upgrade, backup verification and profile discovery. Prevented the test launcher from deleting existing profiles.
- Strengthened the archive selector checker and pixel evidence for focus and the installed-profile smoke test. The five suites passed 207/207. M2 regenerated eight mockups and four comparison sheets. See AUDIT.md #198–204 for evidence and limits.
- Changes are uncommitted. User desktop visual review is pending.

## 2026-11-24, Codex (GPT-6) — fix Firefox focus and profile restoration

- Corrected the inactive tab outline and the probe that masked it. An isolated Firefox negative control reproduced the previous solid outline.
- Fixed profile byte preservation, temporary directory ownership, state locking, cross-filesystem installs and interrupted install/undo recovery. Added regression coverage through the shell entry points.
- All five Firefox suites passed (199/199) on Firefox 160.0.1. See AUDIT.md #192–197. Changes are uncommitted. User visual review is pending.

## 2026-11-24, Codex (GPT-6) — port GTK 4 menus, dropdowns and lists

- Added light-mode GTK 4 menubar, popover menu, dropdown, list view and column header styling in `gtk/Platinum/gtk-4.0/menus-lists.css`. Generated filtered dropdown and header frames in both pixel densities and mirrored the dropdown cap for RTL.
- Extended the GTK 4 fixture and verifier to cover native actions, search, scrolling, sorting, inactive selections, the GTK Settings demo and both display scales. Passed 109/109 nested Wayland, 74/74 Broadway and 74/74 Broadway under ASan/UBSan. All five mandatory project suites and the icon suite passed. Details and the virtual compositor limitation are recorded in AUDIT.md.
- GTK changes are uncommitted. Next are notebook tabs, scales, progress bars and scrollbars. User visual review is pending.

## 2026-11-24, Antigravity (Gemini 4 Carbon) — Firefox Milestone 7 release check and audit (#189–191)

- Audited `firefox/`, `tools/check-firefox-selectors.py`, `dev/check-firefox-m*.sh`, and `README.md` over `ca8ac31`, fixing three pre-release findings before recording the Milestone 7 release check in `AUDIT.md`:
  - **#189 (P2):** Cleared `:focus-visible` / `:focus` `#6666CC` outlines across toolbar buttons, Favorites bar items, horizontal/vertical tabs, sidebar buttons, and Find bar controls under `&:-moz-window-inactive` in `firefox/chrome/platinum/bars-states.css` (previously cleared only on `#urlbar > .urlbar-background`), and added inactive outline checks to `dev/firefox-m4/{probe.py,verify.py}`.
  - **#190 (P3):** Added explicit `2 px` `#6666CC` `:focus-visible` focus rings on secondary tab, sidebar, and Find bar buttons in `firefox/chrome/platinum/{tabs-sidebar.css,bars-states.css}`, verified in `dev/firefox-m5/{probe.py,verify.py}`.
  - **#191 (P3):** Hardened `firefox/profile_ops.py` to detect inner-marker edits in `user.js` after an interrupted `user_js` install step and to unlink an empty post-undo `prefs.js` when `prefs.js` did not exist prior to installation; stabilized the live Wayland teardown check in `dev/firefox-m6/test_suite.py`; and added optional Firefox install/undo instructions and "Known limitations" to `README.md` and `firefox/README.md`.
- Checks:
  - Firefox suites: `tools/check-firefox-selectors.py` **PASS** (`35/35` `#id`, `1/1` `::part()` across 1,904 `omni.ja` files); `dev/check-firefox-m1.sh` **46/46 PASS** (`dev/build/firefox-m1.iJ3Ool`); `dev/check-firefox-m3.sh` **34/34 PASS** (`dev/build/firefox-m3.FopVHl`); `dev/check-firefox-m4.sh` **34/34 PASS** (`dev/build/firefox-m4.2VHMe7`); `dev/check-firefox-m5.sh` **31/31 PASS** (`dev/build/firefox-m5.6HXhws`); `dev/check-firefox-m6.sh` **41/41 PASS** (`dev/build/firefox-m6.235YJD`).
  - Shared project suites: `dev/check-style.sh` **135/135 PASS**, `dev/check-quick.sh` **29/29 PASS**, `dev/test_icons_phase1.py` **80/80 PASS**, `dev/test-install.sh` **727/727 PASS**.
  - Host `~/.mozilla`, `~/.config/mozilla`, and `~/.local/state` untouched; `bash -n`, `python3 -I -m py_compile`, and `git diff --check` clean.
- Remaining: user's approved live Firefox install (`/home/pieman/Files/Archive/projects/macos9-theme/firefox/install.sh` with Firefox closed) and on-screen review on their desktop. Cleared `firefox` and `shared` claims (`nobody`); `#189–191` fixes and `AUDIT.md` entry left uncommitted per `AGENTS.md` until requested.

## 2026-11-24, Antigravity (Gemini 4 Carbon) — Firefox Milestone 6 install and byte-for-byte undo

- Implemented **Firefox Milestone 6** (`docs/FIREFOX-PLAN.md` Milestone 6), separate from root `./install.sh`:
  - `firefox/install.sh`, `firefox/uninstall.sh`, and `firefox/profile_ops.py` (state under `$XDG_STATE_HOME/macos9-theme-firefox`, locked via `flock`).
  - Discovers profiles across both `$XDG_CONFIG_HOME/mozilla/firefox/profiles.ini` and `$HOME/.mozilla/firefox/profiles.ini`, prioritizing `[Install*]` `Default=` over `[Profile*]` `Default=1` (XDG over legacy `~/.mozilla`), warns when the installed Firefox major version is outside `firefox/version.json`, lists profiles, and requires selecting a single target profile (`--profile`, `--list`, `--dry-run`, interactive TTY prompt; refuses non-interactively without `--profile`).
  - Refuses while the profile is in use (`lock` dangling symlink/file via `lexists` or live POSIX `fcntl.lockf`/`flock` lock on `.parentlock`, while allowing closed profiles with an unlocked 0-byte `.parentlock`), refuses symlinks inside `chrome/`/`user.js`/`prefs.js` or repointed parent links, and journals a SHA-256-verified backup of `chrome/`, `user.js`, and `prefs.js` (plus per-pref snapshot) before mutating any profile file.
  - Installs `chrome/platinum/` atomically (displacing any pre-existing foreign `chrome/platinum`), inserts a marker-delimited `@import` block in `chrome/userChrome.css` right after any `@charset` and before `@namespace`/user rules, and appends a marker-delimited `user_pref` block in `user.js`.
  - Undo restores untouched files and modes byte for byte (including displaced foreign `chrome/platinum`), keeps later user edits outside markers and new session prefs in `prefs.js`, restores each managed pref's original value or absence directly in `prefs.js`, archives pre-uninstall snapshots in `~/.local/state/macos9-theme-firefox-uninstalled-*`, and refuses without overwriting on marker or `chrome/platinum/` conflicts.
  - Added `dev/check-firefox-m6.sh` + `dev/firefox-m6/test_suite.py` and updated `firefox/README.md`, `docs/FINDINGS.md`, `docs/DEVELOPMENT.md`, `docs/FIREFOX-PLAN.md`, and `PLAN.md`.
- Checks: `dev/check-firefox-m6.sh` (`dev/build/firefox-m6.jtZ6no`) **40/40 PASS** (fresh & customized profiles, PTY interactive selection, `--dry-run`, post-install user edits, conflict & symlink refusal, reinstall & pref-retiring upgrade, fault-injected mid-install/mid-uninstall crash recovery across all 7 step boundaries, `lock` symlink & live `.parentlock` `fcntl` lock, two-profile isolation & `[Install*]` precedence, XDG-only profile + untested version warning, live Firefox 160.0.1 nested-Wayland cold launch `dev/shots/firefox-m6-installed-live.png` + full post-session undo, and host `~/.mozilla`/`~/.config/mozilla`/`~/.local/state` untouched).
- Remaining: Milestone 7 (release check across all Firefox suites + `AUDIT.md` record, then user's on-screen review after an approved install). Cleared `firefox` and `shared` claims (`nobody`); uncommitted; nothing installed on live profile.

## 2026-11-24, Antigravity (Gemini 4 Neon) — Firefox Milestone 5 robustness (selector checker, version gate, 150%/200% scaling & keyboard focus)

- Implemented **Firefox Milestone 5** robustness tooling and checks per `docs/FIREFOX-PLAN.md`:
  - Added `firefox/version.json` recording the tested Firefox range (`160.0.1`, major `160..160`) and default `application.ini` / `omni.ja` paths (reusable by Milestone 6's `firefox/install.sh`).
  - Added `tools/check-firefox-selectors.py` to extract every `#id` and `::part()` selector from `firefox/chrome/**/*.css` (ignoring comments and declaration hex values), verify each against `/usr/lib/firefox/browser/omni.ja` and `/usr/lib/firefox/omni.ja` via `unzip` (handling MozJar exit code `2`), and enforce the Firefox major-version gate (`rc=0` pass, `rc=1` missing selector, `rc=3` untested major version unless `--allow-untested-version` is passed).
  - Fixed a real Firefox 160 selector mismatch caught on the checker's first run: replaced `#urlbar-searchmode-switcher` with `.searchmode-switcher` in `firefox/chrome/platinum/top-bands.css`.
  - Added the Milestone 5 verification suite (`dev/check-firefox-m5.sh`, `dev/firefox-m5/{probe.py,verify.py}`) covering the selector checker + 4 negative controls (`missing #id`, `missing ::part()`, untested major `999.0.1`, `--allow-untested-version`), 2 px `#6666CC` keyboard focus rings across `#urlbar`, toolbar buttons (with real Shift+Tab `ToolbarKeyboardNavigator`), bookmark items, horizontal `1A` tabs, vertical `1C` tabs, and Find bar input, plus live `150%` and `200%` output scaling in `2400×1600` nested `kwin_wayland --virtual` (`kscreen-doctor`).
  - Documented Milestone 5 findings and tooling in `docs/FINDINGS.md`, `docs/DEVELOPMENT.md`, `docs/FIREFOX-PLAN.md`, and `PLAN.md`.
- Checks: `dev/check-firefox-m5.sh` (`dev/build/firefox-m5.G42eT0`) **29/29 PASS** (`35/35` `#id` and `1/1` `::part()` selectors verified across 1,904 `omni.ja` files; `dpr=1.0/1.5/2.0` with zero clipped buttons/bookmarks, zero overlap, zero false overflow, and intact 16 px status band; host `~/.mozilla`/`~/.config/mozilla` untouched); regressions `dev/check-firefox-m3.sh` (`dev/build/firefox-m3.xMDvbW`) **34/34 PASS** and `dev/check-firefox-m4.sh` (`dev/build/firefox-m4.TxG0IM`) **34/34 PASS**; visually inspected `dev/shots/firefox-m5-{keyboard-focus,scale-150,scale-200}.png`.
- Remaining: user visual review of Milestone 5 renders, then Milestone 6 (`firefox/install.sh` + `firefox/uninstall.sh` with throwaway-HOME install/undo test suite). Cleared `firefox` and `shared` claims (`nobody`); uncommitted; nothing installed on live profile.

## 2026-11-24, Antigravity (Gemini 4 Neon) — Firefox Milestone 4 full browser chrome coverage

- Extended `firefox/chrome/platinum/` (`platinum.css` + 4 new modular sheets) to cover the complete Firefox chrome surface in Platinum Lavender:
  - `tabs-sidebar.css`: live-switchable `1A` slim 24 px horizontal Platinum tabs below Favorites (`#CCCCCC` inactive, `#EEEEEE` active, `#666666`/white pressed, `#6666CC` focus ring) and `1C` vertical Platinum tabs in the pinstriped left `#sidebar-container` (`sidebar.verticalTabs`), plus Platinum framing for both revamped `#sidebar-box` / `<sidebar-main>` variables and legacy (`sidebar.revamp=false`) `#sidebar-header` + `.sidebar-splitter`.
  - `status-activity.css`: locked `5A` permanent 16 px IE5 pinstriped bottom status band (`body::after`) with diagonal `#777777`/`#FFFFFF` corner size grip and live `#statuspanel` docked inside (suppressed cleanly in fullscreen and popup/mini windows), plus a pure-CSS neutral Platinum Lavender orb/barber-pole activity indicator (`#PanelUI-button::after`, driven by `:has(.tabbrowser-tab[selected][busy])`, respecting `prefers-reduced-motion`; zero Microsoft or Apple logos).
  - `menus-panels.css`: measured Platinum menubar (`#toolbar-menubar`/`#main-menubar`), context/dropdown `menupopup`s (`#DDDDDD`, `0 px` radius, 1 px `#000000` border, `#FFFFFF`/`#999999` bevel, `#222222` shadow, `#333399` Lavender highlight with `#6666CC`/`#000088` bevel and `#FFFFFF` text, `#888888`/`#FFFFFF` separators), Platinum `#appMenu-popup` / `#downloadsPanel` / `#widget-overflow` panels, and square `0 px`-radius Platinum `.urlbarView` autocomplete popup.
  - `bars-states.css`: Platinum Find bar (`findbar`), Notification bars (`notification-message`), real `:-moz-window-inactive` flattening (pinstripes flatten to `#DDDDDD`, address band mutes to `#8E8EB8`, labels mute to `#777777`, focus ring clears), clean delegation of Firefox 160's dark-purple Private Browsing windows (`prefers-color-scheme: dark`), compact single-row popup/chromeless/mini windows, and Platinum Customize Mode.
- Added Milestone 4 verification suite (`dev/check-firefox-m4.sh`, `dev/firefox-m4/{probe.py,verify.py}`) and documented Firefox 160 Private-window dark delegation, `:has()` activity indicator, and `::part(content)` panel framing in `docs/FINDINGS.md` and `docs/DEVELOPMENT.md`.
- Checks: `dev/check-firefox-m4.sh` (`dev/build/firefox-m4.SElfWo`) **34/34 PASS**; Milestone 3 regression `dev/check-firefox-m3.sh` (`dev/build/firefox-m3.CUcL8R`) **34/34 PASS**; `bash -n`, `python3 -I -m py_compile`, and `git diff --check` clean; visually inspected all 9 `dev/shots/firefox-m4-*.png` renders (refined idle activity indicator from a cross to a neutral Lavender orb after inspection).
- Remaining: user visual review of Milestone 4 renders, then Milestone 5 (robustness: `omni.ja` selector checker, version gate, 150%/200% scaling & keyboard focus checks) and Milestone 6 (`firefox/install.sh` + `firefox/uninstall.sh`). Cleared `firefox` and `shared` claims (`nobody`); uncommitted; nothing installed on live profile.

## 2026-11-24, Antigravity (Gemini 4 Neon) — Firefox Milestone 3 vertical slice (the three top bands)

- Implemented the **Firefox Milestone 3** modular `userChrome.css` vertical slice in `firefox/chrome/` (`userChrome.css`, `platinum/platinum.css`, `platinum/palette.css`, `platinum/top-bands.css`):
  - **Band 1 (42 px Pinstriped Button Toolbar):** exact KWin `#000000` → `#FFFFFF` top highlight join, whole-pixel 3-row `#DEDEDE`/`#CCCCCC`/`#E8E6E8` horizontal pinstripe, 56 px button pitch with centered labels beneath icons (pick `4A`), `#333399` enabled / `#9999CC` disabled Lavender icons, `#111111` enabled / `#777777` disabled labels, IE5-style dotted Lavender vertical separator, right-aligned account/extensions/menu group, measured Platinum `ToolNormal` hover bevel (`#666666`/`#333333`/`#FFFFFF`/`#888888` on `#CCCCCC`), measured pressed dark Platinum (`#666666` fill + `#FFFFFF` icon/label), and 2 px `#6666CC` keyboard focus ring.
  - **Band 2 (26 px Full-Width Deep Lavender Address Band, pick `2A`):** discrete 24-row `#1B1B52` → `#7A7AE0` → `#111138` tube between `#ADADAD` and `#000000` borders, crisp white `Address:` label block, 20 px white address field with 1 px `#000000` frame, measured 2 px `#6666CC` Platinum focus ring (`#urlbar:is([focused], :focus-within)`), `#CCCCFF` selection highlight, and opaque white Platinum `#urlbar[open]` autocomplete dropdown with `#333399` selected row.
  - **Band 3 (24 px Pinstriped Favorites Bar):** `#FFFFFF` top highlight meeting `#urlbar-container`'s `#000000` border directly, 3-row horizontal pinstripe, `#ADADAD` bottom edge, Lavender bookmark icons, and matching `ToolNormal` hover / `#666666` pressed / `#6666CC` focus states.
  - Scoped exclusively to System light normal-contrast mode (`@media (-moz-native-theme) and (prefers-color-scheme: light) and (not (prefers-contrast)) and (not (forced-colors))` + `:root:not([lwtheme])`) with Customize Mode, popup/chromeless/mini-window, and overflow guards.
- Added Milestone 3 verification suite (`dev/check-firefox-m3.sh`, `dev/firefox-m3/{probe.py,verify.py}`) and recorded Firefox 160 boolean `[focused]`/`[open]` and `#nav-bar` border-bottom findings in `docs/FINDINGS.md` and `docs/DEVELOPMENT.md`.
- Checks: `dev/check-firefox-m3.sh` (`dev/build/firefox-m3.MvJWGf`) **34/34 PASS** (26/26 exact Deep Lavender tube rows, 42 px toolbar + 26 px address + 24 px favorites whole-pixel pinstripe sampling on cold normal-launch `dev/shots/firefox-m3-cold.png`, hover/pressed pixel checks, `4,226` `#6666CC` focus-ring px + `5,557` `#CCCCFF` selection px, opaque `#urlbar[open]` dropdown, `520 px` real overflow, Customize Mode round-trip, theme/dark/HighContrast gating, host `~/.mozilla`/`~/.config/mozilla` untouched); `bash -n`, `python3 -I -m py_compile`, and `git diff --check` clean; visually inspected all 5 `dev/shots/firefox-m3-*.png` renders.
- Remaining: user visual review of Milestone 3 renders, then Milestone 4 (extending `firefox/chrome/platinum/` with `1A`+`1C` live-switchable tabs, permanent `5A` status band, activity indicator, menus/panels, find bar, notification/downloads bars, inactive/private/popup/fullscreen polish). Cleared `firefox` and `shared` claims (`nobody`); uncommitted; nothing installed on live profile.

## 2026-11-24, Antigravity (Gemini 4 Neon) — Firefox Milestone 2 visual mockups

- Implemented **Firefox Milestone 2** (`docs/FIREFOX-PLAN.md` Milestone 2) mockup generator in `dev/render-firefox-m2.sh` and `dev/firefox-m2/render_mockups.py`, plus `M9_NO_CLI_URL=1` multi-tab startup support in `dev/firefox-test.sh` (allowing `browser.startup.homepage` pipe-delimited offline tabs without `--marionette` or the `[remotecontrol]` urlbar stripe).
- Rendered **8 live cold-launch Firefox 160.0.1 mockups** inside nested `kwin_wayland --virtual` (Platinum KWin decoration, Platinum GTK 3 theme, 3 offline tabs, 5 Favorites bookmarks, IE5-style toolbar buttons with Lavender icons and dotted separator) and **4 crisp 1× comparison sheets** in `dev/shots/firefox-m2-*.png` covering all four visual design choices:
  - **Q1 (Tabs):** `1A` slim Platinum tabs below Favorites bar (`firefox-m2-1a-tabs-below-favs.png`), `1B` slim Platinum tabs above button toolbar (`firefox-m2-1b-tabs-above-toolbar.png`), `1C` vertical Platinum tabs in left sidebar (`firefox-m2-1c-tabs-vertical.png`).
  - **Q2 (Address-band Lavender ramp):** `2A` Deep Lavender Tube (IE5 luminance contrast, white `Address:`), `2B` Bright Progress-Bar Tube (`docs/REFERENCE.md` `#333399`–`#EEEEEE`, dark `Address:`), `2C` Soft Beveled Scroll-Box Lavender (`docs/REFERENCE.md` `#CCCCFF`/`#9999FF`/`#6666CC`).
  - **Q4 (Toolbar labels):** `4A` icons + text labels (42 px IE5 default) vs `4B` compact icons only (28 px).
  - **Q5 (Status bar):** `5A` permanent 16 px IE5 pinstriped status band with diagonal `#777777`/`#FFFFFF` size grip vs `5B` floating Platinum `#statuspanel` (0 px height cost at rest).
- Checks: `dev/render-firefox-m2.sh` exited `0` (all 8 mockups + 4 comparison sheets visually inspected, refined Q4 sheet crop cleanly to the Favorites bottom edge); `bash -n`, `python3 -I -m py_compile`, and `git diff --check` clean; host `~/.mozilla` / `~/.config/mozilla` untouched; cleared `firefox` and `shared` claims (`nobody`).
- User reviewed the Milestone 2 mockups (`00:58`) and locked all four choices in `docs/FIREFOX-PLAN.md` and `PLAN.md`: **Tabs `1A` + `1C`** (slim Platinum tabs below Favorites bar when horizontal, switching live to Platinum pinstriped vertical sidebar tabs via `sidebar.verticalTabs`), **Address band `2A`** (Deep Lavender Tube), **Toolbar `4A`** (42 px icons + text labels), and **Status bar `5A`** (permanent 16 px IE5 pinstriped status band with diagonal size grip).
- Next: start Milestone 3 (`firefox/chrome/` vertical slice: button toolbar, Deep Lavender address band, and Favorites bar).

## 2026-11-24, Antigravity (Gemini 4 Carbon) — Firefox Milestone 1 sandbox harness and chrome discovery

- Implemented **Firefox Milestone 1** (`docs/FIREFOX-PLAN.md` Milestone 1):
  - Added `firefox/README.md` (component scope and rules), `dev/firefox-test.sh` (headless nested `kwin_wayland --virtual` Firefox launcher with full `env -i` + isolated `HOME`/`XDG_*`/`XDG_RUNTIME_DIR`, Platinum KDecoration with `browser.tabs.inTitlebar=0`, Platinum GTK 3 theme, and throwaway deterministic Firefox profile), and the Milestone 1 verification suite (`dev/check-firefox-m1.sh`, `dev/firefox-m1/{probe.py,verify.py}`).
  - Verified normal `<profile>/chrome/userChrome.css` cold loading (`29,506` `#CCCCFF` pixels on `#PersonalToolbar`) and negative control (`0` pixels with `toolkit.legacyUserProfileCustomizations.stylesheets = false`), exact KWin Platinum SSD bottom border to `#navigator-toolbox` join (`#999999` → `#000000` → `#DDDDDD`/`#FFFFFF`, no doubled line or corner clipping), and zero host leakage (`~/.mozilla` absent, `~/.config/mozilla` untouched).
  - Recorded verified Firefox 160.0.1 (`browser.nova.enabled = true`) platform facts in `docs/FINDINGS.md`, `docs/DEVELOPMENT.md`, and `docs/FIREFOX-PLAN.md`:
    - Host `profiles.ini` lives at XDG `~/.config/mozilla/firefox/profiles.ini` where `[Install*]` `Default=` selects `*.default-release` over legacy `[Profile1]` `Default=1`; `omni.ja` uses MozJar headers (`unzip` exits `2` on header compensation).
    - Wrapping `#urlbar-container` via `flex-wrap: wrap` on `#nav-bar-customization-target` leaves a `104 px` right-side gap under `#PanelUI-button` and triggers false `OverflowableToolbar` `[overflowing]` at `1120 px`; reserving `padding-bottom: 26px` on `&:not([customizing]) #nav-bar` with `position: absolute; inset-inline: 0; bottom: 0` on `&:not([customizing]) #urlbar-container` renders a full-width 26 px Lavender address band with zero false overflow at `1120 px`, real button overflow at `520 px` (`5` items), clean Customize Mode round-trip, and working `gURLBar.focus()` + Shift+Tab `ToolbarKeyboardNavigator` focus.
    - All primary `.toolbarbutton-1` buttons populate light-DOM `.toolbarbutton-text` labels; `#tabbrowser-tabs[orient="vertical"]` stays light-DOM slotted inside `#vertical-tabs` when `sidebar.verticalTabs=true`; legacy `sidebar.revamp=false` remains functional and light-DOM stylable; `widget.non-native-theme.enabled=true` means `userChrome.css` must style chrome `<menupopup>`s and panels directly while Firefox already inherits GTK 3 `-moz-headerbar = #DDDDDD` and `SelectedItem = #CCCCFF`.
    - Under Nova (`browser.nova.enabled = true`), `firefox-compact-light@mozilla.org` and `firefox-compact-dark@mozilla.org` omit `[lwtheme]`, so `userChrome.css` must gate on `@media (-moz-native-theme) and (prefers-color-scheme: light) and (not (prefers-contrast)) and (not (forced-colors))` alongside `:root:not([lwtheme])`.
- Checks: `dev/check-firefox-m1.sh` (`dev/build/firefox-m1.zVJtP1`) **46/46 PASS**; regressions `dev/check-style.sh` **135/135 PASS**, `dev/check-quick.sh` **29/29 PASS**, `dev/test_icons_phase1.py` **80/80 PASS**; `bash -n`, `python3 -I -m py_compile`, and `git diff --check` clean; visually inspected all 11 `dev/shots/firefox-m1-*.png` renders.
- Remaining: user visual review of Milestone 1 renders and Milestone 2 sandbox mockups (tab placement, Lavender address-band ramp, toolbar labels vs icons-only, and status band); uncommitted in working tree; cleared `firefox` and `shared` claims (`nobody`).

## 2026-11-24, Codex (GPT-6) — re-audit GTK 4 button roles and verification

- Fixed #185–188 in the uncommitted Milestone 4 slice. Restored stock stack-switcher, linked-button and toolbar geometry and corrected disabled label colors.
- Extended the fixture and verifier with a live high-contrast round trip against GTK's own rendering, exact 1× and 2× indicator checks, explicit backdrop state coverage and stock composite comparisons. Rejected six injected defects. A separate Wayland pointer and keyboard run confirmed seven indicator crops and custom-button activation.
- Passed 78/78 Wayland, 56/56 Broadway and 56/56 Broadway with ASan/UBSan. Both backends matched all 36 reference crops. Project suites passed 135/135 Qt Widgets, 29/29 Qt Quick, 19/19 Plasma, 80/80 icons, 727/727 install and undo, and 40/40 nested live install.
- User visual review is pending. GTK 4 menus, dropdowns and lists remain the next batch.

## 2026-11-23, Codex (GPT-6.2 Sol) — fix the GTK 4 initial slice audit

- Fixed #181–184 in the GTK 4 controls and verification harness. Checkboxes and radios keep their artwork on hover, focus rings clear on inactive windows, and framed buttons with custom children use Platinum chrome. The harness checks default-button focus and standalone session completion.
- Wayland now verifies GSettings-only theme discovery and GTK's default 1× renderer. Passed 66/66 Wayland, 55/55 Broadway, 55/55 under ASan/UBSan, and 51/51 Wayland and 47/47 Broadway on GTK 3. All 36 reference crops still match exactly on both GTK 4 backends. Five injected faults were rejected.
- Project regressions passed 135/135 Qt Widgets, 29/29 Qt Quick, 19/19 Plasma, 80/80 icons, 727/727 install and undo, and 40/40 nested live install.
- The Milestone 4 fixes are uncommitted. User visual review and the remaining GTK 4 batches are pending.

## 2026-11-23, Antigravity (Gemini 4 Carbon) — independent audit of GTK Milestone 4 initial slice

- Independently audited Codex (GPT-6.2 Sol)'s uncommitted GTK Milestone 4 initial control slice over `733afcb` (`gtk/Platinum/palette.css`, `gtk/Platinum/gtk-3.0/gtk.css`, `gtk/Platinum/gtk-4.0/{gtk.css,controls.css,assets/}`, `gtk/gen-assets.py`, `dev/check-gtk4.sh`, `dev/gtk4-check/{fixture.c,session.sh,verify.py}`, `docs/GTK-PLAN.md`, `docs/FINDINGS.md`, and saved Wayland/Broadway/negative-control runs).
- Recorded **4 open findings** in `AUDIT.md` (`#181–183` P2, `#184` P3):
  - **#181 (P2):** Hovering checkboxes or radio buttons replaces Platinum sprites with Adwaita fills (`Default-light.css`'s `check:hover, radio:hover` `(0,1,1)` beats `checkbutton > check` / `> radio` `(0,0,2)` → borderless `#F2F2F2` square; `check:checked:hover, radio:checked:hover` and `:indeterminate:hover` `(0,2,1)` beat `controls.css` `(0,1,2)` → solid `#5D9DE9`→`#478FE6` Adwaita blue square; `456` differing indicator pixels in hover probe; `:hover` untested in `fixture.c`).
  - **#182 (P2):** `button.text-button...:focus-visible` (`controls.css:59`) and `checkbutton:focus:focus-visible` (`controls.css:169`) omit `:not(:backdrop)`, leaving `266` active `#6666CC` focus-ring pixels lit on inactive `:backdrop` windows (`fixture.c:341-364` only tested `:backdrop` while `selected` `GtkEntry` held focus).
  - **#183 (P2):** `dev/gtk4-check/session.sh:33-34,40,42` forces `GSK_RENDERER=cairo` in `plasma` mode (skipping GTK 4's default Wayland GPU renderer on the 36 1× crops, 1× gallery, and contrast round-trip), and `dev/check-gtk4.sh:23-28` pre-populates `gtk-theme-name=Platinum` in `gtk-4.0/settings.ini` on `plasma` (masking whether GSettings/portal alone selects `Platinum` on Wayland as stated in `docs/GTK-PLAN.md:56-57`).
  - **#184 (P3):** `button.text-button` (`controls.css:21-97`) misses ordinary framed `GtkButton`s built with custom child widgets (`gtk_button_new()` + `gtk_button_set_child()`, e.g., icon+label `GtkBox`), `fixture.c:356` omits keyboard focus on `default_button`, and standalone `verify.py` does not check `root / "complete"`.
- Verified passing checks: fresh `dev/check-gtk4.sh broadway` (`dev/build/gtk4-m4-broadway.bE9GAF`) **47/47**, saved Wayland `dev/build/gtk4-m4-plasma.wBIFUg` **52/52** (including `0` differing border pixels on 2× GPU-rendered `"Continue"`/`"Cancel"`/`"Disabled"`/entries in `scale-2/output.png`), `dev/gtk4-check/fixture.c` clean under `-Wall -Wextra -Werror` and `-fsanitize=address,undefined` ASan/UBSan, CSS parser error rejection verified without `GTK_DEBUG=css`, `dev/build/gtk4-m4-negative.ea0wBt` `49/52` (`rc=1`), dark-mode delegation (`#353535`) clean, `200` GTK 3 + `4` GTK 4 PNGs regenerate byte-identically, and `dev/check-gtk3.sh broadway` **47/47**.
- Audit-only changes (`AUDIT.md`, `CHANGELOG.md`); no implementation files modified, no claims held, `#95` remains open, no live install/commit/push.

## 2026-11-23, Codex (GPT-6.2 Sol) — start the named GTK 4 Platinum theme

- Published the terminal palette packaging checkpoint in `b34dcb0` and the GTK 3 Milestone 3 Batch 2 checkpoint in `733afcb` on `origin/main` before starting Milestone 4.
- Added `gtk/Platinum/gtk-4.0/` with framed text buttons, default buttons, entries, checks and radios. Both toolkits share `palette.css` and the measured artwork. Four generated GTK 4 variants preserve the normal and pressed button edges when GTK stretches them. The 200 GTK 3 PNGs regenerate byte for byte. The new theme delegates unported widgets, dark mode and high contrast to GTK's default styles.
- Added `dev/check-gtk4.sh` and `dev/gtk4-check/`. Named theme discovery passed 52/52 in virtual Wayland and 47/47 in Broadway with all 36 reference regions pixel-exact on each. Wayland verifies active and backdrop selection, Widget Factory against Adwaita, a high-contrast round trip, native 1.5× and 2× surface scales and unclipped compositor captures. Three deliberately corrupted results were detected.
- Project regressions passed 135/135 Qt Widgets, 29/29 Qt Quick, 19/19 Plasma crops, 80/80 icons, 727/727 install and undo, and 40/40 nested live install.
- Remaining are the GTK 4 menu, list, scroll and window-control batches and user visual review. Milestone 4 changes are uncommitted. The GTK installer is scheduled for Milestone 6.

## 2026-11-23, Antigravity (Gemini 4 Carbon) — verify GTK Milestone 3 Batch 2 audit and fixes (#177–180)

- Independently verified Codex (GPT-6.2 Sol)'s Milestone 3 Batch 2 audit and fixes (`#177–180`) in `gtk/Platinum/gtk-3.0/gtk.css`, `gtk/gen-assets.py` (100 procedural assets = 200 1× + `@2` PNGs, verified 200/200 byte-identical on clean regeneration), and `dev/gtk3-m3b2/{m3b2shot.c,verify.py}`. **Verdict: PASS (zero new findings).**
- Verified each fix and check:
  - **#177:** `min-width: 1px` / `min-height: 1px` on nonempty determinate fills prevents 0px `border-image` `Gtk-CRITICAL`s at tiny nonzero fractions (`0.001`); confirmed with an independent 80-combination ASan/UBSan progressbar matrix (`10` fractions `0.0..1.0` × horizontal/vertical × normal/inverted × LTR/RTL, `0` diagnostics) while keeping `progress-0` and `progress-55` pixel-exact.
  - **#178:** `progress-fill-reversed-{h,v}` + start-edge `:not(.left)`/`:not(.top)` rules preserve the measured divider and 3px cast shadow on inverted/RTL progress fills without spilling at `100%`, and `progressbar.vertical progress.pulse` clears `border-image: none` so the vertical barber-pole tile matches `progress-pulse-v.png` pixel for pixel.
  - **#179:** `m3b2shot.c` maps a real `GDK_WINDOW_TYPE_HINT_TOOLTIP` native `GtkTooltip` (`428×35` on Wayland, `73×168` wrapped on Broadway), exercises both vertical and horizontal Smart Scrolling stepper pairs via real GDK button events, routes a `GDK_SCROLL_DOWN` event through `gtk_widget_event()` in `overlay` mode, and advances indeterminate pulsing across 5 steps.
  - **#180:** `verify.py` enforces `session.log` presence, narrow CSD geometry/stripes + mapped `"Filter"` button bounds, and maximized CSD width/stripes; all 6 negative controls in `dev/build/m3b2-negative.8thkj49j` failed with `rc=1` on their exact injected faults.
- Suites & visual inspection: re-verified virtual Wayland `dev/build/gtk3-m3b2-plasma.EJiAYi` (**62/62 PASS**, visually inspected `meld-active.png`, `m3b2-tooltip.png`, `m3b2-csd-{active,backdrop,narrow}.png`, `m3b2-gallery-{active,backdrop}.png`, and `m3b2-chrome.png`), fresh Broadway `dev/build/gtk3-m3b2-broadway.kDQb5m` (**61/61 PASS**, **45/45** 1× reference crops at `0` differing pixels), `dev/build/gtk3-m3b2-broadway.brykYs` (**61/61 PASS**), `dev/build/m3b2-sanitizers.uwTiMK` (**61/61 PASS**), `dev/check-gtk3-m3b1.sh broadway` (**38/38 PASS**), `dev/check-gtk3.sh broadway` (**47/47 PASS**), `dev/gtk-discovery/test_verify.py` (**32/32 PASS**), `dev/check-style.sh` (**135/135 PASS**), `dev/check-quick.sh` (**29/29 PASS**), `dev/test_icons_phase1.py` (**80/80 PASS**), `index.theme`, `bash -n`, `py_compile`, and `git diff --check`.
- Next: GTK Milestone 3 is complete and cross-verified; ready for GTK Milestone 4 (plain GTK 4 port). Claims remain `nobody`; `#95` remains open; no live install, commit, or push.

## 2026-11-23, Codex (GPT-6.2 Sol) — audit and fix GTK Milestone 3 Batch 2

Fixed #177–180 in the GTK 3 stylesheet, progress asset generator and Batch 2 fixture/verifier. Tiny fills avoid zero-pixel border images, reversed fills keep their divider and shadow, and vertical activity bars show the barber pole. Verified native tooltips, both scrollbar orientations, overlay scroll input, animation and narrow/maximized headers. Fresh Wayland and Broadway runs passed 62/62 and 61/61. Both matched all 45 reference crops. Broadway ASan/UBSan, prior GTK checks and project regression suites passed. The work remains uncommitted. Batch 2 fractional-scale inspection and user visual review are pending. Claims released.

## 2026-11-23, Codex (GPT-6.2 Sol) — fix terminal palette audit findings

Fixed #173–176 in the terminal palette, uninstaller, README and installer tests. Restored light ANSI whites, increased normal-to-bright color separation, and protected palette files still selected by Kwi or a Konsole profile. Verified rendered ANSI samples in both apps. Install and undo passed 727/727, focused checks 26/26 and nested live install 40/40. Qt Widgets, Qt Quick and Plasma passed 135/135, 29/29 and 19/19. Changes remain uncommitted and user visual review is pending. Claims released.

## 2026-11-23, Antigravity (Gemini 4 Neon) — independent audit of Kwi/Konsole terminal palette and install/undo

- Independently audited Codex's uncommitted Platinum Lavender terminal palette and packaging (`extras/terminal/PlatinumLavender.colorscheme`, `scripts/common.sh`, `install.sh`, `uninstall.sh`, `dev/test-install.sh`) over `f1d6045` plus saved logs and Kwi previews (`dev/build/terminal-palette-*.log`, `dev/build/kwi-platinum.x77L3H/preview.png`, `dev/build/kwi-palette-missing.FZaJ5O/preview.png`).
- Recorded 4 open findings in `AUDIT.md` (`#173–174` P2, `#175–176` P3):
  - **#173 (P2):** ANSI `Color7` (`#555555`) and `Color7Intense` (`#676767`) are dark grays with nearly identical luminance to `Color1`–`Color6`, yielding `1.00:1–1.36:1` (`Color7`) and `1.29:1–1.79:1` (`Color7Intense`) contrast on colored ANSI backgrounds and `2.08:1` for `Color0` on `Color7` (making white-on-color and black-on-white TUI chrome unreadable).
  - **#174 (P2):** `uninstall.sh` silently deletes `PlatinumLavender.colorscheme` even while actively selected in Kwi (`kwiterminalrc`) or Konsole (`$data/konsole/*.profile`), leaving dangling config references (violating the `#75`/`#81`/`#110` `kept_packages` contract).
  - **#175 (P3):** Narrow normal-vs-bright separation across `Color1`–`Color6` (`ΔRGB` `14.0–30.6`) and `[ForegroundIntense]` duplicating `[Foreground]` without `Bold=true`.
  - **#176 (P3):** `uninstall.sh:703` summary omits the terminal palette, `README.md` does not document it, and `dev/test-install.sh` omits explicit displacement/empty-konsole-dir/upgrade/selected-scheme assertions.
- Checks: `bash -n`, `configparser` (31 sections), `kreadconfig6`, `git diff --check`, contrast/luminance audit, pixel verification of `kwi-platinum.x77L3H/preview.png` and `kwi-palette-missing.FZaJ5O/preview.png`, and 7 disposable-home `install.sh`/`uninstall.sh` edge-case runs using `M9_PREBUILT=$PWD/dev/build/test-home-live/prebuilt` (fresh install/undo + empty `konsole/` removal, active Kwi/Konsole selection reproduction of `#174`, blocking regular file at `$data/konsole`, pre-existing symlink displacement/restore, retargeted `$data/konsole` symlink refusal, displaced+edited+reinstalled history, and 15-target upgrade).
- Limits: full `dev/test-install.sh` (needs `../WhiteSur-icon-theme`) and virtual KWin (`dev/test-install-live.sh` / live Kwi/Konsole) cannot run inside this sandbox. Review edits only (`AUDIT.md`, `CHANGELOG.md`); no implementation files modified, no claims held, no live install/commit/push. Next: fix `#173–176` under `extras`/`packaging` claims and re-verify in Kwi/Konsole (including ANSI backgrounds) and `dev/test-install.sh`.

## 2026-11-23, Codex (GPT-6.2 Sol) — package the Platinum Lavender terminal palette

Install and upgrade copy the palette to the Konsole data directory used by Kwi and Konsole. The shared install record lets uninstall remove the installed copy, restore a displaced file and preserve user edits. Tests cover dry run, installation, reapplication, chosen Kwi scheme preservation and undo. Install/undo passed 706/706 and nested live install passed 40/40. Qt Widgets passed 135/135, Qt Quick 29/29 and Plasma 19/19. Changes are uncommitted. Claims released.

## 2026-11-23, Antigravity (Gemini 4 Carbon) — verify GTK 3 Batch 1 (#168–172) and implement GTK Milestone 3 Batch 2

- Independently verified Codex's Milestone 3 Batch 1 audit fixes (`#168–172`): fresh Broadway `dev/build/gtk3-m3b1-broadway.aT8Wl5` passed **38/38** (`dDAqMq` post-Batch 2 regression also **38/38**), Codex's Wayland evidence `dev/build/gtk3-m3b1-plasma.6iQhhk` verified **39/39** under `python3 -I -W error`, and visually inspected `dev/shots/gtk3-m3b1-{gallery-active,meld}.png`. Verdict: PASS (no new findings).
- Implemented **GTK Milestone 3 Batch 2** (`docs/GTK-PLAN.md` Milestone 3 remainder: notebook tabs & pane, scales/sliders with ticks, classic Smart Scrolling scrollbars + overlay scrollbar indicator, determinate & indeterminate barber-pole progress bars, Help Balloon tooltips, modal/message dialogs, and active/backdrop/narrow/maximized CSD headerbars):
  - Extended `gtk/gen-assets.py` from 47 to **98 procedural assets (196 1× + `@2` PNGs)** in `gtk/Platinum/gtk-3.0/assets/` generated directly from `style/platinum/{slices,sprites,progress,tabs}.h`, `platinumstyle.cpp`, and `decoration/platinum.cpp` (zero Apple files): `tab-pane`, `tab-{top,bottom}-{normal,active,pressed}` (`25×25`, `12/12` nine-slice), `scale-trough-{h,v}{,-disabled}`, `slider-thumb-{h,v}{,-pressed,-disabled}`, `scale-tick-{h,v}`, `vscroll`/`hscroll` troughs/thumbs/grips/steppers, `progress-trough-{h,v}`, `progress-fill{,-full}-{h,v}`, `progress-pulse-{h,v}`, `tooltip-balloon`, `modal-frame`, `headerbar-stripes`, and `titlebutton-{close,maximize,minimize}{,-pressed}` + `titlebutton-backdrop`.
  - Extended `gtk/Platinum/gtk-3.0/gtk.css` with all Batch 2 rules, including authentic Mac OS 9 Smart Scrolling stepper placement (`-GtkScrollbar-has-backward-stepper: false; -GtkScrollbar-has-secondary-backward-stepper: true; -GtkScrollbar-has-forward-stepper: true;`), GTK 3.24 reverse-ordered `box-shadow` layers for scrollbar thumb and determinate progress shadows, `progressbar trough.empty progress { border-image: none; }` zero-width `Gtk-CRITICAL` guard, cohesive `:backdrop` scrollbar muting, `.overlay-indicator` lavender pill, Help Balloon `tooltip`, `.platinum-modal-frame` / `messagedialog`, and CSD `headerbar` / `.titlebar` / `.titlebutton` active pinstripes + flat `:backdrop`.
  - Added Milestone 3 Batch 2 verification suite (`dev/check-gtk3-m3b2.sh`, `dev/gtk3-m3b2/{m3b2shot.c,verify.py}`) testing 45 fixed-geometry 1× reference crops, natural-size gallery clipping & focus & real `button.down`/`button.up` stepper clicks, separate `GTK_OVERLAY_SCROLLING=1` indicator probe, `GtkTooltip` balloon, `GtkMessageDialog`, CSD active/backdrop/narrow/maximized headerbars, and real GTK 3 app `/usr/bin/meld` (including CSD headerbar chrome check on Wayland).
- Checks: `dev/check-gtk3-m3b2.sh broadway` (`dev/build/gtk3-m3b2-broadway.C6gOzS`) **57/57 PASS** (**45/45** 1× reference crops at 0 differing pixels, `0` CSS/gadget/Gtk-CRITICAL errors, `m3b2shot.c` clean under `cc -Wall -Wextra -Werror` and `-fsanitize=address,undefined` ASan/UBSan); regressions `dev/check-gtk3-m3b1.sh broadway` **38/38**, `dev/check-gtk3.sh broadway` **47/47**, `dev/gtk-discovery/test_verify.py` **32/32**, `dev/check-style.sh` **135/135**, `dev/check-quick.sh` **29/29**, `dev/test_icons_phase1.py` **80/80**, plus `bash -n`, `py_compile`, `index.theme`, and `git diff --check` clean; visually inspected all 11 `dev/shots/gtk3-m3b2-*.png` renders.
- Remaining: user-terminal run of `/home/pieman/Files/Archive/projects/macos9-theme/dev/check-gtk3-m3b2.sh plasma` for virtual KWin Wayland verification (real window deactivation backdrop + Meld Wayland CSD headerbar capture) and independent Codex audit before Milestone 4 (plain GTK 4 port). Cleared `gtk` and `shared` claims (`nobody`); `#95` remains open; no live install, commit, or push.

## 2026-11-23, Codex (GPT-6.2 Sol) — add Platinum Lavender for Kwi

Added `extras/terminal/PlatinumLavender.colorscheme` with a measured Platinum pane background, Lavender blue and an original ANSI palette tuned for the light canvas. Kwi loaded the scheme from the disposable Konsole data directory and rendered all 16 normal and bright ANSI colors in nested KWin. The foreground entries have at least 4.80:1 contrast against the default canvas. The palette is a standalone file and user visual review is pending.

## 2026-11-23, Codex (GPT-6.2 Sol) — audit and fix GTK 3 Milestone 3 Batch 1

Fixed #168–172 in the GTK 3 CSS and Batch 1 harness. TreeView has a visible keyboard cursor, GTK menu overflow arrows have usable dimensions, and the fixtures exercise native sorting, mapping, ListBox selection, clipping and scale. Meld's window identity and rendered style are verified in virtual KWin. Wayland passed 39/39 and Broadway passed 38/38, with 27 pixel-exact reference crops on each. Milestone 1, Milestone 2 and all project regression suites passed. Batch 2 and user visual review remain pending. GTK changes are uncommitted. Claims released.

## 2026-11-23, Antigravity (Gemini 4 Neon) — align Firefox plan status with IE5-inspired fidelity target

- Cleaned up remaining stale references to required IE5 VM captures and the old milestone numbering in `PLAN.md` (status block + `firefox` Claims row) and `docs/FIREFOX-PLAN.md` (measured-values note + open question 2 pointing to Milestone 2 mockups) so the docs consistently reflect the user's clarification: inspired by IE5 for a Mac OS 9 Platinum look and feel, not a 1:1 clone, with further IE5 captures optional.
- Checks: `git diff --check` clean; Claims rows remain `nobody`; no Firefox code written, launched, installed, or committed.
- Next: user confirmation to start Milestone 1 (sandboxed Firefox harness + DOM discovery) and Milestone 2 (visual mockups for tab placement, Lavender address-band shade, toolbar labels, and status bar).

## 2026-11-23, Antigravity (Gemini 4 Neon) — verify Milestone 2 (#163–167) and implement GTK Milestone 3 Batch 1

- Independently verified Codex's Milestone 2 fixes (`#163–167`): fresh Broadway `dev/build/gtk3-m2-broadway.CItwPl` passed **47/47**, Codex's Wayland evidence `dev/build/gtk3-m2-plasma.lM80bV` verified **51/51** under `python3 -I -W error`, and visually inspected `gtk3-output-{150,200}.png`. Verdict: PASS (no new findings), clearing Milestone 3 to start.
- Implemented **GTK Milestone 3 Batch 1** (menus, menu bar, pop-ups/comboboxes, treeview/list headers + disclosure triangles + active/backdrop selection, sunken scrolledwindow frame, etched group boxes, and separators):
  - Extended `gtk/gen-assets.py` from 24 to **47 procedural assets (94 1× + `@2` PNGs)** in `gtk/Platinum/gtk-3.0/assets/`, including an original procedural 9×8 geometric menu checkmark (avoiding any font-glyph copy from `style/platinum/menu.h`), 9-slice pop-up frames (`popup-frame-{normal,disabled,pressed}`) paired with 14×10 `popup-arrows-*` painted on `combobox button.combo arrow`, sorted/normal list headers, disclosure triangles, sunken frame, and etched group box frame.
  - Extended `gtk/Platinum/gtk-3.0/gtk.css` for all Batch 1 controls, including explicit `menubar > menuitem label { color: inherit; }` and the verified GTK 3.24 `treeview.view:backdrop { border-color: #999999; }` invalidation rule so `treeview.view:selected:backdrop` mutes cleanly to `#DCDCEF` (recorded in `docs/FINDINGS.md`).
  - Added Milestone 3 Batch 1 harness (`dev/check-gtk3-m3b1.sh`, `dev/gtk3-m3b1/{m3b1shot.c,verify.py}`) with 27 fixed-geometry 1× Mac OS 9.2.2 reference crops at tolerance 0, natural-size gallery checks (clipping, open `GtkMenu`, `#CCCCFF`/`#DCDCEF` active/backdrop TreeView selection), and real GTK 3 application smoke/CSS validation with `/usr/bin/meld`.
- Checks: `dev/check-gtk3-m3b1.sh broadway` (`dev/build/gtk3-m3b1-broadway.7nEom3`) **34/34 PASS** (**27/27** reference crops at 0 differing pixels, `meld` `status=PASS css_err=False`); Milestone 2 regression `dev/check-gtk3.sh broadway` (`dev/build/gtk3-m2-broadway.ZO2cFV`) **47/47 PASS**; Milestone 1 `dev/gtk-discovery/test_verify.py` **32/32 PASS**; `bash -n`, `py_compile`, `index.theme`, `cc -Wall -Wextra -Werror`, and `git diff --check` clean; visually inspected all `dev/shots/gtk3-m3b1-*.png` renders.
- Remaining: user-terminal run of `/home/pieman/Files/Archive/projects/macos9-theme/dev/check-gtk3-m3b1.sh plasma` for real Wayland backdrop deactivation and `meld` Wayland screenshot, then independent Codex audit / Milestone 3 Batch 2 (notebook tabs, scales, classic+overlay scrollbars, progress bars, tooltips, dialogs, CSD headerbars). Cleared `gtk` and `shared` claims (`nobody`); `#95` remains open; no live install, commit, or push.

## 2026-11-23, Antigravity (Claude Opus 5.5) — Firefox theme plan

- Added `docs/FIREFOX-PLAN.md` for decision 14 (optional IE5 Mac-style Firefox theme in Platinum Lavender). It records the target (Firefox 160.0.1, `userChrome.css` only), the measured IE5 bands from `reference/ie5-window-blank.png` (toolbar y=185–226 with a 3-row `#DEDEDE`/`#CCCCCC`/`#E8E6E8` pinstripe, 26-row teal address tube with every row value, favorites bar y=253–276, Explorer-bar strip, status band, label and icon colors, 56 px button pitch), the IE5 captures still needed, seven milestones, an install/undo contract and five open questions for the user.
- Checked from the installed `omni.ja`: `#nav-bar`, `#urlbar-container`, `#PersonalToolbar`, `#TabsToolbar`, `#sidebar-box`, `#statuspanel` exist in 160.0.1; `<sidebar-main>` is shadow DOM exposing only `part="overflow-button"` and CSS variables, so IE-style rotated Explorer-bar tabs on the new sidebar launcher are not possible through userChrome. Not yet verified in a running Firefox.
- No Firefox profile folder was visible from the agent sandbox (`~/.mozilla`, `~/.config/mozilla`); recorded as open question 3, possibly a sandbox limit.
- Edited only `docs/FIREFOX-PLAN.md` (new), the PLAN.md status block, decision 14 and firefox/shared Claims rows (claimed for the session, now `nobody`), and this entry. No code, nothing installed, nothing committed, no Firefox launched. Scratch crops in the agent's own scratch folder only.
- User clarification (19:36): the Firefox theme is **inspired by IE5, not a 1:1 clone**; go as far as `userChrome.css` allows. Added this to PLAN.md decision 14 and a "Fidelity target" section in `docs/FIREFOX-PLAN.md`: Platinum colors and bevels stay exact from REFERENCE.md, IE5 is a layout guide with no pixel comparison against it, Firefox features get a Platinum treatment instead of being hidden, IE5 captures are optional. Milestone 2 is now sandbox mockups instead of captures.
- Next: the user answers the open questions (tabs, address-band ramp, which profile, toolbar labels, status band), partly through milestone 2 mockups; milestone 1 (sandboxed Firefox harness and DOM discovery) needs the firefox and shared claims.

## 2026-11-23, Codex (GPT-6.2 Sol) — audit and fix GTK 3 Milestone 2

Fixed findings #163–167 in `dev/check-gtk3.sh` and `dev/gtk3-check/`. The chrome fixture hides its caret, Wayland validates compositor output at 150% and 200%, and the verifier rejects incomplete or mismatched evidence. Native Tab traversal and GTK's default-button class exercise the natural dialog. The runner validates the packaged assets in place. Wayland passed 51/51 and Broadway passed 47/47, including 36 pixel-exact reference crops per backend. Milestone 1 and all project regression suites passed. User review of the disposable renders is pending. The GTK work remains uncommitted. Claims released.

## 2026-11-23, Antigravity (Gemini 4 Neon) — GTK Milestone 2 vertical slice (GTK 3 Platinum dialog)

- Implemented the Milestone 2 GTK 3 named theme in `gtk/Platinum/` (`index.theme`, `gtk-3.0/gtk.css`, `gtk/gen-assets.py`, and 24 procedurally generated 1× + `@2` PNG assets in `gtk/Platinum/gtk-3.0/assets/` derived from `style/platinum/{slices,sprites}.h` and `docs/REFERENCE.md`):
  - Covers window/dialog surface (`#DDDDDD`), normal/pressed/disabled/focused push buttons, normal/pressed/disabled/focused default buttons (`.default`, `.suggested-action`), unfocused/focused/disabled/backdrop text entries with `#CCCCFF` active selection and muted `#DCDCEF` backdrop selection, and checkboxes/radio buttons across off/on/mixed/pressed/disabled/focused states.
  - Zero Apple files; 100% original CSS and generated geometry; verified `background-color` + `background-clip: padding-box` with transparent corner cut-outs in `border-image` (GTK 3.24 ignores the CSS `fill` keyword on `border-image`).
- Added Milestone 2 verification suite (`dev/check-gtk3.sh`, `dev/gtk3-check/{gtk3shot.c,verify.py}`) testing normal named-theme discovery, zero CSS parse errors, 36 fixed-geometry 1× reference crops (`tools/compare.py diff --tolerance 0`), and a separate natural-size dialog checking clipping, hit areas, `#CCCCFF` active selection, muted backdrop selection without focus ring, and `#6666CC` keyboard focus on entry/button/checkbox/radio.
- Checks: `dev/check-gtk3.sh broadway` (`dev/build/gtk3-m2-broadway.Tk69OL`) passed **46/46** (**36/36** Mac OS 9.2.2 reference crops at 0 differing pixels); Milestone 1 `dev/gtk-discovery/test_verify.py` **32/32**; `index.theme`, `bash -n`, `py_compile`, and `git diff --check` clean; visually inspected all `dev/shots/gtk3-m2-*.png` captures.
- Remaining before Codex Milestone 2 audit: user-terminal run of `/home/pieman/Files/Archive/projects/macos9-theme/dev/check-gtk3.sh plasma` for native Wayland real deactivation, `HighContrast` round-trip, and `kscreen-doctor` 150%/200% scaling. Cleared `gtk` and `shared` claims (`nobody`); `#95` remains open; no live install, commit, push, or Milestone 3 work.

## 2026-11-23, Antigravity (Gemini 4 Neon) — independent review of Codex #158–162 fixes

- Independently reviewed Codex's `#158–162` fixes across `dev/gtk-discovery.sh`, `dev/gtk-discovery/session.sh`, `dev/gtk-discovery/verify.py`, `dev/gtk-discovery/test_verify.py`, and `docs/FINDINGS.md` (working tree over `edd3e81`).
- Checks: `python3 -I -W error dev/gtk-discovery/test_verify.py` **32/32 PASS**; `python3 -I -W error dev/gtk-discovery/verify.py dev/build/gtk-discovery-plasma.celTLF plasma dev/shots` **41/41 PASS**; fresh sandbox `dev/gtk-discovery.sh broadway` (`dev/build/gtk-discovery-broadway.NIfyvB`) **38/38 PASS** (`3` Wayland-only blocked); `tools/compare.py diff --tolerance 0` (`celTLF` vs `eRqVbl`) **0 differing pixels** across all 5 PNGs; `git diff --check`, `bash -n`, and `py_compile` clean.
- **Verdict:** No new findings (`#158–162` verified); Milestone 1 is cleared to proceed to Milestone 2 (`docs/GTK-PLAN.md`). Review edits only (`AUDIT.md`, `CHANGELOG.md`); no claims held; `#95` remains open; no live install, commit, or push.

## 2026-11-23, Codex (GPT-6.2 Astra) — fix GTK Milestone 1 discovery verification

Fixed and verified #158–162 in the discovery launcher, session, verifier and regression suite. The changes capture the active FFmpeg window under virtual KWin, match both screenshots, check ordered preference changes, verify both GTK 4 styles after global-theme reapply, and select verified positive controls. Updated AUDIT.md, PLAN.md and docs/FINDINGS.md. Fresh virtual Wayland passed 41/41, Broadway passed 38 applicable checks and the regression suite passed 32/32. Qt Widgets, Quick, Plasma, install/undo and nested live-install suites passed 135/135, 29/29, 19/19, 702/702 and 40/40 respectively. FFmpeg coverage is startup and appearance in a disposable session. The GTK discovery work remains uncommitted. Milestone 2 starts with the measured GTK 3 dialog. Claims released.

## 2026-11-23, Codex (GPT-6) — re-audit GTK Milestone 1

Recorded findings #158–162 in AUDIT.md and updated the PLAN.md handoff. Both fresh disposable Wayland runs returned 40 pass and 1 fail at FFmpeg window identification. A disposable copy forcing Qt stderr logging restored the window evidence and passed 41/41. Fresh Broadway returned 38 pass with three Wayland exclusions. Gemini's suite passed 20/20 on known-good evidence. Six independently modified evidence copies incorrectly passed 41/41. Verified #156–157 and reproduced the named-theme and portal observations. The uncommitted GTK plan, discovery harness and findings remain in the working tree. The discovery fixes and a passing native re-test are next, before Milestone 2. Claims are clear. No implementation changes, install, commit or push.

## 2026-11-23, Antigravity (Gemini 4 Neon) — fix GTK Milestone 1 audit findings #153–157

- Fixed all five findings from Codex's independent Milestone 1 audit (`AUDIT.md` `#153–157`) in `dev/gtk-discovery.sh`, `dev/gtk-discovery/session.sh`, `dev/gtk-discovery/verify.py`, `docs/FINDINGS.md`, and `AUDIT.md`, and added negative-control test suite `dev/gtk-discovery/test_verify.py`:
  - `#153`: recorded full `STEP 0..6` source/backend/frontend trace (`portal-trace.log`, adding Step 6 `setGtkTheme(DiscoveryKde)` return to baseline) and `broadway-trace.log`; tightened `verify.py` to assert ordered transitions, `adw` `purple(7)/rgb(145,65,172) → blue(0)/rgb(53,132,228) → purple(7)/rgb(145,65,172)`, return to baseline on all stacks, and explicit `prefer_dark=0_all_rows(gtk3-portal-limitation)` vs missing field.
  - `#154`: removed synthetic `KGlobalSettings.notifyChange` calls; logged `SETGTKTHEME_RC`/`LNF_APPLY_RC`/`LNF_REAPPLY2_RC` and `kdedefaults/package` + `kreadconfig6 LookAndFeelPackage`; split KDE verification into `kded6-setGtkTheme-files`, `platinum-lnf-reapply`, and `platinum-lnf-reapply-user-gtk4` asserting `RC=0`, active `platinum.desktop`, zero symlinks, 5 stores, Platinum `colors.css`, and preserved user `gtk-4.0/gtk.css` rule + `@import`.
  - `#155`: tied FFmpeg capture to KWin's live `workspace.windowList()` + `getWindowInfo` (`ffmpeg-window.log`), D-Bus owner PID (`com.github.pieman.FFmpegConverterGTK`), exact active settings (`ACTIVE_GTK_THEME='DiscoveryKde'`), `1024x768` size, non-identity with stock PNGs, window-rect light chrome + rendered purple pixels, optional `spectacle -a` active capture, and `visual_review=manual-inspection-required`.
  - `#156`: fixed `dev/gtk-discovery.sh` incomplete-session guard to exit `1` when `session_rc=0` and `$root/complete` is absent.
  - `#157`: corrected `docs/FINDINGS.md` and `AUDIT.md` (GTK 3 `prefer_dark=0`, `Qn9Pwd` HighContrast `#272C2E`, `AdwStyleManager` `#9141AC` vs rendered Convert fill `#C69ED3` at `(900,620)`, and exact FFmpeg launch theme).
- Checks: user-terminal `dev/gtk-discovery.sh plasma` (`dev/build/gtk-discovery-plasma.eRqVbl`) passed **41/41** (`0` fail, `0` blocked; visually inspected `dev/shots/gtk-discovery-ffmpeg-{active,plasma}.png`); `dev/gtk-discovery.sh broadway` (`dev/build/gtk-discovery-broadway.7Wt0cn`) passed **38/38** (`3` Wayland-only blocked); `python3 -I -W error dev/gtk-discovery/verify.py ...` and `python3 -I -W error dev/gtk-discovery/test_verify.py` (directly against `eRqVbl` + `7Wt0cn`) passed **20/20** with zero deprecation warnings.
- Ready for independent Codex Milestone 1 re-audit before Milestone 2. Cleared `gtk` and `shared` claims (`nobody`); `#95` remains open; no install, commit, push, or Milestone 2 work.

## 2026-11-23, Codex (GPT-6) — independent GTK Milestone 1 audit

Recorded #153–157 in AUDIT.md and updated the PLAN.md handoff. Fresh disposable Wayland and Broadway runs reproduced Gemini’s counts (38 passes and 35 passes respectively, three Broadway exclusions). Four screenshot comparisons differed by zero pixels. Three independent negative controls still produced 38/38 and the incomplete-session branch returned success. Gemini owns the next Milestone 1 corrections when claimed. Implementation and prior uncommitted handoff files remain in the working tree. No install, commit, push or Milestone 2 work. Both audit claims released.

## 2026-11-23, Antigravity (Gemini 4 Neon) — record GTK Milestone 1 plasma/Wayland results (Milestone 1 implementation handoff for Codex)

- Fixed `AdwApplication` Wayland startup in `dev/gtk-discovery/fixture.c` (using `g_application_run()`/`activate`) and set `GSK_RENDERER=cairo` in `plasma` mode (`dev/gtk-discovery/session.sh`), resolving the `radv` Wayland Error 71 seen in `dev/build/gtk-discovery-plasma.VaXL6F`.
- Recorded the user's completed disposable virtual KWin Wayland run (`dev/build/gtk-discovery-plasma.dxtZOy`, 0 blocked) in `docs/FINDINGS.md`, `AUDIT.md`, and `PLAN.md`:
  - Proved that on native Wayland (`GdkWaylandDisplay`), GSettings (`org.gnome.desktop.interface gtk-theme`, default `'Adwaita'`) overrides `settings.ini` for both GTK 3 and plain GTK 4 (whereas Broadway uses `settings.ini` and ignores GSettings), making GSettings restoration mandatory in Milestone 6.
  - Confirmed both `org.freedesktop.impl.portal.desktop.kde` and `org.freedesktop.impl.portal.desktop.gtk` activate cleanly after `dbus-update-activation-environment`, exposing all four `org.freedesktop.appearance` keys (`accent-color=(0.8,0.8,1.0)`, `color-scheme=2`, `contrast=0`, `reduced-motion=0`).
  - Verified live preference updates on already-running Wayland apps: `AdwApplication` switched `adw_dark` `0→1→0` (`BreezeDark`↔`Platinum`), mapped Platinum's `#CCCCFF` accent to **`purple` (`ADW_ACCENT_COLOR_PURPLE = 7`, `rgb(145,65,172)`)**, and toggled `adw_hc` `0→1→0`; plain GTK 4 received live `color-scheme`, `contrast`, and `setGtkTheme`; GTK 3 switched live to `HighContrast` and `DiscoveryGSettingsLive`; `ffmpeg-converter-gtk` rendered cleanly (`dev/shots/gtk-discovery-ffmpeg-plasma.png`) with `purple` on "Convert" and no breakage from KDE's `gtk-4.0/{gtk,colors}.css`.
- Updated `dev/gtk-discovery/session.sh` (setting GSettings alongside `settings.ini` in conflict trials) and `dev/gtk-discovery/verify.py` (enforcing backend-accurate GSettings vs `settings.ini` expectations). User re-ran `/home/pieman/Files/Archive/projects/macos9-theme/dev/gtk-discovery.sh plasma` (`dev/build/gtk-discovery-plasma.Qn9Pwd`): **`VERDICT=PASS pass=38 fail=0 blocked=0`**. Cleared all claims (`nobody`); `#95` remains open; stopped at Milestone 1 ready for independent Codex audit.

## 2026-11-23, Antigravity (Gemini 4 Neon) — GTK Milestone 1 discovery probe (Milestone 1 implementation handoff for Codex)

- Upgraded and completed the Milestone 1 discovery harness (`dev/gtk-discovery.sh`, `dev/gtk-discovery/fixture.c`, `dev/gtk-discovery/session.sh`, `dev/gtk-discovery/verify.py`) to verify pre-write `HOME`/`XDG_*`/`dconf` isolation, run distinct per-store (`settings.ini`, GSettings, XSettings) and isolated/competing per-layer CSS trials (`#probe` + independent `#ind-theme`/`#ind-app`/`#ind-user` indicators), watch live preference changes on already-running fixtures (`--watch`), inspect every file/symlink/`@import` written by `kded6` before/after `setGtkTheme` and `plasma-apply-lookandfeel -a platinum.desktop`, and compute an observed-result verdict (`verify.py`) instead of trusting script completion.
- Executed `dev/gtk-discovery.sh broadway` (`dev/build/gtk-discovery-broadway.bT4yG8`): **35 PASS, 0 FAIL, 3 BLOCKED** (`VERDICT=PARTIAL_BROADWAY_ONLY`), zero C compiler warnings (`-Wall -Wextra`), zero CSS parse errors, and saved three visually verified stock screenshots (`dev/shots/gtk-discovery-stock-{gtk3,gtk4,adw}.png`). Recorded verified GTK 3.24.52 / GTK 4.24.1 / libadwaita 1.10.0 / `kde-gtk-config` 6.8.3 findings in `docs/FINDINGS.md` and the full per-toolkit results table in `AUDIT.md`.
- Verified `dev/gtk-discovery.sh plasma` is blocked inside this sandbox (`dbus-run-session: failed to exec 'kwin_wayland': Operation not permitted`, logged in `dev/build/gtk-discovery-plasma.JhcHCt/session.log`). Remaining 3 blocked checks (native Wayland, dual KDE/GTK Settings portal backends + live preference trace, `ffmpeg-converter-gtk`) await a user-terminal run of `/home/pieman/Files/Archive/projects/macos9-theme/dev/gtk-discovery.sh plasma` and independent Codex audit.
- Cleared `gtk` and `shared` claims (`nobody`), kept `#95` open, preserved uncommitted working-tree files, and stopped at Milestone 1 (no live desktop changes, commits, pushes, or Milestone 2 work).

## 2026-11-23, Codex (GPT-6) — GTK discovery handoff

Uncommitted probe files: dev/gtk-discovery.sh, dev/gtk-discovery/session.sh and dev/gtk-discovery/fixture.c. All three binaries built. The sandbox denied the private D-Bus socket bind. The permission retry was canceled. Gemini takes the next implementation session and Codex reviews the result.

## 2026-11-23, Antigravity (Gemini 4 Neon) — verify revised GTK plan (#148–152)

- Re-read revised `docs/GTK-PLAN.md` and verified all five findings (`#148–152`) are resolved with no additional plan issues; cross-checked starter Milestone 2 crops against `dev/check-style.sh` (6/6 exact) and confirmed `kscreen-doctor` and `dbus-update-activation-environment` are installed on the host.
- **Verdict:** Milestone 1 is cleared to start (standalone discovery & portal baseline). Plan review only; `docs/GTK-PLAN.md` and implementation files untouched, `#95` open, no claims held.

## 2026-11-23, Codex (GPT-6) — incorporate Gemini GTK audit

Revised docs/GTK-PLAN.md for all five findings (#148–152), with a standalone discovery gate and explicit recovery requirements before GTK selection. Updated the handoff and audit summary. Only documentation changed. Runtime checks await implementation.

## 2026-11-23, Antigravity (Gemini 4 Neon) — independent audit of GTK implementation plan

- Independently audited working-tree `docs/GTK-PLAN.md` (without modifying `docs/GTK-PLAN.md` or any implementation file) and verified Codex's `#144–147` against repository code (`install.sh`, `uninstall.sh`, `scripts/common.sh`, `scripts/icon_prefs.py`, `dev/test-install-live.sh`, `dev/check-style.sh`, `tools/compare.py`), reference captures (`docs/REFERENCE.md`, `docs/CAPTURES.md`, `reference/INDEX.tsv`), and installed GTK 3.24.52 / GTK 4.24.1 / libadwaita 1.10.0 / `kde-gtk-config` 6.8.3 / portal / `ffmpeg-converter-gtk` metadata plus isolated read-only probes in `/tmp`.
- Recorded five open plan findings in `AUDIT.md` (`#148–151` P2, `#152` P3): dual-backend portal activation & single-marker discovery gaps (`#148`), CSS-unachievable targets including GTK 3's inability to draw `text-selection-inactive.png`'s 1 px outline and GTK 4's lack of scrollbar steppers (`#149`), direct contradiction between `GTK-PLAN.md:21`'s undo-survival criteria and existing `uninstall.sh` whole-file restore + missing GSettings/symlink/surviving-selection handling (`#150`), missing `adwaita-1-demo` and conflated app CSS in `ffmpeg-converter-gtk` (`#151`), and Milestone 1/2 handoff conflation + uncaptured states + `compare.py` size/scaling gaps (`#152`).
- **Verdict:** HOLD Milestone 1 until `docs/GTK-PLAN.md` addresses `#148–152`. Live virtual-KWin portal activation and live GUI rendering were not run (sandbox blocks `kwin_wayland` with `Operation not permitted`). `#95` remains open; no claims held.

## 2026-11-23, Codex (GPT-6) — audit GTK plan

Recorded four plan findings (#144–147) in AUDIT.md and corrected the acceptance criteria in docs/GTK-PLAN.md. PLAN.md points to the first implementation checkpoint. Toolkit versions confirmed via pkg-config. Runtime behavior and screenshot comparisons await implementation.

## 2026-11-23, Codex (GPT-6) — plan GTK support

Added docs/GTK-PLAN.md and linked the first implementation checkpoint in PLAN.md. Recorded the three installed toolkit versions. Implementation, sandbox rendering and install testing are pending.

## 2026-11-23, Codex (GPT-6) — user completed plain live reinstall

The user's terminal showed the working-tree installer reaching Done with no inline cache override and all three GTK icon caches created. Platinum was already active. The user previously removed the stale KDE marker manually. The user's live kreadconfig6 query returned WhiteSur-lavender. The user visually approved the desktop appearance after the reinstall. The Lavender reinstall checkpoint is complete.

## 2026-11-23, Codex (GPT-6) — record completed nested Plasma checks

- Recorded the user's 19/19 pixel comparisons with zero differences and 40/40 live-install checks in AUDIT.md and PLAN.md. The #142/#143 working tree is ready for commit and plain reinstall. Real-desktop post-login appearance still awaits the user's check.

## 2026-11-23, Codex (GPT-6) — verify Lavender plain reinstall

- Verified #142 using a genuine 4fe0894 install, including direct undo and preservation of a later icon choice. Checked the completed #143 linked-cache run, its reviewed commit and Git object integrity. See AUDIT.md for the sandbox ownership limit.
- Plain reinstall on the stated setup cleared for commit and user execution. Nested Plasma and post-login visual checks remain pending. Review edits only to AUDIT.md, CHANGELOG.md and PLAN.md.

## 2026-11-23, Antigravity (Gemini 4 Neon) — fix live-install WhiteSur findings #142 and #143

- **#142 (prevent and repair KDE `Theme[$d]` marker):** Replaced `kwriteconfig6 --delete` in `scripts/icon_prefs.py` (`kde_delete_key`) with an atomic mode/ACL-preserving INI editor that removes both `Key=...` and KConfig `Key[$d]` delete markers without writing `Theme[$d]`, and isolated single-layer `kreadconfig6`/`kwriteconfig6` calls from `XDG_CONFIG_DIRS`. Added detection and automatic repair for existing installs carrying a stale `Theme[$d]` marker across plain `./install.sh` (including `--dry-run`), `./install.sh --apply`, and direct `./uninstall.sh`. Updated `dev/test-install.sh` and `dev/test-install-live.sh` to run under the real `XDG_CONFIG_DIRS=$config/kdedefaults:/etc/xdg` cascade and assert effective KDE icon themes via cascaded `kreadconfig6 --file kdeglobals`.
- **#143 (user-owned symlinked `~/.cache`):** Updated `icons/fetch-whitesur.sh` to validate and canonicalize safe user-owned (or root-owned system) ancestor symlinks hop-by-hop (such as `~/.cache -> /mnt/storage0/local/cache`) while strictly refusing symlinked cache leaves, dangling/looping links, non-directory targets, world-writable directories, and foreign-owned links or targets. Updated `icons/build-whitesur-lavender.sh` to canonicalize `$upstream` with `realpath` before git directory verification.
- **Sandbox isolation (`dev/run.sh`):** Exported `XDG_CONFIG_DIRS=/etc/xdg` after borrowing user fonts so a live desktop's `~/.config/kdedefaults` cannot leak into sandboxed `dev/check-quick.sh` / `dev/check-style.sh` runs.
- **Checks:** `dev/test_icons_phase1.py` **80/80**, `dev/test-install.sh` **702/702**, `dev/check-style.sh` **135/135**, `dev/check-quick.sh` **29/29**. `../WhiteSur-icon-theme`, live desktop, and `~/.local/share/icons` untouched.
- **Not verified / what's left:** Nested-KWin suites `dev/check-plasma.sh` and `dev/test-install-live.sh` need the user's terminal outside the sandbox; live desktop update/commit await the user. All claims (`shared`, `icons`, `packaging`) cleared.

## 2026-11-23, Claude (Opus 5.5) — record first live Lavender install

- The user installed `4fe0894` with `XDG_CACHE_HOME=/mnt/storage0/local/cache`. GTK selected Lavender, but KDE read an empty theme because of a `Theme[$d]` marker (#142). A symlinked `~/.cache` also blocks the default path (#143). No code changed here.

## 2026-11-23, Codex (GPT-6) — final WhiteSur Lavender verification

- Verified #127, #131 and #139–141 with the original failure cases. All 50 focused installer assertions passed. Independent process kills confirmed recovery at initial capture, selection and all three unfinished-undo boundaries.
- Two full-source upgrades from committed `8b5c251` records fetched the local pin into an empty cache, installed the trio, and selected Lavender once. Updates kept Adwaita. Two uninstalls in each home restored the exact KDE key placement, all four GTK Breeze values and both GTK 0600 modes despite older 0644 Papirus-Dark backups.
- Recorded the pre-capture control and the limits in AUDIT.md. Live HTTPS, session notifications and named-user ACLs were unverified here. User terminal results were 19/19 Plasma with zero differing pixels and 40/40 live-install. Safe to run plain `install.sh` on the stated setup. Only the audit and this entry changed in this review.

## 2026-11-23, Antigravity (Gemini 4 Neon) — fix WhiteSur Lavender #127, #131, #139, #140, and #141

- **#139 (capture ordering):** Moved `icon_prefs.py capture` in `install.sh` under `take_lock` before `remove_passthrough` and the first `place_file`, so neither installed targets nor `$manifest` change before pre-adoption preferences and the legacy-backup decision are durably saved.
- **#140 (refuse install inside unfinished undo):** Added `$state/uninstall-in-progress` (`scripts/common.sh`, `uninstall.sh`) retained through backup/journal archival, package removal, and manifest retirement until final zero-remainder cleanup, and `check_unfinished_uninstall` + `icon_prefs.py read-tx-status` in `install.sh` (checked before fetch and again under `take_lock`) to refuse without writing whenever an earlier uninstall has not completed.
- **#141 (re-check active global theme on resume):** Passed current `--active-lnf` and `--lnf-id` into `icon_prefs.py apply-tx` so resuming `phase=captured` or `phase=selecting` after switching away from Platinum cancels stale intent (`phase=skipped`, `intended=None`), rolls back only transaction-owned partial writes, and preserves later user choices.
- **#127 (complete outside artwork required):** Required `cand_is_independent_and_complete` (`outside_only=True`) in `scripts/icon_prefs.py` to verify that every directory in `Directories` of both the outside copy and the managed package's `index.theme` exists on disk, resolves outside `forbidden_roots`, and contains readable `.svg`/`.png` artwork resolving outside `forbidden_roots` before authorizing deletion of managed packages.
- **#131 (capture & restore pre-adoption modes and POSIX ACLs):** Captured mode bits and POSIX ACL xattrs for all six config files into `$state/icon-adoption` (`scripts/icon_prefs.py`), stripped stale ACLs when the captured file had none, and staged/applied pre-adoption modes and ACLs during `prepare-restore` even when the legacy backup's icon key already matched.
- **Checks:** `dev/test_icons_phase1.py` **74/74**, `dev/test-install.sh` **677/677** (+50 new regression checks covering `#127`, `#131`, `#139`, `#140` across all 3 crash boundaries, and `#141` in both `captured` and `selecting`), `dev/check-style.sh` **135/135**, `dev/check-quick.sh` **29/29**. `git status` clean of upstream/generated artwork; `../WhiteSur-icon-theme`, `~/.local/share/icons`, and live desktop untouched.
- **Not verified / what's left:** Nested-KWin suites `dev/check-plasma.sh` and `dev/test-install-live.sh` need the user's terminal outside the sandbox; live desktop install/review awaits the user. All claims (`shared`, `icons`, `packaging`) cleared.

## 2026-11-23, Codex (GPT-6) — targeted WhiteSur transaction verification

- Verified #124–138 against the uncommitted tree. All 63 targeted installer assertions passed. Recorded remaining cases for #127 and #131 and new findings #139–141 in AUDIT.md. Hold the live install.
- Two full-source upgrades from genuine 8b5c251 records fetched the reviewed pin locally, selected Lavender and kept a later Adwaita choice on update. Undo restored Breeze in both. With a 0644 historical backup it widened both current 0600 GTK settings files. Cross-checks confirmed the backup mode determines the outcome.
- Interrupted all six transaction phases in throwaway homes. Direct undo and repeated undo recovered after the journal writes. Interrupting before capture revived Papirus-Dark. Starting an install during undo could leave a mixed selection or replay a retired restore decision against a new backup. A pending selection could also override a switch away from Platinum.
- User terminal results are 19/19 Plasma, zero differing pixels, and 40/40 live-install. Live notification delivery and HTTPS were outside this offline verification. Only AUDIT.md and this entry changed. The implementation remains uncommitted.

## 2026-11-23, Antigravity (Gemini 4 Neon) — durable icon-selection transaction & fix WhiteSur Lavender #124–138

- **Unified durable icon-selection transaction (`#124`, `#128`, `#130`):** Replaced split icon-adoption/restore state across `scripts/icon_prefs.py`, `scripts/common.sh`, `install.sh`, and `uninstall.sh` with one fsynced v3 JSON transaction (`$state/icon-adoption`) recording captured KDE + GTK preferences, intended first-install selection values, `phase` (`captured` → `selecting` → `selected` | `skipped` | `restoring` → `restored`), and `restore_decision`. Removed redundant bash icon helpers and post-restore patching.
  - `uninstall.sh` persists `restore_decision="restore_backup"` before touching any file and merges/validates captured icon keys in staged backup copies (`prepare-restore`) before publishing atomically (`#124`), resumes interrupted retries independent of `TAKEN` / `LookAndFeelPackage`, and treats empty displaced targets as restorable (`#130`).
  - `install.sh` resumes unfinished first-install selection on retry whenever `phase in ("captured", "selecting")`, comparing each key against `captured` and `intended` (`#128`), while keeping later user choices untouched once `phase == "selected"`.
- **Removal safety & unified KDE/GTK dependency checks (`#125`, `#126`, `#127`):**
  - Removed `shutil.rmtree` from `scripts/manifest_ops.py` (`cmd_clean_dir`); now unlinks only verified recorded entries and removes directories deepest-first with `os.rmdir`, preserving and reporting any file saved concurrently (`#125`).
  - Unified restore and removal checks in `scripts/icon_prefs.py` (`check-surviving`, `cand_is_independent_and_complete`) covering KDE and all four GTK settings files (`#126`) and resolving every directory advertised in `index.theme` plus symlinks inside them against planned removals (`#127`).
- **KDE layers, permissions, dry-run, worktrees, locking & preflight (`#129`, `#131–138`):**
  - Restored explicit `kdeglobals` and inherited `kdedefaults/kdeglobals` independently so explicit `breeze` never hides stale `Adwaita` (`#129`).
  - Preserved existing file permissions (`0600` stays `0600`) and POSIX ACLs when updating config files and used `0600` for newly created settings (`#131`).
  - Journaled `existed_before` and `rolled_back` in `icons/whitesur-lavender.py` before cleaning private staging so interrupted recovery never deletes already-restored themes, and documented the sequential-rename reader gap in `icons/README.md` (`#132`).
  - Represented absent backup KDE paths as `None` in dry-run previews (`#133`).
  - Switched `is_git_worktree` to `git rev-parse --show-toplevel` so linked Git worktrees enforce tracked-file and git-ignore checks (`#134`).
  - Required `flock` (`util-linux`) unconditionally in `install.sh`, `uninstall.sh`, `scripts/common.sh`, and `icons/fetch-whitesur.sh` (`#135`).
  - Added C++/Qt/KF6/KDecoration 3 build preflight (`pkg-config`, `moc`, `/usr/include/KDecoration3`, `-lkdecorations3`) in `install.sh` before fetching or locking (`#136`).
  - Validated `TMPDIR` and installed cleanup trap before the first persistent allocation in `icons/fetch-whitesur.sh` (`#137`).
  - Documented the active-Platinum one-time plain-install icon switch in `install.sh` header and `--help` (`#138`).
- **Checks:** `dev/test_icons_phase1.py` **74/74**, `dev/test-install.sh` **627/627**, `dev/check-style.sh` **135/135**, `dev/check-quick.sh` **29/29**. `git status` clean of upstream/generated artwork; `../WhiteSur-icon-theme`, `~/.local/share/icons`, and live desktop untouched.
- **Not verified / what's left:** Nested-KWin suites `dev/check-plasma.sh` and `dev/test-install-live.sh` need the user's terminal outside the sandbox; targeted re-check of `#124–138` and live desktop install await the user. All claims (`shared`, `icons`, `packaging`) cleared.

## 2026-11-23, Codex (GPT-6) — re-review the WhiteSur upgrade and undo

- Recorded open findings #124–138 in AUDIT.md. Hold the live install. An interrupted legacy undo can leave GTK on the older Papirus-Dark and KDE on a missing WhiteSur. A retry can skip unfinished selection, and ordinary undo can retain the wrong inherited KDE key beneath explicit Breeze.
- Used the committed installer to create genuine records in throwaway homes. A no-Git release tree fetched the reviewed pin from a read-only local remote, built the full trio, selected Lavender and retained a later Adwaita choice on a full offline update. Inherited Breeze and all tested GTK keys survived ordinary undo and repeated undo. Verified 75 recolors, 20,326 physical SVGs, 24,284 links and the measured Finder face.
- Independently ran 68/68 selected icon checks and 90/90 selected install assertions, plus the failure cases in AUDIT.md. The user reports 19/19 Plasma with zero differing pixels and 40/40 live-install. HTTPS and running-desktop GTK/KDE synchronization were outside this test. Three synthetic-release assertions were omitted to avoid creating a commit.
- Review-only edits are confined to this entry and AUDIT.md. The implementation remains uncommitted. The next fixes should address #124–127 first, then rerun the exact committed-backup upgrade with interruptions and compare both KDE layers and all GTK selections.

## 2026-11-23, Antigravity (Gemini 4 Neon) — fix WhiteSur Lavender #112–123, remaining #110 paths, and active-Platinum auto-select

- **Blockers (#112–115, #117, remaining #110) & active-Platinum one-time auto-select:**
  - Added `scripts/icon_prefs.py` (v2 JSON `$state/icon-adoption`, backward-compatible with v1) to capture, apply, and restore exact KDE (`kdeglobals` explicit vs. `kdedefaults/kdeglobals` inherited) and GTK (`gtk-3.0/settings.ini`, `gtk-4.0/settings.ini`, `.gtkrc-2.0`, `xsettingsd/xsettingsd.conf`) icon preferences without touching unrelated settings or ever selecting a missing theme (`#117`).
  - Added active-Platinum one-time plain-install auto-select in `install.sh`: when `platinum.desktop` is already active, a plain `install.sh` (without `--apply`) records prior KDE/GTK icon preferences, takes or preserves `$backup` first, and selects `WhiteSur-lavender` once for both KDE and GTK without changing panels, wallpaper, cursors, or `kwinrc`. Subsequent plain updates preserve later user icon choices; non-Platinum plain installs leave icon selection untouched.
  - Fixed `#112` in `scripts/common.sh` (`displace_foreign` rollback + `reconcile_displaced`) and `uninstall.sh` (`first_aside` selects earliest completed displacement so incomplete records never demote the real original to `later-versions`).
  - Fixed `#113` in `install.sh` (`backup_predated=true` covers both `TAKEN=apply` and `TAKEN=install` with Platinum active before backup promotion).
  - Fixed `#114` in `uninstall.sh` (`$icon_adoption` stays in `$state/` until after `mv -T "$backup" "$keep/original"` succeeds).
  - Fixed `#115` in `scripts/common.sh` + `scripts/icon_prefs.py has-outside-copy` (resolves candidate theme dirs, `index.theme`, `places`, and `status/32` with `realpath`, rejecting symlinks pointing into any managed `$data/icons/WhiteSur-lavender*` directory).
- **Test hardening (#122):** Replaced multi-operand `! ls -d` undo assertions in `dev/test-install.sh` and `dev/test-install-live.sh` with per-ID absence checks (`icons_absent`), upgraded offline-miss verification to full `snapshot`, and added genuine `git archive 8b5c251` full-size upgrades in both legacy backup states (`TAKEN=apply` and `TAKEN=install`+picker) plus `#112`, `#114`, `#115`, `#117`, `#118`, and active-Platinum auto-select coverage.
- **Builder, cache, preflight & archive fixes (#116, #118–121, #123):**
  - `#116` & `#121` (`icons/fetch-whitesur.sh`, `install.sh`): serialized fetches per cache with a private `/tmp` `flock`, removed wildcard `.WhiteSur-fetch.??????` deletion (preserving unrelated `.WhiteSur-fetch.mydata`), cleaned newly-created empty parent dirs on failed fetch, ran fetch before `take_lock` for zero-footprint offline misses, and switched to full `git fsck --full --no-progress`.
  - `#118` (`icons/whitesur-lavender.py --preflight`, `scripts/common.sh` `need_pkg`, `install.sh`, `uninstall.sh`, `icons/build-whitesur-lavender.sh`, `README.md`, `icons/README.md`): preflighted all required CLI tools and Python/GTK/conditional-Pillow modules with Arch package names before locks, temp cleanup, fetches, or writes.
  - `#119` (`icons/whitesur-lavender.py`): materialized symlinked ancestor directories for cross-directory custom aliases whose logical target differs in `-light`/`-dark` and added byte-level GTK3 variant verification.
  - `#120` (`icons/whitesur-lavender.py`): added fsynced `.whitesur-lavender-publish.json` journal under the destination `flock` with automatic recovery on next `--publish` and explicit `--recover-dest` recovery after abrupt process termination.
  - `#123` (`icons/whitesur-lavender.py`, `icons/README.md`): allowed default `dev/build/icons` and external destinations when running standalone from an extracted source archive without `.git` while keeping full git safeguards in checkouts.
- **Checks:** `dev/test_icons_phase1.py` **71/71**, `dev/test-install.sh` **564/564**, `dev/check-style.sh` **135/135**, `dev/check-quick.sh` **29/29**. `git status` clean of upstream/generated artwork; `../WhiteSur-icon-theme`, `~/.local/share/icons`, and live desktop untouched.
- **Not verified / what's left:** Nested-KWin suites `dev/check-plasma.sh` and `dev/test-install-live.sh` need to be run from the user's terminal outside the sandbox; live HTTPS fetch and live desktop install/review await the user. All claims (`shared`, `icons`, `packaging`) cleared.

## 2026-11-23, Claude (Opus 5.5) — spot-check WhiteSur recovery review

- Confirmed #114, #116, #118, #121, and #122 in code. Found that #117 applies to the live backup's GTK icon setting. Accepted #112, #113, #115, #119, #120, and #123 from Astra's evidence without re-running them.
- No fixes, install, or commit. Don't run the new `install.sh` on the live desktop until #112–115 and #117 are fixed and reviewed.

## 2026-11-23, Codex (GPT-6) — review full-size WhiteSur adoption, undo and dependencies

- Recorded 12 confirmed findings (#112–123) in `AUDIT.md`. The normal
  full-size upgrade from HEAD restored all three unstamped originals exactly.
  A failed first displacement stranded the manual base in `later-versions`.
  Two other upgrade/undo paths silently selected the deleted `WhiteSur` ID.
  A theme-level alias could also let uninstall remove the last selected copy.
- A release archive without a project `.git` completed offline install and
  undo from source, using a local pinned remote. Masked each icon dependency
  separately and recorded the Arch packages and persistent side effects.
  Pillow was needed only for custom PNGs. Verified the overlay lookup
  failures in GTK 3 and KDE and found a light-only custom alias regression.
- #102–109 and #111 passed their original pinned cases. #101 and #110 remain
  partial. User-reported terminal results were 19/19 Plasma with zero pixel
  differences and 40/40 live install. This review changed only the audit log
  and this entry. The fixes and live-desktop verification remain pending.

## 2026-11-23, Claude (Opus 5.5) — add Firefox theme to project scope

- Recorded PLAN.md decision 14: an optional IE5 Mac-style Firefox theme with Platinum Lavender replacing IE's teal. Added its Claims row, component entry, and work order. AGENTS.md now records the user's `userChrome.css` exception.
- Reference so far: `reference/ie5-window-blank.png` (native 1920x1080, not yet committed in the private reference repo). Toolbar, address-bar, sidebar, and inactive-window captures are still needed.
- No Firefox files were created and no theme code changed. Nothing was installed or committed. Don't start this work until the user asks.

## 2026-11-23, Antigravity (Gemini 4 Neon) — custom icon layer, overlay evaluation, auto-fetch cache & fast test-install fixture

- **Overlay evaluation:** Empirically tested a thin WhiteSur Lavender overlay inheriting upstream `WhiteSur` in both GTK3 (`Gtk.IconTheme`) and KDE (`KIconLoader`). Rejected the overlay due to four reproduced failures: 16/22/24 px monochrome icons shadowed by `places/scalable/` in both GTK3 and KDE, `KIconLoader` prefix fallback hijacking `folder-blue@64` to `WhiteSur-lavender/places/scalable/folder.svg`, unresolvable `WhiteSur-lavender-dark` inheritance ordering, and Plasma picker/undo collision. Kept full-copy + custom layer (recorded in `AUDIT.md` and `icons/README.md`).
- **Tracked custom icon layer (`icons/custom/{all,light,dark}/`):** Added `icons/custom/README.md`, `all/`, `light/`, and `dark/` trees (`.gitkeep`), strict pre-install validation (`icons/whitesur-lavender.py`), safe directory materialization for `light/` and `dark/` overrides (zero bleed-through into base `WhiteSur-lavender`), cache regeneration and GTK3 verification, and override-change reporting in `icons/review-whitesur-update.sh` (section 7).
- **Automatic WhiteSur fetch & bare cache (`icons/fetch-whitesur.sh`, `install.sh`):** `install.sh` now uses `M9_WHITESUR_UPSTREAM` when set, otherwise `${XDG_CACHE_HOME:-$HOME/.cache}/macos9-theme/WhiteSur-icon-theme`, fetching only the exact reviewed commit into a bare git cache (`core.hooksPath=/dev/null`, `core.symlinks=false`, `GIT_CEILING_DIRECTORIES` containment) and verifying full commit + `git fsck` + all pinned digests before running any upstream code. `--dry-run` never downloads or writes. Offline reuse, offline miss, corrupt cache, wrong-commit cache, symlinked cache, and interrupted download leftovers all verified with a local `file://` fixture remote (zero real network access).
- **`dev/test-install.sh` optimization:** Added a 19-entry (`0.13 MiB`) valid 3-theme fixture for 89 general scenarios while keeping 4 real-size (`44,628`-entry, `41.78 MiB`) round-trip/custom/auto-fetch installs. Runtime fell from **29m 10s** (448 checks) to **11m 38s** (468 checks, **2.5× faster**), and icon write volume fell **95.2%** (`3,971,892` → `180,203` entries; `~3.63 GiB` → `178.7 MiB`).
- **Checks:** `dev/test_icons_phase1.py` **59/59**, `dev/test-install.sh` **468/468**, `dev/check-style.sh` **135/135**, `dev/check-quick.sh` **29/29**. `git status` clean of upstream/generated artwork; `~/.local/share/icons`, live desktop, and `../WhiteSur-icon-theme` untouched.
- **Not verified / what's left:** Nested-KWin suites `dev/check-plasma.sh` and `dev/test-install-live.sh` need the user's terminal outside the sandbox; live HTTPS fetch and live desktop install/review await the user. All claims (`icons`, `shared`, `packaging`) cleared.

## 2026-11-23, Antigravity (Gemini 4 Neon) — WhiteSur Lavender pin/review workflow & #110 install/undo integration

- **Phase 1 follow-ups:** Moved pin metadata and digests from `icons/whitesur-lavender.py` into `icons/whitesur-pin.json`; added read-only upstream update review command `icons/review-whitesur-update.sh` (exports candidate tag/commit without executing its `install.sh`, reports diffs across installer, 25 color inputs, launchers, licenses, symlinks, and SVG namespace exceptions, and writes a proposed pin for review without touching `icons/whitesur-pin.json`); added disposable suite `dev/test_icons_phase1.py`; documented both commands in `icons/README.md`. Recorded Claude's 2026-11-22 Phase 1 spot-check in `AUDIT.md`.
- **Phase 2 (`#110`):** Updated `plasma/make-plasma.py` and `plasma/look-and-feel/platinum.desktop/contents/defaults` to select `WhiteSur-lavender` (all other Platinum global theme defaults unchanged). Added `scripts/manifest_ops.py` (O(N) format-v4-compatible manifest/checksum operations for 44,619+ files/links). Wired `WhiteSur-lavender`, `WhiteSur-lavender-light`, and `WhiteSur-lavender-dark` into `scripts/common.sh`, `install.sh`, `uninstall.sh`, `dev/test-install.sh`, and `dev/test-install-live.sh`: validates/builds the pinned trio before touching targets, preserves relative symlinks, captures first manual copies even when byte-identical to the build, records pre-adoption icon selection and manual/absent state in `$state/icon-adoption` without modifying any pre-existing `$state/backup`, restores manual copies and manual Lavender selection on undo without assuming old `WhiteSur` exists, and retains selected variants together with base `WhiteSur-lavender` when removing them would leave the selection unusable.
- **Checks:** `dev/test_icons_phase1.py` 42/42 passed; `dev/check-style.sh` 135/135 passed; `dev/check-quick.sh` 29/29 passed; `dev/test-install.sh` 448/448 passed (up from 367, +81 `#110` checks); real non-`M9_PREBUILT` throwaway-home round trip passed (25.99 s install, 5.07 s uninstall). `git status` clean of upstream/generated artwork; `../WhiteSur-icon-theme`, `~/.local/share/icons`, and live desktop untouched.
- **Not verified / what's left:** Nested-KWin suites `dev/check-plasma.sh` (hit Wayland sandbox limit) and `dev/test-install-live.sh` need to be run from the user's terminal outside the sandbox; live desktop install/update/review and commit/push await the user. All claims (`icons`, `shared`, `plasma`, `packaging`) cleared.

## 2026-11-22, Antigravity (Gemini 4 Neon) — fix WhiteSur Lavender builder (#101–109, #111)

- Fixed Phase 1 builder findings `#101–109` and `#111` in `icons/whitesur-lavender.py`, `icons/build-whitesur-lavender.sh`, `icons/README.md`, and `docs/REFERENCE.md` (all uncommitted; `#110` intentionally deferred to Phase 2 pending user approval).
- **Staging, destination safety, minimal env, and pin (#101–104):** `build-whitesur-lavender.sh` enforces pinned full commit `73d8040da51a9ed74e47c7366e7e9ff437601a5c` (archives only that commit, reports that single ID), resolves caller paths once, runs `git`, `tar`, `python3 -I`, and patched upstream `install.sh` under `env -i` with a minimal explicit environment and `umask 022`, builds into a private `0700` staging directory, verifies the entire trio before publishing, and publishes atomically under a per-destination `flock` with ownership stamps (`.macos9-whitesur-lavender-build`) and rollback on failure. Refuses symlinks in `OUTPUT_DIR` or its parent chain, upstream paths, trackable project paths / `reference/` / `.git`, and unowned existing theme directories. Patches upstream `install.sh` quoting so spaces in both `OUTPUT_DIR` and `TMPDIR` work.
- **Strict input checks, literal variant, Finder palette, KDE launcher, notices, and SVG namespaces (#105–109, #111):** `whitesur-lavender.py` pins the 25-file `colors/color-purple/` manifest, SHA-256 digests, and per-file expected paints plus pinned digests for `install.sh`, `COPYING`, `AUTHORS`, `plasma/places/{16,22,24}/start-here.svg`, `src/status/32/start-here.svg`, and the 64 missing-xmlns SVGs; validates XML, SVG namespace, `xmllint`, `rsvg-convert`, and `bash -n` before modifying the export; selects literal `themes+=('-lavender')` (removing `THEME_VARIANTS[9]`); maps `#f299ff -> #ddddfe`, `#e791f3 -> #b5b4f9`, `#c75cd6 -> #7e7dd9` (recorded in `docs/REFERENCE.md`); builds with `-p` and derives 32 px KDE Plasma `status/32/start-here.svg` from `plasma/places/24/start-here.svg`; separates script license (`BSD-2-Clause`) from derived artwork (`GPL-3.0-only`) and installs `COPYING`, `AUTHORS`, and dated `LAVENDER-NOTICE.txt` into each theme; normalizes all 64 missing-xmlns upstream `src/` SVGs.
- **Checks:** 38/38 automated Phase 1 test cases passed (including all `#101–109`/`#111` failure modes, poisoned env, spaces in `OUTPUT_DIR` + `TMPDIR`, mid-publish rollback, concurrent writers, and default `dev/build/icons/` clean build + owned rebuild). Rebuilt `dev/build/icons/` cleanly (55,034 resolved files per theme, 20,326 physical SVGs / 0 missing namespaces, 0 broken/escaping links, 3/3 valid caches, 18/18 KDE Plasma launcher lookups at 16–64 px). `#107` visual comparison (`dev/build/icons-compare-107/`): `folder.svg` center `(16,20)` matches `reference/finder-rename.png` `#B5B4F9` with 0 channel delta (down from `(-28, -27, +6)`), and `user-identity.svg` dark rim max channel error dropped from 23 to 1. Upstream clone untouched; `~/.local/share/icons` untouched; `git status` shows zero upstream or generated artwork.
- **Not verified / what's left:** Not installed, not tested in live Plasma or on physical displays, and the five unrelated C++/Plasma/installer suites were not run. Next: await user approval to start Phase 2 (`#110` install, apply, update, and undo integration). Claims cleared.

## 2026-11-22, Claude (Opus 5.5) — verify WhiteSur Lavender audit

- Reproduced #101, #102, and #104, and confirmed #103 and #105–110 in code or built output. #111 was accepted from Astra's evidence. Updated `AUDIT.md` and `CHANGELOG.md` only.
- No fixes, install, or commit. Next: fix the builder (#101–109, #111), then integrate install and undo (#110).

## 2026-11-22, Codex (GPT-6) — audit WhiteSur Lavender against the pinned release

- Recorded 11 confirmed findings (#101–111) in `AUDIT.md`. Two P1 findings
  cover deletion of existing output and inherited variables that select
  upstream's uninstall mode. Update tests also reproduced a stock folder
  falling through, an unrecolored accent and a successful build of Nord.
- At `73d8040`, all 75 variant/asset combinations matched the generator's
  current mapping, parsed, rendered and resolved through GTK. All three
  caches validated and all 24,280 physical symlinks resolved inside the
  three-theme output. #107 records the corrected Finder folder colors and
  repeatable pixel samples from `reference/finder-rename.png`.
- #110 covers adoption and restoration of the user's manually installed,
  already-selected Lavender theme, including the base dependencies of the
  light and dark variants. Install/apply/undo and live appearance remain
  untested. The icon and installer fixes are pending. Only this entry and
  `AUDIT.md` changed during the review.

## 2026-11-22, Claude (Opus 5.5) — add WhiteSur Lavender generator

- Added `icons/whitesur-lavender.py`, `icons/build-whitesur-lavender.sh`, and `icons/README.md`. The upstream clone is outside the repo at `../WhiteSur-icon-theme`, pinned to release `2026-09-10` (`73d8040`) and left unmodified.
- The generator derives 25 Lavender folder SVGs from WhiteSur's purple set: `#f299ff` to `#ccccff`, `#e791f3` to `#9999ff`, `#c75cd6` to `#6666cc`. It stops if upstream's palette or installer layout changes.
- Built `WhiteSur-lavender`, `-light`, and `-dark` in ignored `dev/build/icons/`: 55,030 resolved files each, 0 broken links. Three rendered folders were inspected. Upstream's named `purple-*` icons remain by design.
- Not done: live install, desktop review, `install.sh` and `uninstall.sh` integration, global theme selection, and commit. Claim released.

## 2026-11-22, Claude (Opus 5.5) — record remaining theming decisions

- Recorded the user's decisions in `PLAN.md`: WhiteSur icons with our own Lavender patch set, Apple SF fonts kept as an external dependency, Konsole and Kwi as the only terminal targets, and Plasma Login Manager instead of SDDM.
- Checked upstream WhiteSur (release 2026-09-10, GPL-3.0): a color variant is 25 folder SVGs in `colors/color-*` plus installer entries. Plasma Login Manager 6.8.3 is the active login service here.
- No theme code changed, nothing installed, nothing committed. Lavender icons have not been started.
- What's left: WhiteSur Lavender, GTK 3, GTK 4/libadwaita, Plasma Login Manager, Konsole and Kwi colors, splash, lock screen, and the small Qt gaps.

## 2026-11-22, Codex (GPT-6) — close checkpoint 5

The user's final private-D-Bus runs passed 19/19 Plasma, 367/367 install
and 37/37 live install checks, all exit 0. The earlier sandbox runs passed
135/135 widget and 29/29 Qt Quick checks, and 200/200 images matched the
baseline at eight scales.

The user's original nested-KWin #99 probe measured correct geometry through
the second restore, then failed with `No matching paint for resize` because
its action left the window at the old size. Claude's scratch copy assigned
a fresh frame geometry object and passed all seven steps across 23 paints
on the current decoration. The resized frame measured 708 × 438 px with
a 708 px title and the rightmost button edge at 704 px. Applied the same
one-line correction to `dev/build/audit-baseline/test-nested-99.py` and
checked its Python syntax. Theme code did not change during closeout.

#99 and #100 are verified in the working tree. #95 remains open. Claims
are free. The final working-tree patch and separate one-line probe patch
are `checkpoint-5-final.patch` and `checkpoint-5-probe.patch` under
`dev/build/audit-baseline/`.

## 2026-11-22, Codex (GPT-6) — fix #99 and #100, checkpoint 5 awaits terminal tests

In `style/quick/platinumitem.cpp`, use the checked QApplication pointer
throughout styleWatcher(). In `decoration/platinum.cpp`, restore the
applied-border notification and remove the immediate before/after margin
comparison. Unchanged-border font and reconfiguration events still lay out
the title and buttons. UBSan passed the QGuiApplication-only construction
test. A controlled deferred-apply probe distinguished the old and fixed
callbacks. Widget and Quick suites passed 135/135 and 29/29. All 200 final
images matched the existing eight-scale baseline. #95 remains open.

Saved `dev/build/audit-baseline/checkpoint-5.patch`. The nested geometry
probe is `dev/build/audit-baseline/test-nested-99.py`. Build-only check
passed. The next step is the user's private-D-Bus suite rerun and nested
geometry probe, followed by verification of their fresh logs. The working
tree is uncommitted and the decoration and style claims are free.

## 2026-11-22, Claude (Opus 5.5) — verify Gemini's review findings #99 and #100

- Updated `AUDIT.md`, `CHANGELOG.md`, and the `PLAN.md` status only. No theme code changed, nothing installed, live desktop untouched, nothing committed.
- #100 confirmed (P2): UBSan reports invalid `QApplication` downcasts at `platinumitem.cpp:25` in a `QGuiApplication` app, and none on `dc8b76f`.
- #99 re-rated P3: the removed `bordersChanged` relayout is a real API-level risk, but nested KWin showed 0 wrong decoration paints across maximize, restore, horizontal and vertical maximize, and resize, on both `dc8b76f` and the working tree.
- Not verified: Gemini's other clean verdicts, X11 clients, clients that ignore a maximize size, the user's GPU, and physical displays.
- What's left: fix #99 and #100, rerun all five suites and the pixel comparison, then commit only when the user asks.

## 2026-11-22, Antigravity (Gemini 4 Neon) — independent review of uncommitted C++ audit fixes (#85–98)

- Reviewed the full uncommitted working-tree diff against `dc8b76f` (`decoration/`, `style/platinum/`, `style/quick/`, `tools/nineslice.py`, `plasma/make-plasma.py`). Updated `AUDIT.md` and `CHANGELOG.md` only (no code edits, no install, `dev/build/audit-baseline/` untouched).
- Verified #85–93, #97, and #98 as clean (and #95 properly left open): 0 differing pixels across all 8 scales (`1` to `3×`) on widget controls including translucent palettes, 0 cross-thread dynamic-property writes under `QSG_RENDER_LOOP=threaded`, 0 binding loops even during an open-menu style switch, 69× faster closed 200-item `ComboBox` resize (`559.4 → 8.1 µs`), immediate `QProgressBar` timer stop on parent tab hide (0 fires in 350 ms), and full `QMenu` shortcut-cache invalidation.
- Found and confirmed two P2 regressions recorded in `AUDIT.md`:
  - **#99** (`decoration/platinum.cpp:240–252`): removing `bordersChanged` → `updateButtonsGeometry` and checking `previous != borders()` breaks double-buffered `KDecoration3::DecorationState` geometry (`borders()` reads `currentState()` at `0xc0` while `setBorders()` writes `nextState()` at `0xb0`). Confirmed via `KDecoration3::DecorationBridge` probe: `init()+apply()` leaves `titleBar` and right buttons 12 px too far left (`400/396` vs `412/408`), and `maxH+widthChanged(1000)+apply()` leaves them 12 px past the right edge (`1012/1008` vs `1000/996`).
  - **#100** (`style/quick/platinumitem.cpp:25`): `styleWatcher()` evaluates `qApp` (`static_cast<QApplication *>`) before `qobject_cast<QApplication *>`. Confirmed under UBSan on a `QGuiApplication`-only app (`runtime error: downcast ... object is of type 'QGuiApplication'`).
- Not verified: live nested `kwin_wayland` / Plasma session and physical displays.
- Next: whoever claims `decoration` and `style` should fix #99 and #100 before committing, then re-verify with the full suites and a `QGuiApplication` UBSan run.

## 2026-11-22, Codex (GPT-6) — checkpoint 4 passed

Final working tree against `dc8b76f`: 12 of 13 verified C++ findings fixed
(#85–94, #96–97). #95 stays open after reverting fractional-scale differences.
The #98 generator fix passed the rerun. Sandbox suites were 135/135 and 29/29.
The user's final private-D-Bus runs were 19/19, 367/367 and 37/37, all exit 0.
All 200 final images matched across eight scales (228,376,750 pixels).
Threaded #85 runtime results and before/after costs are in AUDIT.md.
Median 400 px progress paint fell from 135.1 to 7.5 µs, slider paint from
74.2 to 4.1 µs and 1,000 menu size requests from 19.324 to 0.082 ms.

Final renders, cost logs, all checkpoint patches and the preserved failed
D-Bus run are in `dev/build/audit-baseline/`. The working tree is uncommitted.
Claims are free. Physical-display review and a pixel-equivalent #95 solution
remain outstanding.

## 2026-11-22, Codex (GPT-6) — fix #91 Plasma parser regression, checkpoint 4 pending

Archived the failed final suite logs in `dbus-suites-final-failed-1/`.
The user's Plasma run exited 1 in the generator before rendering. Both
install suites passed (367/367 and 37/37). Fixed the single NineSlice regex
in `plasma/make-plasma.py` (#98). Regeneration preserved all tracked output.
All 13 tables parsed equivalently with either qualifier. No second text reader
was found. Sandbox suites passed 135/135 and 29/29 after the change.

The user's threaded #85 negative control detected 82 violations and 18
property changes in 16 active off-GUI paints. The working tree passed with
16 active off-GUI paints, zero paint-time changes, 18 GUI controls and zero
violations. Next: user reruns all three private-D-Bus suites, then Codex
verifies their exits and completes the final comparisons and measurements.

## 2026-11-22, Codex (GPT-6) — C++ audit checkpoint 3 passed with #95 open

Implemented #86, #87, #90, #91, #92, #94, #96 and #97, each with
offscreen baseline comparisons at eight scales. The compact thumbs in #95
changed 45 fractional-scale frames and were reverted. See AUDIT.md.
Widget/Quick suites 135/135 and 29/29. ASan/UBSan exercised all three plugins
with no reported errors (leak detection off). Both shadow references now
expire, and a late item leaves zero watcher widgets. Five hover cycles emit
10 damage signals instead of 20. A maximize emits 6 instead of 15. Ten width
changes still emit 40. Relayout with unchanged borders and all 40 combinations
of scrollbar hit target, orientation, direction and reversal passed.

During validation we found the widget sheet's standalone translucent field
used a generic option. A second harness sets a positive frame width on a
QStyleOptionFrame and verifies a 50% white fill over the black underlay
renders #808080. Two fresh runs using the archived dc8b76f style matched,
as did the working style at all eight scales. Total baseline: 200 images.

Checkpoint 4 awaits the user's final private-D-Bus suites. The separate
threaded #85 probe and its negative control built; nested execution awaits
the user. No commit, install or live desktop test by Codex.

## 2026-11-22, Codex (GPT-6) — C++ audit checkpoint 2 passed

Moved the four PlatinumItem property writes out of paint (#85, 152/152 images).
Hidden and determinate progress bars stop their timers (#88, 8/8 widget sheets).
Separated Quick notifications and combo width dependencies (#89/#93, 152/152
images). The 200-row probe went from 69,800 to zero size recalculations in
350 width assignments. Median time for 50 assignments fell from 56 to 20 ms.
The menu probe went from 29 shortcut-column loop warnings to zero. Widget and
Quick suites passed 135/135 and 29/29. Threaded GPU rendering was outside
this run. Next is checkpoint 3 in the verified order.

## 2026-11-22, Codex (GPT-6) — C++ audit checkpoint 1 passed

At `dc8b76f` the suites matched 135/135, 29/29, 19/19, 367/367 and 37/37.
The user ran the last three. Two independent offscreen software passes matched
192/192 full RGBA images across 1, 1.25, 1.5, 1.75, 2, 2.25, 2.5 and 3×.
Each scale has a DPR-aware widget sheet (including translucent field and
dialog colors), 19 Quick frames and four decoration frames, including held
and drag-off. Barber phase 4. Raw images, harness sources and cost logs are
in `dev/build/audit-baseline/`. This covers the software preview only.
Checkpoint 1 patch includes the pre-existing documentation edits and GEMINI.md.

## 2026-11-22, Claude (Opus 5.5) — diagnose Codex sandbox handoff

- Cause of the launch failure: a Codex chat opened on `/home/pieman` makes the home folder writable, and `~/.codex` is a symlink there, so bubblewrap refuses to start. The same sandbox starts correctly from this project folder.
- Tested the suites at `dc8b76f` under Codex's sandbox. With network off and display variables unset: `check-style` 135/135, `check-quick` 29/29. `test-install` stops because `dbus-run-session` can't bind its socket. `check-plasma`, `test-install-live`, and nested KWin need the same private D-Bus.
- **Do not enable sandbox network access for this project.** With it on, the sandbox could connect to the live session bus, Wayland, and X11. During that test run, a blocked `kreadconfig6` write opened a KDialog on the user's real desktop. I stopped the run and the dialog closed.
- Afterward the live widget style, global theme, color scheme, and decoration still read Platinum, and tracked theme code was unchanged. `~/.config/kdeglobals` has a 19:12:39 timestamp near the user's screenshot. The sandbox mounted home read-only, but no earlier copy exists to diff.
- Not done: checkpoint 1, the baseline renders, and all fixes for #85–97. Next agent: follow the Codex sandbox note in the `PLAN.md` status.

## 2026-11-22, Codex (GPT-6) — checkpoint 1 blocked at baseline destination

Verified HEAD at `dc8b76f` and read the claims and Claude's verification of
#85–97. The requested sibling directory
`/home/pieman/Files/Archive/projects/macos9-theme-audit-baseline/`
is absent and outside this sandbox's writable roots. Checkpoint 1 failed
before the five suites or either render pass ran. All eight scales and
both opaque and translucent palette cases are unverified. No costs were
measured, no C++ or QML changed, and both component claims are free.
Resume at checkpoint 1 with the baseline directory writable. Existing
uncommitted work is preserved.

## 2026-11-22, Claude (Opus 5.5) — verify Gemini's C++ audit (#85–97)

- Verified all 13 findings against `dc8b76f` with code review and probes (offscreen and disposable nested KWin 6.8.3, threaded render loop). Updated `AUDIT.md`, `CHANGELOG.md`, and the `PLAN.md` status only. No theme code changed, nothing installed, live desktop untouched, nothing committed.
- Re-rated to 0 P1, 4 P2 (#85, #88, #89, #93), 9 P3. #85 drops from P1: all 44 observed `paint()` calls ran during scene graph sync with the GUI thread blocked, and no crash appeared. Its `setProperty()` calls on the render thread still need to move.
- Four suggested fixes must not be applied as written: #86 `weak_ptr` rebuilds shadows on focus changes (8 created versus 2 over 6 windows); #90's conditional button connections leave KDecoration's own damage (10 either way, so delete them); #93 alone leaves about 216 row recalculations per width step; #95 edge-only fills change pixels with translucent colors.
- Disproved: null `viewport()` (#87), the progress range mismatch (#88), and the style name bug (#94). Gemini's "~91 wakeups/s" is timer events: ten bars wake the thread 10 times per second.
- Not verified: the user's GPU and displays, debug Qt, a style switch with a menu open, and any of the proposed fixes (none were implemented).
- What's left: whoever claims `style` and `decoration` should fix in the order #85, #88, #89 + #93, then the P3s, following the notes in the `AUDIT.md` verification section and running all suites.

## 2026-11-22, Antigravity (Gemini 4 Neon) — C++ performance, resource, latency, and stability audit

- Audited `decoration/`, `style/platinum/`, `style/quick/`, and relevant C++ in `tools/` and `dev/` at commit `dc8b76f`. Updated `AUDIT.md` and `CHANGELOG.md` only (no code changes, no install, no live desktop edits).
- Recorded 13 new open findings (`#85`–`#97`: 1 P1, 8 P2, 4 P3) in `AUDIT.md`:
  - P1: `#85` `PlatinumItem::paint()` calls `setProperty()` and GUI-thread-only Qt Widgets/`QPixmap` APIs from `QSGRenderThread` under Qt Quick's threaded render loop (12 cross-thread `QDynamicPropertyChangeEvent`s confirmed; hidden by `QT_QUICK_BACKEND=software` in `dev/check-quick.sh`).
  - P2: `#86` static `std::shared_ptr<DecorationShadow>` outliving `~QCoreApplication()`; `#87` SIGSEGV in `sizeFromContents(CT_HeaderSection, nullptr)` and `polish/unpolish(nullptr)` (Fusion exits 0); `#88` always-on 100 ms `QTimer` per polished `QProgressBar` (10 hidden determinate bars fired 50 wakeups in 550 ms); `#89` shared `NOTIFY changed` causing `Menu.qml` / `MenuItem.qml` binding loops and hover recomputation; `#90` `Decoration::paint()` ignoring `repaintArea` (31.89 µs for a 13×13 button), unpressed/inactive hover duplicate damage (20 signals per 5 enter+leave), and 1×1 `drawBox` loops; `#91` 1×1 `fillRect` loops in `Platinum::Style` (3×–60× slower than coalesced spans; verified 0-diff at 1×/1.25×/1.5×/2× for RLE spans and 348/746 px drift at 1.25×/1.5× for unconditional `QImage` blitting); `#92` $O(N^2)$ `QMenu::sizeHint()` without shortcuts (19.9 ms vs Fusion 1.9 ms at 1,000 items); `#93` `ComboBox.qml` re-measuring all items on every `width` change while closed (559–590 µs/resize at 200 items).
  - P3: `#94` `styleWatcher()` recreating a leaked `QWidget` during/after `aboutToQuit` and missing `QApplication::style()` null guards; `#95` full-width `RangeSlider` thumb textures (`400×16` each) and panel interior overdraw; `#96` redundant `Decoration` maximize/resize damage bursts (15 per maximize, 40 per 10 width steps), per-resize `Qt::UniqueConnection`, and unguarded `Button` factory constructor (SIGSEGV on empty args); `#97` 3× redundant `QFontMetrics::boundingRect` in `drawGroupBox()`.
- Checks: compiled all three plugins (`-O2` and ASan/UBSan) into a separate scratch folder with 0 warnings; ran offscreen Qt / KDecoration3 preview / threaded-render-loop probes and scale-factor pixel-diff tests (1.0×, 1.25×, 1.5×, 2.0×).
- Not verified: live GPU Wayland/OpenGL/Vulkan desktop, nested KWin session, and physical displays.
- What's left: the next agent claiming `style` or `decoration` can fix `#85`–`#97` (starting with `#85`–`#89`) and verify pixel parity across 1×, 1.25×, 1.5×, and 2× with `dev/check-style.sh`, `dev/check-quick.sh`, and `tools/compare.py diff`.

## 2026-11-22, Codex (GPT-6.2) — audit and repair bundled cursors

- `install.sh` verifies the whole cursor archive before installing and
  adds its icon directory to Plasma's cursor search path at login.
- `uninstall.sh` keeps the selected cursor pack until the user switches
  away, or restores the earlier pack under the same ID.
- `scripts/common.sh` preserves edited cursor aliases. The offline suite
  covers each fix. `cursors/README.md` links to the tagged upstream source.
- Passed installer 367/367, live 37/37, Plasma 19/19,
  Qt Widgets 135/135, Qt Quick 29/29. The changes are in the working tree.
  Desktop review awaits the user.

## 2026-11-21, Claude Code (Claude Opus 5.5) — bundle the cursors

- `cursors/macOS-cursors.tar.xz`: Apple Cursor v2.0.1's black theme
  (GPL-3.0, license inside; provenance and how it was repacked in
  `cursors/README.md`), the folder renamed `macOS-cursors`.
- install.sh unpacks it, checks the pointer file, installs it to
  `~/.local/share/icons/macOS-cursors` (a recorded, checksummed target;
  links inside installed folders are now recorded by where they point);
  the global theme's defaults select it. Uninstall removes it.
- Removed: `--black-cursors` and `tools/install-black-cursors.sh` (no
  download step any more).
- Checks: install 335/335, live 37/37, Plasma 19/19. Uncommitted.

## 2026-11-21, Claude Code (Claude Opus 5.5) — black cursor fixes (#78–#80), theme renamed macOS-cursors

- The optional black cursor theme's ID is now `macOS-cursors`.
- `tools/install-black-cursors.sh` installs it from the upstream archive
  without replacing anything already there (#78); install.sh matches the
  exact ID (#79) and refuses a pack whose pointer file is broken (#80).
- Checks: install 339/339, live 36/36. Uncommitted, on top of the other
  uncommitted working-tree changes (Qt Quick ToolButton, wallpapers, panel
  fixes).

## 2026-11-21, Codex (GPT-6.2) — audit the black cursor option

Verified selection and byte-for-byte cursor config restoration in a
disposable home. Recorded #78–80 for extraction over an existing theme,
a false theme ID match, and accepting broken cursor data. Updated the
plan and audit log. Documentation only.

## 2026-11-21, Codex (GPT-6.2) — select the external black cursor theme

Added the optional `--apply --black-cursors` switch. Plasma must list
the separately installed black `macOS` theme before installation
proceeds. The README shows how to extract that folder alone and select
it from Plasma without reapplying the desktop layout. The live test
verified selection and undo with the upstream pack in a disposable
home. The integration is in the working tree and awaits desktop review.

## 2026-11-21, Codex (GPT-6.2) — preserve selected wallpapers during uninstall

Fixed wallpaper findings #75–77 in the working tree. Uninstall keeps a
package while a desktop still selects it and finishes when run again
after the selection changes. The installer checks JPEG XL support before
applying. Live tests compare the actual wallpaper on both screens and
reject an incorrect default. Installer checks passed 326/326, live
installer 33/33, Plasma artwork 19/19, Qt Widgets 135/135, and Qt Quick
29/29. The user can check the visuals on their desktop after updating
and selecting a wallpaper in Plasma.

## 2026-11-21, Codex (GPT-6.2) — audit wallpaper install, apply, and undo

Recorded findings #75–77 in AUDIT.md. A picker-only install leaves stale
wallpaper selections on uninstall, a shell without JPEG XL support
renders a white desktop after apply, and a missing default still passes
all 25 live installer checks. Verified these cases in disposable homes.
Updated the plan with the open findings. Documentation only.

## 2026-11-21, Codex (GPT-6.2) — add Lavender Desktop Pattern

Packaged the second user-supplied 3840 × 2160 JPEG XL wallpaper byte for
byte and registered both wallpaper packages with the installer. Both
appear in Plasma’s picker, and applying the global theme selects Pastel
Ribbon Landscape. Verified the new wallpaper in nested Plasma and tested
an upgrade from the one-wallpaper installer. Install and undo passed
316/316, live install and undo 25/25, Plasma artwork 19/19, Qt Widgets
135/135, and Qt Quick 29/29. The second package is in the working tree and
awaits the user’s desktop review.

## 2026-11-21, Codex (GPT-6.2) — package the Pastel Ribbon Landscape wallpaper

Moved the user’s original 3840 × 2160 JPEG XL image into a Plasma wallpaper
package without changing its bytes. The installer adds it to the picker
and Platinum’s global theme selects it on apply. Nested Plasma verified
that the image renders and is listed in the picker. The two-screen test
verified that a plain install keeps both backgrounds and that uninstall
restores both originals after applying the theme. Tests passed 314/314
installer, 24/24 live installer, 19/19 Plasma artwork, 135/135 Qt Widgets,
and 29/29 Qt Quick. The wallpaper and integration are in the working
tree and await desktop review.

## 2026-11-21, Codex (GPT-6.2) — record the Kwi desktop review

The user reported that the updated Kwi tab close button worked well on their desktop. Recorded the result for #71–74 in AUDIT.md and marked the desktop review complete in PLAN.md. Documentation only.

## 2026-11-21, Codex (GPT-6.2) — keep custom tab icons and restore Kwi's selected close cue

Fixed #72–74 in the working tree. The Qt Quick style takes the tab's selected state and keeps customized icons on their ordinary rendering path. Closed a tab after checking idle and hover in a disposable Kwi session and verified Konsole's tabs pixel for pixel. Added eight regression checks to the Qt Quick suite (29/29). Desktop review waits on a reinstall and a full restart of Kwi.

## 2026-11-21, Codex (GPT-6.2) — audit the Kwi tab close fix

Verified the compact close button, hover and press feedback, and pixel-identical Konsole tabs in a disposable Plasma session. Recorded open findings #72–74 in AUDIT.md. The fix discards custom icon settings and loses the active tab's colored close cue. Both style suites still passed with the fix removed. This audit changed only AUDIT.md, PLAN.md, and this log. The #71 patch remains in the working tree and awaits desktop review.

## 2026-11-21, Codex (GPT-6.2) — use the standard tab close indicator in Kwi

Fixed finding #71 in the working tree. Flat icon-only tab close controls now use Qt's compact close indicator. Confirmed the appearance and tested hover and closing a tab in Kwi under nested KWin. The Qt Widgets, Qt Quick, Plasma artwork, and both installer suites passed. Desktop review still waits on the user. Rerun the installer over the existing install and fully reopen Kwi to load the new application style.

## 2026-11-21, Codex (GPT-6.2) — finish divider dots and check resized panel pieces

Fixed #69 and #70. The menu-bar plasmoid skips a trailing dot when its highlight would reach the bottom margin. The artwork suite now checks every pixel of all three pieces at 32, 34, 38, and 40 px. It rejects the earlier clipped dots and a capture with artwork erased from all three pieces.

Plasma artwork passed 19/19, Qt Widgets 135/135, Qt Quick 21/21, install 312/312, and nested install/undo 19/19. The generator, generated QML, resize test and audit notes are in the working tree. The panel fix was verified at 100% display scale in nested Plasma. Review on a physical display is pending.

## 2026-11-21, Codex (GPT-6) — audit the resized top panel

Verified the user’s 32 px desktop capture and reran the Plasma artwork suite (8/8). Recorded two P3 follow-ups in AUDIT.md for the next panel pass. At 34 and 40 px one dot loses its highlight, and the resized-artwork test accepts missing pixels in all three pieces. Updated the plan with the user’s on-screen result. This review adds documentation only. The panel changes and audit remain in the working tree.

## 2026-11-21, Codex (GPT-6) — resize the top panel corners and dotted grip

The Platinum menu-bar pieces follow panel height during resizing. The original
20 px artwork still matches the reference. Tested 16 height and display-scale
combinations in nested Plasma. Plasma checks passed 8/8, widgets 135/135,
Qt Quick 21/21, install 312/312 and nested install/undo 19/19. Local update
awaits the user's desktop review at their preferred 38 px height.

## 2026-11-21, Codex (GPT-6) — archive first desktop scaling comparison

Saved the user's three 3840 × 2160 Plasma screenshots at 100%, 150% and
200% under the private reference repository's testing folder. Each indexed
PNG matched the source checksum. Private backup commit `34dfcad`.

## 2026-11-21, Codex (GPT-6) — preserve personal cleanup files and repair Qt Quick model updates

Audited Claude's changes through `49c340b` and fixed findings #59–68 in
the working tree. Reinstall preserves copies and edits of the login hook.
Cleanup preserves an edited QML module, and an interrupted uninstall can
finish on retry. Backups restore GTK assets with a trailing newline in
their name. The dry run accounts for originals waiting to be restored.

Qt Quick combo lists now resize when a model renames an option. The idle
menu-bar comparison runs clear of the offscreen pointer. The install
instructions list the build dependencies and explain when Qt Quick apps
need a new login, both after the first switch and after an uninstall that
restores a personal file at the module path.

Verified 312 installer checks, 19 nested Plasma install/undo checks,
135 widget comparisons, 21 Qt Quick checks and seven Plasma artwork checks.
Three additional pairs of Fusion renders produced identical idle menu bars.
AUDIT.md records the reproductions, migration checks and test limits.
The fixes are in `ef8250a` and `fb4156f`. The later desktop captures are indexed above.

## 2026-11-21, Claude Code (Claude Opus 5.5) — fixes for findings #53–#58

- **Pass-through after uninstall (#54–#56, #58)**: never over anything of
  yours (a login script, a link or a file or folder at its places); removes
  only what it made; shown by a dry run.
- **Backslash in a copied file's name (#57)** no longer blocks uninstall.
- **Narrow combo boxes (#53)**: the Qt Quick list widens exactly as the
  widget one (QComboBox's width hint).
- Checks: install 272/272, live 19/19, Qt Quick 21/21.

## 2026-11-21, Codex (GPT-6) — audit uninstall cleanup and retest Qt Quick fixes

Reviewed `0cd95a2` and recorded #54–58 in AUDIT.md. The original inherited-launcher case now passes. Uninstall can overwrite a personal login script, and its next-login cleanup can delete a user's restored Kirigami link. Other rollback cases involve an occupied QML module path and an escaped filename in a valid checksum list. The packaging maintainer should address #54–57 before desktop installation. The dry-run omission and narrow combo width mismatch can wait.

All 429 project checks passed in disposable homes. The original 102 px combo fixture still reproduced #53 in a separate run. Instrumented Quick and decoration renders completed. Physical login and systemd behavior remain unverified. Only the review logs changed.

## 2026-11-21, Claude Code (Claude Opus 5.5) — fixes for findings #49–#53

- **Uninstall keeps the session's Qt Quick apps working (#49)**: a
  pass-through to KDE's style stays until the next login, then removes
  itself.
- **Profiles with none of the copied files (#50)** uninstall cleanly; a
  cut-short checksum list is now refused.
- **Menu icons in Qt Quick menus (#51).**
- **Keyboard focus shows on sliders (#52)**: widget and Qt Quick sliders
  and range slider handles.
- **Combo list check (#53)** no longer depends on the font; no binding
  loop of ours when an app switches styles.
- Checks: install 249/249, live 19/19, Qt Quick 19/19, style 135/135,
  Plasma 7/7.

## 2026-11-21, Codex (GPT-6) — audit Qt Quick packaging and desktop rollback

Recorded findings #49–53 against `88a3732` in AUDIT.md. The packaging maintainer should address two rollback cases before the first desktop install: a successful uninstall leaves existing launchers selecting a deleted Qt Quick module, and a valid empty config backup prevents uninstall. Qt Quick menu icons and range-slider focus also disappear. The combo popup differed from the widget fixture by one pixel in width.

Passed 230/230 installer, 17/17 nested live, 135/135 widget, 7/7 Plasma and 18/19 Qt Quick checks. Ran instrumented renderers, opened System Settings in nested KWin, and compared disposable-session screenshots. Real login, systemd, physical monitor transitions and upgrades remain unverified. Only the review logs changed.

## 2026-11-21, Claude Code (Claude Opus 5.5) — Qt Quick dialogs, drawers and range sliders (finding 3, step 6)

- **Dialogs**: the Mac OS 9 plain modal frame, measured from the captures
  and drawn by the style (`PE_PlatinumModalFrame`, pixel exact against the
  capture); white body; no dimmed window behind.
- **Drawers**: framed like a menu on the side that slides in.
- **Range sliders**: the Platinum slider groove with two Platinum thumbs.
- **Style**: sliders draw only the parts asked for (no change for QSlider).
- Checks: style 135/135, Qt Quick 19/19, install 230/230.

## 2026-11-21, Claude Code (Claude Opus 5.5) — install the Qt Quick style (finding 3, step 8)

- **install.sh / uninstall.sh**: install the Qt Quick style and Kirigami's
  plugin link for it (links are a new, checked target kind); the login
  script turns the Qt Quick style on only with Platinum selected, never
  over your own choice, and not after a KDE Frameworks upgrade.
- **Checks**: switches still toggle with Space and look the same to
  screen readers (`dev/quickkeys.cpp`, in `dev/check-quick.sh`, 13/13);
  real pop-ups in the nested KWin (`dev/quick-live.qml`); install 230/230,
  live 17/17.
- **Open**: a menu opened as its own window lands at the window's corner.

## 2026-11-21, Claude Code (Claude Opus 5.5) — Qt Quick Controls style (finding 3, steps 2-5 and 7)

- **`style/quick`**: the Platinum Qt Quick Controls style, built from the
  spike. Menus, the menu bar, the combo box's list (Mac style: over the
  button, current row checked), tooltips (the help balloon, laid out like
  the widget tooltip) and switches (drawn as check boxes) now match the
  widget style; everything else falls back to KDE's style, and so does
  everything when the app's style isn't Platinum. Not installed yet.
- **Checks**: `dev/check-quick.sh` 12/12 (widget equality and fallback
  equality); `dev/quick-inventory.qml` lists every control the plan covers.
- **Tools**: `dev/run.sh` takes `M9_QUICK=1`; `quickshot` shows its window
  on the offscreen platform so pop-ups place themselves correctly.

## 2026-11-21, Claude Code (Claude Opus 5.5) — Qt Quick spike (finding 3, step 1)

- **Spike** in `spikes/qtquick/`: a Qt Quick Controls style overriding
  tooltips and menus, falling back to KDE's, drawn by a small C++ item
  through the QStyle. Qt Quick menus now match widget menus pixel for
  pixel; the overrides follow the app's style at run time; plain Qt Quick
  apps are unaffected; Kirigami needs a link to KDE's platform plugin.
- **Style:** menu rows read their place (first, last, combo, shortcuts)
  from `styleObject` when there's no widget. Style 131/131, Plasma 7/7.
- Results in docs/FINDINGS.md; PLAN.md's plan updated with what changed.

## 2026-11-21, Claude Code (Claude Opus 5.5) — revise the Qt Quick plan (#43–#48)

Rewrote PLAN.md's plan for #3 after Codex's review: the fallback import
pinned to KDE's 1.0; the style on only when Platinum is selected, and each
override only while the app's style is Platinum; drawing through our own
small C++ Qt Quick item (public Qt API) so menu rows keep their first/last
bevels; list rows #CCCCFF and menus #333399 as in the captures; the combo
box's pop-up overridden on its own; pop-up captures that can't silently
miss the pop-up. The user chose our own drawing item (PLAN.md decision 13). Nothing built
yet.

## 2026-11-21, Codex (GPT-6) — audit the Qt Quick styling plan

Recorded plan findings #43–48 in AUDIT.md. A temporary tooltip override and KDE-backed button loaded together with an explicit KDE 1.0 fallback. The proposed auto-version import failed with and without the KDE platform theme. Further probes distinguished standalone menus from combo popups, and in-window from separate-window popup captures. Private reference pixels confirmed different highlight colors for lists and menus.

The style maintainer should revise the fallback, activation conditions, menu and combo coverage, selection fixtures and popup tests before packaging #3. Tests ran offscreen. System Settings, a real login and accessibility interaction remain unverified. This review changed the audit and changelog only.

## 2026-11-21, Claude Code (Claude Opus 5.5) — fixes for findings #39–#42

- **Two versions moved aside from one place (#39):** uninstall puts back
  the one from before the first install and keeps the later ones in the
  dated folder (`later-versions/`), naming them.
- **Config copy check (#40):** a file missing or changed anywhere in the
  copy, inside copied folders too, now stops uninstall before any change.
- **Empty folders you add (#41):** count as a change, so a reinstall moves
  the installed folder aside instead of replacing it.
- **Dry run (#42):** no more "No such file" lines on a fresh home.

Checks: install 214/214, live 15/15. Not run on the real desktop.

## 2026-11-21, Codex (GPT-6) — review repeated installs and backup integrity

Audited `cdbde37` and recorded #39–42 in AUDIT.md. Reinstall followed by uninstall can overwrite the original of two displaced color schemes. A missing child of a backed-up directory can also pass validation and disappear from the restored config. The packaging maintainer should address these two cases before the first real install. Empty user directories lost on reinstall and spurious dry-run diagnostics are lower priority.

Passed 193/193 installer checks, 15/15 nested live checks, 131/131 style regions and 7/7 Plasma regions. Rendered four scale factors, a maximized window and sanitizer builds of both renderers. Physical screens, real systemd recovery and library upgrades remain unverified. Only the audit and changelog changed.

## 2026-11-21, Claude Code (Claude Opus 5.5) — fixes for findings #34–#38; plan for #3

- **Links inside copied folders (#34):** install refuses them before any
  change, as it already did for linked entries.
- **Your additions and changes stay (#35):** the record keeps a checksum of
  every installed file; uninstall removes only files that still match, and
  a reinstall moves a changed one aside (put back on uninstall).
- **Checked config copy (#36):** the copy has a checksum list; uninstall
  refuses an incomplete or changed copy before changing anything.
- **Dry run (#37):** reports the same put-backs as the real run.
- **Shell left stopped (#38):** the next uninstall starts it again; the
  failing run exits 1 and says how to start it.
- **#3:** plan in PLAN.md (a small Qt Quick Controls style of our own that
  falls back to KDE's and draws menus, tooltips and switches through the
  QStyle). Nothing built yet.
- **Decisions (user):** right-to-left isn't supported (#26 closed,
  decision 11); #25 waits until going public and #23 is on hold
  (decision 12).

Checks: install 193/193, live 15/15. Not run on the real desktop.

## 2026-11-21, Codex (GPT-6) — audit rollback before the first desktop install

Recorded open findings #34–38 in AUDIT.md against `05cd9bd`. An apply/uninstall cycle changed a linked dotfile permanently, and plain uninstall deleted a user-added theme file. A missing backup file and a failed shell restart also exposed gaps in recovery. The dry-run collision warning can be deferred.

The sandbox passed 131/131 style regions, 7/7 Plasma regions, 155/155 installer checks and 14/14 nested live checks. Rendered four scale factors and ran the style and decoration renderers under ASan/UBSan. Physical mixed-DPI monitors, real systemd recovery and a plugin upgrade remain unverified. The packaging maintainer should address #34–36 and #38 before the first desktop install. This pass changed the two review logs only.

## 2026-11-21, Claude Code (Claude Opus 5.5) — fixes for Codex's findings #27–#33

Verified and fixed all seven (AUDIT.md has the per-finding table).

- **Uninstall can be run again safely (#27):** `uninstall.sh` takes each
  entry off the install record as soon as it's done. What it can't do stays
  on the record; it then exits 1 and says to run it again. A file it put
  back is never removed by a later run. New test: uninstall interrupted at
  16 points and run again leaves the home as before the install.
- **Platinum already selected (#28):** install copies the settings as they
  are before changing anything, so uninstall puts that state back.
- **Folder links pointed elsewhere (#29):** the record and the config copy
  keep where each path led; both scripts stop before any change if that
  differs now.
- **Leftovers by record only (#30):** temporary copies are recorded before
  they're made; nothing is removed just because of its name.
- **Same XDG folders (#31):** the record keeps the data and config folders;
  install and uninstall refuse to run with different ones (record format 3).
- **Reversed scroll bars (#32):** clicks on the track and arrows now move
  towards the click.
- **Live test (#33):** checks that the shell process was replaced and that
  panel widgets and a widget setting come back.
- **#21 closed by the user's decision:** the menu bar and the dock stay
  on the main screen only (PLAN.md decision 10; comment in
  `plasma/layout.js`).
- Also: a second uninstall no longer leaves an empty state folder with a
  lock file. README, DEVELOPMENT.md, FINDINGS.md and AUDIT-REQUEST.md
  updated; #26 widened to right-to-left scroll bars (they don't mirror).

Checks: style 131/131, Plasma 7/7, install 155/155, live 14/14. Not run on
the real desktop; the systemd restart path is still untested.

## 2026-11-21, Codex (GPT-6) — retest the packaging and theme audit fixes

Added #27–#33 to AUDIT.md after reviewing the working tree over `ece4355`.
All four suites passed (131 style regions, 7 Plasma comparisons, 94 install
checks and 10 running-shell checks). Both plugins rendered under ASan/UBSan.
A failed uninstall followed by a retry erased a restored user login hook in
a disposable home. An already-selected Platinum theme could also be reset
without a backup. Hold the real install pending packaging fixes and retry
coverage. The actual desktop and systemd restart remain untested.

This pass edited only AUDIT.md and CHANGELOG.md. The earlier implementation
edits and new live test were present before this audit. All remain uncommitted.

## 2026-11-21, Claude Code (Claude Opus 5.5) — fixes for Codex's pre-install audit

Verified Codex's findings #4–#25 and fixed all but the ones that are the
user's call (AUDIT.md has the per-finding table).

- **Packaging (#4–#14), rebuilt:** `scripts/common.sh`, `install.sh`,
  `uninstall.sh`.
  - Install checks everything it can before the first write. It writes the
    record before each change and moves aside anything in its way (put back
    on uninstall).
  - The config copy is taken at install and frozen at the switch. It covers
    the GTK files Plasma's GTK sync rewrites.
  - Install refuses symbolic links in the copy list, holds a lock, and
    fails the run if the theme switch fails.
  - Uninstall removes only recorded install targets of the recorded kind.
    It stops Plasma's shell while it restores the layout (the shell saves
    its layout on quit), starts it again, and keeps the copy it put back.
  - The plugins moved to `~/.local/lib/macos9-theme/`. The login script
    leaves the decoration off the plugin path when KDecoration was upgraded
    since the build.
  - Dry runs list every step.
- **Tests:** `dev/test-install.sh` rewritten: 11 scenarios, 94 checks,
  including install interrupted at 12 points. New
  `dev/test-install-live.sh`: nested KWin with two screens, plasmashell and
  kded6, 10 checks.
- **Style (#15–#19)** in `style/platinum/platinumstyle.cpp`:
  - 64-bit scroll bar and tick math.
  - A keyboard-only focus ring (#6666CC, not Mac OS 9).
  - A mixed check box (derived).
  - polish/unpolish put widget settings back.
  - Right-to-left: scroll bars honor `upsideDown`; pop-up menus, spin boxes
    and group boxes use Fusion. Menu items don't mirror yet (new finding
    #26).
- **Decoration (#20):** only the close, zoom and collapse boxes are created.
  `dev/kwin-test.sh` takes `M9_BUTTONS_LEFT` and `M9_BUTTONS_RIGHT`.
- **Plasma (#22):** readable selection text roles in `plasma/make-plasma.py`
  (regenerated `plasma/platinum/colors`).
- **#25:** `tools/gen-style-data.sh` no longer writes the raw crops with
  pointer pixels to `sprites.h` (the clean sprites are unchanged). README
  wording on provenance fixed.
- **Docs (#24):** `docs/DEVELOPMENT.md` (isolation per tool, both install
  tests), `README.md` (install, undo, upgrade), `AGENTS.md` and `PLAN.md`
  stale lines, `docs/FINDINGS.md` (new "Installing and undoing" section).

**Checks:**
- check-style: 131 of 131 regions.
- check-plasma: 7 of 7.
- test-install: 94 of 94.
- test-install-live: 10 of 10.
- ASan+UBSan style runs clean.
- No build warnings.

**Not verified:**
- uninstall's systemd path for the shell
- a real login
- anything on the user's screens

**Left for the user:**
- #21: one screen gets the menu bar and the dock (as on Mac OS 9), or every
  screen gets a menu bar.
- #25 before publishing.

**Still open:** #3, #23, #26 (P3).

The work is uncommitted at the time of writing.

## 2026-11-21, Codex (GPT-6) — independent pre-install audit

Added findings #4–#25 and updated the open list in AUDIT.md at commit
`591e96d`. Hold the first desktop install. A plain install destroyed
pre-existing same-name assets in a throwaway home. Applying and undoing
with kded6 running left GTK and xsettingsd changes behind. A linked
defaults directory lost its original contents, and a partial first
install left plugins without a manifest.

The baseline suites passed 131/131 style regions, 7/7 Plasma regions and
31/31 install assertions. Two virtual outputs confirmed that both new
panels land on screen 0. Offscreen keyboard tests at four scales confirmed
invisible focus on buttons, check boxes and tabs. Both plugin render
harnesses ran under ASan/UBSan. The history review found sampled glyph
and pointer data in source tables.

Only AUDIT.md and this entry changed. The review and test images stayed
local. A real user-systemd shell restart, a package upgrade and interaction
on the physical displays remain unverified. Packaging should address and
retest #4–#12 before the first real install. Publication needs a separate
asset review under #25. These two documentation edits are uncommitted.

## 2026-11-21, Claude Code (Claude Opus 5.5) — packaging: install and uninstall scripts

Claimed `packaging` (and `shared` for scripts/dev/docs), released at the
end. Over Remote Control. Nothing was installed on the user's desktop.

- `install.sh`: builds the style and decoration plugins and installs them
  under `~/.local/lib/qt6/plugins`, a Plasma login script
  (`~/.config/plasma-workspace/env/macos9-theme.sh`) that adds that folder
  to `QT_PLUGIN_PATH`, the color scheme, Plasma style, menu bar widget and
  global theme; records everything in `~/.local/state/macos9-theme`.
  `--apply` copies the config files the switch touches (whole files:
  kdeglobals, kwinrc, plasmarc, kcminputrc, ksplashrc, the panel layout,
  plasmashellrc, kdedefaults/), applies the global theme with the plugin
  folder on `QT_PLUGIN_PATH`, and sets the button order. `--dry-run`.
- `uninstall.sh`: keeps the current config files in
  `~/.local/state/macos9-theme-uninstalled-DATE`, puts back the copies
  (removing files that didn't exist), removes every recorded file and the
  folders it made, restarts plasmashell through systemd if it runs.
- `scripts/common.sh` (adapted from windows2000-union), `dev/test-install.sh`
  (throwaway home, private D-Bus and runtime folder, stand-in systemctl):
  31 of 31.
- README: install / uninstall instructions. docs/DEVELOPMENT.md,
  docs/FINDINGS.md.

Not done: a run on the real desktop (the user's call, at the PC); the
panel layout switch and the shell restart only run with Plasma.

## 2026-11-21, Claude Code (Claude Opus 5.5) — plasma: the dock

Claimed `plasma` (and `shared` for dev/docs), released at the end. Over
Remote Control. The user's design decision (PLAN.md decision 9): bring the
dock over, designed around the Mac OS 9 look.

- Design: a bottom panel (52 px, sized to its apps, centered) drawn as
  Mac OS 9's pop-up window tab (the OS 9 element that already lives on the
  bottom screen edge): rounded top corners, white highlight, `#CCCCCC`,
  `#999999` edge and `#444444` shadow. Apps are the Monitors / Launcher
  bevel buttons: pinned = bare icon, running = raised, active = selected.
- `plasma/make-plasma.py`: `south-` panel background elements (the menu
  bar keeps the unprefixed ones), `widgets/tasks.svg` with insets built
  into the frames. `plasma/layout.js` (and so the global theme): the dock
  with Dolphin, Kate and System Settings pinned.
- `dev/plasma-session.sh` opens a second window so the dock shows both
  running states; `dev/check-plasma.sh` checks the dock's corners.
- docs: REFERENCE (pop-up tab outline), FINDINGS (south prefix, task
  insets), DEVELOPMENT.

Checks: `dev/check-plasma.sh` 7 of 7 exact. Headless only; the user's
next live test shows it (`dev/live-test.sh` uses this layout). From the
previews: "I love it so far".

## 2026-11-21, Claude Code (Claude Opus 5.5) — plasma: bar ends, divider, look-and-feel package

Claimed `plasma` (and `shared` for dev/docs), released at the end. Over
Remote Control.

- `platinum.menubarpiece` plasmoid (generated by `plasma/make-plasma.py`
  into `plasma/plasmoids/`): draws the menu bar's rounded ends (measured
  8x20 each, with the bar's white / gray edges following the curve) and
  the divider before the Application menu (6x20, the dotted grip), as
  pixel runs. `plasma/layout.js` puts a piece at each end and before the
  Window List.
- `plasma/look-and-feel/platinum.desktop` (generated; its layout is copied
  from `plasma/layout.js`): color scheme, Platinum widget style, Plasma
  style, Platinum decoration; icons and cursors Breeze for now.
- `dev/plasma-test.sh`: `M9_APPLY=lnf` applies the package in the sandbox
  and prints what it set; `XDG_CONFIG_DIRS` includes `kdedefaults` like a
  real session. `dev/check-plasma.sh` also checks both ends and the
  divider. `dev/live-test.sh` installs the plasmoid into the sandbox too.
- docs/FINDINGS.md: Plasma facts (panel borders at screen edges, applet
  height, global menu colors, kdedefaults, button order not applied).

Checks: `dev/check-plasma.sh` 5 of 5 exact; `dev/check-style.sh` 131 of
131. Headless only.

Next: a neutral icon for the Apple menu stand-in, the spacing around the
clock and divider, then install / uninstall scripts (they must write the
button order, back up the user's settings, and undo everything).

## 2026-11-21, Claude Code (Claude Opus 5.5) — step 5: Plasma style and menu bar

Claimed `plasma` (and `shared` for dev/docs), released at the end. Done
over Remote Control. Decisions recorded in PLAN.md: icons from an existing
set (7), cursors our own or a temporary Mac OS X pack (8); the menu bar
layout (6).

- `plasma/make-plasma.py` (9-patch writer from the user's
  windows2000-union, BSD-2-Clause) writes `plasma/platinum/`: the 20 px
  menu bar panel, Lavender open menu titles (`menubaritem`), popups in the
  Mac menu frame, help-balloon tooltips, `#333399` list highlights, push
  buttons and tool buttons from the style's measured nine-slices, text
  fields with the focus ring, frames, the open-applet look (derived
  `#CCCCFF`), etched popup headings, and a `colors` file (the menu
  highlight as the selection, white text, for Plasma only).
- `plasma/layout.js`: one top panel: Kicker (Apple menu stand-in, neutral
  icon for now), global menu, spacer, system tray, clock, Window List
  (Application menu stand-in); a plain desktop color close to the default
  pattern's.
- `dev/plasma-test.sh` + `dev/plasma-session.sh`: nested plasmashell with
  a fresh layout, `kded6` for the global menu, its own Desktop folder;
  screenshots of the desktop, an open menu and the launcher.
  `dev/check-plasma.sh` compares the bar and an open title with the
  captures (both exact).
- `dev/live-test.sh` / `dev/live-session.sh`: the user's live test now
  runs the Plasma shell with this layout by default (`M9_PLASMA=0` to
  skip); the session waits only on the apps.
- `docs/REFERENCE.md`: the rest of the menu bar (corners, titles, clock,
  divider, Application menu). `docs/DEVELOPMENT.md`: the Plasma tools.

Checks: `dev/check-plasma.sh` 2 of 2 exact; SVGs valid. Not seen by the
user (headless only). Limits in AUDIT.md.

Next (plasma): a neutral Apple menu icon, the divider before the Window
List, rounded screen corners (maybe not possible), title font (bold, like
Charcoal), then a look-and-feel package with this layout for the install.

## 2026-11-21, Claude Code (Claude Opus 5.5) — real-app pass, Qt Quick, tooltips

Claimed `style` and `shared`, released at the end. Done over Remote
Control.

- Real apps, headless (`dev/app-test.sh` with `QSTYLE=Platinum`,
  `M9_DECORATION=platinum`): Dolphin and Kate look Platinum throughout.
  System Settings first looked untouched: `dev/run.sh` wrote
  `widgetStyle=Union` into the sandbox even with `QSTYLE`, so Qt Quick used
  `org.kde.union`. Now `dev/run.sh` writes `QSTYLE` as the widget style,
  KDE picks `org.kde.desktop`, and Qt Quick apps draw their controls
  through the Platinum style (docs/FINDINGS.md). This also applies to
  `dev/live-test.sh`, so the user's next live test will show it.
- Tooltips: Mac OS 9 help balloons without the tail (white, 1 px black
  top/left, 2 px right/bottom, measured corners; top-right derived),
  see-through corners, 10 px padding.
- `dev/check-style.sh`: the balloon outline by pixel class (131 regions).
- AUDIT finding 3 (open): Qt Quick menus, tooltips and switches are drawn
  by qqc2-desktop-style itself, not through the QStyle.

Checks: `dev/check-style.sh` 131 of 131; ASan + UBSan clean (styleshot,
tooltip, Kirigami gallery). Not seen live by the user.

Next: the user's live check (now with Qt Quick themed), then finding 3
(how to reach Qt Quick menus / tooltips), editable combo boxes, the size
grip.

## 2026-11-21, Claude Code (Claude Opus 5.5) — step 4: application style, batch 7 (tool buttons)

Claimed `style` (and `shared` for tools/dev/docs), released at the end.
Done over Remote Control.

- Tool buttons (`QToolButton`) as Mac OS 9 bevel buttons, always drawn:
  toolbar (auto-raise) buttons use Mac Help's small square 25x25 bevel
  (16 px icons; pressed / checked derived from the large bevel's color
  change), others the Monitors panel's large rounded bevel (normal and
  selected both measured). Menu buttons get a second bevel with the arrow;
  buttons with a menu a small triangle (derived). Pressed / checked text
  is white.
- Toolbars: no background or handle (window gray, like Mac Help's);
  separators are the etched `#888888` / white pair.
- `tools/gen-style-data.sh`: `BevelNormal`, `BevelPressed`, `ToolNormal`
  nine-slices. `dev/styleshot.cpp` / `dev/check-style.sh`: the three
  bevels. `dev/livedemo.cpp`: a toolbar (back, disabled forward, home,
  separator, two checkable view modes).
- `docs/REFERENCE.md`: bevel button sizes.

Checks: `dev/check-style.sh` 130 of 130 regions pixel exact; ASan + UBSan
clean. Not seen live by the user yet (batches 5 and 6 neither); from the
previews sent to the phone: "everything is looking great so far".

Next: the user's live check of batches 5-7; then editable combo boxes, the
size grip, and a pass over real apps (Dolphin, Kate, System Settings) for
whatever is still Fusion.

## 2026-11-21, Claude Code (Claude Opus 5.5) — step 4: application style, batch 6 (groups, lists)

Claimed `style` (and `shared` for tools/dev/docs), released at the end.
Done over Remote Control.

- Group boxes (`QGroupBox`): the etched `#888888` / white rectangle from
  General Controls, title 13 px in with its bottom row on the top line and
  a 4 px gap each side; checkable ones put the check box there; flat ones
  draw only the top line pair.
- Separators (`QFrame` HLine / VLine): `#888888` and white lines.
- List headers (`QHeaderView`): the Finder's 21 px sections as nine-slices
  (normal and the darker sorted column), label 8 px in, no sort arrow; the
  empty area after the last section closes it.
- Disclosure triangles (`PE_IndicatorBranch`): measured closed and open
  sprites, no tree lines. A pressed sprite is generated too (pointer
  pixels removed), unused since Qt has no pressed branch state.
- Scroll-area frames (`PE_Frame`, `PM_DefaultFrameWidth` 2): the text
  field's sunken edge and black line (derived; no capture of a Platinum
  list box frame).
- `tools/gen-style-data.sh`: header nine-slices and triangle sprites.
  `dev/styleshot.cpp` / `dev/check-style.sh`: group box, headers,
  triangles, separator. `dev/livedemo.cpp`: the old "Not Themed Yet" tab is
  now "Lists & Groups" (group boxes, separator, sorted tree; only the
  editable combo box is still Fusion).
- `docs/REFERENCE.md`: group box, separator, list header, triangle
  sprites, Standard File list box.

Checks: `dev/check-style.sh` 118 of 118 regions pixel exact; ASan + UBSan
clean. Not seen live by the user yet. Batch 5 (text fields) is also still
uncommitted in this working tree.

Next: editable combo boxes, the mixed check box, the size grip, tool
buttons (toolbars), then a wider pass over real apps (Dolphin, Kate,
System Settings) for whatever is still Fusion.

## 2026-11-21, Claude Code (Claude Opus 5.5) — step 4: application style, batch 5 (text fields)

Claimed `style` (and `shared` for tools/dev/docs), released at the end.
Done over Remote Control.

- Text fields (`QLineEdit` with a frame): measured from the Fonts tab's
  size fields: 1 px margin, 1 px sunken edge (`#888888` / white), black
  line, white inside, text 3 px in; 26 px minimum height. Focused (and the
  window active, not read-only): the 2 px `#6666CC` ring in place of the
  margin and edge, corners cut.
- Spin boxes (`QSpinBox`, `QDoubleSpinBox`): the same field plus the
  Appearance control panel's rounded 22x20 little arrows, 2 px to its
  right (sprite in `sprites.h`); the pressed half (not captured) is drawn
  like a pressed push button. Frameless line edits get no size padding, so
  spin boxes and line edits are both 26 px.
- `dev/styleshot.cpp` / `dev/check-style.sh`: both Fonts tab spin boxes;
  `dev/livedemo.cpp` has text fields and a spin box on its Controls tab.
- `docs/REFERENCE.md`: text field and little arrows (with Memory's older
  stacked variant).

Checks: `dev/check-style.sh` 103 of 103 regions pixel exact; ASan + UBSan
clean. Not seen live by the user yet.

Next batch: group boxes, list and text area frames, list headers and
disclosure triangles; editable combo boxes after that.

## 2026-11-21, Claude Code (Claude Opus 5.5) — step 4: application style, batch 4 (menus)

Claimed `style` (and `shared` for tools/dev/docs), released at the end.
Done from the user's phone over Remote Control; nothing needed the VM.

- Menus (`QMenu`): measured frame (black line, white/`#999999` bevel,
  `#222222` drop shadow, see-through outer corners via
  `WA_TranslucentBackground` and a 1 px right/bottom contents margin),
  16 px items (18 with an icon), 6 px separators, Lavender highlight
  bevel, check mark 4 px in (left of the icon; icon 19 px in, label 22 or
  41 px in), submenu arrow, shortcut column ending 21 px before the edge.
  Fixes AUDIT finding 2 (Fusion's frame around a checked icon).
- Pop-up menu lists (`QComboBox` popups): the same menu look; the list is
  see-through and each item draws its slice of the bevel, because Qt's
  delegate fills items first (docs/FINDINGS.md).
- Menu bar (`QMenuBar`): 20 px bar (white top row, `#999999` and black at
  the bottom), open title in the Lavender bevel, titles padded 7 px.
- `tools/gen-style-data.sh` writes `style/platinum/menu.h`: the check mark
  as a coverage mask (any color) and as a sprite on the highlight (Mac OS 9
  blends it to `#FEFEFE` there).
- `dev/styleshot.cpp` renders a real QMenu (the Finder's View menu), a
  real combo popup (Appearance's Highlight Color list) and menu bar
  titles; `dev/check-style.sh` compares them. `dev/livedemo.cpp` has a menu
  bar (File / View / Special with checks, icons, a submenu, shortcuts) and
  a right-click menu.
- `docs/REFERENCE.md`: menu frame, items, separator, highlight, check mark
  and arrow, pop-up list, menu bar title.

Checks: `dev/check-style.sh` 93 of 93 regions pixel exact; ASan + UBSan
clean. The user tried it live (`dev/live-test.sh`): looks good, no findings.

Next batch: text fields and the 2 px `#6666CC` focus ring, then group
boxes, list headers + disclosure triangles, mixed check box, size grip.

## 2026-11-21, Claude Code (Claude Opus 5.5) — live test script, document-mode tabs

- `dev/live-test.sh` + `dev/live-session.sh` + `dev/livedemo.cpp`: the
  theme on the user's own desktop for trying by hand: a windowed nested
  KWin (sandboxed config, private D-Bus, nothing installed) with the
  Platinum decoration, style and colors, running an interactive demo of
  every themed control, Dolphin and Kate. Documented in
  `docs/DEVELOPMENT.md`.
- First live test by the user: two findings (AUDIT.md 1-2).
- Style fix (finding 1): document-mode tab widgets (KDE settings pages)
  now get the Platinum pane; Qt draws none there, which left a white seam
  under the tabs. The pane rect is computed the same way in both modes.
  Icon tabs use the Platinum label area and colors (were Fusion's, text
  clipped); `PM_TabBarTabVSpace` = 0.
- Finding 2 (Fusion's frame around a checked menu item's icon, touching
  the menu border) waits for the menu batch.

Checks: `dev/check-style.sh` 78 of 78; document mode renders identical to
normal mode offscreen. Not yet seen by the user after the fix.

Next (user's call, asked 2026-11-21): the menu batch (finding 2,
`menu-view-checked.png`, `menu-file-open.png`, `menu-submenu.png`,
`popup-open.png`) or text fields + focus ring first. Also open: how
standalone document-mode tab bars (Dolphin/Kate document tabs) should look.

## 2026-11-20, Claude Code (Claude Opus 5.5) — step 4: application style, batch 3 (tabs)

Claimed `style` (and `shared` for the tools/dev/docs edits), released at
the end.

- Tabs (north tab bars): drawn row by row from measured edges. New
  `tools/tabs.py` reads each tab state's left and right edge, row by row,
  from a tab whose edge has no neighbor (first tab's left, last tab's
  right) and writes `style/platinum/tabs.h`; the pressed tab's right edge
  turned out to be clean in `tab-pressed.png` (the pointer is inside the
  tab), so nothing is derived. Fill per row = first color repeated 3 times
  after the edge (labels can start right after the edge).
- Tab pane (`PE_FrameTabWidget`): a measured 9-slice (`TabPane`, added to
  `tools/gen-style-data.sh`); `PE_FrameTabBarBase` draws the pane's top
  3 rows under a lone `QTabBar`.
- Metrics: tab height 24 (21 + the 3 pane rows it overlaps), width = text
  + 24, no tab overlap, first tab 5 px in from the pane, contents 3 px
  inside the pane. Label centered in the 20 rows below the top line, black,
  white on the pressed tab, `#777777` disabled. No focus rectangle on tab
  bars. `SH_TabBar_SelectMouseType` = release: the tab shows pressed while
  held and switches on release, as in Mac OS 9.
- `dev/styleshot.cpp` lays out the Appearance control panel's six tabs
  three times (Themes current with the whole pane; Appearance current with
  Sound pressed; Options current); `dev/check-style.sh` compares them.
- `docs/REFERENCE.md`: tab shape, tab row layout and pane rows.

Checks: `dev/check-style.sh` 78 of 78 regions pixel exact (31 new tab
regions). A live `QTabWidget` (offscreen) lays out as measured: tab bar at
x=5, tab widths = text + 24, page at the pane's inside; a press on "Sound"
keeps "Themes" current until release. First ASan + UBSan run of the style
(styleshot and the tab test): no reports, identical render.

Not done: vertical (west/east) and south tabs still come from Fusion;
pressing the current tab and disabled tabs were not captured (current look
kept / normal shape with gray label); labels use the substitute font, so
widths differ from Charcoal's by a few pixels.

Next batch: text fields and the 2 px `#6666CC` focus ring, then group
boxes, list headers + disclosure triangles, menus, mixed check box, size
grip.

## 2026-11-20, Claude Code (Claude Opus 5.5) — step 4: application style, batch 2

Claimed `style`, released at the end. Tabs moved to their own batch: their
slanted, overlapping edges need clean ends from several captures.

- Pop-up menus (non-editable combo boxes): measured body 9-slice plus a
  22-column arrow box sprite, normal / pressed / disabled; label black or
  `#777777`. The pressed box is merged from two captures (pointer in each).
- Sliders: 7-row groove from measured end pieces and a stretched middle
  column (disabled: 5 rows, no outer lines), 15×16 thumb sprites (normal,
  pressed, disabled), tick marks (white, black, `#888888`) under the
  thumb's center; vertical sliders transposed.
- Progress bars: drawn column by column from profiles measured in the 55 %
  frame (frame, fill start, fill middle, fill end, black divider, 2-column
  trough shadow, trough, last column); 0 % matches the empty copy window.
  The barber pole uses the measured stripe ramps, 8 px Lavender / 8 px
  gray, slanting one pixel per row, moving 20 px/s; busy bars get a
  100 ms repaint timer from `polish()`. No text, as in Mac OS 9.
- `tools/gen-style-data.sh` also writes `progress.h` and the new sprites;
  `dev/styleshot.cpp` and `dev/check-style.sh` cover the new widgets.

Checks: 47 of 47 regions pixel exact; the gallery renders. Limits in
AUDIT.md.

## 2026-11-20, Claude Code (Claude Opus 5.5) — step 4: application style, batch 1

Claimed `style`, released at the end (more batches to come).

- `style/platinum/`: a Qt style plugin ("Platinum", a QProxyStyle over
  Fusion, built by `style/build.sh`). Themed so far: scroll bars (vertical
  from the spike, horizontal by transposition), push buttons (normal,
  pressed, disabled, default ring, default pressed), check boxes and radio
  buttons (captured states plus derived pressed-on / disabled states), no
  focus rectangle on buttons. Metrics in `Metrics` in `platinumstyle.h`.
- Measured data instead of hand-coded pixels: `tools/nineslice.py`
  (9-slice tables, checks edge uniformity, marks only background connected
  to the outside), `tools/sprite.py` (fixed-size parts), and
  `tools/gen-style-data.sh`, which regenerates `slices.h` and `sprites.h`
  from the captures and repairs the few pointer-covered pixels from the
  unpressed outline. The default ring measured from two different captures
  came out identical (289 values).
- `dev/styleshot.cpp` + `dev/check-style.sh`: render every state through
  the style's draw calls at the captures' sizes and diff them;
  `dev/run.sh` now puts the built style and decoration on QT_PLUGIN_PATH
  and only links folders with `contents/` as Union styles.

Checks: `dev/check-style.sh` 31 of 31 regions pixel exact; the widget
gallery renders with the style. Limits in AUDIT.md (labels, derived states,
offscreen only). PLAN.md notes that the measured check mark and radio dot
should be redrawn by hand before any public release.

Next batches: pop-up menus (combo boxes), tabs, sliders, progress bars
(determinate and barber pole), text fields and focus ring, group boxes,
list headers and disclosure triangles, menus, the mixed check box, the size
grip.

## 2026-11-20, Claude Code (Claude Opus 5.5) — step 4: window decoration plugin

Claimed `decoration`, released at the end.

- `decoration/platinum.{h,cpp,json}` + `build.sh`: a KDecoration3 plugin,
  structure adapted from the user's windows2000-union decoration. 6 px
  frame with raised and sunken bevels, 22-row title bar, close / zoom /
  collapse boxes (normal and pressed), etched pinstripes, centered icon and
  title (condensed, then dropped when too long), flat inactive look with
  `#555555` lines, hard 1 px drop shadow (black / `#555555`). All metrics in
  `Metrics` in `platinum.h` (true 1x). Builds with no warnings.
- Measured on the way: the full window frame, inactive lines `#555555`,
  pressed box ramp `#44`→`#CC` capped at `#99` on its last row/column.
  REFERENCE.md "Window frame".
- Found: Wayland windows report `isShadeable() == false` in KWin 6.8.3, so
  the Shade button never shows; the minimize button now wears the collapse
  box and the Mac layout is `X` | `AI`. KWin's decoration preview ignores
  the button layout, draws no shadow and is 1 px smaller. FINDINGS.md.
- `dev/`: `decoshot.cpp`, `decoration.qml`, `shoot-deco.sh` from
  windows2000-union, adapted; `kwin-test.sh` / `app-test.sh` set the Mac
  layout with `M9_DECORATION=platinum`; `VT_SINGLE=1` for one window.
  DEVELOPMENT.md section "The window decoration".

Checks: every frame region compared is pixel exact against the captures,
active (nested KWin, KWrite), inactive and pressed (preview). Details and
limits in AUDIT.md: title text, the drop shadow, maximized and X11 windows
aren't verified, nothing is installed, and the user hasn't seen it.

## 2026-11-20, Claude Code (Claude Opus 5.5) — step 4: color scheme

Claimed `colors`, released at the end.

- Measured the remaining text colors: disabled text is `#777777` everywhere
  (menu items, button labels), inactive title and header text `#777777`,
  inactive title bar face `#DDDDDD`, links `#0000FF`. Added to REFERENCE.md.
- `colors/Platinum.colors`: Window/Button/Header `#DDDDDD`, View and
  Tooltip `#FFFFFF`, Selection `#CCCCFF` with black text, focus/hover
  decoration `#6666CC`, links `#0000FF`, `[WM]` title faces
  `#CCCCCC`/`#DDDDDD`. Disabled text comes from a contrast fade of 0.54,
  which turns black on `#DDDDDD` into exactly `#777777` without touching
  backgrounds. Inactive-window effects off. Not measured (Mac OS 9 has no
  such colors): negative/neutral/positive, visited links, Complementary;
  the file's header says so. The menu highlight (`#333399`, white text)
  can't share KDE's single Selection group with text selection; the C++
  style will draw it.

Checks: the file parses (13 sections, all 12 keys in each of the 8 color
groups, every value a valid RGB triple); `dev/shoot.sh breeze platinum`
renders the widgets, Quick and Kirigami galleries with it; in the widgets
render the selected row is exactly `#CCCCFF`, views `#FFFFFF`, and disabled
button and check box labels exactly `#777777` on `#DDDDDD`. Shapes are still
Breeze's (no Platinum style yet). Not installed or applied to the desktop.

## 2026-11-20, Claude Code (Claude Opus 5.5) — step 3 spikes: style and decoration engines

Claimed `style` and `decoration` for the spikes, released at the end.
Details and numbers in the new `docs/FINDINGS.md`.

- `spikes/scrollbar/probe.cpp`: Union 6.8.3 gives a scroll bar's arrow,
  groove and page areas 0×0 (Qt Windows/Fusion give 16×16 arrows), so
  Union can't draw Platinum scroll arrows.
- `spikes/scrollbar/platinum.cpp`: a C++ QProxyStyle (over Fusion) drawing
  a vertical Platinum scroll bar from the measured values. After three
  fixes (thumb shadow start, grip `#EEEEEE` pixels, track starting below
  the bar's top edge) it matches two captures pixel exact: 0 of 5536 px
  (System Folder, thumb at top) and 0 of 5152 px (Applications, thumb
  partway down).
- Aurorae (read in `/usr/share/kwin/aurorae/aurorae.qml`): the title is
  elided `Text` over a fixed FrameSvg, so no pinstripe gap around the
  title, no condensing, no dropping.
- `spikes/titlebar/titlebar.cpp`: a QPainter Platinum title bar (frame,
  drop shadow, three boxes with their gradient and glyphs, etched
  pinstripes); first try pixel exact on both sides of the title in the
  417 px Mac OS window (0 of 6940 px) and in the 289 px long-title window
  (0 of 920 px left; 2 of 980 px right, both in the drop-shadow corner
  where the window behind shows).

PLAN.md decisions 2 and 3: the user approved C++ for both (C++ QStyle,
C++ KDecoration3), same day. Not checked: pressed/inactive states in the spikes, horizontal bars,
title text, real KDecoration3 plugin, Qt Quick apps through
qqc2-desktop-style, Kvantum (not installed).

## 2026-11-20, Claude Code (Claude Opus 5.5) — step 2: sandbox, compare tool, scale

Claimed `shared` for PLAN step 2, released at the end.

- `dev/`: ported the generic parts of the user's windows2000-union test rig
  (BSD-2-Clause): `run.sh` (sandbox; schemes `platinum`/`breeze`/`user`/file,
  every folder under `style/` linked as a Union style, new `EXTRA_FONT_DIRS`
  for stand-in fonts, Wine Tahoma bits dropped), `build.sh` (gallery,
  quickshot, tabdemo, fakeinput; decoration tools deferred), `shoot.sh`,
  `kwin-test.sh` / `app-test.sh` (decoration chosen with `M9_DECORATION`,
  default Breeze), session scripts, test QML/C++ and the fake-input
  protocol. `dev/shots/` git-ignored.
- `tools/compare.py`: `row`, `col`, `colors`, `bbox`, `zoom`, and `diff`
  (same-size regions, any image with an `@X,Y,W,H` crop; counts, max
  difference, bounding box, side-by-side picture, exit 1 on differences).
- `docs/DEVELOPMENT.md`: how to use both. AGENTS.md and PLAN.md point to it.

Checks: `dev/build.sh` builds all four tools; `dev/shoot.sh breeze breeze`
renders the widgets, Quick and Kirigami galleries; `dev/kwin-test.sh breeze`
screenshots two Breeze windows in a nested KWin. `compare.py` reproduces
earlier hand measurements (selected bevel button column, 12×12 check box),
gives 0 / 120 differing pixels for identical / normal-vs-pressed check box
crops, refuses crops outside the image, and runs clean under
`-W error::DeprecationWarning`. No shellcheck on this machine. Found on the
way: the watch cursor crop has two `#9C9C63` pixels (the desktop color
inverted), so Mac OS cursors can invert pixels, not just paint them.

Decision 1 (scale) settled by the user: true 1x at Plasma 100%, to be
tweaked after testing; recorded in PLAN.md with the numbers behind it.

Next: step 3 spikes (style engine, decoration engine), or measuring passes
per component.

## 2026-11-20, Claude Code (Claude Opus 5.5) — reference capture tool

The user set up Mac OS 9.2.2 in QEMU (`/mnt/storage1/local/VM/mac-os-9`,
QEMU 9.1 screamer fork). It was started without a QMP socket, so it can't be
captured yet.

- `tools/capture.py`: connects to QEMU's QMP socket, runs `screendump`
  (PPM, because this QEMU build has no libpng), converts it to PNG with
  Pillow, checks that the PNG matches the PPM pixel for pixel, and logs time,
  size, and sha256 in `reference/INDEX.tsv`. Never overwrites, names limited
  to `[a-z0-9._-]`.
- Tested against a second, throwaway headless QEMU (OpenBIOS, no disk):
  800×600 capture saved and logged, overwrite and bad name refused. Not yet
  run against the real VM.
- AGENTS.md: reference VM facts and capture rules. PLAN.md: step 1 status.

Later the same day: the user relaunched the VM with
`-boot c -qmp unix:$XDG_RUNTIME_DIR/mac9-qmp.sock,server=on,wait=off`;
`--check` reported QMP ok. First real capture
`reference/desktop-first-check.png`: 1440×1050, crisp 1x, logged in
INDEX.tsv, and git ignores it as intended. Started `docs/REFERENCE.md` with
the guest resolution, desktop base color `#63639C`, and the 20 px menu bar
(1 px `#FFFFFF`, 17 px `#DDDDDD`, 1 px `#999999`, 1 px `#000000`).

Then captured every tab of the Appearance control panel
(`reference/appearance-1-themes.png` … `appearance-6-options.png`) and
recorded the settings in `docs/REFERENCE.md`: Mac OS Default theme, Apple
platinum, Purple highlight, Lavender variation, Charcoal / Geneva / Geneva
10, smoothing from 12 pt, Mac OS Default pattern, Platinum Sounds, Smart
Scrolling on, double-click collapse off. Alt+Tab out of the VM typed `^` into
the focused size box twice; the user retyped 10 and 12, and
`appearance-3-fonts-clean.png` is the clean Fonts capture. Release the VM
with Ctrl+Alt+G before switching away.

Then wrote `docs/CAPTURES.md`: the checklist of states to capture (eight
groups, priority A/B/C, with names, setup steps, and which theme part each
serves), and added `--delay SECONDS` to `tools/capture.py` so the user can
hold a button down while it captures (countdown, then a terminal beep;
tested 2.5 s against a throwaway QEMU). Linked from AGENTS.md and PLAN.md.

Group 1 started: `window-close-pressed.png` (user ran it with `--delay`;
the pressed close box is a dark gradient, the cursor covers its lower-right
corner). INDEX.tsv had two entries for it because the user deleted a
failed first try (empty shot) and retook it; I removed the deleted one's
line. While checking, I found that two overlapping runs with the same name
could both pass the exists check before `--delay` ends, so the PNG is now
created with `open(..., "xb")` and each run uses its own temp PPM: an
overlapping run refuses instead of overwriting (tested with two overlapping
runs against a throwaway QEMU). Deleting a bad capture and retaking it
under the same name is fine; remove its INDEX line too.

Group 1 (windows and title bars) finished, 12 captures; details are in
the ticked items of `docs/CAPTURES.md`. Findings for the decoration:

- Pressed close/zoom/collapse boxes fill with a dark gradient, glyphs stay.
- Inactive windows drop the pinstripes, all three boxes, scroll arrows, and
  the size box grip; title and header text turn gray.
- Long titles are drawn condensed first; when even that doesn't fit, the
  text is dropped and only the title icon stays (no "…" seen; an
  in-between ellipsis stage is unchecked).
- Moving and resizing draw an outline (every other pixel color-inverted)
  instead of moving the window; the resize outline sketches the frame and
  title bar. KWin likely can't do this; to check.
- A collapsed window keeps its full title bar and frame.

At the user's request, `reference/` became its own git repo, pushed to the
**private** GitHub repo `orlfman/macos9-theme-reference` as a cloud backup
(21 captures, INDEX.tsv, a README warning it must stay private, and a
.gitignore for capture.py's temp PPMs). This repo keeps ignoring
`reference/`. AGENTS.md says how to clone it and when to push captures.

Group 2 (dialogs and alerts) finished: 8 captures plus the user's extra
System Profiler list shot (`list-view-profiler-applications.png`). Findings:

- Alerts and movable modals share a frame with a pinstriped drag strip and
  no title. The Finder's Empty Trash alert has a **red-tinted** strip
  (`#FFCCCC`/`#FF6666`/`#FF9999` instead of `#CCCCCC`/`#777777`/
  `#999999`); unconfirmed, check against real hardware.
- SimpleText uses the classic Standard File Open and Save As dialogs (plain
  modal frame, no title bar); a Navigation Services dialog is still to get.
- Get Info windows have no zoom box. Classic Dialog Manager text fields
  (SimpleText Find) have no focus ring; Appearance-aware ones do.
- First list and scroll bar values went into REFERENCE.md: Purple
  selection `#CCCCFF`, active track `#AAAAAA`, Lavender scroll box
  `#CCCCFF` with `#333399` grip lines, sorted column header `#888888`.
- Renamed two captures: the accidental Save As shot is
  `dialog-save-as-standard-file.png`, the user's extra shot is
  `list-view-profiler-applications.png` (INDEX.tsv updated).

Group 3 (buttons and toggles) finished: General Controls, Memory, Monitors,
open pop-ups, Finder list with disclosure triangles, and pressed states for
check box, radio, slider, triangle, push and default buttons. Measured into
REFERENCE.md (sizes and pixel rows):

- Check boxes and radios are 12×12; disabled ones are flat `#888888`
  outlines; pressed ones go dark with the bevel reversed.
- Pressed push buttons, selected bevel buttons, and the inside of a pressed
  default button share one look: `#444444`/`#555555` top, `#666666` fill,
  `#777777`/`#888888` bottom, white label. The default ring never changes.
- Sliders don't track live: the real thumb darkens to `#6666CC` and a gray
  ghost follows the pointer.
- Menus: `#DDDDDD`, highlight `#333399` with white text, `#999999` inner
  shadow, black border, 1 px `#222222` drop shadow. Pop-up menus open over
  the control with the current item in place; Mac OS 9 menus stay open after
  one click, so open menus need no `--delay`.
- Disclosure triangles: Lavender with black outline and gray shadow, dark
  `#333399` when pressed, Lavender even in inactive windows.

Two missed captures (radio, pop-up) were deleted and retaken. From
`controls-monitors.png` on, the VM runs at 1920×1080 (user's change), still
1x. Little arrows pressed is skipped for now (pressing changes settings);
a mixed check box is optional. Captures pushed to the reference repo
(`ce910d1`, 41 captures).

Group 4 started: `scroll-vertical-inactive` (inactive windows hide the
scroll box and arrows even when content overflows), `scroll-arrow-pressed`,
`scroll-thumb-dragging` (scroll box one step darker, Finder scrolls live, no
ghost), `scroll-track-pressed` (no visual change). Corrected REFERENCE.md:
the normal scroll box is highlight `#CCCCFF` / fill `#9999FF` / shadow
`#6666CC`; the earlier "fill `#CCCCFF`" came from the top row of a 16 px box.

A Finder copy is too quick to capture by hand, so `tools/capture.py` got
`--burst SECONDS` (and `--interval`, default 0.1 s): one QMP connection,
PPM frames to a temp dir under `$XDG_RUNTIME_DIR`, consecutive identical
frames dropped, the rest saved as `NAME-001.png`... with the same PNG check
and INDEX lines. Refuses if `NAME-001.png` etc. exist; limits 0–120 s and
≥ 0.02 s. Tested against throwaway QEMUs: 5 s burst while typing 5 keys
into the console = 50 frames, 5 kept; a static 2 s burst = 1 kept; reuse
and limits refused; no temp dirs left. Not yet run on the real VM.

Burst mode worked on the real VM. Group 4 finished:

- A small file copies too fast for the progress window to stay up
  (`progress-copy-window.png`, empty bar, under 0.3 s); duplicating the
  625 MB Starcraft zip gave a 35 s copy: `progress-determinate-early`,
  `-40`, `-55`, `-80`, `-expanded`. The fill is a Lavender tube
  (`#333399`→`#EEEEEE` center→`#000055`), the empty part a sunken
  `#BBBBBB` trough.
- Barber pole from a Sherlock 2 search (`progress-indeterminate-a/-b`):
  diagonal 8 px Lavender / 8 px gray stripes, tube-shaded, moving 4 px
  right per 0.2 s.
- Bonus frames kept: `menu-file-open.png` (File menu with disabled items,
  shortcuts, submenu arrows, pressed menu title) and
  `dialog-get-info-inactive.png` (dimmed controls in an inactive window).
- Bursts are pruned by hand: only the useful frames are kept (renamed),
  the rest deleted with their INDEX lines.

Group 5 (text, lists, tabs) finished. Most items were already covered
by earlier captures; new ones:

- Text selection by burst: `text-selection-word.png` (`#CCCCFF` fill),
  `text-selection-to-line-end.png` (fills to the right edge past the line
  end), `cursor-ibeam.png`. Inactive window: `text-selection-inactive.png`
  shows only a 1 px `#CCCCFF` outline.
- Finder list selection inverts just the name label (black box) and darkens
  the icon, no row highlight (`list-view-selection.png`); in an inactive
  window it isn't shown at all (`list-view-selection-inactive.png`).
- Tabs: normal `#CCCCCC`, current `#EEEEEE` (joined to the panel), pressed
  `#666666` with a white label (`tab-pressed.png`).

Group 6 (menus) finished, plus an extra `help-viewer.png` (the user's
idea: toolbar bevel buttons with Lavender icons, the 2 px `#6666CC` text
field focus ring, an inactive Appearance panel with every control dimmed).
Menus: `menu-view-checked` (hover and pressed title both `#333399`, check
marks, disabled item, submenu arrow, shortcut), `menu-submenu` (Apple menu
with icons; submenu's top edge 1 px above the highlighted parent row, left
edge at the parent's right edge; 1 px white inner top/left edge),
`menu-application` (Hide/Show items, running apps with icons, front app
checked), `menu-contextual` (plain menu, Help first, opens at the click
point). A scrolling menu is optional and skipped (nothing is long enough at
1920×1080).

Group 7 (Finder and desktop) finished; icon view, icon selection, desktop
pattern, and both Trash icons were already covered. New: `finder-marquee-many`
/ `-partial` (burst; the selection rectangle is a dotted line of inverted
pixels, like the window drag outline), `finder-button-view` (square bevel
buttons), `finder-rename` (black-framed edit box, `#CCCCFF` selection),
`finder-popup-open` / `-zoom-outline` / `-tab` (pop-up windows dock to the
bottom edge, animate as a gray zoom outline, and close to a rounded
`#CCCCCC` tab; the tab hid behind the Control Strip until dragged), and four
Control Strip frames from a burst (volume slider pop-up, module menus that
open upward). Launcher and spring-loaded folders are optional and skipped.
Bursts pruned to the useful frames.

Group 8 (help, cursors, misc) finished as far as practical:
`help-balloon.png` (white rounded balloon, black outline heavier right and
bottom, pointed tail). The user saw the watch and hand cursors during two
bursts, but no dump contains them; probably they aren't in the guest
framebuffer that `screendump` reads (unverified). Skipped for now (see
CAPTURES.md for options). Bonus keepers: `finder-icon-opening.png` (opening items get a
dark dotted "open" icon) and `dialog-modal-plain.png` ("About Balloon Help":
plain modal, thick double frame, no drag strip). Note and stop alert icons
and the startup screen are optional.

**Capture pass done**: 81 captures in the private reference repo, all
priority A and B items in CAPTURES.md ticked. PLAN.md step 1 updated.

At the user's request, `tools/capture.py` got `--fast` (burst every 0.01 s,
interval floor lowered to 0.005 s) and stops a burst early when the temp dir
has under 1 GiB free. Measured on the real VM first (20 dumps to scratch,
nothing written to `reference/`): a 1920×1080 dump takes 4.0–4.5 ms, hashing
it ~2 ms. Tested on a throwaway QEMU: a 2 s `--fast` burst took 199 frames
and kept the 4 that changed while 3 keys were typed; `--fast` without
`--burst` and too small intervals are refused; no temp dirs left. Then run on
the real VM: an 8 s `--fast` burst took 791 frames (175 different) while the
user opened Apple System Profiler and caught the watch cursor, three steps of
the spinning-disc cursor, and the contextual-menu cursor. So those cursors
are in the framebuffer after all, just very brief; the earlier guess was
wrong and the notes are corrected. The user also confirmed an earlier
all-identical fast burst was their own miss, not the VM freezing.

**Mistake:** while pruning that burst I used a zsh `for` loop with
`set -- $p`; zsh doesn't word-split, every rename failed, and the following
`rm` still ran and deleted all 175 frames, keepers included (not yet backed
up). Recovered the five cursor crops (32×32 around the pointer) pixel-exact
from the 4× nearest-neighbour zoom image I'd made just before, verified by
round trip, and logged them in INDEX.tsv. Full-frame context is lost.
CAPTURES.md now has a pruning rule: rename keepers, verify, then delete, in
one Python script.

Next: commit; then PLAN.md step 2 (sandbox tooling from windows2000-union,
plus a screenshot comparison tool) and settle decision 1 (scale).

## 2026-11-19, Claude Code (Claude Opus 5.5) — project setup

Started the project at the user's request. Created the shared agent docs,
modeled on htop-gpu's setup and extended for several agents working on
separate components:

- `AGENTS.md`: purpose, read-first order, layout, claims-based multi-agent
  rules, audit procedure and severities, fidelity rules (measured reference
  only), legal rules (no Apple material in git), general rules, checks, prior
  work to reuse (windows2000-union), machine facts.
- `CLAUDE.md`: points Claude Code at AGENTS.md.
- `PLAN.md`: status with the Claims table, open decisions (scale, style engine,
  decoration engine, name, fonts, menu bar), components, order of work.
- `AUDIT.md`: empty log with the entry template.
- `README.md`, `.gitignore` (`reference/` and build output ignored).

Checked: Plasma/KWin/union/aurorae/kdecoration 6.8.3 and Qt 6.12.0 installed;
both displays 3840×2160 at scale 1.

At the user's request: `git init` (branch `main`, identity `orlfman` with
the GitHub noreply address), first commit, and a **private** GitHub repo
https://github.com/orlfman/macos9-theme as `origin`, pushed.

Not done: no reference captures, no theme files. Next: step 1 in PLAN.md (reference captures), which
needs Mac OS 9.2.2 media from the user.
