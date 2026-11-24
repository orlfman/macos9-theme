#!/usr/bin/env python3
"""Generates Milestone 2 Firefox mockup stylesheets, seeds a realistic offline
profile (bookmarks + IE5-style toolbar buttons + 3 local tabs), renders all
design variants through dev/firefox-test.sh without --marionette (so no remote-
control stripe appears), and builds side-by-side comparison contact sheets.

Covers docs/FIREFOX-PLAN.md open questions 1, 2, 4, and 5:
  Q1 (Tabs):         below-favs (1A) vs above-toolbar (1B) vs vertical-sidebar (1C)
  Q2 (Address ramp): deep-lavender (2A) vs classic-tube (2B) vs soft-scrollbox (2C)
  Q4 (Toolbar):      icons-and-labels (4A) vs icons-only (4B)
  Q5 (Status bar):   permanent-ie5-band (5A) vs floating-platinum (5B)

SPDX-License-Identifier: BSD-2-Clause
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont

# Discrete whole-pixel 24px address-band Lavender ramps (rows 0..23 inside the
# 1px top #ADADAD and 1px bottom #000000 borders -> 26px total IE5 band).
RAMPS: dict[str, dict[str, str]] = {
    # 2A: Deep Lavender Tube — matches IE5's dark-edge / luminous-center tube contrast
    # in Platinum Lavender hues, with crisp white "Address:" text.
    "deep": {
        "gradient": (
            "linear-gradient(to bottom,"
            " #1B1B52 0px 1px, #212162 1px 2px, #282874 2px 3px, #2E2E85 3px 4px,"
            " #333399 4px 5px, #3F3FA5 5px 6px, #4C4CB2 6px 7px, #5959BF 7px 8px,"
            " #6666CC 8px 9px, #7070D6 9px 10px, #7A7AE0 10px 14px,"
            " #7070D6 14px 15px, #6666CC 15px 16px, #5959BF 16px 17px, #4C4CB2 17px 18px,"
            " #3F3FA5 18px 19px, #333399 19px 20px, #2B2B7E 20px 21px, #222266 21px 22px,"
            " #1A1A4F 22px 23px, #111138 23px 24px)"
        ),
        "label_color": "#FFFFFF",
        "label_shadow": "0 1px 0 rgba(0, 0, 0, 0.55)",
        "sep_color": "#1E1E5C",
    },
    # 2B: Bright Progress-Bar Lavender Tube — stretched directly from REFERENCE.md's
    # measured Mac OS 9 determinate progress bar (#333399 -> #6666CC -> #9999FF ->
    # #CCCCFF -> #EEEEEE highlight -> symmetric down to #000055).
    "progress": {
        "gradient": (
            "linear-gradient(to bottom,"
            " #333399 0px 2px, #4C4CB2 2px 3px, #6666CC 3px 5px, #8080E6 5px 6px,"
            " #9999FF 6px 8px, #B3B3FF 8px 9px, #CCCCFF 9px 11px, #EEEEEE 11px 13px,"
            " #CCCCFF 13px 15px, #B3B3FF 15px 16px, #9999FF 16px 18px, #8080E6 18px 19px,"
            " #6666CC 19px 21px, #333399 21px 23px, #000055 23px 24px)"
        ),
        "label_color": "#000033",
        "label_shadow": "0 1px 0 rgba(255, 255, 255, 0.7)",
        "sep_color": "#333399",
    },
    # 2C: Soft Beveled Scroll-Box Lavender — directly from REFERENCE.md's scroll box
    # (#CCCCFF top highlight, #9999FF flat body, #6666CC/#333399 bottom bevel).
    "scrollbox": {
        "gradient": (
            "linear-gradient(to bottom,"
            " #CCCCFF 0px 1px, #B3B3FF 1px 2px,"
            " #9999FF 2px 21px,"
            " #6666CC 21px 23px, #333399 23px 24px)"
        ),
        "label_color": "#000033",
        "label_shadow": "0 1px 0 rgba(255, 255, 255, 0.55)",
        "sep_color": "#6666CC",
    },
}


def build_css(
    *,
    tabs: str = "below",       # "below" | "above" | "vertical"
    ramp: str = "deep",        # "deep" | "progress" | "scrollbox"
    labels: bool = True,       # True = icons+labels (IE5), False = icons-only
    status: str = "floating",  # "floating" | "permanent" | "floating-preview"
) -> str:
    r = RAMPS[ramp]

    if tabs == "below":
        order_css = """
    #toolbar-menubar { order: 0 !important; }
    #nav-bar         { order: 1 !important; }
    #PersonalToolbar { order: 2 !important; }
    #TabsToolbar     { order: 3 !important; }
