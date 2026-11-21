# macos9-theme: audit log

Rules: AGENTS.md "Audits". Newest sections first. Finding numbers run across
the whole project and are never reused.

Status: two checks so far (decoration, style batch 1; 2026-11-20). Open findings: none.

## 2026-11-20, Claude Code (Claude Opus 5.5) — style batch 1 fidelity check

Audited: `style/platinum/` (C++ Qt style), working tree before its first
commit. Reference: the captures named in `dev/check-style.sh`; values in
REFERENCE.md and FINDINGS.md.

Findings: none open. Fixed during development: derived marks for uncaptured
radio states first took the whole shading (now only black mark pixels);
push button corner diffs turned out to be the white dialog behind the
captures (the render now matches it); the default button's bottom band
included the "p" of "Open" (now starts a row lower).

### Checks

`dev/check-style.sh`: 31 of 31 regions pixel exact (0 differing pixels each):
push buttons normal / pressed / disabled / default / default pressed (four
edge bands each), check box off / on / off pressed / on disabled, radio off
/ on / off pressed / off disabled, vertical scroll bars with the thumb at
the top and partway down, and the horizontal scroll bar (drawn by
transposing the vertical one, exact on the first try). The style also
renders the real widget gallery without warnings.

### Limits

- Labels not compared (no Charcoal); the label color rule (black, white when
  pressed, `#777777` disabled) is from REFERENCE.md, not diffed.
- Not captured, so derived and unchecked: check box on + pressed, off +
  disabled; radio on + pressed, on + disabled; the mixed (partial) check
  box isn't themed yet.
- The pressed captures' pointer hides a few pixels; those were taken from
  the unpressed outline (gen-style-data.sh says where).
- Rendered offscreen at 1x only; not in a running app in a real compositor,
  not at scale 2. Nothing installed; the user hasn't seen it.

## 2026-11-20, Claude Code (Claude Opus 5.5) — decoration fidelity check

Audited: `decoration/` (Platinum KDecoration3 plugin), working tree before
its first commit. Reference: `window-document-active.png`,
`window-document-inactive.png`, `window-close-pressed.png`,
`window-zoom-pressed.png`; values in REFERENCE.md "Window frame".

Findings: none open. Fixed during development, before this check: the
pinstripes started 1 px late (QRectF::right() is one past the group), the
inactive window's lines and shadow are `#555555`, not black, and the
collapse box was missing on Wayland (see FINDINGS.md; now drawn on the
minimize button).

### Checks

All with `tools/compare.py diff`, reference region against the plugin's
output; 0 differing pixels in every case:

- Active, nested KWin (`kwin-test.sh`, `VT_SINGLE=1`): title bar left end
  60×22 (frame, close box, pinstripe start), left side 6×20, right side
  6×20, bottom edge 20×6, bottom-left corner frame 16×6.
- Active, KWrite in nested KWin (`app-test.sh`): title bar right end 60×22
  (pinstripe end, zoom and collapse boxes, frame), left end 60×22.
- Inactive, KWin's decoration preview (`shoot-deco.sh`): title bar left and
  right 150×22 each, left side, right side, bottom edge.
- Pressed, preview: zoom box top 13×8, close box top 13×7 (the capture's
  pointer covers the rest).

### Limits

- Title text and icon not compared: no Charcoal, and the reference icons
  are Apple artwork. Condensing and dropping long titles was seen working
  in the preview, not measured against Mac OS 9's thresholds.
- Drop shadow not seen: the nested KWin background is black and the
  preview draws no shadow. Code path reviewed only.
- Not tested: maximized windows, X11 apps (real shading), Plasma scale 2,
  the user's real session. Nothing installed. The user hasn't seen it on
  screen yet.

<!--
Template for a new section (copy above the previous newest one):

## YYYY-MM-DD, <Agent> (<model>) — <what was audited>

Audited: <component(s)>, <git commit or "working tree">.
Reference: <reference/ files and docs/REFERENCE.md entries used>.

### Finding N (P1/P2/P3, open): <short title>

What: ...
Where: <file:line or screenshot>
Expected (reference): ...
Measured: ...
Suggested fix: ...

### Checks

- <command or method>: <result with numbers>

### Limits

- <offscreen only / not seen by the user / one app / one scale / ...>
-->
