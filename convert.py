"""
Markdown → HTML 转换脚本
用法: python convert.py

扫描 docs/ 下所有 .md 文件，转换为完整 HTML 页面。
生成的 HTML 包含：顶部导航、左侧 Wiki 侧边栏、右侧目录、评论区、返回顶部。
学院与专业下的 .html 文件保持不变。

保留原 md 文件，在同目录生成同名 .html 文件。
"""

import re
from pathlib import Path

BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR / 'docs'

# ============================================================
# 16 个学院（顺序固定）
# ============================================================

COLLEGES = [
    "应急技术与指挥学院", "矿山安全学院", "城市安全学院",
    "地震工程与建筑安全学院", "地震科学与技术学院", "化工安全学院",
    "环境与灾害治理学院", "计算机与信息安全学院",
    "应急通信与控制工程学院", "应急装备学院",
    "应急经济与物资保障学院", "应急国际交流学院",
    "应急救援训练中心", "应急文化传播与法学院",
    "理学院", "防灾减灾工程学院",
]

# ============================================================
# 侧边栏结构（根据 docs/ 实际 .md 文件动态生成）
# ============================================================

# section_name -> 子页面列表（从 .md 文件名提取）
SECTION_MAP = {
    "学校概览": ["学校简介", "燕郊特色", "周边配套"],
    "入学指南": ["来校路线", "报到流程", "军训须知", "体育课选择"],
    "选课指南": ["选课流程", "推荐课程", "选课时间线"],
    "学分绩点": ["学分要求", "绩点计算", "毕业条件", "奖学金", "四六级", "选修课"],
    "校园生活": ["宿舍篇", "食堂篇", "校园地图", "学生组织", "心理健康", "体测要求", "常用电话", "地铁指南", "公交指南"],
    "学院与专业": None,  # 动态生成
    "友情链接": [],
}

def scan_sections():
    """扫描 docs/ 目录，动态构建侧边栏结构"""
    result = {}
    for section_name in SECTION_MAP:
        section_dir = DOCS_DIR / section_name
        if not section_dir.exists():
            continue
        if section_name == "学院与专业":
            # 学院与专业：扫描子目录
            colleges = {}
            for college_dir in sorted(section_dir.iterdir()):
                if college_dir.is_dir() and not college_dir.name.startswith('.'):
                    pages = []
                    for md_file in sorted(college_dir.glob('*.md')):
                        if md_file.stem not in ('index', 'README'):
                            pages.append(md_file.stem)
                    colleges[college_dir.name] = pages
            result[section_name] = colleges
        else:
            pages = []
            for md_file in sorted(section_dir.glob('*.md')):
                if md_file.stem not in ('index', 'README'):
                    pages.append(md_file.stem)
            result[section_name] = pages
    return result


def build_sidebar(section_data, current_section=None, current_page=None):
    """构建左侧 Wiki 侧边栏 HTML"""
    lines = [
        '<nav class="wiki-sidebar" id="wikiSidebar">',
        '<ul class="sidebar-nav">',
    ]

    for section_name, children in section_data.items():
        is_active_section = (section_name == current_section)
        active_cls = ' active' if is_active_section else ''
        lines.append(f'<li class="sidebar-item{active_cls}">')

        if section_name == "学院与专业":
            # 学院与专业：链接到 index.html，展开16个学院
            lines.append(f'<a href="../学院与专业/index.html" class="sidebar-link has-children{active_cls}">{section_name}</a>')
            lines.append('<ul class="sidebar-children">')
            for college in COLLEGES:
                lines.append(f'<li><a href="../学院与专业/{college}/index.html" class="sidebar-link">{college}</a></li>')
            lines.append('</ul>')
        elif isinstance(children, list) and len(children) > 0:
            # 有子页面的板块
            lines.append(f'<a href="../{section_name}/index.html" class="sidebar-link has-children{active_cls}">{section_name}</a>')
            lines.append('<ul class="sidebar-children">')
            for page_name in children:
                page_active = ' active' if (is_active_section and page_name == current_page) else ''
                lines.append(f'<li><a href="../{section_name}/{page_name}.html" class="sidebar-link{page_active}">{page_name}</a></li>')
            lines.append('</ul>')
        elif section_name == "友情链接":
            lines.append(f'<a href="../友情链接/index.html" class="sidebar-link has-children{active_cls}">{section_name}</a>')
        else:
            # 空板块或只有一个 index
            lines.append(f'<a href="../{section_name}/index.html" class="sidebar-link has-children{active_cls}">{section_name}</a>')

        lines.append('</li>')

    lines.append('</ul>')
    lines.append('</nav>')
    return '\n'.join(lines)