"""
        tabs_border_css = """
    #TabsToolbar {
      border-top: 1px solid #FFFFFF !important;
      border-bottom: 0 !important;
    }
    #navigator-toolbox {
      border-bottom: 1px solid #000000 !important;
    }
"""
    elif tabs == "above":
        order_css = """
    #toolbar-menubar { order: 0 !important; }
    #TabsToolbar     { order: 1 !important; }
    #nav-bar         { order: 2 !important; }
    #PersonalToolbar { order: 3 !important; }
"""
        tabs_border_css = """
    #TabsToolbar {
      border-top: 1px solid #FFFFFF !important;
      border-bottom: 1px solid #888888 !important;
    }
    #navigator-toolbox {
      border-bottom: 1px solid #000000 !important;
    }
"""
    else:  # vertical
        order_css = """
    #toolbar-menubar { order: 0 !important; }
    #nav-bar         { order: 1 !important; }
    #PersonalToolbar { order: 2 !important; }
"""
        tabs_border_css = """
    #navigator-toolbox {
      border-bottom: 1px solid #000000 !important;
    }
    #sidebar-container {
      background: repeating-linear-gradient(
        to bottom,
        #DEDEDE 0px 1px, #CCCCCC 1px 2px, #E8E6E8 2px 3px
      ) !important;
      border-inline-end: 1px solid #000000 !important;
      box-shadow: inset 1px 0 0 #FFFFFF, inset -1px 0 0 #ADADAD !important;
    }
    sidebar-main {
      background: transparent !important;
      --tab-min-height: 24px !important;
      --toolbarbutton-icon-fill: #333399 !important;
    }
    #vertical-tabs {
      padding: 4px 4px 0 4px !important;
    }
    #tabbrowser-tabs[orient="vertical"] .tabbrowser-tab {
      padding-block: 1px !important;
    }
    #tabbrowser-tabs[orient="vertical"] .tab-background {
      background: #CCCCCC !important;
      border: 1px solid #000000 !important;
      border-radius: 0 !important;
      box-shadow: inset 1px 1px 0 #FFFFFF, inset -1px -1px 0 #888888 !important;
      min-height: 22px !important;
      margin: 0 !important;
    }
    #tabbrowser-tabs[orient="vertical"] .tabbrowser-tab[selected] .tab-background {
      background: #EEEEEE !important;
      box-shadow: inset 1px 1px 0 #FFFFFF, inset -1px -1px 0 #999999 !important;
    }
    #tabbrowser-tabs[orient="vertical"] .tab-label {
      color: #000000 !important;
      font-size: 11px !important;
    }
    #tabbrowser-tabs[orient="vertical"] .tabbrowser-tab[selected] .tab-label {
      font-weight: 600 !important;
    }
    #vertical-tabs-newtab-button {
      margin-top: 3px !important;
      color: #111111 !important;
      fill: #333399 !important;
    }
"""

    if labels:
        btn_css = """
    #nav-bar {
      min-height: 68px !important;
    }
    #nav-bar-customization-target {
      min-height: 42px !important;
      padding-inline: 4px !important;
    }
    #nav-bar .toolbarbutton-1 {
      flex-direction: column !important;
      min-width: 52px !important;
      padding: 3px 4px 2px !important;
      align-items: center !important;
      justify-content: center !important;
    }
    #nav-bar .toolbarbutton-1 > .toolbarbutton-icon,
    #nav-bar .toolbarbutton-1 > .toolbarbutton-badge-stack {
      padding: 2px !important;
      width: 20px !important;
      height: 20px !important;
      border-radius: 0 !important;
      background: transparent !important;
      outline: none !important;
    }
    #nav-bar .toolbarbutton-1 > .toolbarbutton-text {
      display: block !important;
      width: auto !important;
      max-width: none !important;
      min-height: 0 !important;
      padding: 1px 2px 0 !important;
      font-size: 10px !important;
      line-height: 11px !important;
      text-align: center !important;
      color: #111111 !important;
      background: transparent !important;
      outline: none !important;
    }
    #nav-bar .toolbarbutton-1[disabled] > .toolbarbutton-text {
      color: #777777 !important;
    }
    #nav-bar-overflow-button > .toolbarbutton-text {
      display: none !important;
    }
