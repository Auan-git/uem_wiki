"""
Markdown → HTML 转换脚本
用法: python convert.py

保留原 md 文件，在同目录生成同名 .html 文件。
"""

import re
from pathlib import Path

BASE_DIR = Path(__file__).parent

# ============================================================
# Twikoo 评论配置（公共版本，无需配置）
# ============================================================

# ============================================================
# Markdown → HTML 简易转换器（纯 Python，无第三方依赖）
# ============================================================

def md_to_html(text: str) -> str:
    """将 Markdown 文本转换为 HTML（支持常用语法）。"""
    lines = text.split('\n')
    html_lines = []
    in_code_block = False
    code_lang = ''
    code_lines = []
    in_table = False
    table_lines = []
    in_blockquote = False
    bq_lines = []
    in_ul = False
    in_ol = False

    def flush_list(non_list_lines):
        """在切换出列表时输出列表 HTML"""
        return non_list_lines

    def process_inline(t: str) -> str:
        """处理行内 Markdown：加粗、斜体、行内代码、链接、复选框。"""
        # 复选框
        t = re.sub(r'^\s*- \[x\]\s*', '<input type="checkbox" checked disabled> ', t)
        t = re.sub(r'^\s*- \[ \]\s*', '<input type="checkbox" disabled> ', t)
        # 行内代码（必须在加粗/斜体之前，避免内部被处理）
        t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
        # 加粗
        t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
        t = re.sub(r'__(.+?)__', r'<strong>\1</strong>', t)
        # 斜体
        t = re.sub(r'\*(.+?)\*', r'<em>\1</em>', t)
        t = re.sub(r'_(.+?)_', r'<em>\1</em>', t)
        # 链接 [text](url)
        t = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', t)
        return t

    i = 0
    while i < len(lines):
        line = lines[i]

        # 代码块
        if line.strip().startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_lang = line.strip()[3:].strip()
                code_lines = []
            else:
                lang_attr = f' class="language-{code_lang}"' if code_lang else ''
                html_lines.append(f'<pre><code{lang_attr}>')
                html_lines.append('\n'.join(code_lines).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
                html_lines.append('</code></pre>')
                in_code_block = False
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        stripped = line.strip()

        # 空行 → 结束当前块
        if not stripped:
            if in_table:
                rows = []
                for tl in table_lines:
                    cells = [c.strip() for c in tl.strip('|').split('|')]
                    rows.append(cells)
                if len(rows) >= 1:
                    html_lines.append('<table>')
                    # 第一行是表头
                    html_lines.append('<thead><tr>')
                    for cell in rows[0]:
                        html_lines.append(f'  <th>{process_inline(cell)}</th>')
                    html_lines.append('</tr></thead>')
                    # 如果有分隔行 (---|---) 则跳过，其余为数据行
                    data_start = 1
                    if len(rows) > 1 and all(set(c.strip()) <= {'-', ':', ' '} for c in rows[1]):
                        data_start = 2
                    if data_start < len(rows):
                        html_lines.append('<tbody>')
                        for row in rows[data_start:]:
                            html_lines.append('<tr>')
                            for cell in row:
                                html_lines.append(f'  <td>{process_inline(cell)}</td>')
                            html_lines.append('</tr>')
                        html_lines.append('</tbody>')
                    html_lines.append('</table>')
                in_table = False
                table_lines = []

            if in_blockquote:
                html_lines.append('<blockquote>')
                for bl in bq_lines:
                    html_lines.append(f'<p>{process_inline(bl)}</p>')
                html_lines.append('</blockquote>')
                in_blockquote = False
                bq_lines = []

            if in_ul:
                html_lines.append('</ul>')
                in_ul = False
            if in_ol:
                html_lines.append('</ol>')
                in_ol = False

            i += 1
            continue

        # 标题
        heading_match = re.match(r'^(#{1,4})\s+(.*)', stripped)
        if heading_match:
            level = len(heading_match.group(1))
            content = process_inline(heading_match.group(2))
            html_lines.append(f'<h{level}>{content}</h{level}>')
            i += 1
            continue

        # 水平线
        if re.match(r'^[-*_]{3,}\s*$', stripped):
            html_lines.append('<hr>')
            i += 1
            continue

        # 引用
        if stripped.startswith('>'):
            bq_text = stripped[1:].strip()
            if not in_blockquote:
                in_blockquote = True
                bq_lines = []
            bq_lines.append(bq_text)
            i += 1
            continue

        # 表格行
        if '|' in stripped and stripped.startswith('|'):
            if not in_table:
                in_table = True
                table_lines = []
            table_lines.append(stripped)
            i += 1
            continue

        # 无序列表
        ul_match = re.match(r'^[-*+]\s+(.*)', stripped)
        if ul_match:
            if not in_ul:
                if in_ol:
                    html_lines.append('</ol>')
                    in_ol = False
                html_lines.append('<ul>')
                in_ul = True
            html_lines.append(f'<li>{process_inline(ul_match.group(1))}</li>')
            i += 1
            continue

        # 有序列表
        ol_match = re.match(r'^\d+\.\s+(.*)', stripped)
        if ol_match:
            if not in_ol:
                if in_ul:
                    html_lines.append('</ul>')
                    in_ul = False
                html_lines.append('<ol>')
                in_ol = True
            html_lines.append(f'<li>{process_inline(ol_match.group(1))}</li>')
            i += 1
            continue

        # 普通段落
        if in_ul:
            html_lines.append('</ul>')
            in_ul = False
        if in_ol:
            html_lines.append('</ol>')
            in_ol = False
        if in_blockquote:
            html_lines.append('<blockquote>')
            for bl in bq_lines:
                html_lines.append(f'<p>{process_inline(bl)}</p>')
            html_lines.append('</blockquote>')
            in_blockquote = False
            bq_lines = []

        # 纯 HTML 行（如 <div class="doc-links">）直接透传
        if stripped.startswith('<div') or stripped.startswith('</div') or stripped.startswith('<a ') or stripped.startswith('</a'):
            html_lines.append(stripped)
            i += 1
            continue

        html_lines.append(f'<p>{process_inline(stripped)}</p>')
        i += 1

    # 处理未关闭的块
    if in_blockquote:
        html_lines.append('<blockquote>')
        for bl in bq_lines:
            html_lines.append(f'<p>{process_inline(bl)}</p>')
        html_lines.append('</blockquote>')
    if in_ul:
        html_lines.append('</ul>')
    if in_ol:
        html_lines.append('</ol>')

    return '\n'.join(html_lines)


# ============================================================
# HTML 模板
# ============================================================

def build_html(title: str, body_content: str, css: str, nav_html: str, relative_prefix: str) -> str:
    """用统一模板包裹内容。"""
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>{title} - 应大Wiki</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Crimson+Pro:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
  <style>{css}</style>
</head>
<body>
  {nav_html}
  <div class="content">
    <div class="markdown-section">
{body_content}

      <div id="twikoo-comment"></div>
    </div>
  </div>
  <script src="https://unpkg.com/twikoo@1.6.41/dist/twikoo.all.min.js"></script>
  <script>
    const pages = [
      {{ url: '../选课/index.html', title: '选课指南', desc: '选课流程、推荐课程、时间线' }},
      {{ url: '../选课/选课流程.html', title: '选课流程', desc: '详细的选课步骤和注意事项' }},
      {{ url: '../选课/推荐课程.html', title: '推荐课程', desc: '学长学姐推荐的优质课程' }},
      {{ url: '../选课/选课时间线.html', title: '选课时间线', desc: '每学期选课关键时间节点' }},
      {{ url: '../学分绩点/index.html', title: '学分绩点', desc: '学分要求、绩点计算、毕业条件' }},
      {{ url: '../学分绩点/学分要求.html', title: '学分要求', desc: '毕业所需学分及构成' }},
      {{ url: '../学分绩点/绩点计算.html', title: '绩点计算', desc: '绩点计算方法和等级对应' }},
      {{ url: '../学分绩点/毕业条件.html', title: '毕业条件', desc: '完整的毕业要求清单' }},
      {{ url: '../体育军训/index.html', title: '体育军训', desc: '体育课选择、体测要求、军训须知' }},
      {{ url: '../体育军训/体育课选择.html', title: '体育课选择', desc: '体育课项目介绍和选择建议' }},
      {{ url: '../体育军训/体测要求.html', title: '体测要求', desc: '体能测试项目和标准' }},
      {{ url: '../体育军训/军训须知.html', title: '军训须知', desc: '军训准备和注意事项' }},
      {{ url: '../生活指南/index.html', title: '生活指南', desc: '宿舍、食堂、校园地图' }},
      {{ url: '../生活指南/宿舍篇.html', title: '宿舍篇', desc: '宿舍环境、管理规定、生活技巧' }},
      {{ url: '../生活指南/食堂篇.html', title: '食堂篇', desc: '食堂介绍、美食推荐、用餐时间' }},
      {{ url: '../生活指南/校园地图.html', title: '校园地图', desc: '校园设施分布、重要地点' }},
      {{ url: '../常见问题/index.html', title: '常见问题', desc: '新生常见问题解答' }},
    ];
    const searchInput = document.getElementById('searchInput');
    const searchResults = document.getElementById('searchResults');
    if (searchInput && searchResults) {{
      searchInput.addEventListener('input', function() {{
        const query = this.value.toLowerCase().trim();
        if (!query) {{ searchResults.classList.remove('active'); return; }}
        const results = pages.filter(p => p.title.toLowerCase().includes(query) || p.desc.toLowerCase().includes(query));
        if (results.length === 0) {{
          searchResults.innerHTML = '<div class="search-no-result">没有找到相关结果</div>';
        }} else {{
          searchResults.innerHTML = results.map(p =>
            '<a href="' + p.url + '" class="search-result-item"><div class="search-result-title">' + p.title + '</div><div class="search-result-desc">' + p.desc + '</div></a>'
          ).join('');
        }}
        searchResults.classList.add('active');
      }});
      document.addEventListener('click', function(e) {{
        if (!e.target.closest('.search-box')) {{ searchResults.classList.remove('active'); }}
      }});
      searchInput.addEventListener('keypress', function(e) {{
        if (e.key === 'Enter') {{
          const query = this.value.toLowerCase().trim();
          if (query) {{
            const result = pages.find(p => p.title.toLowerCase().includes(query) || p.desc.toLowerCase().includes(query));
            if (result) {{ window.location.href = result.url; }}
          }}
        }}
      }});
    }}
  </script>
  <script>
    twikoo.init({{
      envId: 'https://taupe-zuccutto-aa14a0.netlify.app/.netlify/functions/twikoo',
      el: '#twikoo-comment',
      requiredMetaField: [],
      anonymousNickName: '匿名',
      commentPermission: 'anyone',
    }});
  </script>
</body>
</html>'''


# ============================================================
# 导航栏 HTML
# ============================================================

def build_nav(prefix: str, is_sub: bool = False) -> str:
    """生成顶部导航栏。
    prefix: 根目录 '' 或子目录 '../'
    is_sub: 是否是子页面（子页面的链接不需要 docs/ 前缀）
    """
    def p(path):
        return f'{prefix}{path}'
    if is_sub:
        # 子页面在 docs/子目录/ 下，需要 ../../ 回到根目录
        root = f'{prefix}../'
        return f'''<nav class="app-nav">
    <a href="{root}index.html" class="nav-brand">
      <img src="{root}圆形logo.png" alt="应大Wiki" class="nav-logo">
      <span>应大Wiki</span>
    </a>
    <div class="nav-links">
      <a href="{p('学校概览/index.html')}">概览</a>
      <a href="{p('入学指南/index.html')}">入学</a>
      <a href="{p('选课指南/index.html')}">选课</a>
      <a href="{p('学分绩点/index.html')}">学业</a>
      <a href="{p('校园生活/index.html')}">生活</a>
    </div>
    <div class="search-box">
      <input type="text" id="searchInput" class="nav-search" placeholder="搜索..." autocomplete="off">
      <div id="searchResults" class="search-results"></div>
    </div>
  </nav>'''
    else:
        return f'''<nav class="app-nav">
    <a href="{p('index.html')}" class="nav-brand">
      <img src="{p('圆形logo.png')}" alt="应大Wiki" class="nav-logo">
      <span>应大Wiki</span>
    </a>
    <div class="nav-links">
      <a href="{p('docs/学校概览/index.html')}">概览</a>
      <a href="{p('docs/入学指南/index.html')}">入学</a>
      <a href="{p('docs/选课指南/index.html')}">选课</a>
      <a href="{p('docs/学分绩点/index.html')}">学业</a>
      <a href="{p('docs/校园生活/index.html')}">生活</a>
    </div>
    <div class="search-box">
      <input type="text" id="searchInput" class="nav-search" placeholder="搜索..." autocomplete="off">
      <div id="searchResults" class="search-results"></div>
    </div>
  </nav>'''


# ============================================================
# CSS（从 index.html 提取的样式，去除 coverpage 相关）
# ============================================================

CSS = '''
:root {
  --paper: #ffffff;
  --paper-dark: #eddcba;
  --paper-edge: #e8e0d0;
  --ink: #2c2416;
  --ink-light: #5a4e3c;
  --ink-faint: #8a7e6c;
  --ink-fainter: #b8ad9c;
  --vermilion: #c23616;
  --vermilion-light: #e74c3c;
  --link: #8b4513;
  --link-hover: #c23616;
  --border: #d4c9b8;
  --shadow: rgba(44, 36, 22, 0.08);
  --font-serif: 'Noto Serif SC', 'Crimson Pro', 'Georgia', 'Songti SC', serif;
  --font-mono: 'Courier New', 'Noto Sans Mono', monospace;
}
* { box-sizing: border-box; }
html, body {
  margin: 0; padding: 0;
  background: var(--paper); color: var(--ink);
  font-family: var(--font-serif);
  font-size: 16px; line-height: 1.85;
  -webkit-font-smoothing: antialiased;
}
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: var(--paper-dark); }
::-webkit-scrollbar-thumb { background: var(--ink-fainter); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--ink-faint); }

