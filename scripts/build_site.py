"""Build the static GitHub Pages landing page from Markdown."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

import markdown


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT = REPO_ROOT / "docs" / "index.md"
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "index.html"


PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title}</title>
    <meta name="description" content="{description}" />
    <link rel="icon" href="./rag-comparison/favicon.ico" />
    <style>
      :root {{
        color-scheme: light;
        --ink: #191919;
        --muted: #5d646b;
        --line: #d7d7d7;
        --paper: #fbfaf7;
        --panel: #ffffff;
        --accent: #255d68;
        --accent-soft: #eef5f6;
        --code: #f1f1ef;
        font-family: Georgia, "Times New Roman", serif;
      }}

      * {{
        box-sizing: border-box;
      }}

      body {{
        background: var(--paper);
        color: var(--ink);
        font-size: 18px;
        line-height: 1.62;
        margin: 0;
      }}

      a {{
        color: var(--accent);
        text-underline-offset: 0.16em;
      }}

      .page {{
        margin: 0 auto;
        max-width: 980px;
        padding: 56px 24px 80px;
      }}

      .paper {{
        background: var(--panel);
        border: 1px solid var(--line);
        box-shadow: 0 14px 45px rgba(25, 25, 25, 0.07);
        padding: 56px;
      }}

      h1,
      h2,
      h3 {{
        font-weight: 600;
        letter-spacing: 0;
        line-height: 1.18;
      }}

      h1 {{
        border-bottom: 1px solid var(--line);
        font-size: clamp(2.1rem, 5vw, 3.6rem);
        margin: 0 0 18px;
        padding-bottom: 24px;
      }}

      h2 {{
        border-top: 1px solid var(--line);
        font-size: 1.65rem;
        margin: 44px 0 14px;
        padding-top: 28px;
      }}

      h3 {{
        font-size: 1.18rem;
        margin: 28px 0 8px;
      }}

      h1 + p {{
        color: var(--muted);
        font-size: 1.18rem;
        margin-top: 0;
      }}

      p {{
        margin: 0 0 1rem;
      }}

      ul,
      ol {{
        padding-left: 1.4rem;
      }}

      li {{
        margin: 0.22rem 0;
      }}

      table {{
        border-collapse: collapse;
        font-size: 0.96rem;
        margin: 20px 0 28px;
        width: 100%;
      }}

      th,
      td {{
        border-bottom: 1px solid var(--line);
        padding: 9px 10px;
        text-align: left;
        vertical-align: top;
      }}

      th {{
        background: var(--accent-soft);
        font-weight: 650;
      }}

      td[align="right"],
      th[align="right"] {{
        text-align: right;
      }}

      img {{
        border: 1px solid var(--line);
        display: block;
        height: auto;
        margin: 24px auto 8px;
        max-width: 100%;
      }}

      img + em {{
        color: var(--muted);
        display: block;
        font-size: 0.92rem;
        line-height: 1.4;
        margin: 0 auto 24px;
        max-width: 820px;
        text-align: center;
      }}

      code {{
        background: var(--code);
        border-radius: 3px;
        font-family: "Cascadia Mono", Consolas, monospace;
        font-size: 0.88em;
        padding: 0.08em 0.28em;
      }}

      pre {{
        background: #242424;
        border-radius: 4px;
        color: #f6f2e9;
        font-size: 0.9rem;
        line-height: 1.5;
        overflow-x: auto;
        padding: 16px;
      }}

      pre code {{
        background: transparent;
        color: inherit;
        padding: 0;
      }}

      blockquote {{
        background: var(--accent-soft);
        border-left: 4px solid var(--accent);
        margin: 22px 0;
        padding: 14px 18px;
      }}

      .site-nav {{
        border-bottom: 1px solid var(--line);
        color: var(--muted);
        display: flex;
        flex-wrap: wrap;
        font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        font-size: 0.92rem;
        gap: 14px;
        justify-content: space-between;
        margin-bottom: 34px;
        padding-bottom: 14px;
      }}

      .site-nav a {{
        color: var(--muted);
        text-decoration: none;
      }}

      .site-nav a:hover {{
        color: var(--accent);
        text-decoration: underline;
      }}

      .footnote {{
        border-top: 1px solid var(--line);
        color: var(--muted);
        font-size: 0.9rem;
        margin-top: 44px;
        padding-top: 18px;
      }}

      @media (max-width: 720px) {{
        body {{
          font-size: 16px;
        }}

        .page {{
          padding: 0;
        }}

        .paper {{
          border-left: 0;
          border-right: 0;
          box-shadow: none;
          padding: 28px 20px 48px;
        }}

        table {{
          display: block;
          overflow-x: auto;
        }}
      }}
    </style>
  </head>
  <body>
    <main class="page">
      <article class="paper">
        <nav class="site-nav" aria-label="Site navigation">
          <a href="./">SRD Rules Agent</a>
          <span>
            <a href="./rag-comparison/">Paired answer browser</a>
            &nbsp;·&nbsp;
            <a href="https://github.com/TecKnow/SRD-rules-agent">Repository</a>
          </span>
        </nav>
        {body}
        <p class="footnote">
          Static landing page generated from <code>docs/index.md</code>.
          The paired answer browser is an exported marimo WebAssembly app.
        </p>
      </article>
    </main>
  </body>
</html>
"""


def extract_title(markdown_text: str) -> str:
    match = re.search(r"^#\s+(.+)$", markdown_text, flags=re.MULTILINE)
    if not match:
        return "SRD Rules Agent"
    return re.sub(r"[*_`]", "", match.group(1)).strip()


def build_page(input_path: Path, output_path: Path) -> None:
    markdown_text = input_path.read_text(encoding="utf-8")
    title = extract_title(markdown_text)
    body = markdown.markdown(
        markdown_text,
        extensions=["extra", "toc", "sane_lists"],
        output_format="html5",
    )
    description = (
        "A D&D SRD 5.2.1 benchmark study comparing model answers with and "
        "without retrieved rules context."
    )
    output_path.write_text(
        PAGE_TEMPLATE.format(
            title=html.escape(title),
            description=html.escape(description),
            body=body,
        ),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build docs/index.html from docs/index.md.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    build_page(args.input, args.output)


if __name__ == "__main__":
    main()