"""
    else:
        btn_css = """
    #nav-bar {
      min-height: 54px !important;
    }
    #nav-bar-customization-target {
      min-height: 28px !important;
      padding-inline: 4px !important;
    }
    #nav-bar .toolbarbutton-1 {
      flex-direction: row !important;
      min-width: 28px !important;
      padding: 2px 3px !important;
      align-items: center !important;
      justify-content: center !important;
    }
    #nav-bar .toolbarbutton-1 > .toolbarbutton-icon,
    #nav-bar .toolbarbutton-1 > .toolbarbutton-badge-stack {
      padding: 3px !important;
      width: 22px !important;
      height: 22px !important;
      border-radius: 0 !important;
      background: transparent !important;
      outline: none !important;
    }
    #nav-bar .toolbarbutton-1 > .toolbarbutton-text {
      display: none !important;
    }
"""

    if status == "permanent":
        status_css = """
    /* Option 5A: permanent 16px IE5-style pinstriped status band + diagonal size grip */
    &:not([inFullscreen], [popup-window]) body::after {
      content: "Done — http://macos9.local/platinum/welcome.html";
      display: flex !important;
      align-items: center !important;
      flex: 0 0 16px !important;
      height: 16px !important;
      padding-inline: 8px 20px !important;
      font-size: 10px !important;
      line-height: 14px !important;
      color: #111111 !important;
      border-top: 1px solid #000000 !important;
      box-shadow: inset 0 1px 0 #FFFFFF, inset 0 -1px 0 #ADADAD !important;
      background-image:
        linear-gradient(135deg,
          transparent 0px, transparent 5px,
          #777777 5px, #777777 6px, #FFFFFF 6px, #FFFFFF 7px, transparent 7px,
          transparent 9px,
          #777777 9px, #777777 10px, #FFFFFF 10px, #FFFFFF 11px, transparent 11px,
          transparent 13px,
          #777777 13px, #777777 14px, #FFFFFF 14px, #FFFFFF 15px, transparent 15px),
        linear-gradient(to right, #CCCCCC, #CCCCCC),
        repeating-linear-gradient(to bottom, #DEDEDE 0px 1px, #CCCCCC 1px 2px, #E8E6E8 2px 3px) !important;
      background-size: 15px 15px, 16px 15px, 100% 100% !important;
      background-position: right bottom, right bottom, left top !important;
      background-repeat: no-repeat, no-repeat, repeat !important;
    }
    #statuspanel {
      bottom: 0 !important;
      left: 0 !important;
      max-width: 75% !important;
      padding: 0 !important;
    }
    #statuspanel-label {
      background: transparent !important;
      border: none !important;
      color: #111111 !important;
      font-size: 10px !important;
      padding: 1px 8px !important;
    }
"""
    elif status == "floating-preview":
        status_css = """
    /* Option 5B preview: floating Platinum #statuspanel shown on hover/load (zero height cost at rest) */
    #statuspanel {
      display: flex !important;
      visibility: visible !important;
      opacity: 1 !important;
      position: fixed !important;
      bottom: 0 !important;
      left: 0 !important;
      z-index: 99 !important;
      margin: 0 !important;
      padding: 0 !important;
    }
    #statuspanel-label {
      display: block !important;
      min-width: 260px !important;
      background: #DDDDDD !important;
      color: #000000 !important;
      font-size: 11px !important;
      border: 1px solid #000000 !important;
      border-bottom: 0 !important;
      border-left: 0 !important;
      border-radius: 0 !important;
      box-shadow: inset 1px 1px 0 #FFFFFF, inset -1px -1px 0 #999999 !important;
      padding: 2px 8px !important;
    }
    #statuspanel-label::before {
      content: "http://macos9.local/platinum/appearance.html";
    }
"""
    else:
        status_css = """
    /* Option 5B: floating Platinum #statuspanel (hidden at rest, zero vertical page cost) */
    #statuspanel-label {
      background: #DDDDDD !important;
      color: #000000 !important;
      font-size: 11px !important;
      border: 1px solid #000000 !important;
      border-radius: 0 !important;
      box-shadow: inset 1px 1px 0 #FFFFFF, inset -1px -1px 0 #999999 !important;
      padding: 2px 8px !important;
    }
"""

    return f"""/* Milestone 2 mockup: tabs={tabs}, ramp={ramp}, labels={labels}, status={status} */
