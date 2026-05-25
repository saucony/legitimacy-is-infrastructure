#!/usr/bin/env python3
"""Render paper.md into a dark-mode HTML artifact and PDF snapshot."""

from __future__ import annotations

import argparse
import html
import os
import re
import shutil
import subprocess
from pathlib import Path


LINK_RE = re.compile(r"(?<!!)\[([^\]]+)\]\((https?://[^)\s]+)\)")
CODE_RE = re.compile(r"`([^`]+)`")
BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
ITALIC_RE = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "section"


def inline(markdown: str) -> str:
    escaped = html.escape(markdown)
    escaped = CODE_RE.sub(lambda m: f"<code>{m.group(1)}</code>", escaped)
    escaped = BOLD_RE.sub(lambda m: f"<strong>{m.group(1)}</strong>", escaped)
    escaped = ITALIC_RE.sub(lambda m: f"<em>{m.group(1)}</em>", escaped)
    escaped = LINK_RE.sub(lambda m: f'<a href="{m.group(2)}">{m.group(1)}</a>', escaped)
    return escaped


def is_table_separator(line: str) -> bool:
    stripped = line.strip()
    return bool(stripped.startswith("|") and set(stripped.replace("|", "").replace(":", "").replace("-", "").strip()) == set())


def split_table_row(line: str) -> list[str]:
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in stripped.split("|")]


def render_table(lines: list[str]) -> str:
    header = split_table_row(lines[0])
    rows = [split_table_row(line) for line in lines[2:]]
    head_html = "".join(f"<th>{inline(cell)}</th>" for cell in header)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{inline(cell)}</td>" for cell in row)
        body_rows.append(f"<tr>{cells}</tr>")
    return f"<div class=\"table-wrap\"><table><thead><tr>{head_html}</tr></thead><tbody>{''.join(body_rows)}</tbody></table></div>"


def markdown_to_html(markdown: str) -> tuple[str, list[tuple[int, str, str]]]:
    lines = markdown.splitlines()
    body: list[str] = []
    toc: list[tuple[int, str, str]] = []
    paragraph: list[str] = []
    in_code = False
    code_lines: list[str] = []
    i = 0
    first_h1_seen = False

    def flush_paragraph() -> None:
        if paragraph:
            body.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph.clear()

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()

        if line.startswith("```"):
            if in_code:
                body.append("<pre><code>" + html.escape("\n".join(code_lines)) + "</code></pre>")
                code_lines.clear()
                in_code = False
            else:
                flush_paragraph()
                in_code = True
            i += 1
            continue

        if in_code:
            code_lines.append(line)
            i += 1
            continue

        if not line.strip():
            flush_paragraph()
            i += 1
            continue

        if line.startswith("|") and i + 1 < len(lines) and is_table_separator(lines[i + 1]):
            flush_paragraph()
            table_lines = [line, lines[i + 1].rstrip()]
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].rstrip())
                i += 1
            body.append(render_table(table_lines))
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            level = len(heading.group(1))
            text = heading.group(2).strip()
            slug = slugify(text)
            toc.append((level, text, slug))
            if level == 1 and not first_h1_seen:
                first_h1_seen = True
                i += 1
                continue
            class_name = ""
            class_attr = f' class="{class_name}"' if class_name else ""
            body.append(f'<h{level} id="{slug}"{class_attr}>{inline(text)}</h{level}>')
            i += 1
            continue

        if line.startswith("> "):
            flush_paragraph()
            quote_lines = []
            while i < len(lines) and lines[i].startswith("> "):
                quote_lines.append(lines[i][2:].strip())
                i += 1
            body.append(f"<blockquote>{inline(' '.join(quote_lines))}</blockquote>")
            continue

        if line.startswith("- "):
            flush_paragraph()
            items = []
            while i < len(lines) and lines[i].startswith("- "):
                items.append(lines[i][2:].strip())
                i += 1
            body.append("<ul>" + "".join(f"<li>{inline(item)}</li>" for item in items) + "</ul>")
            continue

        ordered = re.match(r"^\d+\.\s+(.+)$", line)
        if ordered:
            flush_paragraph()
            items = []
            while i < len(lines):
                match = re.match(r"^\d+\.\s+(.+)$", lines[i].rstrip())
                if not match:
                    break
                items.append(match.group(1).strip())
                i += 1
            body.append("<ol>" + "".join(f"<li>{inline(item)}</li>" for item in items) + "</ol>")
            continue

        paragraph.append(line.strip())
        i += 1

    flush_paragraph()
    return "\n".join(body), toc


