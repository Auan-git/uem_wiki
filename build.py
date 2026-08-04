"""
Wiki 文章管理器
用法: python build.py

扫描 articles/ 目录下的 .md 文件，自动：
1. 将 .md 转换为带完整模板的 .html 文章页
2. 生成 articles.json 文章清单
3. 首页 index.html 通过 JS 读取 articles.json 展示文章列表

只需要把写好的 .md 文件丢进 articles/ 目录，然后运行 python build.py 即可。
"""

import json
import os
import re
import sys
import io
from datetime import date
from pathlib import Path

# 修复 Windows 控制台编码问题
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", write_through=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", write_through=True)

# ============================================================
# 配置
# ============================================================

BASE_DIR = Path(__file__).parent
ARTICLES_DIR = BASE_DIR / "articles"
MICRO_TUTORIALS_DIR = BASE_DIR / "micro-tutorials"
LONG_GUIDES_DIR = BASE_DIR / "long-guides"
SITE_TITLE = "Edge's Wiki"
SITE_URL = "/"

# ============================================================
# 模板
# ============================================================

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {site_title}</title>
    <script>!function(){{var t=localStorage.getItem('wiki-theme');if(t==='dark')document.documentElement.setAttribute('data-theme','dark')}}()</script>
    <link rel="stylesheet" href="../styles.css">
</head>
<body>
    <header class="header">
        <div class="header-inner">
            <a href="/" class="site-title">{site_title}</a>
            <nav class="nav">
                <ul class="nav-list">
                    <li><a href="https://xingqiwu.net.cn/">个人网站</a></li>
                    <li><a href="../about.html">关于我</a></li>
                </ul>
            </nav>
            <a class="nav-right-link" href="https://ucnift0madf0.feishu.cn/wiki/WPelwNGQ8ifj2kkCDjIcHKywnMf?from=from_copylink">讲座信息</a>
        </div>
    </header>

    <main class="container">
        <article class="wiki article-page">
            <header class="article-header">
                <h1>{title}</h1>
                <div class="article-meta">
                    <time datetime="{date}">{date}</time>
                    {category_html}
                </div>
            </header>
            <div class="article-layout">
                <aside class="article-sidebar">
                    {toc_html}
                </aside>
                <div class="article-body">
                    {content}
                </div>
            </div>
        </article>
    </main>

    <footer class="footer">
        <div class="footer-inner">
            <p><a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">Creative Commons License: BY-NC 4.0</a></p>
            <p>&copy; {year} {site_title}</p>
        </div>
    </footer>

    <!-- 暗色/亮色 切换按钮 -->
    <button class="theme-toggle" id="theme-toggle" aria-label="切换暗色/亮色模式" title="切换暗色/亮色模式">🌙</button>

    <script src="../script.js"></script>
</body>
</html>
"""

# 关于页模板（路径相对于根目录）
ABOUT_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - {site_title}</title>
    <script>!function(){{var t=localStorage.getItem('wiki-theme');if(t==='dark')document.documentElement.setAttribute('data-theme','dark')}}()</script>
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    <header class="header">
        <div class="header-inner">
            <a href="/" class="site-title">{site_title}</a>
            <nav class="nav">
                <ul class="nav-list">
                    <li><a href="https://xingqiwu.net.cn/">个人网站</a></li>
                    <li><a href="about.html">关于我</a></li>
                </ul>
            </nav>
            <a class="nav-right-link" href="https://ucnift0madf0.feishu.cn/wiki/WPelwNGQ8ifj2kkCDjIcHKywnMf?from=from_copylink">讲座信息</a>
        </div>
    </header>

    <main class="container">
        <article class="wiki article-page">
            <div class="article-body">
                {content}
            </div>
        </article>
    </main>

    <footer class="footer">
        <div class="footer-inner">
            <p><a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">Creative Commons License: BY-NC 4.0</a></p>
            <p>&copy; {year} {site_title}</p>
        </div>
    </footer>

    <!-- 暗色/亮色 切换按钮 -->
    <button class="theme-toggle" id="theme-toggle" aria-label="切换暗色/亮色模式" title="切换暗色/亮色模式">🌙</button>

    <script src="script.js"></script>
</body>
</html>
"""

CATEGORY_COLORS = {
    "编程基础": "box-green",
    "操作系统": "box-blue",
    "计算机网络": "box-violet",
    "开发工具": "box-gray",
    "数据库": "box-green",
    "其他": "box-gray",
}