@media (-moz-native-theme) and (prefers-color-scheme: light) and (not (prefers-contrast)) and (not (forced-colors)) {{
  :root:not([lwtheme]) {{
    --toolbar-background-color: #DDDDDD !important;
    --toolbar-text-color: #111111 !important;
    --toolbox-background-color: #DDDDDD !important;
    --toolbarbutton-icon-fill: #333399 !important;
    --toolbarbutton-border-radius: 0px !important;
    --focus-outline-color: #6666CC !important;
    --chrome-content-separator-color: #000000 !important;
    --tab-min-height: 22px !important;
    --tab-border-radius: 2px !important;
    --urlbar-min-height: 20px !important;
    --urlbar-height: 20px !important;

{order_css}
{tabs_border_css}

    /* IE5 pinstriped button toolbar + reserved 26px Lavender address band */
    #nav-bar {{
      position: relative !important;
      padding: 0 !important;
      background: repeating-linear-gradient(
        to bottom,
        #DEDEDE 0px 1px, #CCCCCC 1px 2px, #E8E6E8 2px 3px
      ) !important;
      border-top: 1px solid #FFFFFF !important;
      border-bottom: 1px solid #ADADAD !important;
    }}
    &:not([customizing]) #nav-bar {{
      padding-bottom: 26px !important;
    }}
    &:not([customizing]) #nav-bar-customization-target > toolbarspring {{
      display: none !important;
    }}
    &:not([customizing]) #fxa-toolbar-menu-button {{
      margin-inline-start: auto !important;
    }}
    /* IE5-inspired dotted Lavender separator after Home button */
    #home-button {{
      margin-inline-end: 6px !important;
      position: relative !important;
    }}
    #home-button::after {{
      content: "";
      position: absolute;
      right: -4px;
      top: 5px;
      bottom: 5px;
      width: 1px;
      background: repeating-linear-gradient(
        to bottom,
        #333399 0px 1px, transparent 1px 3px
      );
      pointer-events: none;
    }}