# ============================================================
# 侧边栏路径前缀（根据文件深度计算）
# ============================================================

def get_sidebar_prefix(md_file_path):
    """计算从当前 md 文件到 docs/ 目录的相对路径前缀"""
    rel = md_file_path.relative_to(DOCS_DIR)
    depth = len(rel.parts) - 1  # 排除文件名
    return '../' * depth


def build_sidebar_for_file(md_file_path, section_data):
    """为特定文件构建侧边栏"""
    rel = md_file_path.relative_to(DOCS_DIR)
    parts = rel.parts

    current_section = parts[0] if len(parts) > 0 else None
    current_page = md_file_path.stem if md_file_path.stem != 'index' else None

    # 临时替换 section_data 中的路径前缀
    # 因为 build_sidebar 用的是 ../ 一级前缀，需要根据实际深度调整
    prefix = get_sidebar_prefix(md_file_path)

    lines = [
        '<nav class="wiki-sidebar" id="wikiSidebar">',
        '<ul class="sidebar-nav">',
    ]

    for section_name, children in section_data.items():
        is_active_section = (section_name == current_section)
        active_cls = ' active' if is_active_section else ''
        lines.append(f'<li class="sidebar-item{active_cls}">')

        if section_name == "学院与专业":
            lines.append(f'<a href="{prefix}学院与专业/index.html" class="sidebar-link has-children{active_cls}">{section_name}</a>')
            lines.append('<ul class="sidebar-children">')
            for college in COLLEGES:
                lines.append(f'<li><a href="{prefix}学院与专业/{college}/index.html" class="sidebar-link">{college}</a></li>')
            lines.append('</ul>')
        elif isinstance(children, list) and len(children) > 0:
            lines.append(f'<a href="{prefix}{section_name}/index.html" class="sidebar-link has-children{active_cls}">{section_name}</a>')
            lines.append('<ul class="sidebar-children">')
            for page_name in children:
                page_active = ' active' if (is_active_section and page_name == current_page) else ''
                lines.append(f'<li><a href="{prefix}{section_name}/{page_name}.html" class="sidebar-link{page_active}">{page_name}</a></li>')
            lines.append('</ul>')
        elif section_name == "友情链接":
            lines.append(f'<a href="{prefix}友情链接/index.html" class="sidebar-link has-children{active_cls}">{section_name}</a>')
        else:
            lines.append(f'<a href="{prefix}{section_name}/index.html" class="sidebar-link has-children{active_cls}">{section_name}</a>')

        lines.append('</li>')

    lines.append('</ul>')
    lines.append('</nav>')
    return '\n'.join(lines)


# ============================================================
# Markdown → HTML 转换器
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

    def process_inline(t: str) -> str:
        """处理行内 Markdown：加粗、斜体、行内代码、链接、复选框。"""
        t = re.sub(r'^\s*- \[x\]\s*', '<input type="checkbox" checked disabled> ', t)
        t = re.sub(r'^\s*- \[ \]\s*', '<input type="checkbox" disabled> ', t)
        t = re.sub(r'`([^`]+)`', r'<code>\1</code>', t)
        t = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', t)
        t = re.sub(r'__(.+?)__', r'<strong>\1</strong>', t)
        t = re.sub(r'\*(.+?)\*', r'<em>\1</em>', t)
        t = re.sub(r'_(.+?)_', r'<em>\1</em>', t)
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
                    html_lines.append('<thead><tr>')
                    for cell in rows[0]:
                        html_lines.append(f'  <th>{process_inline(cell)}</th>')
                    html_lines.append('</tr></thead>')
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

        # 纯 HTML 行直接透传
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
# 内部链接修正
# ============================================================

