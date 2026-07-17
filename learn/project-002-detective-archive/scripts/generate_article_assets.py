#!/usr/bin/env python3
"""
generate_article_assets.py
──────────────────────────
Run every Build 2 script once and produce reusable article assets:

  article-assets/
  ├── outputs/          plain-text terminal captures  (.txt)
  ├── html/             styled terminal HTML views    (.html)
  ├── screenshots/      dark-theme PNG screenshots    (.png)
  └── SUMMARY.md        execution manifest

Usage (from any directory — the script locates itself):
    python3 scripts/generate_article_assets.py

External dependency (PNG screenshots only):
    pip install Pillow

    Pillow is the only non-stdlib package required. The Python standard
    library has no image-drawing primitives, so there is no way to render
    text onto a dark canvas without an external package. Pillow is the
    minimal, widely-used choice. All other asset types (txt, html,
    SUMMARY.md) use stdlib only and generate even if Pillow is absent.
"""

from __future__ import annotations

import html as html_module
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Optional: Pillow for PNG generation ───────────────────────────────────────
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ── Resolve paths from this file's location ───────────────────────────────────
SCRIPTS_DIR = Path(__file__).resolve().parent   # .../scripts/
BUILD_ROOT  = SCRIPTS_DIR.parent                # .../project-002-detective-archive/
ASSETS      = BUILD_ROOT / "article-assets"
OUT_DIR     = ASSETS / "outputs"
HTML_DIR    = ASSETS / "html"
SHOT_DIR    = ASSETS / "screenshots"

# ── Script manifest — ordered to match the article reading flow ───────────────
MANIFEST: list[tuple[str, str]] = [
    ("detective-archive/01_intelligence_gap.py",   "MILESTONE 01 — The Intelligence Gap"),
    ("detective-archive/02_case_file_splitter.py", "MILESTONE 02 — The Case File Splitter"),
    ("detective-archive/03_fingerprint_engine.py", "MILESTONE 03 — The Fingerprint Engine"),
    ("detective-archive/04_relevance_scorer.py",   "MILESTONE 04 — The Relevance Scorer"),
    ("detective-archive/05_evidence_archive.py",   "MILESTONE 05 — The Evidence Archive"),
    ("detective-archive/06_retrieval_desk.py",     "MILESTONE 06 — The Retrieval Desk"),
    ("detective-archive/07_precision_ranker.py",   "MILESTONE 07 — The Precision Ranker"),
    ("detective-archive/08_detective_brief.py",    "MILESTONE 08 — The Detective's Brief"),
    ("detective-archive/09_complete_archive.py",   "MILESTONE 09 — The Complete Detective Archive"),
]

# ── PNG theme and dimensions ───────────────────────────────────────────────────
# 1700 × variable px at 2× effective resolution — suitable for Medium articles.
# Menlo 24 pt gives ~14.8 px/char; 1700 px accommodates the widest output
# (107 visible chars) with 104 px of horizontal padding to spare.

THEME = {
    "bg":        (13, 17, 23),      # #0d1117  GitHub dark background
    "fg":        (230, 237, 243),   # #e6edf3  primary text
    "title_bg":  (22, 27, 34),      # #161b22  title bar
    "title_fg":  (88, 166, 255),    # #58a6ff  blue accent
    "border":    (48, 54, 61),      # #30363d  separator line
    "dot_red":   (255, 95, 87),
    "dot_amber": (255, 189, 46),
    "dot_green": (40, 201, 64),
}

IMG_WIDTH     = 1700
IMG_FONT_SIZE = 24
IMG_TITLE_FS  = 22
IMG_LINE_H    = 36
IMG_PADDING_X = 52
IMG_PADDING_Y = 44
IMG_TITLE_H   = 68
IMG_DOT_R     = 9
IMG_DOT_GAP   = 26