{btn_css}

    #nav-bar .toolbarbutton-1:not([disabled]):hover {{
      background: rgba(255, 255, 255, 0.45) !important;
      box-shadow: inset 1px 1px 0 #FFFFFF, inset -1px -1px 0 #888888 !important;
    }}
    #nav-bar .toolbarbutton-1:not([disabled]):hover:active,
    #nav-bar .toolbarbutton-1:not([disabled])[open="true"] {{
      background: #666666 !important;
      box-shadow: inset 1px 1px 0 #444444, inset -1px -1px 0 #888888 !important;
    }}
    #nav-bar .toolbarbutton-1:not([disabled]):hover:active > .toolbarbutton-icon,
    #nav-bar .toolbarbutton-1:not([disabled]):hover:active > .toolbarbutton-text {{
      fill: #FFFFFF !important;
      color: #FFFFFF !important;
    }}
    #nav-bar .toolbarbutton-1[disabled] {{
      opacity: 0.55 !important;
    }}
    /* Subtle Platinum activity badge frame on far-right Menu button */
    #PanelUI-button {{
      border-inline-start: 1px solid #ADADAD !important;
      box-shadow: inset 1px 0 0 #FFFFFF !important;
      padding-inline: 2px !important;
    }}

    /* Full-width 26px Lavender address band (Row 2 of #nav-bar) */
    &:not([customizing]) #urlbar-container {{
      position: absolute !important;
      inset-inline: 0 !important;
      bottom: 0 !important;
      width: 100% !important;
      max-width: none !important;
      height: 26px !important;
      min-height: 26px !important;
      margin: 0 !important;
      padding: 2px 8px 2px 68px !important;
      box-sizing: border-box !important;
      align-items: center !important;
      background: {r["gradient"]} !important;
      border-top: 1px solid #ADADAD !important;
      border-bottom: 1px solid #000000 !important;
    }}
    &:not([customizing]) #urlbar-container::before {{
      content: "Address:";
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 62px;
      display: flex;
      align-items: center;
      justify-content: flex-end;
      padding-right: 6px;
      font-size: 11px;
      font-weight: 600;
      color: {r["label_color"]};
      text-shadow: {r["label_shadow"]};
      border-right: 1px solid {r["sep_color"]};
      pointer-events: none;
    }}
    &:not([customizing]) #urlbar {{
      top: 0 !important;
      min-height: 20px !important;
      height: 20px !important;
      margin: 0 !important;
    }}
    &:not([customizing]) #urlbar > .urlbar-background {{
      background: #FFFFFF !important;
      border: 1px solid #000000 !important;
      border-radius: 0 !important;
      box-shadow: none !important;
      outline: none !important;
    }}
    &:not([customizing]) #urlbar[focused="true"] > .urlbar-background {{
      border: 1px solid #000000 !important;
      outline: 2px solid #6666CC !important;
      outline-offset: 0px !important;
    }}
    &:not([customizing]) #urlbar > .urlbar-input-container {{
      height: 20px !important;
      padding: 0 4px !important;
      border: 0 !important;
    }}
    #urlbar-input {{
      font-size: 12px !important;
      color: #000000 !important;
    }}
    #urlbar-input::selection {{
      background-color: #CCCCFF !important;
      color: #000000 !important;
    }}
    #urlbar-searchmode-switcher,
    .urlbar-page-action,
    #identity-box,
    #trust-icon-container {{
      height: 18px !important;
      padding-block: 0 !important;
      border-radius: 0 !important;
    }}

    /* IE5-inspired pinstriped Favorites (Bookmarks) bar */
    #PersonalToolbar {{
      min-height: 24px !important;
      max-height: 24px !important;
      padding: 0 6px !important;
      background: repeating-linear-gradient(
        to bottom,
        #DEDEDE 0px 1px, #CCCCCC 1px 2px, #E8E6E8 2px 3px
      ) !important;
      border-top: 1px solid #FFFFFF !important;
      border-bottom: 1px solid #ADADAD !important;
    }}
    #PersonalToolbar toolbarbutton.bookmark-item:not(.subviewbutton) {{
      margin: 1px 3px !important;
      padding: 1px 6px !important;
      border-radius: 0 !important;
      color: #111111 !important;
      font-size: 11px !important;
    }}
    #PersonalToolbar toolbarbutton.bookmark-item:not(.subviewbutton):hover {{
      background: rgba(255, 255, 255, 0.55) !important;
      box-shadow: inset 1px 1px 0 #FFFFFF, inset -1px -1px 0 #888888 !important;
    }}
    #PersonalToolbar .bookmark-item > .toolbarbutton-icon {{
      width: 14px !important;
      height: 14px !important;
      fill: #333399 !important;
    }}

    /* Slim horizontal Platinum tabs (used in 1A and 1B) */
    #TabsToolbar {{
      min-height: 24px !important;
      background: #DDDDDD !important;
      padding: 2px 6px 0 6px !important;
    }}
    #tabbrowser-tabs[orient="horizontal"] {{
      --tab-min-height: 22px !important;
      min-height: 22px !important;
    }}
    #tabbrowser-tabs[orient="horizontal"] .tabbrowser-tab {{
      padding-inline: 1px !important;
      padding-block: 0 !important;
      min-height: 22px !important;
      max-height: 22px !important;
    }}
    #tabbrowser-tabs[orient="horizontal"] .tab-background {{
      background: #CCCCCC !important;
      border: 1px solid #000000 !important;
      border-bottom: 0 !important;
      border-radius: 2px 2px 0 0 !important;
      box-shadow: inset 1px 1px 0 #E0E0E0, inset -1px 0 0 #999999 !important;
      margin-block: 0 !important;
      min-height: 21px !important;
      outline: none !important;
    }}
    #tabbrowser-tabs[orient="horizontal"] .tabbrowser-tab:hover:not([selected]) .tab-background {{
      background: #D8D8D8 !important;
    }}
    #tabbrowser-tabs[orient="horizontal"] .tabbrowser-tab[selected] .tab-background {{
      background: #EEEEEE !important;
      border-color: #000000 !important;
      box-shadow: inset 1px 1px 0 #FFFFFF, inset -1px 0 0 #BBBBBB !important;
      min-height: 22px !important;
    }}
    #tabbrowser-tabs[orient="horizontal"] .tab-content {{
      padding: 0 8px !important;
    }}
    #tabbrowser-tabs[orient="horizontal"] .tab-label {{
      color: #000000 !important;
      font-size: 11px !important;
    }}
    #tabbrowser-tabs[orient="horizontal"] .tabbrowser-tab[selected] .tab-label {{
      font-weight: 600 !important;
    }}
    #tabs-newtab-button,
    #alltabs-button {{
      padding: 0 2px !important;
      --toolbarbutton-padding-inner: 2px !important;
    }}

