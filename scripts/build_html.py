#!/usr/bin/env python3
"""
Build static HTML from JSON exam data.

Usage:
  python3 scripts/build_html.py
"""

import hashlib
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "exams"
DOCS_DIR = ROOT / "docs"


def _password_hash() -> str | None:
    pw = os.environ.get("VIEW_PASSWORD", "")
    if not pw:
        return None
    return hashlib.sha256(pw.encode()).hexdigest()


def _gate_html(session_key: str) -> str:
    h = _password_hash()
    if not h:
        return ""
    return f"""<body class="locked">
<section id="gate">
  <h1>SC 午後問題</h1>
  <input id="pw" type="password" autocomplete="current-password" placeholder="Password">
  <button id="unlock" type="button">Open</button>
  <p id="gate-error" class="error"></p>
</section>
<script>
  const expected = "{h}";
  const gate = document.getElementById("gate");
  async function sha256(t) {{
    const b = new TextEncoder().encode(t);
    const h = await crypto.subtle.digest("SHA-256", b);
    return Array.from(new Uint8Array(h)).map(x => x.toString(16).padStart(2,"0")).join("");
  }}
  async function unlock() {{
    if (await sha256(document.getElementById("pw").value) === expected) {{
      sessionStorage.setItem("{session_key}", "1");
      document.body.classList.remove("locked");
      gate.remove();
    }} else {{
      document.getElementById("gate-error").textContent = "パスワードが違います";
    }}
  }}
  if (sessionStorage.getItem("{session_key}") === "1") {{
    document.body.classList.remove("locked");
    gate.remove();
  }}
  document.getElementById("unlock").addEventListener("click", unlock);
  document.getElementById("pw").addEventListener("keydown", e => {{ if (e.key === "Enter") unlock(); }});
</script>"""


def load_all_exams() -> list[dict]:
    exams = []
    for p in sorted(DATA_DIR.glob("*.json")):
        with open(p, encoding="utf-8") as f:
            exams.append(json.load(f))
    exams.sort(key=lambda e: (e["year"], e.get("split") or 0, e["period"]))
    return exams


def group_by_year(exams: list[dict]) -> dict:
    groups: dict[int, list] = {}
    for exam in exams:
        year = exam["year"]
        groups.setdefault(year, []).append(exam)
    return dict(sorted(groups.items(), reverse=True))


def exam_href(exam: dict) -> str:
    return f"exams/{exam['id']}.html"


def build_index(exams: list[dict]) -> str:
    groups = group_by_year(exams)

    rows = []
    for year, year_exams in groups.items():
        for exam in year_exams:
            label = exam["label"]
            href = exam_href(exam)
            rows.append(f'<li><a href="{href}">{label}</a></li>')

    items_html = "\n".join(rows)
    gate = _gate_html("sc_pm_unlocked")
    body_open = gate if gate else "<body>"
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive">
<title>SC 午後問題 まとめ</title>
<link rel="stylesheet" href="assets/style.css">
</head>
{body_open}
<header class="site-header">
  <h1>情報処理安全確保支援士 午後問題</h1>
</header>
<main class="index-main">
  <ul class="exam-list">
{items_html}
  </ul>