def fix_links(md_text: str, md_file_path: Path) -> str:
    """把 md 文件中的链接修正为指向 html 文件。"""
    def replacer(m):
        text = m.group(1)
        url = m.group(2)
        if url.startswith(('http://', 'https://', 'mailto:', '#', 'javascript:')):
            return m.group(0)
        if url.endswith('.md'):
            return f'[{text}]({url[:-3]}.html)'
        if url.endswith('.html'):
            return m.group(0)
        if '.' in url.split('/')[-1]:
            return m.group(0)
        if url.endswith('/'):
            return f'[{text}]({url}index.html)'
        else:
            return f'[{text}]({url}.html)'
    return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', replacer, md_text)


# ============================================================
# 搜索索引
# ============================================================

def build_search_entries(section_data):
    """从侧边栏结构生成搜索条目"""
    entries = []
    for section_name, children in section_data.items():
        if section_name == "学院与专业":
            for college in COLLEGES:
                entries.append({
                    'url': f'../学院与专业/{college}/index.html',
                    'title': college,
                    'desc': f'{college}专业介绍',
                })
        elif isinstance(children, list):
            for page_name in children:
                entries.append({
                    'url': f'../{section_name}/{page_name}.html',
                    'title': page_name,
                    'desc': f'{section_name} - {page_name}',
                })
    return entries


def build_search_js(search_entries, prefix):
    """生成搜索 JS 代码，替换路径前缀"""
    entries_json = []
    for e in search_entries:
        url = prefix + e['url'].lstrip('../')
        entries_json.append(f'{{ url: \'{url}\', title: \'{e["title"]}\', desc: \'{e["desc"]}\' }}')
    entries_str = ',\n      '.join(entries_json)

    return f'''
    const pages = [
      {entries_str}
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
    }}'''


# ============================================================
# CSS
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