.app-nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 300;
  display: flex; justify-content: center; align-items: center;
  padding: 0 28px; height: 56px;
  background: var(--paper);
  border-bottom: 1px solid var(--border);
  box-shadow: 0 1px 4px var(--shadow);
}
.app-nav .nav-brand {
  display: flex; align-items: center; gap: 8px;
  font-family: var(--font-serif); font-weight: 700; font-size: 20px;
  color: var(--ink); letter-spacing: 2px; margin-right: auto; text-decoration: none;
}
.app-nav .nav-logo {
  width: 32px; height: 32px; border-radius: 50%; object-fit: cover;
}
.nav-links {
  display: flex; align-items: center; gap: 4px; margin-left: auto;
}
.app-nav a {
  font-family: var(--font-serif); font-size: 14px;
  color: var(--ink-faint) !important;
  text-decoration: none; border-bottom: none !important;
  transition: color 0.2s; letter-spacing: 0.5px; line-height: 56px;
  padding: 0 10px;
}
.app-nav a:hover { color: var(--vermilion) !important; }
.app-nav a.active { color: var(--ink) !important; border-bottom: 2px solid var(--vermilion) !important; }
.search-box { position: relative; margin-left: 12px; }
.nav-search {
  padding: 6px 12px; border: 1px solid var(--border); border-radius: 4px;
  font-size: 13px; width: 160px; background: white; font-family: var(--font-serif);
}
.nav-search:focus { outline: none; border-color: var(--ink-faint); }
.search-results {
  position: absolute; top: 100%; right: 0; background: white;
  border: 1px solid var(--border); border-radius: 4px; margin-top: 4px;
  min-width: 280px; max-height: 400px; overflow-y: auto;
  display: none; box-shadow: 0 4px 12px rgba(0,0,0,0.1); z-index: 1000;
}
.search-results.active { display: block; }
.search-result-item {
  padding: 10px 14px; border-bottom: 1px solid var(--border);
  text-decoration: none; color: var(--ink); display: block;
}
.search-result-item:hover { background: var(--paper-dark); }
.search-result-item:last-child { border-bottom: none; }
.search-result-title { font-weight: 600; font-size: 14px; margin-bottom: 2px; }
.search-result-desc { font-size: 12px; color: var(--ink-faint); }
.search-no-result { padding: 14px; text-align: center; color: var(--ink-faint); }