</main>
<footer class="site-footer">本サイトは個人学習目的のみで使用し、商用利用・公開配布はしていません。</footer>
</body>
</html>
"""


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_inline(s: str) -> str:
    """Convert [[u:text]] → <span class="u">text</span> after HTML-escaping."""
    escaped = esc(s)
    return re.sub(r'\[\[u:(.*?)\]\]', r'<span class="u">\1</span>', escaped)


def _figure_lines_to_html(text: str) -> str:
    import re
    parts = []
    for raw in text.split('\n'):
        s = raw.strip()
        if not s:
            parts.append('<div class="fig-spacer"></div>')
            continue
        if re.match(r'^[0-9]+[．.]', s):
            m = re.match(r'^([0-9]+[．.]\s*)', s)
            marker, body = m.group(1).strip(), s[m.end():]
            parts.append(
                f'<div class="fig-l1"><span class="fig-marker">{esc(marker)}</span>'
                f'<span class="fig-body">{render_inline(body)}</span></div>'
            )
        elif re.match(r'^（[0-9]+）', s):
            m = re.match(r'^(（[0-9]+）\s*)', s)
            marker, body = m.group(1).strip(), s[m.end():]
            parts.append(
                f'<div class="fig-l2"><span class="fig-marker">{esc(marker)}</span>'
                f'<span class="fig-body">{render_inline(body)}</span></div>'
            )
        elif re.match(r'^（[ivxIVXcdlm]+）', s):
            m = re.match(r'^(（[ivxIVXcdlm]+）\s*)', s)
            marker, body = m.group(1).strip(), s[m.end():]
            parts.append(
                f'<div class="fig-l3"><span class="fig-marker">{esc(marker)}</span>'
                f'<span class="fig-body">{render_inline(body)}</span></div>'
            )
        elif s.startswith('：'):
            parts.append(f'<pre class="fig-code">{render_inline(s[1:].strip())}</pre>')
        else:
            parts.append(f'<div class="fig-text">{render_inline(s)}</div>')
    return '\n'.join(parts)


def render_figure(b: dict) -> str:
    caption = esc(b.get("caption", ""))
    content = _figure_lines_to_html(b.get("content", ""))
    cap_html = f'<figcaption>{caption}</figcaption>' if caption else ""
    return (
        f'<figure class="text-figure">'
        f'<div class="text-figure-body">{content}</div>'
        f'{cap_html}'
        f'</figure>'
    )


def render_dialogue(b: dict) -> str:
    lines_html = ""
    for line in b.get("lines", []):
        speaker = esc(line.get("speaker", ""))
        text = render_inline(line.get("text", ""))
        lines_html += f'<div class="dialogue-line"><dt>{speaker}</dt><dd>{text}</dd></div>'
    return f'<dl class="dialogue">{lines_html}</dl>'


def render_table(b: dict) -> str:
    caption = b.get("caption", "")
    col_groups = b.get("col_groups", [])
    headers = b.get("headers", [])
    rows = b.get("rows", [])

    cap_html = f'<caption>{esc(caption)}</caption>' if caption else ""

    thead = ""
    if col_groups:
        # First row: col_groups (span=1 gets rowspan=2, span>1 gets colspan=N)
        row1 = ""
        for g in col_groups:
            label = esc(g.get("label", ""))
            span = g.get("span", 1)
            if span == 1:
                row1 += f'<th rowspan="2">{label}</th>'
            else:
                row1 += f'<th colspan="{span}">{label}</th>'
        # Second row: sub-headers
        row2 = "".join(f'<th>{esc(h)}</th>' for h in headers)
        thead = f'<thead><tr>{row1}</tr><tr>{row2}</tr></thead>'
    elif headers:
        ths = "".join(f'<th>{esc(h)}</th>' for h in headers)
        thead = f'<thead><tr>{ths}</tr></thead>'

    tbody_rows = []
    for row in rows:
        tds = "".join(f'<td>{render_inline(str(cell))}</td>' for cell in row)
        tbody_rows.append(f'<tr>{tds}</tr>')
    tbody = f'<tbody>{"".join(tbody_rows)}</tbody>'

    return f'<div class="table-wrap"><table class="exam-table">{cap_html}{thead}{tbody}</table></div>'


_PROBLEM_HEADING_RE = re.compile(r'^(問\d+)\s+(.+?)(?:に関する次の記述を読んで.*)?$')


def blocks_to_html(blocks: list[dict]) -> str:
    parts = []
    for b in blocks:
        if b["type"] == "text":
            content = b["content"]
            m = _PROBLEM_HEADING_RE.match(content.split('\n')[0])
            if m and 'に関する次の記述を読んで' in content:
                prob = esc(m.group(1))
                title = esc(m.group(2).rstrip('　 '))
                parts.append(f'<h2 class="page-problem-title">{prob}　{title}</h2>')
            else:
                parts.append(f'<pre class="text-block">{render_inline(content)}</pre>')
        elif b["type"] == "code":
            caption = esc(b.get("caption", ""))
            lang = esc(b.get("language", ""))
            content = esc(b.get("content", ""))
            cap_html = f'<div class="code-caption">{caption}</div>' if caption else ""
            lang_badge = f'<span class="code-lang">{lang}</span>' if lang else ""
            parts.append(
                f'<figure class="code-block">'
                f'<div class="code-header">{cap_html}{lang_badge}</div>'
                f'<pre><code>{content}</code></pre>'
                f'</figure>'
            )
        elif b["type"] == "figure":
            parts.append(render_figure(b))
        elif b["type"] == "dialogue":
            parts.append(render_dialogue(b))
        elif b["type"] == "table":
            parts.append(render_table(b))
        else:
            src = b.get("src") or ""
            caption = b.get("caption") or ""
            if src:
                img_tag = f'<img src="../../{esc(src)}" alt="{esc(caption)}" class="inserted-image">'
                cap_tag = f'<p class="image-caption">{esc(caption)}</p>' if caption else ""
                parts.append(f'<figure class="image-block has-image">{img_tag}{cap_tag}</figure>')
            else:
                cap_display = esc(caption) if caption else "キャプションを入力（任意）"
                parts.append(
                    f'<figure class="image-block">'
                    f'<div class="image-placeholder-inner">&#128444; ここに図・表が入ります</div>'
                    f'<p class="image-caption placeholder-caption">{cap_display}</p>'
                    f'</figure>'
                )
    return "\n".join(parts)


def render_problems(problems: list[dict]) -> str:
    content_pages = [p for p in problems if p.get("is_content", True)]
    if not content_pages:
        return ""

    has_metadata = any(p.get("problem") for p in content_pages)
    if not has_metadata:
        # fallback: render pages sequentially without section grouping
        raw = []
        for p in content_pages:
            page_num = p.get("page", "")
            blocks = p.get("blocks") or p.get("items", [])
            content_html = blocks_to_html(blocks)
            raw.append(
                f'<div class="pdf-page" data-page="{page_num}">'
                f'<span class="page-num">p.{page_num}</span>'
                f'{content_html}'
                f'</div>'
            )
        return "\n".join(raw)

    parts = ['<div class="expl-container">']
    current_problem = None
    section_open = False

    for p in content_pages:
        prob = p.get("problem")
        title = p.get("title", "")
        blocks = p.get("blocks") or p.get("items", [])
        content_html = blocks_to_html(blocks)
        page_html = f'<div class="problem-content">{content_html}</div>'

        if prob and prob != current_problem:
            if section_open:
                parts.append('</section>')
            heading = f"{esc(prob)}　{esc(title)}" if title else esc(prob)
            parts.append(
                f'<section class="expl-problem">'
                f'<h2 class="expl-problem-title">{heading}</h2>'
            )
            current_problem = prob
            section_open = True

        parts.append(page_html)

    if section_open:
        parts.append('</section>')
    parts.append('</div>')
    return "\n".join(parts)


def render_explanations(exam: dict) -> str:
    explanations = exam.get("explanations", [])
    if not explanations:
        return render_problems(exam.get("answer_pages", []))

    parts = ['<div class="expl-container">']
    for prob in explanations:
        problem = esc(prob.get("problem", ""))
        title = esc(prob.get("title", ""))
        heading = f"{problem}　{title}" if title else problem
        parts.append(f'<section class="expl-problem"><h2 class="expl-problem-title">{heading}</h2><div class="expl-items">')
        for item in prob.get("items", []):
            label = esc(item.get("label", ""))
            answer = render_inline(item.get("answer", ""))
            explanation = render_inline(item.get("explanation", ""))
            parts.append(
                f'<div class="expl-item">'
                f'<div class="expl-label">{label}</div>'
                f'<div class="expl-answer-box"><span class="expl-answer-tag">解答例</span>'
                f'<div class="expl-answer-text">{answer}</div></div>'
                f'<div class="expl-explanation">{explanation}</div>'
                f'</div>'
            )
        parts.append('</div></section>')
    parts.append('</div>')
    return "\n".join(parts)


def build_exam_page(exam: dict) -> str:
    label = exam["label"]
    exam_id = exam["id"]
    qs_html = render_problems(exam.get("problems", exam.get("pages", [])))
    ans_html = render_explanations(exam)
    pdf_links = (
        f'<a href="../pdf/{exam_id}_qs.pdf" class="pdf-link" target="_blank">問題PDF</a>'
        f'<a href="../pdf/{exam_id}_ans.pdf" class="pdf-link" target="_blank">解答PDF</a>'
    )

    gate = _gate_html("sc_pm_unlocked")
    body_open = gate if gate else "<body>"
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex,nofollow,noarchive">
<title>{label} | SC 午後問題</title>
<link rel="stylesheet" href="../assets/style.css">
</head>
{body_open}
<header class="site-header">
  <a href="../index.html" class="back-link">← 一覧</a>
  <h1>{label}</h1>
  <div class="pdf-links">{pdf_links}</div>
</header>
<main class="exam-main">
  <div class="tab-bar">
    <button class="tab-btn active" data-target="tab-question">問題</button>
    <button class="tab-btn" data-target="tab-answer">解答例</button>
  </div>

  <div id="tab-question" class="tab-content active">
    <div class="pages-container">
{qs_html}
    </div>
  </div>

  <div id="tab-answer" class="tab-content">
    <div class="pages-container">
{ans_html}
    </div>
  </div>
</main>
<script>
document.querySelectorAll('.tab-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(btn.dataset.target).classList.add('active');
  }});
}});
</script>
<footer class="site-footer">本サイトは個人学習目的のみで使用し、商用利用・公開配布はしていません。</footer>
</body>
</html>
"""