{status_css}
  }}
}}
"""


def make_pages(pdir: pathlib.Path) -> list[str]:
    pages = [
        (
            "welcome.html",
            "Mac OS 9 Platinum",
            "Mac OS 9.2.2 Platinum Appearance",
            "Sample offline page for Firefox Milestone 2 visual mockups. "
            "Compare tab placement, Lavender address band ramps, toolbar labels, and status bar options.",
        ),
        (
            "appearance.html",
            "Appearance Notes",
            "Platinum Palette & Controls",
            "Measured Platinum Lavender accents (#CCCCFF, #9999FF, #6666CC, #333399) on #DDDDDD/#CCCCCC/#EEEEEE surfaces.",
        ),
        (
            "bookmarks.html",
            "Favorites Guide",
            "IE5-Inspired Browser Chrome",
            "Pure userChrome.css layout keeping Firefox tabs, extensions, downloads, and Customize Mode functional.",
        ),
    ]
    uris = []
    for fname, title, heading, body in pages:
        f = pdir / fname
        f.write_text(
            f"""<!doctype html>
<html><head><meta charset="utf-8"><title>{title}</title>
<style>
  body {{ font: 13px/1.5 "SF Pro Text", sans-serif; margin: 24px 32px; background: #FFFFFF; color: #111111; }}
  h1 {{ font-size: 18px; margin: 0 0 8px; color: #333399; border-bottom: 1px solid #CCCCCC; padding-bottom: 6px; }}
  p {{ max-width: 640px; color: #222222; }}
  .box {{ margin-top: 16px; padding: 12px 14px; background: #EEEEEE; border: 1px solid #888888; max-width: 520px; }}
</style></head>
<body>
  <h1>{heading}</h1>
  <p>{body}</p>
  <div class="box">
    <strong>Offline local test page</strong> — zero network traffic, native 1× scale inside headless nested KWin with the Platinum window decoration.
  </div>
</body></html>
""",
            encoding="utf-8",
        )
        uris.append(f.as_uri())
    return uris


def build_contact_sheet(
    items: list[tuple[str, pathlib.Path, tuple[int, int, int, int]]],
    out_path: pathlib.Path,
    title: str,
) -> None:
    """Stack labeled 1x crops vertically for side-by-side visual comparison."""
    pad = 12
    label_h = 24
    header_h = 34
    crops = []
    max_w = 0
    total_h = header_h + pad
    for label, p, box in items:
        im = Image.open(p).convert("RGB").crop(box)
        crops.append((label, im))
        max_w = max(max_w, im.width)
        total_h += label_h + im.height + pad

    canvas = Image.new("RGB", (max_w + pad * 2, total_h), (0xDD, 0xDD, 0xDD))
    draw = ImageDraw.Draw(canvas)
    try:
        font_b = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 14)
        font_r = ImageFont.truetype("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf", 12)
    except OSError:
        font_b = ImageFont.load_default()
        font_r = font_b

    # Platinum header strip
    draw.rectangle([0, 0, canvas.width - 1, header_h - 1], fill=(0x33, 0x33, 0x99))
    draw.text((pad, 9), title, fill=(0xFF, 0xFF, 0xFF), font=font_b)

    y = header_h + pad
    for label, im in crops:
        draw.rectangle([pad, y, pad + im.width - 1, y + label_h - 1], fill=(0xCC, 0xCC, 0xCC), outline=(0x00, 0x00, 0x00))
        draw.text((pad + 8, y + 5), label, fill=(0x00, 0x00, 0x00), font=font_r)
        y += label_h
        canvas.paste(im, (pad, y))
        draw.rectangle([pad - 1, y - 1, pad + im.width, y + im.height], outline=(0x00, 0x00, 0x00))
        y += im.height + pad

    canvas.save(out_path)


def main() -> int:
    project = pathlib.Path(__file__).resolve().parents[2]
    dev = project / "dev"
    shots = dev / "shots"
    work = pathlib.Path(os.environ["M9_M2_WORK"])
    pages_dir = work / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)
    page_uris = make_pages(pages_dir)

    # Step 1: Seed one reusable offline profile with 5 IE5-style bookmarks and
    # IE5-style toolbar buttons (Back, Forward, Reload, Home, Print, Find).
    seed_prof = work / "seed-profile"
    seed_script = work / "seed.py"
    seed_script.write_text(
        f"""
import json, os, socket, sys, time
from pathlib import Path
sys.path.insert(0, str(Path({str(dev / 'firefox-m1')!r})))
from probe import Marionette, shoot

m = Marionette(int(os.environ["M9_MARIONETTE_PORT"]))
try:
    m.send("WebDriver:NewSession", {{"capabilities": {{}}}})
    m.send("Marionette:SetContext", {{"value": "chrome"}})
    m.exec_chrome('''
        const done = arguments[arguments.length - 1];
        (async () => {{
          if (window.gBrowserInit && !gBrowserInit.delayedStartupFinished) {{
            await new Promise(r => {{
              const obs = (s) => {{ if (s === window) {{ Services.obs.removeObserver(obs, "browser-delayed-startup-finished"); r(); }} }};
              Services.obs.addObserver(obs, "browser-delayed-startup-finished");
            }});
          }}
          const bms = [
            ["Live Home Page", {page_uris[0]!r}],
            ["Appearance Notes", {page_uris[1]!r}],
            ["Favorites Guide", {page_uris[2]!r}],
            ["Mozilla Docs", "about:support"],
            ["Add-ons", "about:addons"]
          ];
          for (const [title, url] of bms) {{
            await PlacesUtils.bookmarks.insert({{ parentGuid: PlacesUtils.bookmarks.toolbarGuid, title, url }});
          }}
          CustomizableUI.addWidgetToArea("home-button", "nav-bar", 4);
          CustomizableUI.addWidgetToArea("print-button", "nav-bar", 5);
          CustomizableUI.addWidgetToArea("find-button", "nav-bar", 6);
          Services.prefs.savePrefFile(null);
          await new Promise(r => setTimeout(r, 400));
          done(true);
        }})();
    ''', async_mode=True)
    shoot(Path(os.environ["M9_OUT"]), settle=0.2)
finally:
    m.close()
""",
        encoding="utf-8",
    )

    print("=== Seeding offline Milestone 2 profile (bookmarks + IE5 button set) ===")
    env = os.environ.copy()
    env.update(
        {
            "M9_FF_PROFILE": str(seed_prof),
            "M9_USERCHROME": "none",
            "M9_MARIONETTE_SCRIPT": f"python3 -I -W error '{seed_script}'",
        }
    )
    subprocess.run([str(dev / "firefox-test.sh"), "m2-seed", page_uris[0]], env=env, check=True)
    # Remove any lock/sessionstore files from seed profile before cloning.
    for stale in ("lock", ".parentlock", "sessionstore.jsonlz4", "sessionstore-backups"):
        p = seed_prof / stale
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        elif p.exists() or p.is_symlink():
            p.unlink(missing_ok=True)

    # Step 2: Render all 8 clean cold-launch mockups (NO --marionette, NO remote stripe!).
    variants = [
        ("m2-1a-tabs-below-favs",     dict(tabs="below",    ramp="deep",      labels=True,  status="floating"),         False),
        ("m2-1b-tabs-above-toolbar",  dict(tabs="above",    ramp="deep",      labels=True,  status="floating"),         False),
        ("m2-1c-tabs-vertical",       dict(tabs="vertical", ramp="deep",      labels=True,  status="floating"),         True),
        ("m2-2b-ramp-progress-tube",  dict(tabs="below",    ramp="progress",  labels=True,  status="floating"),         False),
        ("m2-2c-ramp-scrollbox",      dict(tabs="below",    ramp="scrollbox", labels=True,  status="floating"),         False),
        ("m2-4b-toolbar-icons-only",  dict(tabs="below",    ramp="deep",      labels=False, status="floating"),         False),
        ("m2-5a-status-permanent",    dict(tabs="below",    ramp="deep",      labels=True,  status="permanent"),        False),
        ("m2-5b-status-floating",     dict(tabs="below",    ramp="deep",      labels=True,  status="floating-preview"), False),
    ]

    # Open all 3 local offline pages as real tabs via browser.startup.homepage pipe syntax!
    homepage_pipe = "|".join(page_uris)
    extra_prefs = (
        f'user_pref("browser.startup.page", 1);\n'
        f'user_pref("browser.startup.homepage", "{homepage_pipe}");\n'
        f'user_pref("browser.startup.firstrunSkipsHomepage", false);\n'
    )

    for idx, (name, cfg, vtabs) in enumerate(variants, 1):
        print(f"=== [{idx}/{len(variants)}] Rendering {name} ===")
        prof = work / f"prof-{name}"
        shutil.copytree(seed_prof, prof)
        css_file = work / f"{name}.css"
        css_file.write_text(build_css(**cfg), encoding="utf-8")

        v_env = os.environ.copy()
        v_env.update(
            {
                "M9_FF_PROFILE": str(prof),
                "M9_KEEP_PROFILE": "1",
                "M9_USERCHROME": str(css_file),
                "M9_VERTICAL_TABS": "true" if vtabs else "false",
                "M9_WAIT": "5",
                "M9_EXTRA_PREFS": extra_prefs,
            }
        )
        # Pass empty URL argument? firefox-test.sh defaults $2 to about:blank, so pass
        # the 3 tabs via startup homepage by passing -new-tab? Simpler: pass the first
        # URL as $2 — Wait: passing a URL on CLI overrides browser.startup.homepage!
        # So pass a special sentinel "--" or handle M9_URL="" cleanly in firefox-test.sh!
        v_env["M9_NO_CLI_URL"] = "1"
        subprocess.run([str(dev / "firefox-test.sh"), name], env=v_env, check=True)

    # Step 3: Build crisp 1x side-by-side comparison contact sheets!
    # Window sits around x=75..1205, y=46..805 on the 1280x860 virtual output.
    top_chrome = (72, 44, 1208, 250)
    tall_left = (72, 44, 720, 420)
    bottom_chrome = (72, 710, 1208, 816)

    build_contact_sheet(
        [
            ("Option 1A: Slim Platinum tabs BELOW Favorites bar (classic IE5 top silhouette)", shots / "firefox-m2-1a-tabs-below-favs.png", top_chrome),
            ("Option 1B: Slim Platinum tabs ABOVE button toolbar (standard Firefox muscle memory)", shots / "firefox-m2-1b-tabs-above-toolbar.png", top_chrome),
            ("Option 1C: Vertical Platinum tabs in left sidebar (IE5 Explorer-bar silhouette)", shots / "firefox-m2-1c-tabs-vertical.png", (72, 44, 1208, 340)),
        ],
        shots / "firefox-m2-compare-q1-tabs.png",
        "Question 1: Tab Placement Options (1x native in KWin Platinum)",
    )
    build_contact_sheet(
        [
            ("Option 2A: Deep Lavender Tube (IE5 luminance contrast, white 'Address:' label)", shots / "firefox-m2-1a-tabs-below-favs.png", (72, 108, 1208, 160)),
            ("Option 2B: Bright Progress-Bar Tube (REFERENCE.md #333399..#EEEEEE specular highlight)", shots / "firefox-m2-2b-ramp-progress-tube.png", (72, 108, 1208, 160)),
            ("Option 2C: Soft Beveled Scroll-Box Lavender (REFERENCE.md #CCCCFF/#9999FF/#6666CC)", shots / "firefox-m2-2c-ramp-scrollbox.png", (72, 108, 1208, 160)),
        ],
        shots / "firefox-m2-compare-q2-address-ramps.png",
        "Question 2: Address Band Lavender Ramp Options (1x native)",
    )
    build_contact_sheet(
        [
            ("Option 4A: Icons + Text Labels under icons (IE5 default, 42px toolbar)", shots / "firefox-m2-1a-tabs-below-favs.png", (72, 44, 1208, 162)),
            ("Option 4B: Compact Icons Only (28px toolbar, saves ~14px vertical height)", shots / "firefox-m2-4b-toolbar-icons-only.png", (72, 44, 1208, 148)),
        ],
        shots / "firefox-m2-compare-q4-toolbar-labels.png",
        "Question 4: Toolbar Labels vs Icons Only (1x native)",
    )
    build_contact_sheet(
        [
            ("Option 5A: Permanent 16px IE5 pinstriped status band + diagonal size grip", shots / "firefox-m2-5a-status-permanent.png", bottom_chrome),
            ("Option 5B: Floating Platinum #statuspanel (shown on hover/load, 0px height at rest)", shots / "firefox-m2-5b-status-floating.png", bottom_chrome),
        ],
        shots / "firefox-m2-compare-q5-status-band.png",
        "Question 5: Permanent Status Band vs Floating Status Panel (1x native)",
    )

    print("ok      Milestone 2 mockups & 4 comparison sheets generated in", shots)
    return 0


if __name__ == "__main__":
    sys.exit(main())
