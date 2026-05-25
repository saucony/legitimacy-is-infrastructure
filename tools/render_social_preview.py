#!/usr/bin/env python3
"""Render a deterministic social preview image for the paper."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    * { box-sizing: border-box; }
    html, body {
      background: #080a0f;
      height: 100%;
      margin: 0;
      overflow: hidden;
      width: 100%;
    }
    body {
      align-items: stretch;
      color: #f3f4ee;
      display: flex;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .card {
      background:
        radial-gradient(circle at 82% 6%, rgba(139, 211, 255, 0.25), transparent 24rem),
        radial-gradient(circle at 18% 88%, rgba(214, 255, 127, 0.14), transparent 22rem),
        linear-gradient(135deg, #090c12 0%, #0f1522 52%, #07090d 100%);
      border: 1px solid rgba(139, 211, 255, 0.22);
      height: 640px;
      overflow: hidden;
      padding: 76px 84px;
      position: relative;
      width: 1280px;
    }
    .grid {
      background-image:
        linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px);
      background-size: 34px 34px;
      inset: 0;
      mask-image: linear-gradient(90deg, rgba(0,0,0,0.7), transparent 82%);
      opacity: 0.9;
      position: absolute;
    }
    .content {
      max-width: 900px;
      position: relative;
      z-index: 1;
    }
    .eyebrow {
      color: #d6ff7f;
      font-size: 22px;
      font-weight: 800;
      letter-spacing: 0.12em;
      margin-bottom: 28px;
      text-transform: uppercase;
    }
    h1 {
      color: #ffffff;
      font-size: 91px;
      letter-spacing: 0;
      line-height: 0.95;
      margin: 0 0 26px;
      max-width: 820px;
    }
    .dek {
      color: #c4cfdd;
      font-size: 29px;
      line-height: 1.22;
      max-width: 870px;
    }
    .footer {
      align-items: center;
      bottom: 62px;
      color: #8bd3ff;
      display: flex;
      font-size: 21px;
      font-weight: 700;
      gap: 18px;
      letter-spacing: 0;
      position: absolute;
      z-index: 1;
    }
    .dot {
      background: #d6ff7f;
      border-radius: 999px;
      box-shadow: 0 0 28px rgba(214, 255, 127, 0.35);
      height: 10px;
      width: 10px;
    }
    .rail {
      background: linear-gradient(180deg, rgba(139, 211, 255, 0.75), rgba(214, 255, 127, 0.62));
      border-radius: 999px;
      bottom: 78px;
      position: absolute;
      right: 86px;
      top: 78px;
      width: 10px;
    }
  </style>
</head>
<body>
  <main class="card">
    <div class="grid"></div>
    <div class="rail"></div>
    <section class="content" aria-label="Social preview">
      <div class="eyebrow">Technical Position Paper</div>
      <h1>Legitimacy Is Infrastructure</h1>
      <div class="dek">A pro-build operating doctrine for AI data centers: proof, category discipline, civic legitimacy, and strategic compute capacity.</div>
    </section>
    <div class="footer"><span class="dot"></span><span>saucony.github.io/legitimacy-is-infrastructure</span></div>
  </main>
</body>
</html>
"""


def find_chrome(explicit: str | None) -> str:
    candidates = [
        explicit,
        os.environ.get("CHROME_PATH"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        shutil.which("chromium-browser"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    raise SystemExit("Chrome/Chromium not found; pass --chrome or set CHROME_PATH.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--chrome")
    args = parser.parse_args()

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    chrome = find_chrome(args.chrome)

    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = Path(tmpdir) / "social-preview.html"
        html_path.write_text(HTML, encoding="utf-8")
        subprocess.run(
            [
                chrome,
                "--headless",
                "--disable-gpu",
                "--hide-scrollbars",
                "--no-sandbox",
                "--window-size=1280,640",
                f"--screenshot={output}",
                html_path.resolve().as_uri(),
            ],
            check=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
