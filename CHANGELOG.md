# macos9-theme: changelog

Newest first. Format and rules: AGENTS.md "CHANGELOG entries".

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