def get_category_box(category):
    """返回分类标签的 HTML"""
    if not category:
        return ""
    cls = CATEGORY_COLORS.get(category, "box-gray")
    return f'<span class="box {cls}">{category}</span>'


def generate_toc(html_content: str) -> str:
    """从 HTML 内容中提取 h2/h3 标题，生成目录"""
    headings = []
    for m in re.finditer(r'<(h[23])(?:\s[^>]*)?>(.*?)</\1>', html_content):
        level = int(m.group(1)[1])
        text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
        # 尝试从已有 id 属性获取锚点，否则生成
        id_match = re.search(r'id="([^"]*)"', m.group(0))
        anchor = id_match.group(1) if id_match else re.sub(r'[^\w一-鿿]+', '-', text).strip('-').lower()
        headings.append((level, text, anchor))

    if len(headings) < 2:
        return ""

    lines = ['<nav class="article-toc">', '<p><strong>目录</strong></p>', '<ul>']
    for level, text, anchor in headings:
        if level == 2:
            lines.append(f'<li><a href="#{anchor}">{text}</a></li>')
        else:
            lines.append(f'<li class="toc-h3"><a href="#{anchor}">{text}</a></li>')
    lines.append('</ul>')
    lines.append('</nav>')
    return '\n'.join(lines)


def add_heading_anchors(html_content: str) -> str:
    """给 h2/h3 标题添加 id 锚点"""
    def replace_heading(m):
        tag = m.group(1)
        text = m.group(2)
        plain = re.sub(r'<[^>]+>', '', text).strip()
        anchor = re.sub(r'[^\w一-鿿]+', '-', plain).strip('-').lower()
        return f'<{tag} id="{anchor}">{text}</{tag}>'
    return re.sub(r'<(h[23])>(.*?)</\1>', replace_heading, html_content)


# ============================================================
# Markdown 转换
# ============================================================

# 优先使用 python-markdown 库，否则使用内置简单转换器
try:
    import markdown as md_lib

    HAS_MARKDOWN_LIB = True
except ImportError:
    HAS_MARKDOWN_LIB = False


def convert_markdown(text: str) -> str:
    """将 markdown 文本转换为 HTML"""
    if HAS_MARKDOWN_LIB:
        return md_lib.markdown(
            text,
            extensions=["fenced_code", "tables", "codehilite", "toc"],
        )
    else:
        return simple_markdown_to_html(text)


def simple_markdown_to_html(text: str) -> str:
    """
    内置的简易 markdown → HTML 转换器
    支持：标题、代码块、行内代码、链接、图片、列表、粗体、斜体、表格、引用、段落
    """
    lines = text.split("\n")
    out = []
    in_code_block = False
    code_lang = ""
    code_content = []
    in_table = False
    table_rows = []
    in_list = None  # "ul" or "ol"
    list_tag = ""

    i = 0
    while i < len(lines):
        line = lines[i]

        # 代码块
        if line.strip().startswith("```"):
            if in_code_block:
                # 结束代码块
                lang_attr = f' class="language-{code_lang}"' if code_lang else ""
                code_html = (
                    f"<pre><code{lang_attr}>"
                    + "\n".join(code_content)
                    + "</code></pre>"
                )
                out.append(code_html)
                in_code_block = False
                code_content = []
                code_lang = ""
            else:
                # 开始代码块
                in_code_block = True
                code_lang = line.strip()[3:].strip()
            i += 1
            continue

        if in_code_block:
            code_content.append(line)
            i += 1
            continue

        # 表格
        if "|" in line and line.strip().startswith("|"):
            if not in_table:
                in_table = True
                table_rows = []
            table_rows.append(line)
            i += 1
            continue
        elif in_table:
            # 结束表格
            out.append(build_table(table_rows))
            in_table = False
            table_rows = []
            # 不要 i+=1，继续处理当前行
            continue

        # 空行
        if line.strip() == "":
            if in_list:
                out.append(f"</{list_tag}>")
                in_list = None
            i += 1
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{inline_parse(m.group(2))}</h{level}>")
            i += 1
            continue

        # 无序列表
        m = re.match(r"^(\s*)[-*+]\s+(.+)$", line)
        if m:
            if in_list != "ul":
                if in_list:
                    out.append(f"</{list_tag}>")
                out.append("<ul>")
                in_list = "ul"
                list_tag = "ul"
            out.append(f"<li>{inline_parse(m.group(2))}</li>")
            i += 1
            continue

        # 有序列表
        m = re.match(r"^(\s*)\d+\.\s+(.+)$", line)
        if m:
            if in_list != "ol":
                if in_list:
                    out.append(f"</{list_tag}>")
                out.append("<ol>")
                in_list = "ol"
                list_tag = "ol"
            out.append(f"<li>{inline_parse(m.group(2))}</li>")
            i += 1
            continue

        # 引用
        if line.strip().startswith("> "):
            out.append(f"<blockquote><p>{inline_parse(line.strip()[2:])}</p></blockquote>")
            i += 1
            continue

        # 水平线
        if line.strip() in ("---", "***", "___"):
            out.append("<hr>")
            i += 1
            continue

        # 普通段落
        out.append(f"<p>{inline_parse(line)}</p>")
        i += 1

    # 收尾
    if in_code_block:
        lang_attr = f' class="language-{code_lang}"' if code_lang else ""
        out.append(
            f"<pre><code{lang_attr}>"
            + "\n".join(code_content)
            + "</code></pre>"
        )
    if in_table:
        out.append(build_table(table_rows))
    if in_list:
        out.append(f"</{list_tag}>")

    return "\n".join(out)