/* Wiki侧边栏 */
.content { display: flex; padding-top: 56px !important; }
.wiki-sidebar {
  position: fixed; top: 56px; left: 0; bottom: 0;
  width: 240px; background: #002f82;
  border-right: 1px solid #002466;
  overflow-y: auto; padding: 0 0 20px 0;
  font-family: var(--font-serif); font-size: 14px;
  z-index: 50;
  transition: width 0.3s ease, opacity 0.3s ease;
}
.wiki-sidebar.collapsed { width: 0; opacity: 0; pointer-events: none; }
.content.sidebar-collapsed .markdown-section {
  max-width: 960px; margin: 0 auto; padding-left: 40px; padding-right: 40px;
  transform: translateX(-176px);
  transition: max-width 0.3s ease, transform 0.3s ease;
}
.sidebar-toggle {
  position: fixed; top: 64px; left: 240px;
  width: 18px; height: 36px; border-radius: 0 4px 4px 0;
  background: #002f82; color: #fff;
  border: none; cursor: pointer; font-size: 12px;
  display: flex; align-items: center; justify-content: center;
  transition: left 0.3s ease; z-index: 51;
}
.sidebar-toggle:hover { background: #0040b3; }
.sidebar-toggle.collapsed { left: 0; }
.sidebar-title {
  font-weight: 700; font-size: 13px; color: rgba(255,255,255,0.7);
  text-transform: uppercase; letter-spacing: 2px;
  padding: 0 20px 8px 20px; border-bottom: 1px solid rgba(255,255,255,0.2);
  margin-bottom: 0;
  position: sticky; top: 56px; background: #002f82; z-index: 10;
}
.sidebar-nav { list-style: none; padding: 0; margin: 0; }
.sidebar-item { margin: 0; }
.sidebar-link {
  display: block; padding: 8px 20px; color: rgba(255,255,255,0.8) !important;
  text-decoration: none !important; border-bottom: none !important;
  transition: all 0.15s; border-left: 3px solid transparent;
}
.sidebar-link:hover {
  background: rgba(255,255,255,0.1); color: #fff !important;
  border-left-color: rgba(255,255,255,0.5);
}
.sidebar-link.has-children {
  font-weight: 600; color: #fff !important;
}
.sidebar-link.has-children.active {
  color: #ffd700 !important;
  font-weight: 700;
  border-left-color: #ffd700;
  background: rgba(255, 215, 0, 0.1);
}
.sidebar-children .sidebar-link {
  padding: 6px 16px; font-size: 13px; font-weight: 400;
  color: rgba(255,255,255,0.65) !important;
}
.sidebar-children .sidebar-link:hover {
  color: #fff !important;
}
.sidebar-children {
  list-style: none; padding: 0; margin: 0;
  border-left: 1px solid rgba(255,255,255,0.2); margin-left: 20px;
}
.wiki-main {
  margin-left: 240px; flex: 1; min-width: 0;
}

/* 文章内容 */
.markdown-section {
  max-width: 680px; margin: 0; margin-left: 0; margin-right: 220px;
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
  content: ''; color: var(--paper); font-size: 12px; position: absolute; top: -1px; left: 2px;
}
.markdown-section kbd {
  font-family: var(--font-mono); font-size: 13px; background: var(--paper-dark);
  border: 1px solid var(--border); border-bottom: 2px solid var(--ink-fainter);
  border-radius: 3px; padding: 1px 6px; color: var(--ink-light); box-shadow: 0 1px 1px var(--shadow);
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

/* 目录 */
.toc-sidebar {
  position: fixed; top: 70px; right: 20px; width: 200px;
  max-height: calc(100vh - 100px); overflow-y: auto;
  font-family: var(--font-serif); font-size: 13px; z-index: 100;
}
.toc-sidebar::-webkit-scrollbar { width: 3px; }
.toc-sidebar::-webkit-scrollbar-thumb { background: var(--ink-fainter); border-radius: 2px; }
.toc-title {
  font-weight: 700; font-size: 14px; color: var(--ink);
  margin-bottom: 12px; padding-bottom: 8px;
  border-bottom: 1px solid var(--border); letter-spacing: 1px;
}
.toc-title::before { content: ''; }
.toc-list { list-style: none; padding: 0; margin: 0; }
.toc-list li { margin: 0; padding: 0; }
.toc-list a {
  display: block; padding: 5px 0 5px 12px;
  color: var(--ink-faint) !important; text-decoration: none !important;
  border-left: 2px solid transparent; transition: all 0.2s;
  line-height: 1.5; border-bottom: none !important;
}
.toc-list a:hover { color: var(--ink) !important; border-left-color: var(--ink-faint); }
.toc-list a.active { color: var(--vermilion) !important; border-left-color: var(--vermilion); font-weight: 600; }
.toc-list .toc-h3 { padding-left: 24px; font-size: 12px; }
.toc-toggle {
  display: none; position: fixed; bottom: 20px; right: 20px;
  width: 44px; height: 44px; border-radius: 50%;
  background: #002f82; color: var(--paper); border: none;
  font-size: 20px; cursor: pointer; z-index: 200;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

/* 返回顶部 */
.back-to-top {
  position: fixed; bottom: 80px; right: 30px;
  width: 44px; height: 44px; border-radius: 50%;
  background: #002f82; color: var(--paper); border: none;
  font-size: 20px; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; visibility: hidden; transition: all 0.3s;
  box-shadow: 0 2px 8px rgba(0,0,0,0.2); z-index: 150;
}
.back-to-top.visible { opacity: 1; visibility: visible; }
.back-to-top:hover { background: #0040b3; transform: translateY(-2px); }

/* 评论区 */
#twikoo-comment {
  max-width: 680px; margin: 60px 0 0 20px; padding: 0 0 40px;
  border-top: 2px solid var(--ink); padding-top: 30px;
}
.twikoo-title {
  font-family: var(--font-serif); font-size: 20px; font-weight: 700;
  color: var(--ink); margin-bottom: 20px; text-align: center;
}

/* 移动端适配 */
@media screen and (max-width: 1200px) {
  .toc-sidebar {
    position: fixed; left: auto; right: -260px; top: 0; bottom: 0;
    width: 260px; max-height: 100vh; background: var(--paper);
    padding: 60px 20px 20px; border-left: 1px solid var(--border);
    box-shadow: -4px 0 12px rgba(0,0,0,0.1); transition: right 0.3s ease; z-index: 500;
  }
  .toc-sidebar.open { right: 0; }
  .toc-toggle { display: flex; align-items: center; justify-content: center; }
  .toc-overlay {
    display: none; position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.3); z-index: 499;
  }
  .toc-overlay.open { display: block; }
}
@media screen and (max-width: 900px) {
  .wiki-sidebar {
    position: fixed; left: -260px; width: 260px;
    transition: left 0.3s ease; z-index: 500; box-shadow: none; background: #002f82;
  }
  .wiki-sidebar.open { left: 0; box-shadow: 4px 0 12px rgba(0,0,0,0.1); }
  .wiki-main { margin-left: 0 !important; }
  .sidebar-toggle { display: none; }
}
@media screen and (max-width: 768px) {
  .markdown-section { padding: 24px 20px 60px !important; margin-right: 0; }
  .markdown-section h1 { font-size: 24px; }
  .markdown-section h2 { font-size: 20px; }
  .markdown-section p { font-size: 15.5px; }
  .app-nav { padding: 0 12px; height: auto; flex-wrap: wrap; }
  .app-nav .nav-brand { font-size: 16px; }
  .nav-links { flex-wrap: wrap; justify-content: center; gap: 2px; margin-top: 4px; width: 100%; order: 3; }
  .app-nav a { font-size: 13px; line-height: 36px; padding: 0 8px; }
  .search-box { order: 2; margin-left: auto; }
  .back-to-top { bottom: 70px; right: 20px; width: 40px; height: 40px; font-size: 18px; }
}
@media print {
  .app-nav, .wiki-sidebar, .toc-sidebar, .toc-toggle, .toc-overlay, .back-to-top, body::before { display: none !important; }
  .markdown-section { max-width: 100%; padding: 20px !important; margin: 0 !important; }
  .wiki-main { margin-left: 0; }
  .content { padding-top: 0 !important; }
  body { background: white; }
}
'''


# ============================================================
# 导航栏 HTML
# ============================================================

def build_nav(prefix: str) -> str:
    """生成顶部导航栏。prefix: docs/ 相对路径前缀（如 '../'）"""
    def p(path):
        return f'{prefix}{path}'
    # logo 和品牌链接需要回到网站根目录，比 prefix 多一层
    root = prefix + '../' if prefix else ''
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


# ============================================================
# 完整 HTML 模板
# ============================================================

def build_full_html(title, body_content, sidebar_html, search_js, prefix):
    """生成完整的 HTML 页面"""
    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>{title} - 应大Wiki</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;600;700&family=Crimson+Pro:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">
  <style>{CSS}</style>
</head>
<body>
  {build_nav(prefix)}
  <button class="sidebar-toggle" id="sidebarToggle" onclick="toggleSidebar()">◂</button>
  <div class="content">
    {sidebar_html}
    <div class="wiki-main">
        <div class="toc-sidebar" id="toc">
      <div class="toc-title">目录</div>
      <ul class="toc-list" id="tocList"></ul>
    </div>
    <div class="toc-overlay" id="tocOverlay"></div>
    <button class="toc-toggle" id="tocToggle" onclick="toggleToc()">☰</button>
    <div class="markdown-section">
{body_content}

          </div>
    <div style="max-width:620px;margin:0 0 0 40px;padding:0 20px;">
      <div class="twikoo-title">评论区</div>
      <div id="twikoo-comment"></div>
    </div>
    </div>
  </div>
  <script src="https://unpkg.com/twikoo@1.6.41/dist/twikoo.all.min.js"></script>
  <script>
    {search_js}
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

  <script>
  (function() {{
    var section = document.querySelector('.markdown-section');
    var tocList = document.getElementById('tocList');
    if (!section || !tocList) return;

    var headings = section.querySelectorAll('h2, h3');
    if (headings.length === 0) return;

    headings.forEach(function(h, i) {{
      if (!h.id) h.id = 'toc-' + i;
      var li = document.createElement('li');
      var a = document.createElement('a');
      a.href = '#' + h.id;
      a.textContent = h.textContent.replace(/^§\\s*/, '');
      a.className = h.tagName === 'H3' ? 'toc-h3' : '';
      li.appendChild(a);
      tocList.appendChild(li);
    }});

    var links = tocList.querySelectorAll('a');
    function onScroll() {{
      var scrollY = window.scrollY + 80;
      var current = null;
      headings.forEach(function(h) {{
        if (h.offsetTop <= scrollY) current = h;
      }});
      links.forEach(function(a) {{
        a.classList.remove('active');
        if (current && a.getAttribute('href') === '#' + current.id) {{
          a.classList.add('active');
        }}
      }});
    }}
    window.addEventListener('scroll', onScroll);
    onScroll();
  }})();

  function toggleToc() {{
    document.getElementById('toc').classList.toggle('open');
    document.getElementById('tocOverlay').classList.toggle('open');
  }}
  document.getElementById('tocOverlay').addEventListener('click', toggleToc);
  </script>

    <button class="back-to-top" id="backToTop" onclick="scrollToTop()">↑</button>

  <script>
  (function() {{
    var btn = document.getElementById('backToTop');
    if (!btn) return;
    window.addEventListener('scroll', function() {{
      if (window.scrollY > 300) {{ btn.classList.add('visible'); }}
      else {{ btn.classList.remove('visible'); }}
    }});
    window.scrollToTop = function() {{
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }};
  }})();
  </script>

  <script>
  function toggleSidebar() {{
    var sidebar = document.getElementById('wikiSidebar');
    var btn = document.getElementById('sidebarToggle');
    var content = document.querySelector('.content');
    sidebar.classList.toggle('collapsed');
    btn.classList.toggle('collapsed');
    content.classList.toggle('sidebar-collapsed');
    if (sidebar.classList.contains('collapsed')) {{
      btn.textContent = '▸';
    }} else {{
      btn.textContent = '◂';
    }}
  }}
  </script>

</body>
</html>'''


# ============================================================
# 主流程
# ============================================================

def convert_all():
    """扫描所有 md 文件，生成对应 html。"""
    print('Scanning docs/ ...')
    section_data = scan_sections()
    search_entries = build_search_entries(section_data)

    # 找到所有 .md 文件（排除根目录和 README）
    md_files = sorted(DOCS_DIR.rglob('*.md'))
    md_files = [f for f in md_files if f.name != '_coverpage.md']
    md_files = [f for f in md_files if not (f.parent == DOCS_DIR and f.name == 'README.md')]
    md_files = [f for f in md_files if 'node_modules' not in str(f)]
    md_files = [f for f in md_files if '学院与专业' not in f.parts]

    count = 0
    for md_file in md_files:
        rel = md_file.relative_to(BASE_DIR)
        # README.md -> index.html
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

        # 计算路径前缀
        prefix = get_sidebar_prefix(md_file)

        # 生成侧边栏
        sidebar = build_sidebar_for_file(md_file, section_data)

        # 生成搜索 JS
        search_js = build_search_js(search_entries, prefix)

        # 提取标题
        title_match = re.match(r'^#\s+(.+)', md_text.split('\n')[0])
        title = title_match.group(1) if title_match else md_file.stem

        # 构建完整 HTML
        full_html = build_full_html(title, body, sidebar, search_js, prefix)

        # 写入
        html_file.write_text(full_html, encoding='utf-8')
        count += 1
        print(f'  OK {rel} -> {html_file.relative_to(BASE_DIR)}')

    print(f'\nDone! Generated {count} HTML files.')
    print(f'Run: python serve.py to preview the site.')


if __name__ == '__main__':
    print('Converting Markdown to HTML...\n')
    convert_all()