.content { padding-top: 56px !important; }
.markdown-section {
  max-width: 860px; margin: 0 auto;
  padding: 48px 60px 80px !important; background: var(--paper);
  animation: fadeIn 0.4s ease-out;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.markdown-section p {
  font-family: var(--font-serif); font-size: 16.5px; line-height: 1.9;
  color: var(--ink); margin: 1.2em 0; text-align: justify; text-indent: 2em;
}
.markdown-section h1, .markdown-section h2, .markdown-section h3, .markdown-section h4 { text-indent: 0; }
.markdown-section h1 {
  font-weight: 700; font-size: 28px; color: var(--ink);
  margin: 1.5em 0 0.8em; padding-bottom: 12px; border-bottom: 2px solid var(--ink); letter-spacing: 1px;
}
.markdown-section h2 {
  font-weight: 700; font-size: 22px; color: var(--ink);
  margin: 1.8em 0 0.6em; padding-bottom: 8px; border-bottom: 1px solid var(--border); position: relative;
}
.markdown-section h2::before { content: '§ '; color: var(--vermilion); font-weight: 400; }
.markdown-section h3 { font-weight: 600; font-size: 18px; color: var(--ink-light); margin: 1.4em 0 0.5em; }
.markdown-section h4 { font-weight: 600; font-size: 16px; color: var(--ink-light); margin: 1.2em 0 0.4em; }
.markdown-section a { color: var(--link); text-decoration: none; border-bottom: 1px solid var(--ink-fainter); transition: all 0.2s; }
.markdown-section a:hover { color: var(--vermilion); border-bottom-color: var(--vermilion); }
.markdown-section blockquote {
  margin: 1.5em 0; padding: 16px 20px; background: var(--paper-dark);
  border-left: 4px solid var(--vermilion); border-radius: 0 4px 4px 0;
  color: var(--ink-light); font-style: italic;
}
.markdown-section blockquote p { text-indent: 0; margin: 0.5em 0; color: var(--ink-light); }
.markdown-section table {
  width: 100%; border-collapse: collapse; margin: 1.5em 0; font-size: 15px; background: var(--paper);
}
.markdown-section thead th {
  background: var(--paper-dark); font-weight: 700; color: var(--ink);
  padding: 10px 14px; text-align: left; border-bottom: 2px solid var(--ink);
}
.markdown-section tbody td { padding: 10px 14px; border-bottom: 1px solid var(--border); color: var(--ink); }
.markdown-section tbody tr:hover { background: var(--paper-dark); }
.markdown-section code {
  font-family: var(--font-mono); font-size: 14px; background: var(--paper-dark);
  border: 1px solid var(--border); border-radius: 3px; padding: 2px 6px; color: var(--ink-light);
}
.markdown-section pre {
  background: var(--paper-dark) !important; border: 1px solid var(--border);
  border-radius: 4px; padding: 20px !important; margin: 1.5em 0;
  overflow-x: auto; box-shadow: inset 0 1px 3px var(--shadow);
}
.markdown-section pre code { background: none; border: none; padding: 0; font-size: 14px; line-height: 1.7; color: var(--ink); }
.markdown-section ul, .markdown-section ol { padding-left: 1.8em; margin: 1em 0; }
.markdown-section li { font-size: 16px; line-height: 1.85; color: var(--ink); margin: 0.4em 0; }
.markdown-section ul li::marker { color: var(--vermilion); }
.markdown-section ol li::marker { color: var(--ink-faint); font-weight: 600; }
.markdown-section hr { border: none; height: 1px; background: var(--border); margin: 2.5em 0; }
.markdown-section strong { color: var(--ink); font-weight: 700; }
.markdown-section em { color: var(--ink-light); font-style: italic; }
.markdown-section input[type="checkbox"] {
  appearance: none; -webkit-appearance: none; width: 16px; height: 16px;
  border: 2px solid var(--ink-faint); border-radius: 3px; background: var(--paper);
  cursor: pointer; position: relative; top: 3px; margin-right: 6px;
}
.markdown-section input[type="checkbox"]:checked { background: var(--ink); border-color: var(--ink); }
.markdown-section input[type="checkbox"]:checked::after {
  content: '✓'; color: var(--paper); font-size: 12px; position: absolute; top: -1px; left: 2px;
}
.markdown-section kbd {
  font-family: var(--font-mono); font-size: 13px; background: var(--paper-dark);
  border: 1px solid var(--border); border-bottom: 2px solid var(--ink-fainter);
  border-radius: 3px; padding: 1px 6px; color: var(--ink-light); box-shadow: 0 1px 1px var(--shadow);
}
.markdown-section > :last-child::after {
  content: '◆ ◆ ◆'; display: block; text-align: center;
  color: var(--ink-fainter); font-size: 12px; letter-spacing: 8px; margin-top: 3em;
}
.doc-links {
  display: flex; flex-wrap: wrap; gap: 10px; margin: 20px 0 30px;
  padding-bottom: 20px; border-bottom: 1px solid var(--border);
}
.doc-links a {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 18px; border-radius: 6px;
  background: var(--paper-dark); border: 1px solid var(--border);
  color: var(--ink) !important; font-size: 14px; font-weight: 600;
  text-decoration: none !important; border-bottom: none !important;
  transition: all 0.2s;
}
.doc-links a:hover {
  background: var(--ink); color: var(--paper) !important;
  border-color: var(--ink); transform: translateY(-1px);
  box-shadow: 0 2px 8px var(--shadow);
}
body::before {
  content: ''; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  pointer-events: none; z-index: 9999;
  background-image: repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(139,119,86,0.015) 2px, rgba(139,119,86,0.015) 4px);
}
.markdown-section::after {
  content: ''; display: block; width: 60px; height: 60px; margin: 40px auto 0;
  border: 2px solid var(--vermilion); border-radius: 50%; opacity: 0.15; position: relative; top: 20px;
}
#twikoo-comment {
  max-width: 780px; margin: 0 auto; padding: 0 0 40px;
  border-top: 2px solid var(--ink); padding-top: 30px; margin-top: 50px;
}
@media print {
  .app-nav, body::before { display: none !important; }
  .markdown-section { max-width: 100%; padding: 20px !important; }
  .content { padding-top: 0 !important; }
  body { background: white; }
}
@media screen and (max-width: 768px) {
  .markdown-section { padding: 24px 20px 60px !important; }
  .markdown-section h1 { font-size: 24px; }
  .markdown-section h2 { font-size: 20px; }
  .markdown-section p { font-size: 15.5px; }
  .app-nav { padding: 0 12px; height: auto; flex-wrap: wrap; }
  .app-nav .nav-brand { font-size: 16px; }
  .nav-links { flex-wrap: wrap; justify-content: center; gap: 2px; margin-top: 4px; width: 100%; order: 3; }
  .app-nav a { font-size: 13px; line-height: 36px; padding: 0 8px; }
  .search-box { order: 2; margin-left: auto; }
  .content { padding-top: 90px !important; }
}
'''


# ============================================================
# 内部链接修正：把 md 相对链接 → html 相对链接
# ============================================================

def fix_links(md_text: str, md_file_path: Path) -> str:
    """
    把 md 文件中的链接修正为指向 html 文件。
    - 无后缀的相对路径（如 选课流程）→ 选课流程.html
    - 带 / 结尾的目录路径（如 选课/）→ 选课/index.html
    - 已经是 .html 或 http 链接的不动
    """
    def replacer(m):
        text = m.group(1)
        url = m.group(2)
        # 外部链接不动
        if url.startswith(('http://', 'https://', 'mailto:', '#', 'javascript:')):
            return m.group(0)
        # .md 链接 → .html
        if url.endswith('.md'):
            return f'[{text}]({url[:-3]}.html)'
        # 已经是 .html 的不动
        if url.endswith('.html'):
            return m.group(0)
        # 其他有扩展名的不动
        if '.' in url.split('/')[-1]:
            return m.group(0)
        # 目录链接（以 / 结尾或无后缀）
        if url.endswith('/'):
            return f'[{text}]({url}index.html)'
        else:
            return f'[{text}]({url}.html)'
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replacer, md_text)


# ============================================================
# 主流程
# ============================================================

def convert_all():
    """扫描所有 md 文件，生成对应 html。"""
    # 找到所有 .md 文件
    md_files = sorted(BASE_DIR.rglob('*.md'))
    # 排除不需要转换的文件
    md_files = [f for f in md_files if f.name != '_coverpage.md']
    md_files = [f for f in md_files if not (f.parent == BASE_DIR and f.name == 'README.md')]
    md_files = [f for f in md_files if not (f.parent == BASE_DIR / 'docs' and f.name == 'README.md')]
    md_files = [f for f in md_files if 'node_modules' not in str(f)]

    # 先清理 docs 下旧的 HTML 文件（保留根目录的 index.html）
    for old_html in (BASE_DIR / 'docs').rglob('*.html'):
        old_html.unlink(missing_ok=True)
    # 清理 docs 下可能残留的 README.html
    for old_readme in (BASE_DIR / 'docs').rglob('README.html'):
        old_readme.unlink(missing_ok=True)

    count = 0
    for md_file in md_files:
        rel = md_file.relative_to(BASE_DIR)
        # README.md -> index.html，其他文件保持原名
        if md_file.stem == 'README':
            html_name = 'index.html'
        else:
            html_name = md_file.stem + '.html'
        html_file = md_file.parent / html_name

        # 读取 md
        md_text = md_file.read_text(encoding='utf-8')

        # 修正内部链接
        md_text = fix_links(md_text, md_file)

        # 转换为 HTML
        body = md_to_html(md_text)

        # 判断是根目录还是子目录，选择对应导航栏
        is_root = (md_file.parent == BASE_DIR)
        nav = build_nav('', is_sub=False) if is_root else build_nav('../', is_sub=True)
        prefix = '' if is_root else '../'

        # 从文件名提取标题（第一行 h1 或文件名）
        title_match = re.match(r'^#\s+(.+)', md_text.split('\n')[0])
        title = title_match.group(1) if title_match else md_file.stem

        # 构建完整 HTML
        full_html = build_html(title, body, CSS, nav, prefix)

        # 写入
        html_file.write_text(full_html, encoding='utf-8')
        count += 1
        print(f'  OK {rel} -> {html_file.relative_to(BASE_DIR)}')

    print(f'\nDone! Generated {count} HTML files.')
    print(f'Run: python serve.py to preview the site.')


if __name__ == '__main__':
    print('Converting Markdown to HTML...\n')
    convert_all()