def build_table(rows):
    """构建 HTML 表格"""
    if len(rows) < 2:
        return ""
    html = "<table>\n"
    # 表头
    html += "<thead>\n<tr>\n"
    for cell in parse_table_row(rows[0]):
        html += f"<th>{inline_parse(cell.strip())}</th>\n"
    html += "</tr>\n</thead>\n"
    # 跳过对齐行 (|---|---|)
    body_start = 2 if re.match(r"^[\|\s\-:]+$", rows[1]) else 1
    html += "<tbody>\n"
    for row in rows[body_start:]:
        html += "<tr>\n"
        for cell in parse_table_row(row):
            html += f"<td>{inline_parse(cell.strip())}</td>\n"
        html += "</tr>\n"
    html += "</tbody>\n</table>"
    return html


def parse_table_row(line):
    """解析表格行"""
    cells = line.strip().split("|")
    # 去掉首尾空元素
    if cells and cells[0].strip() == "":
        cells = cells[1:]
    if cells and cells[-1].strip() == "":
        cells = cells[:-1]
    return cells


def inline_parse(text: str) -> str:
    """行内元素解析：粗体、斜体、行内代码、链接、图片"""
    # 图片 ![alt](url)
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1">', text)
    # 链接 [text](url)
    text = re.sub(r"\[([^\]]*)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    # 行内代码 `code`
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    # 粗体+斜体 ***text***
    text = re.sub(r"\*\*\*(.+?)\*\*\*", r"<strong><em>\1</em></strong>", text)
    # 粗体 **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    # 斜体 *text*
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    return text


# ============================================================
# 文章解析
# ============================================================


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """
    解析 YAML frontmatter
    返回 (元数据字典, 剩余正文)
    """
    meta = {}
    content = text

    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            for line in parts[1].strip().split("\n"):
                line = line.strip()
                if ":" in line:
                    key, _, value = line.partition(":")
                    meta[key.strip()] = value.strip()
            content = parts[2]

    return meta, content


def extract_title_from_body(text: str) -> str:
    """从正文提取第一个 # 标题作为文章标题"""
    m = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    if m:
        return m.group(1).strip()
    return ""


def build_about():
    """构建关于页：about.md → about.html"""
    about_md = BASE_DIR / "about.md"
    if not about_md.exists():
        print("[提示] about.md 不存在，跳过")
        return

    print(f"[处理] about.md ...", end=" ")
    text = about_md.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)

    title = meta.get("title", "关于我")

    # 去掉正文中的第一个 # 标题行
    body = re.sub(r"^#\s+.+$", "", body, count=1, flags=re.MULTILINE).strip()

    body_html = convert_markdown(body)

    full_html = ABOUT_TEMPLATE.format(
        title=title,
        site_title=SITE_TITLE,
        content=body_html,
        year=date.today().year,
    )

    about_html = BASE_DIR / "about.html"
    about_html.write_text(full_html, encoding="utf-8")
    print("✓")


