"""Render lesson markdown files into styled HTML with Mermaid support.

Outputs to `.lesson-cache/<original-relative-path>.html` so the source
tree stays clean. `action_read` in cli.main auto-builds on demand.
"""

import re
from pathlib import Path

import markdown as _md

from cli.curriculum import CURRICULUM, ROOT

CACHE_DIR = ROOT / ".lesson-cache"


_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — net-learn</title>
  <style>{style}</style>
</head>
<body>
  <main class="markdown-body">
{body}
  </main>
  <script type="module">
    import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs";
    mermaid.initialize({{ startOnLoad: true, theme: "default", securityLevel: "loose" }});
  </script>
</body>
</html>
"""


_STYLE = """
:root {
  --fg: #24292f;
  --muted: #6e7781;
  --bg: #ffffff;
  --panel: #f6f8fa;
  --border: #d0d7de;
  --link: #0969da;
  --accent: #0969da;
}
@media (prefers-color-scheme: dark) {
  :root {
    --fg: #e6edf3;
    --muted: #8b949e;
    --bg: #0d1117;
    --panel: #161b22;
    --border: #30363d;
    --link: #2f81f7;
    --accent: #2f81f7;
  }
}
html, body { background: var(--bg); color: var(--fg); }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  max-width: 900px;
  margin: 0 auto;
  padding: 48px 32px 120px;
  line-height: 1.6;
  font-size: 16px;
}
h1, h2, h3, h4, h5, h6 { line-height: 1.25; margin-top: 1.6em; margin-bottom: 0.6em; }
h1 { font-size: 2em; border-bottom: 1px solid var(--border); padding-bottom: 0.3em; }
h2 { font-size: 1.5em; border-bottom: 1px solid var(--border); padding-bottom: 0.2em; }
h3 { font-size: 1.2em; }
p, ul, ol, blockquote { margin: 0.8em 0; }
code {
  font-family: "SF Mono", Menlo, Consolas, monospace;
  background: var(--panel);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}
pre {
  background: var(--panel);
  padding: 14px 16px;
  border-radius: 6px;
  overflow-x: auto;
  line-height: 1.45;
}
pre code { background: transparent; padding: 0; font-size: 0.88em; }
table { border-collapse: collapse; margin: 1em 0; width: 100%; }
th, td { border: 1px solid var(--border); padding: 6px 12px; text-align: left; }
th { background: var(--panel); font-weight: 600; }
blockquote {
  color: var(--muted);
  border-left: 4px solid var(--border);
  padding: 0.2em 1em;
  margin-left: 0;
}
a { color: var(--link); text-decoration: none; }
a:hover { text-decoration: underline; }
hr { border: 0; border-top: 1px solid var(--border); margin: 2em 0; }
img { max-width: 100%; }
.mermaid {
  background: var(--panel);
  padding: 20px;
  border-radius: 6px;
  text-align: center;
  margin: 1em 0;
}
"""


def _unescape(html_snippet: str) -> str:
    return (
        html_snippet.replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&amp;", "&")
    )


def _md_to_html(md_path: Path) -> str:
    text = md_path.read_text()
    body = _md.markdown(
        text,
        extensions=["fenced_code", "tables", "sane_lists", "toc"],
    )

    # Convert `<pre><code class="language-mermaid">...</code></pre>`
    # blocks back to `<div class="mermaid">...</div>` with their
    # characters unescaped so mermaid.js can render them.
    def _mermaid_sub(m: re.Match) -> str:
        return f'<div class="mermaid">{_unescape(m.group(1))}</div>'

    body = re.sub(
        r'<pre><code class="language-mermaid">(.*?)</code></pre>',
        _mermaid_sub,
        body,
        flags=re.DOTALL,
    )

    title = md_path.stem.replace("_", " ").replace("-", " ").strip().title() or "Lesson"
    return _TEMPLATE.format(title=title, style=_STYLE, body=body)


def target_path(src: Path) -> Path:
    """Return the cached-HTML path for a given markdown source file."""
    rel = src.resolve().relative_to(ROOT.resolve())
    return (CACHE_DIR / rel).with_suffix(".html")


def build_one(src: Path) -> Path:
    """Render `src` to its cached HTML and return the output path."""
    dst = target_path(src)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(_md_to_html(src))
    return dst


def needs_rebuild(src: Path) -> bool:
    dst = target_path(src)
    if not dst.exists():
        return True
    return dst.stat().st_mtime < src.stat().st_mtime


def build_all() -> list[Path]:
    """Render every lesson markdown referenced by the curriculum."""
    built: list[Path] = []
    seen: set[Path] = set()
    for item in CURRICULUM:
        p = item.lesson_path
        if not p or not p.exists() or p.suffix.lower() != ".md":
            continue
        rp = p.resolve()
        if rp in seen:
            continue
        seen.add(rp)
        built.append(build_one(p))
    return built
