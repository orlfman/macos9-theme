# Cursors

`macOS-cursors.tar.xz` is the cursor theme the Platinum global theme uses
(PLAN.md decision 8: no cursors of our own, the user's choice). `install.sh`
unpacks it and installs it as `~/.local/share/icons/macOS-cursors`;
`uninstall.sh` removes it once it is no longer selected.

## Where it comes from

- Apple Cursor v2.0.1 by Abdulkaiz Khatri (ful1e5):
  https://github.com/ful1e5/apple_cursor/releases/tag/v2.0.1
- [Source for v2.0.1](https://github.com/ful1e5/apple_cursor/archive/refs/tags/v2.0.1.tar.gz),
  including the SVGs, cursor configuration and build script.
- The release asset `macOS.tar.xz`, SHA-256
  `9c6e5e13b068ce51a9e90a9abd6ce232ec7d25d4ceb05aa8ac76efbb99c76762`.
- License: GNU GPL v3 (the release's `LICENSE`, included in the archive).
  The cursors are a separate work shipped alongside this project's
  BSD-licensed code; they're redrawn cursors, not Apple's files.

## What was changed

Only packaging: the black `macOS` folder is renamed `macOS-cursors` (its
theme ID here) and the white variant is left out. The cursor files, their
links and `index.theme` are as released. The archive is reproducible:

```bash
mkdir pack && tar -xJf macOS.tar.xz -C pack && mkdir out
cp -a pack/macOS out/macOS-cursors && cp pack/LICENSE out/LICENSE
tar --sort=name --owner=0 --group=0 --numeric-owner --mtime=@0 -C out -cJf macOS-cursors.tar.xz LICENSE macOS-cursors
```

After updating the archive, record its new SHA-256 in `install.sh`. The
installer checks that digest before changing the installation.