def render_document(markdown: str) -> str:
    body, toc = markdown_to_html(markdown)
    title = next((text for level, text, _ in toc if level == 1), "Legitimacy Is Infrastructure")
    toc_links = "\n".join(
        f'<a class="toc-level-{level}" href="#{slug}">{html.escape(text)}</a>'
        for level, text, slug in toc
        if level == 2
    )
    css = """
    :root {
      color-scheme: dark;
      --bg: #080a0f;
      --panel: #0f131c;
      --text: #f3f4ee;
      --muted: #aeb7c5;
      --faint: #6f7a8c;
      --rule: #273246;
      --accent: #8bd3ff;
      --accent-2: #d6ff7f;
      --code: #151b27;
    }
    @page {
      size: Letter;
      margin: 0.62in;
      background: var(--bg);
    }
    * { box-sizing: border-box; }
    html { background: var(--bg); }
    body {
      margin: 0;
      background:
        radial-gradient(circle at 80% 0%, rgba(139, 211, 255, 0.12), transparent 28rem),
        linear-gradient(180deg, #0a0d13 0%, var(--bg) 18rem);
      color: var(--text);
      font-family: ui-serif, Georgia, Cambria, "Times New Roman", serif;
      font-size: 18px;
      line-height: 1.62;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }
    .page {
      max-width: 980px;
      margin: 0 auto;
      padding: 72px 34px 96px;
    }
    .masthead {
      border-bottom: 1px solid var(--rule);
      margin-bottom: 42px;
      padding-bottom: 30px;
    }
    .eyebrow {
      color: var(--accent-2);
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }
    .masthead-title {
      color: var(--text);
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: clamp(52px, 8vw, 92px);
      letter-spacing: 0;
      line-height: 0.98;
      margin: 20px 0 20px;
      max-width: 820px;
    }
    .dek {
      color: var(--muted);
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 18px;
      line-height: 1.45;
      margin-top: -8px;
      max-width: 760px;
    }
    .meta {
      color: var(--faint);
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 13px;
      margin-top: 18px;
    }
    .toc {
      background: rgba(15, 19, 28, 0.72);
      border: 1px solid var(--rule);
      border-radius: 14px;
      margin: 32px 0 54px;
      padding: 22px 24px;
    }
    .toc-title {
      color: var(--accent);
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.1em;
      margin-bottom: 14px;
      text-transform: uppercase;
    }
    .toc a {
      border: 0;
      color: var(--muted);
      display: block;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 14px;
      line-height: 1.35;
      margin: 8px 0;
      text-decoration: none;
    }
    .toc a:hover { color: var(--text); }
    .toc-level-2 { padding-left: 12px; }
    h1, h2, h3, h4, h5, h6 {
      color: var(--text);
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
      line-height: 1.12;
      page-break-after: avoid;
    }
    h1 { font-size: 44px; margin: 46px 0 18px; }
    h2 {
      border-top: 1px solid var(--rule);
      font-size: 30px;
      margin: 52px 0 18px;
      padding-top: 26px;
    }
    h3 { color: #d8e5f4; font-size: 22px; margin: 34px 0 12px; }
    p { margin: 0 0 18px; max-width: 760px; }
    a {
      border-bottom: 1px solid rgba(139, 211, 255, 0.42);
      color: var(--accent);
      text-decoration: none;
    }
    ul, ol {
      margin: 0 0 22px 1.2em;
      max-width: 760px;
      padding: 0;
    }
    li { margin: 7px 0; padding-left: 0.2em; }
    blockquote {
      border-left: 3px solid var(--accent);
      color: #dce3ed;
      margin: 28px 0;
      max-width: 760px;
      padding: 4px 0 4px 22px;
    }
    code {
      background: var(--code);
      border: 1px solid var(--rule);
      border-radius: 5px;
      color: #e9edf5;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.9em;
      padding: 0.08em 0.32em;
    }
    pre {
      background: var(--code);
      border: 1px solid var(--rule);
      border-radius: 12px;
      max-width: 900px;
      overflow-x: auto;
      padding: 18px;
      white-space: pre-wrap;
    }
    pre code { background: none; border: 0; padding: 0; }
    .table-wrap {
      border: 1px solid var(--rule);
      border-radius: 12px;
      margin: 28px 0;
      max-width: 940px;
      overflow-x: auto;
    }
    table {
      border-collapse: collapse;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-size: 13px;
      line-height: 1.38;
      width: 100%;
    }
    th, td {
      border-bottom: 1px solid var(--rule);
      padding: 11px 12px;
      text-align: left;
      vertical-align: top;
    }
    th {
      background: #121927;
      color: #f4f7fb;
      font-weight: 700;
    }
    tr:last-child td { border-bottom: 0; }
    @media print {
      body { font-size: 11.4pt; }
      .page { max-width: none; padding: 0; }
      .toc { break-inside: avoid; }
      h2 { break-after: avoid; }
      a { color: var(--accent); }
    }
    """
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <style>{css}</style>
</head>
<body>
  <main class="page">
    <header class="masthead">
      <div class="eyebrow">Technical Position Paper</div>
      <h1 class="masthead-title">{html.escape(title)}</h1>
      <div class="dek">A pro-build operating doctrine for AI data centers: proof, category discipline, civic legitimacy, and strategic compute capacity.</div>
      <div class="meta">Sasan Salmanzadeh - Version 0.1.0 - May 24, 2026</div>
    </header>
    <nav class="toc" aria-label="Table of contents">
      <div class="toc-title">Contents</div>
      {toc_links}
    </nav>
    {body}
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
    parser.add_argument("--paper", required=True, type=Path)
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--pdf", required=True, type=Path)
    parser.add_argument("--chrome")
    args = parser.parse_args()

    markdown = args.paper.read_text(encoding="utf-8")
    html_text = render_document(markdown)
    args.html.write_text(html_text, encoding="utf-8")

    chrome = find_chrome(args.chrome)
    subprocess.run(
        [
            chrome,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--no-pdf-header-footer",
            f"--print-to-pdf={args.pdf}",
            args.html.resolve().as_uri(),
        ],
        check=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