def build_css() -> str:
    return """\
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #f8f9fa;
  --surface: #ffffff;
  --border: #dee2e6;
  --text: #212529;
  --text-muted: #6c757d;
  --accent: #0d6efd;
  --accent-hover: #0b5ed7;
  --radius: 6px;
  --font-mono: "Menlo", "Consolas", "Courier New", monospace;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic UI", sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.8;
}

.site-header {
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  padding: 12px 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.site-header h1 {
  font-size: 1.1rem;
  font-weight: 600;
}

.back-link {
  color: var(--accent);
  text-decoration: none;
  font-size: 0.9rem;
  white-space: nowrap;
}
.back-link:hover { text-decoration: underline; }

.pdf-links { margin-left: auto; display: flex; gap: 8px; }

.pdf-link {
  color: var(--accent);
  text-decoration: none;
  font-size: 0.82rem;
  border: 1px solid var(--accent);
  border-radius: var(--radius);
  padding: 3px 10px;
  white-space: nowrap;
}
.pdf-link:hover { background: var(--accent); color: #fff; }

/* Index */
.index-main { max-width: 700px; margin: 40px auto; padding: 0 24px; }

.exam-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.exam-list li a {
  display: block;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 12px 16px;
  color: var(--text);
  text-decoration: none;
  font-size: 0.95rem;
  transition: border-color 0.15s, box-shadow 0.15s;
}
.exam-list li a:hover {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(13,110,253,0.1);
}

/* Exam page */
.exam-main { padding: 24px; }

.tab-bar {
  display: flex;
  gap: 4px;
  margin-bottom: 16px;
  border-bottom: 2px solid var(--border);
  padding-bottom: 0;
}

.tab-btn {
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  padding: 8px 20px;
  cursor: pointer;
  font-size: 0.95rem;
  color: var(--text-muted);
  transition: color 0.15s, border-color 0.15s;
}
.tab-btn:hover { color: var(--text); }
.tab-btn.active {
  color: var(--accent);
  border-bottom-color: var(--accent);
  font-weight: 600;
}

.tab-content { display: none; }
.tab-content.active { display: block; }

.pages-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 900px;
}

.pdf-page {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px 24px;
  position: relative;
}


.text-block {
  font-family: "Hiragino Sans", "Yu Gothic", sans-serif;
  font-size: 0.88rem;
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}

.text-block { margin-top: 30px; }

.image-block {
  margin: 30px 0 0;
  border: 2px dashed var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}

.image-block.has-image { border-style: solid; border-color: var(--border); }

.image-placeholder-inner {
  background: #f0f4ff;
  color: var(--text-muted);
  text-align: center;
  padding: 28px 16px;
  font-size: 0.9rem;
  letter-spacing: 0.02em;
}

.inserted-image {
  display: block;
  max-width: 100%;
  height: auto;
}

.image-caption {
  font-size: 0.8rem;
  color: var(--text-muted);
  padding: 4px 12px 8px;
  margin: 0;
}

.placeholder-caption { font-style: italic; }

.table-wrap {
  margin: 30px 0 0;
  width: 100%;
}

.exam-table {
  border-collapse: collapse;
  font-size: 0.88rem;
  line-height: 1.6;
  table-layout: auto;
}

.exam-table caption {
  text-align: left;
  font-weight: 600;
  margin-bottom: 6px;
  font-size: 0.9rem;
  caption-side: top;
}

.exam-table th,
.exam-table td {
  border: 1px solid var(--border);
  padding: 6px 10px;
  vertical-align: top;
  white-space: pre-wrap;
}

.exam-table th {
  background: #f0f4ff;
  font-weight: 600;
  text-align: center;
}

.exam-table td:first-child { text-align: center; white-space: nowrap; }

/* underline span */
.u { text-decoration: underline; }

/* figure (bordered text box) */
.text-figure {
  margin: 12px 0;
  border: 1px solid var(--text);
  border-radius: var(--radius);
}

.text-figure-body {
  padding: 16px 20px;
  font-family: "Hiragino Sans", "Yu Gothic", sans-serif;
  font-size: 0.88rem;
  line-height: 1.8;
}

.fig-l1, .fig-l2, .fig-l3, .fig-text {
  display: flex;
  gap: 0.4em;
  margin-top: 6px;
}
.fig-l1 { margin-top: 12px; }
.fig-l2 { padding-left: 1.5em; }
.fig-l3 { padding-left: 3em; }
.fig-spacer { height: 6px; }
.fig-marker { white-space: nowrap; font-weight: 600; flex-shrink: 0; }
.fig-body { flex: 1; }

.fig-code {
  margin: 4px 0 4px 2em;
  padding: 6px 12px;
  background: #f5f5f5;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-family: var(--font-mono);
  font-size: 0.82rem;
  white-space: pre-wrap;
  word-break: break-all;
}

.text-figure figcaption {
  border-top: 1px solid var(--border);
  padding: 6px 20px;
  font-size: 0.82rem;
  color: var(--text-muted);
  text-align: center;
}

/* dialogue */
.dialogue {
  margin: 30px 0 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.dialogue-line {
  display: grid;
  grid-template-columns: 6em 1fr;
  gap: 0 12px;
  font-size: 0.88rem;
  line-height: 1.7;
}

.dialogue dt {
  font-weight: 600;
  color: var(--accent);
  text-align: right;
  white-space: nowrap;
  padding-top: 1px;
}

.dialogue dd {
  border-left: 2px solid var(--border);
  padding-left: 10px;
  white-space: pre-wrap;
}

/* explanations tab */
.expl-container { display: flex; flex-direction: column; gap: 24px; max-width: 900px; padding-top: 8px; }

.expl-problem {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}

.expl-problem-title {
  font-size: 1rem;
  font-weight: 700;
  padding: 12px 20px;
  background: #f0f4ff;
  border-bottom: 1px solid var(--border);
}

.expl-items { display: flex; flex-direction: column; }

.expl-item {
  padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.expl-item:last-child { border-bottom: none; }

.expl-label {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--accent);
}

.expl-answer-box {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: var(--radius);
  padding: 8px 12px;
}

.expl-answer-tag {
  font-size: 0.72rem;
  font-weight: 700;
  color: #92400e;
  background: #fde68a;
  border-radius: 3px;
  padding: 1px 5px;
  white-space: nowrap;
  flex-shrink: 0;
  margin-top: 2px;
}

.expl-answer-text {
  font-size: 0.9rem;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-all;
}

.expl-explanation {
  font-size: 0.85rem;
  color: #374151;
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-all;
  padding-left: 4px;
  border-left: 3px solid var(--border);
}

.problem-content {
  padding: 14px 20px;
}

.problem-content > *:first-child { margin-top: 0; }

/* code block */
.code-block {
  margin: 16px 0;
  border-radius: var(--radius);
  overflow: hidden;
  border: 1px solid #334155;
}
.code-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #1e293b;
  padding: 6px 14px;
  gap: 8px;
}
.code-caption {
  font-size: 0.8rem;
  color: #94a3b8;
  font-family: "Hiragino Sans", sans-serif;
}
.code-lang {
  font-size: 0.72rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  flex-shrink: 0;
}
.code-block pre {
  margin: 0;
  padding: 16px;
  background: #0f172a;
  overflow-x: auto;
}
.code-block code {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
  font-size: 0.82rem;
  line-height: 1.65;
  color: #e2e8f0;
  white-space: pre;
}

/* site footer */
.site-footer {
  text-align: center;
  font-size: 0.78rem;
  color: #9ca3af;
  padding: 24px 16px;
  margin-top: 32px;
  border-top: 1px solid var(--border);
}

/* password gate */
.locked header, .locked main { display: none; }
#gate { max-width: 360px; margin: 24vh auto 0; padding: 0 16px; }
#gate h1 { font-size: 1.2rem; font-weight: 700; margin-bottom: 8px; }
#gate input, #gate button { width: 100%; font: inherit; padding: 10px 12px; margin-top: 10px; border: 1px solid var(--border); border-radius: var(--radius); box-sizing: border-box; }
#gate button { cursor: pointer; background: var(--text); color: #fff; font-weight: 600; }
#gate .error { color: #c2410c; min-height: 1.5em; font-size: 0.88rem; margin-top: 6px; }

@media (max-width: 600px) {
  .exam-main { padding: 16px; }
  .pdf-page { padding: 16px; }
}
"""


def main():
    exams = load_all_exams()
    print(f"Found {len(exams)} exam JSON files")

    DOCS_DIR.mkdir(exist_ok=True)
    (DOCS_DIR / "assets").mkdir(exist_ok=True)
    (DOCS_DIR / "exams").mkdir(exist_ok=True)

    css_path = DOCS_DIR / "assets" / "style.css"
    css_path.write_text(build_css(), encoding="utf-8")
    print(f"  Written: {css_path.relative_to(ROOT)}")

    index_html = build_index(exams)
    index_path = DOCS_DIR / "index.html"
    index_path.write_text(index_html, encoding="utf-8")
    print(f"  Written: {index_path.relative_to(ROOT)}")

    for exam in exams:
        html = build_exam_page(exam)
        out = DOCS_DIR / "exams" / f"{exam['id']}.html"
        out.write_text(html, encoding="utf-8")
        print(f"  Written: {out.relative_to(ROOT)}")

    print(f"\nDone. Open docs/index.html in a browser.")


if __name__ == "__main__":
    main()