def build_articles():
    """主构建函数"""
    if not ARTICLES_DIR.exists():
        print(f"[错误] articles/ 目录不存在: {ARTICLES_DIR}")
        sys.exit(1)

    md_files = sorted(
        ARTICLES_DIR.glob("*.md"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    if not md_files:
        print("[提示] articles/ 目录下没有 .md 文件，创建一个示例...")
        create_sample_article()
        md_files = list(ARTICLES_DIR.glob("*.md"))

    articles_meta = []
    converted = 0

    for md_path in md_files:
        print(f"[处理] {md_path.name} ...", end=" ")

        text = md_path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)

        # 标题优先级: frontmatter title > 正文第一个 # heading > 文件名
        title = meta.get("title", "")
        if not title:
            title = extract_title_from_body(body)
        if not title:
            title = md_path.stem

        # 去掉正文中的第一个 # 标题行（会作为页面标题显示）
        body = re.sub(r"^#\s+.+$", "", body, count=1, flags=re.MULTILINE).strip()

        # 日期
        article_date = meta.get("date", "")
        if not article_date:
            mtime = date.fromtimestamp(md_path.stat().st_mtime)
            article_date = mtime.isoformat()

        # 分类
        category = meta.get("category", "")

        # 摘要（取正文前200字，去掉markdown标记）
        summary = re.sub(r"[#*`\[\]\(\)\|]", "", body[:200]).strip()
        summary = re.sub(r"\s+", " ", summary)

        # 生成 HTML 文件名
        html_name = md_path.stem + ".html"
        html_path = ARTICLES_DIR / html_name

        # 转换 markdown → HTML
        body_html = convert_markdown(body)
        body_html = add_heading_anchors(body_html)
        toc_html = generate_toc(body_html)

        # 生成分类标签
        category_html = get_category_box(category)

        # 填充模板
        full_html = PAGE_TEMPLATE.format(
            title=title,
            site_title=SITE_TITLE,
            date=article_date,
            category_html=category_html,
            toc_html=toc_html,
            content=body_html,
            year=date.today().year,
        )

        html_path.write_text(full_html, encoding="utf-8")
        converted += 1
        print("✓")

        articles_meta.append(
            {
                "id": md_path.stem,
                "title": title,
                "date": article_date,
                "category": category,
                "summary": summary,
                "md_file": md_path.name,
                "html_file": html_name,
            }
        )

    # 生成 articles.json
    manifest_path = BASE_DIR / "articles.json"
    manifest_path.write_text(
        json.dumps(articles_meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\n[完成] 转换了 {converted} 篇文章")
    print(f"[清单] articles.json 已更新 ({len(articles_meta)} 条)")

    # 直接注入文章列表到 index.html（避免 file:// 下 fetch 跨域问题）
    inject_article_list(articles_meta)
    print(f"[首页] index.html 文章列表已更新")


def build_section(section_dir: Path, section_name: str, marker_start: str, marker_end: str):
    """通用栏目构建函数：扫描目录下的 .md 文件，生成 HTML 并注入首页"""
    if not section_dir.exists():
        print(f"[提示] {section_name}/ 目录不存在，创建空目录")
        section_dir.mkdir(parents=True, exist_ok=True)
        inject_section_list([], marker_start, marker_end)
        return

    md_files = sorted(
        section_dir.glob("*.md"),
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )

    items_meta = []
    converted = 0

    for md_path in md_files:
        print(f"[处理] {section_name}/{md_path.name} ...", end=" ")

        text = md_path.read_text(encoding="utf-8")
        meta, body = parse_frontmatter(text)

        title = meta.get("title", "")
        if not title:
            title = extract_title_from_body(body)
        if not title:
            title = md_path.stem

        body = re.sub(r"^#\s+.+$", "", body, count=1, flags=re.MULTILINE).strip()

        article_date = meta.get("date", "")
        if not article_date:
            mtime = date.fromtimestamp(md_path.stat().st_mtime)
            article_date = mtime.isoformat()

        category = meta.get("category", "")

        summary = re.sub(r"[#*`\[\]\(\)\|]", "", body[:200]).strip()
        summary = re.sub(r"\s+", " ", summary)

        html_name = md_path.stem + ".html"
        html_path = section_dir / html_name

        body_html = convert_markdown(body)
        body_html = add_heading_anchors(body_html)
        toc_html = generate_toc(body_html)
        category_html = get_category_box(category)

        full_html = PAGE_TEMPLATE.format(
            title=title,
            site_title=SITE_TITLE,
            date=article_date,
            category_html=category_html,
            toc_html=toc_html,
            content=body_html,
            year=date.today().year,
        )

        html_path.write_text(full_html, encoding="utf-8")
        converted += 1
        print("✓")

        items_meta.append(
            {
                "id": md_path.stem,
                "title": title,
                "date": article_date,
                "category": category,
                "summary": summary,
                "md_file": md_path.name,
                "html_file": html_name,
            }
        )

    inject_section_list(items_meta, marker_start, marker_end, section_dir.name)
    print(f"[完成] {section_name}: 转换了 {converted} 篇，首页已更新")


def inject_section_list(items_meta: list, marker_start: str, marker_end: str, section_dir_name: str = ""):
    """把列表 HTML 注入 index.html，替换指定标记之间的内容"""
    index_path = BASE_DIR / "index.html"

    if not index_path.exists():
        print(f"[警告] index.html 不存在，跳过注入")
        return

    html = index_path.read_text(encoding="utf-8")

    if not items_meta:
        list_html = '<ul class="article-list">\n<li class="empty">还没有内容。在对应目录下创建 .md 文件，然后运行 <code>python build.py</code></li>\n</ul>'
    else:
        li_items = []
        for a in items_meta:
            cat_html = get_category_box(a["category"])
            href = f"{section_dir_name}/{a['html_file']}" if section_dir_name else a["html_file"]
            li_items.append(
                f'<li class="article-item">'
                f'<a href="{href}">{a["title"]}</a>'
                f'{cat_html}'
                f' <time class="article-date" datetime="{a["date"]}">{a["date"]}</time>'
                f'</li>'
            )
        list_html = '<ul class="article-list">\n' + "\n".join(li_items) + '\n</ul>'

    pattern = rf"<!-- {marker_start} -->.*?<!-- {marker_end} -->"
    replacement = f"<!-- {marker_start} -->\n{list_html}\n<!-- {marker_end} -->"
    html = re.sub(pattern, replacement, html, count=1, flags=re.DOTALL)
    index_path.write_text(html, encoding="utf-8")


def inject_article_list(articles_meta: list):
    """把文章列表 HTML 直接注入 index.html，替换 <!-- ARTICLE_LIST_START --> ... <!-- ARTICLE_LIST_END --> 之间的内容"""
    index_path = BASE_DIR / "index.html"

    if not index_path.exists():
        print(f"[警告] index.html 不存在，跳过注入")
        return

    html = index_path.read_text(encoding="utf-8")

    if not articles_meta:
        article_html = '<ul id="article-list" class="article-list">\n<li class="empty">还没有文章。在 articles/ 目录下创建 .md 文件，然后运行 <code>python build.py</code></li>\n</ul>'
    else:
        items = []
        for a in articles_meta:
            cat_html = get_category_box(a["category"])
            items.append(
                f'<li class="article-item">'
                f'<a href="articles/{a["html_file"]}">{a["title"]}</a>'
                f'{cat_html}'
                f' <time class="article-date" datetime="{a["date"]}">{a["date"]}</time>'
                f'</li>'
            )
        article_html = '<ul id="article-list" class="article-list">\n' + "\n".join(items) + '\n</ul>'

    # 替换标记之间的内容（支持反复构建）
    pattern = r"<!-- ARTICLE_LIST_START -->.*?<!-- ARTICLE_LIST_END -->"
    replacement = f"<!-- ARTICLE_LIST_START -->\n{article_html}\n<!-- ARTICLE_LIST_END -->"
    html = re.sub(pattern, replacement, html, count=1, flags=re.DOTALL)
    index_path.write_text(html, encoding="utf-8")


def create_sample_article():
    """创建示例文章"""
    sample = """---
title: Hello World - 第一篇文章
date: 2024-01-15
category: 编程基础
---

## 关于这篇文章

这是我的第一篇 Wiki 文章。

## 代码示例

```c
#include <stdio.h>

int main() {
    printf("Hello, World!\\n");
    return 0;
}
```

## 要点

- 保持好奇心
- **实践**比理论更重要
- 善用工具，比如 `gdb` 和 `git`

> 程序 = 数据结构 + 算法
"""
    sample_path = ARTICLES_DIR / "hello-world.md"
    sample_path.write_text(sample, encoding="utf-8")
    print(f"[创建] 示例文章: {sample_path.name}")


if __name__ == "__main__":
    build_about()
    build_section(MICRO_TUTORIALS_DIR, "微教程", "MICRO_TUTORIALS_START", "MICRO_TUTORIALS_END")
    build_section(LONG_GUIDES_DIR, "长指北", "LONG_GUIDES_START", "LONG_GUIDES_END")