# ── Font detection ─────────────────────────────────────────────────────────────
_FONT_CANDIDATES = [
    # macOS
    ("/System/Library/Fonts/Menlo.ttc",                                   {"index": 0}),
    ("/System/Library/Fonts/Monaco.ttf",                                  {}),
    ("/System/Library/Fonts/Courier.ttc",                                 {"index": 0}),
    ("/Library/Fonts/Courier New.ttf",                                    {}),
    # Linux
    ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",               {}),
    ("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",   {}),
    ("/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",                 {}),
    # Windows
    ("C:/Windows/Fonts/consola.ttf",                                      {}),
    ("C:/Windows/Fonts/cour.ttf",                                         {}),
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    """Return the best available monospace TrueType font at the given size."""
    for path, kwargs in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(path, size, **kwargs)
        except (IOError, OSError, AttributeError):
            continue
    # Bitmap fallback — no size control, limited Unicode coverage
    print("  [font] No TrueType font found — falling back to Pillow default.")
    print("         Unicode characters (█ ─ ★) may not render correctly.")
    return ImageFont.load_default()


def _text_width(draw: ImageDraw.ImageDraw, text: str, font) -> float:
    """Measure rendered text width, compatible with Pillow 8–11."""
    try:
        return float(draw.textlength(text, font=font))
    except AttributeError:
        try:
            w, _ = font.getsize(text)
            return float(w)
        except Exception:
            bbox = font.getbbox(text)
            return float(bbox[2] - bbox[0]) if bbox else len(text) * IMG_FONT_SIZE * 0.6


# ── HTML generation ────────────────────────────────────────────────────────────
_HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: #0a0a0a;
      min-height: 100vh;
      display: flex;
      justify-content: center;
      align-items: flex-start;
      padding: 48px 24px;
      font-family: 'Menlo', 'Monaco', 'Lucida Console', 'Courier New', monospace;
    }}
    .window {{
      width: 100%;
      max-width: 880px;
      border-radius: 10px;
      overflow: hidden;
      box-shadow: 0 24px 80px rgba(0, 0, 0, 0.75);
      border: 1px solid #21262d;
    }}
    .titlebar {{
      background: #161b22;
      padding: 13px 20px;
      display: flex;
      align-items: center;
      gap: 12px;
      border-bottom: 1px solid #30363d;
    }}
    .dots {{ display: flex; gap: 7px; flex-shrink: 0; }}
    .dot {{
      width: 12px; height: 12px;
      border-radius: 50%; flex-shrink: 0;
    }}
    .dot-red   {{ background: #ff5f57; }}
    .dot-amber {{ background: #ffbd2e; }}
    .dot-green {{ background: #28c940; }}
    .title-text {{
      color: #58a6ff;
      font-size: 13px;
      font-weight: 500;
      flex: 1;
      text-align: center;
      letter-spacing: 0.02em;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .meta-text {{ color: #484f58; font-size: 11px; flex-shrink: 0; }}
    .body {{
      background: #0d1117;
      padding: 28px 32px 36px;
      overflow-x: auto;
    }}
    pre {{
      font-family: inherit;
      font-size: 13px;
      line-height: 1.65;
      color: #e6edf3;
      white-space: pre;
      tab-size: 2;
    }}
    .footer {{
      background: #161b22;
      padding: 9px 20px;
      border-top: 1px solid #30363d;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .footer-left  {{ color: #484f58; font-size: 11px; }}
    .footer-right {{ color: #484f58; font-size: 11px; }}
  </style>
</head>
<body>
  <div class="window">
    <div class="titlebar">
      <div class="dots">
        <div class="dot dot-red"></div>
        <div class="dot dot-amber"></div>
        <div class="dot dot-green"></div>
      </div>
      <div class="title-text">{title_esc}</div>
      <div class="meta-text">{elapsed:.2f}s</div>
    </div>
    <div class="body"><pre>{output_esc}</pre></div>
    <div class="footer">
      <span class="footer-left">Build 2 — Building The Detective Archive</span>
      <span class="footer-right">{timestamp}</span>
    </div>
  </div>
</body>
</html>
"""


def make_html(title: str, output: str, elapsed: float, timestamp: str) -> str:
    return _HTML_TEMPLATE.format(
        title      = html_module.escape(title),
        title_esc  = html_module.escape(title),
        output_esc = html_module.escape(output),
        elapsed    = elapsed,
        timestamp  = html_module.escape(timestamp),
    )


# ── PNG generation ─────────────────────────────────────────────────────────────
def make_png(
    title: str,
    output: str,
    body_font: ImageFont.FreeTypeFont,
    title_font: ImageFont.FreeTypeFont,
) -> Image.Image:
    """Render a dark-theme terminal PNG.  Height is dynamic; width is fixed."""
    lines        = output.splitlines()
    body_height  = IMG_PADDING_Y + max(len(lines), 1) * IMG_LINE_H + IMG_PADDING_Y
    total_height = IMG_TITLE_H + body_height

    img  = Image.new("RGB", (IMG_WIDTH, total_height), THEME["bg"])
    draw = ImageDraw.Draw(img)

    # Title bar
    draw.rectangle([(0, 0), (IMG_WIDTH, IMG_TITLE_H)], fill=THEME["title_bg"])
    draw.line([(0, IMG_TITLE_H), (IMG_WIDTH, IMG_TITLE_H)], fill=THEME["border"])

    # Traffic-light dots
    dot_y = IMG_TITLE_H // 2
    for i, key in enumerate(("dot_red", "dot_amber", "dot_green")):
        cx = IMG_PADDING_X + i * IMG_DOT_GAP
        draw.ellipse(
            [(cx - IMG_DOT_R, dot_y - IMG_DOT_R),
             (cx + IMG_DOT_R, dot_y + IMG_DOT_R)],
            fill=THEME[key],
        )

    # Centred title
    tw = _text_width(draw, title, title_font)
    tx = int((IMG_WIDTH - tw) // 2)
    ty = (IMG_TITLE_H - IMG_TITLE_FS) // 2
    draw.text((tx, ty), title, font=title_font, fill=THEME["title_fg"])

    # Body text — one line at a time; fall back on unencodable characters
    y = IMG_TITLE_H + IMG_PADDING_Y
    for line in lines:
        try:
            draw.text((IMG_PADDING_X, y), line, font=body_font, fill=THEME["fg"])
        except Exception:
            safe = "".join(c if ord(c) < 128 else "?" for c in line)
            draw.text((IMG_PADDING_X, y), safe, font=body_font, fill=THEME["fg"])
        y += IMG_LINE_H

    return img


# ── Script execution ───────────────────────────────────────────────────────────
def run_script(script_path: Path) -> tuple[str, float, bool]:
    """Execute a Build 2 script and return (stdout, elapsed_s, success)."""
    t0     = time.perf_counter()
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(BUILD_ROOT),
    )
    elapsed = time.perf_counter() - t0
    output  = result.stdout
    if result.returncode != 0:
        output += f"\n── stderr ──────────────────────────────\n{result.stderr}"
    return output, elapsed, (result.returncode == 0)


# ── SUMMARY.md ────────────────────────────────────────────────────────────────
def write_summary(rows: list[dict], timestamp: str) -> None:
    ok_n   = sum(1 for r in rows if r["ok"])
    fail_n = len(rows) - ok_n

    lines = [
        "# Article Assets — Build 2",
        "",
        f"Generated: {timestamp}  ",
        f"Scripts: {len(rows)}  ",
        f"Results: {ok_n} OK / {fail_n} FAIL  ",
        "",
        "---",
        "",
        "| # | Chapter | Script | Output | HTML | Screenshot | Status | Time |",
        "|---|---------|--------|--------|------|------------|--------|------|",
    ]

    for i, r in enumerate(rows, 1):
        status = "✅" if r["ok"] else "❌"
        png    = f"[png]({r['png_rel']})" if r["png_rel"] else "—"
        lines.append(
            f"| {i} | {r['title']} "
            f"| `{r['script']}` "
            f"| [txt]({r['out_rel']}) "
            f"| [html]({r['html_rel']}) "
            f"| {png} "
            f"| {status} "
            f"| {r['elapsed']:.2f}s |"
        )

    lines += [
        "",
        "---",
        "",
        "## Asset Notes",
        "",
        "- **outputs/**: plain-text UTF-8 captures — no ANSI escape codes.",
        "- **html/**: self-contained files — open any `.html` directly in a browser.",
        "- **screenshots/**: 1700 × variable px, 2× resolution for Medium.",
        "  Font: Menlo (macOS) · DejaVu Sans Mono (Linux) · Courier New (fallback).",
        "- Scripts run with `python3` (stdlib only — no pip install needed to run them).",
        "",
        "## Regenerating",
        "",
        "```bash",
        "# From builds/project-002-detective-archive/",
        "pip install Pillow          # once, for PNG screenshots",
        "python3 scripts/generate_article_assets.py",
        "```",
        "",
    ]

    (ASSETS / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")


# ── Main ───────────────────────────────────────────────────────────────────────
def main() -> None:
    print("=" * 62)
    print("  Article Asset Generator — Build 2")
    print("=" * 62)
    print(f"  Build root : {BUILD_ROOT}")
    print(f"  Assets dir : {ASSETS}")
    print()

    if not PIL_AVAILABLE:
        print("  WARNING: Pillow not installed — PNG screenshots will be skipped.")
        print("  To generate screenshots:  pip install Pillow")
        print()

    for d in (OUT_DIR, HTML_DIR, SHOT_DIR):
        d.mkdir(parents=True, exist_ok=True)

    body_font  = load_font(IMG_FONT_SIZE) if PIL_AVAILABLE else None
    title_font = load_font(IMG_TITLE_FS)  if PIL_AVAILABLE else None

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows: list[dict] = []

    print(f"  {'Script':<52}  {'Status':>6}  {'Time':>8}  {'Dimensions':>16}")
    print(f"  {'─' * 88}")

    for rel_path, title in MANIFEST:
        script_path = BUILD_ROOT / rel_path
        stem        = script_path.stem
        folder      = script_path.parent.name
        asset_stem  = f"{folder}__{stem}"

        out_path  = OUT_DIR  / f"{asset_stem}.txt"
        html_path = HTML_DIR / f"{asset_stem}.html"
        png_path  = SHOT_DIR / f"{asset_stem}.png"

        output, elapsed, ok = run_script(script_path)

        out_path.write_text(output, encoding="utf-8")
        html_path.write_text(make_html(title, output, elapsed, timestamp), encoding="utf-8")

        dim_str = "—"
        png_rel = None
        if PIL_AVAILABLE and body_font:
            img = make_png(title, output, body_font, title_font)
            img.save(str(png_path), "PNG", optimize=False, dpi=(144, 144))
            dim_str = f"{img.width}×{img.height}px"
            png_rel = f"screenshots/{asset_stem}.png"

        rows.append({
            "title":    title,
            "script":   rel_path,
            "out_rel":  f"outputs/{asset_stem}.txt",
            "html_rel": f"html/{asset_stem}.html",
            "png_rel":  png_rel,
            "ok":       ok,
            "elapsed":  elapsed,
        })

        status_str = "OK" if ok else "FAIL"
        print(f"  {rel_path:<52}  {status_str:>6}  {elapsed:>7.2f}s  {dim_str:>16}")

    write_summary(rows, timestamp)

    ok_n   = sum(1 for r in rows if r["ok"])
    fail_n = len(rows) - ok_n

    print(f"\n  {'─' * 88}")
    print(
        f"  Done. {ok_n}/{len(rows)} scripts OK"
        + (f" — {fail_n} FAILED" if fail_n else "") + "."
    )
    print()
    print(f"  Generated:")
    print(f"    {len(rows)} × .txt    →  article-assets/outputs/")
    print(f"    {len(rows)} × .html   →  article-assets/html/")
    if PIL_AVAILABLE:
        print(f"    {len(rows)} × .png    →  article-assets/screenshots/")
    print(f"    SUMMARY.md        →  article-assets/SUMMARY.md")
    print()


if __name__ == "__main__":
    main()
