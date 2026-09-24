"""
应大Wiki MD转HTML构建脚本
用法:
  python build_wiki.py              # 构建所有文件
  python build_wiki.py --watch      # 监听文件变化
  python build_wiki.py docs/校园生活/恋爱.md  # 构建单个文件
"""

import re
import sys
import json
import hashlib
import argparse
import posixpath
from pathlib import Path
from datetime import datetime

# 修复 Windows 控制台编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR / "docs"
TEMPLATES_DIR = BASE_DIR / "templates"
ASSETS_DIR = BASE_DIR / "assets"
CACHE_FILE = BASE_DIR / ".build_cache.json"
NAVIGATION_FILE = BASE_DIR / "navigation.json"
SEARCH_INDEX_FILE = ASSETS_DIR / "search-index.json"
SITE_BASE = "/"


def site_url(path):
    """生成站点根路径 URL。"""
    return SITE_BASE + "docs/" + str(path).lstrip("/")


URL_ATTRIBUTE_RE = re.compile(
    r'(?P<prefix>\b(?:href|src)\s*=\s*)(?P<quote>["\'])(?P<url>.*?)(?P=quote)',
    re.IGNORECASE
)
CSS_URL_RE = re.compile(
    r'url\(\s*(?P<quote>["\']?)(?P<url>.*?)(?P=quote)\s*\)',
    re.IGNORECASE
)


def absolutize_content_urls(content_html, page_path):
    """将正文中的本地链接和资源路径转换为站点根路径。"""
    page_url = site_url(page_path)
    page_dir = posixpath.dirname(page_url)

    def replace_url(match):
        url = match.group('url').strip()
        if (
            not url
            or url.startswith(("#", "/", "?", "http://", "https://", "//", "mailto:", "tel:", "data:", "javascript:"))
        ):
            return match.group(0)

        path_part, separator, suffix = url.partition("#")
        query = ""
        if "?" in path_part:
            path_part, query = path_part.split("?", 1)
            query = "?" + query

        resolved = posixpath.normpath(posixpath.join(page_dir, path_part))
        if not resolved.startswith("/"):
            resolved = "/" + resolved
        resolved += query
        if separator:
            resolved += "#" + suffix

        return f"{match.group('prefix')}{match.group('quote')}{resolved}{match.group('quote')}"

    return URL_ATTRIBUTE_RE.sub(replace_url, content_html)


def absolutize_css_urls(content, page_path):
    """将 CSS url(...) 中的本地资源转换为站点根路径。"""
    page_url = site_url(page_path)
    page_dir = posixpath.dirname(page_url)

    def replace_url(match):
        url = match.group('url').strip()
        if (
            not url
            or url.startswith(("#", "/", "?", "http://", "https://", "//", "data:", "var("))
        ):
            return match.group(0)

        resolved = posixpath.normpath(posixpath.join(page_dir, url))
        if not resolved.startswith("/"):
            resolved = "/" + resolved
        return f"url({match.group('quote')}{resolved}{match.group('quote')})"

    return CSS_URL_RE.sub(replace_url, content)


def md_to_html(md_content):
    """将Markdown转换为HTML（支持表格、嵌套列表、行内格式全量转换）"""
    def convert_inline(text):
        # 图片
        text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" style="max-width:100%;border-radius:4px;">', text)
        # 链接
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
        # 粗体（全部对，非贪婪）
        text = re.sub(r'\*\*([^*]+?)\*\*', r'<strong>\1</strong>', text)
        # 斜体（全部对，避开 **）
        text = re.sub(r'(?<!\*)\*([^*\s][^*]*?)\*(?!\*)', r'<em>\1</em>', text)
        # 行内代码
        if '`' in text:
            parts = text.split('`')
            text = ''.join(p if i % 2 == 0 else f'<code>{p}</code>' for i, p in enumerate(parts))
        return text

    lines = md_content.split('\n')
    html_lines = []
    in_blockquote = False
    in_code_block = False
    code_content = []
    table_lines = []
    list_stack = []  # [{'tag': 'ul'/'ol', 'level': int, 'li_open': bool}]

    LIST_RE = re.compile(r'^(\s*)([-*]|\d+[.)]) (.*)$')
    TABLE_ROW_RE = re.compile(r'^\s*\|.*\|\s*$')
    SEP_CELL_RE = re.compile(r'^:?-{2,}:?$')

    def close_top_li():
        if list_stack and list_stack[-1]['li_open']:
            html_lines.append('</li>')
            list_stack[-1]['li_open'] = False

    def close_all_lists():
        while list_stack:
            close_top_li()
            html_lines.append(f"</{list_stack[-1]['tag']}>")
            list_stack.pop()

    def flush_table():
        nonlocal table_lines
        rows = []
        for tl in table_lines:
            cells = [c.strip() for c in tl.strip().strip('|').split('|')]
            if cells and all(SEP_CELL_RE.match(c) for c in cells if c != ''):
                continue  # 分隔行
            rows.append(cells)
        table_lines = []
        if not rows:
            return
        html_lines.append('<table>')
        html_lines.append('<thead><tr>' + ''.join(f'<th>{convert_inline(c)}</th>' for c in rows[0]) + '</tr></thead>')
        html_lines.append('<tbody>')
        for r in rows[1:]:
            html_lines.append('<tr>' + ''.join(f'<td>{convert_inline(c)}</td>' for c in r) + '</tr>')
        html_lines.append('</tbody></table>')

    for line in lines:
        stripped = line.strip()

        # 代码块
        if stripped.startswith('```'):
            if in_code_block:
                html_lines.append('<pre><code>' + '\n'.join(code_content) + '</code></pre>')
                in_code_block = False
                code_content = []
            else:
                close_all_lists()
                in_code_block = True
            continue
        if in_code_block:
            code_content.append(line)
            continue

        # 表格行收集（先于其他分支，保证表格被任何行打断时都能先落盘）
        if TABLE_ROW_RE.match(line):
            close_all_lists()
            table_lines.append(stripped)
            continue
        if table_lines:
            flush_table()

        # 空行
        if not stripped:
            close_all_lists()
            if in_blockquote:
                html_lines.append('</blockquote>')
                in_blockquote = False
            continue

        # 标题
        if stripped.startswith('#'):
            close_all_lists()
            if in_blockquote:
                html_lines.append('</blockquote>')
                in_blockquote = False
            level = min(len(stripped) - len(stripped.lstrip('#')), 4)
            text = stripped[level:].strip()
            html_lines.append(f'<h{level}>{convert_inline(text)}</h{level}>')
            continue

        # 引用
        if stripped.startswith('>'):
            close_all_lists()
            if not in_blockquote:
                html_lines.append('<blockquote>')
                in_blockquote = True
            text = stripped[1:].strip()
            html_lines.append(f'<p>{convert_inline(text)}</p>')
            continue
        if in_blockquote:
            html_lines.append('</blockquote>')
            in_blockquote = False

        # 列表（含嵌套）
        m = LIST_RE.match(line)
        if m:
            indent_str, marker, content = m.group(1), m.group(2), m.group(3)
            level = len(indent_str) // 2
            tag = 'ul' if marker in '-*' else 'ol'
            if not list_stack:
                html_lines.append(f'<{tag}>')
                list_stack.append({'tag': tag, 'level': level, 'li_open': False})
            else:
                top = list_stack[-1]
                if level > top['level']:
                    # 嵌套层级：进入当前未闭合 <li> 内部
                    html_lines.append(f'<{tag}>')
                    list_stack.append({'tag': tag, 'level': level, 'li_open': False})
                else:
                    while len(list_stack) > 1 and list_stack[-1]['level'] > level:
                        close_top_li()
                        html_lines.append(f"</{list_stack[-1]['tag']}>")
                        list_stack.pop()
                    if list_stack[-1]['tag'] != tag:
                        close_top_li()
                        html_lines.append(f"</{list_stack[-1]['tag']}>")
                        list_stack.pop()
                        html_lines.append(f'<{tag}>')
                        list_stack.append({'tag': tag, 'level': level, 'li_open': False})
            close_top_li()
            html_lines.append(f'<li>{convert_inline(content)}')
            list_stack[-1]['li_open'] = True
            continue

        # 普通文本前关闭列表
        close_all_lists()

        # 水平线
        if stripped in ('---', '***', '___'):
            html_lines.append('<hr>')
            continue

        # 普通段落
        html_lines.append(f'<p>{convert_inline(stripped)}</p>')

    if table_lines:
        flush_table()
    close_all_lists()
    if in_blockquote:
        html_lines.append('</blockquote>')
    if in_code_block:
        html_lines.append('<pre><code>' + '\n'.join(code_content) + '</code></pre>')

    return '\n'.join(html_lines)


def validate_sidebar_item(item, parent_name=None):
    """校验侧边栏配置项，并确认目标页面或其 Markdown 源存在。"""
    if not isinstance(item, dict):
        raise ValueError("侧边栏配置项必须是对象")

    name = item.get("name")
    path = item.get("path")
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"侧边栏配置缺少有效 name: {item!r}")
    if not isinstance(path, str) or not path.strip():
        raise ValueError(f"侧边栏配置缺少有效 path: {item!r}")

    target = DOCS_DIR / path
    markdown_source = target.with_suffix(".md")
    if not target.exists() and not markdown_source.exists():
        prefix = f"{parent_name} -> " if parent_name else ""
        raise ValueError(f"侧边栏目标不存在: {prefix}{path}")

    children = item.get("children")
    if children is None:
        return
    if not isinstance(children, list):
        raise ValueError(f"侧边栏 children 必须是数组: {path}")
    for child in children:
        validate_sidebar_item(child, name)


def load_sidebar_structure():
    """从 navigation.json 加载并校验侧边栏结构。"""
    data = json.loads(NAVIGATION_FILE.read_text(encoding="utf-8"))
    sidebar = data.get("sidebar")
    if not isinstance(sidebar, list):
        raise ValueError("navigation.json 缺少 sidebar 数组")
    for item in sidebar:
        validate_sidebar_item(item)
    return sidebar


def build_search_entries():
    """生成全站搜索索引。"""
    # 定义页面列表（路径相对 docs/）
    pages = [
        {"path": "学校概览/周边配套.html", "title": "周边配套", "desc": "学校概览 - 周边配套"},
        {"path": "学校概览/学校简介.html", "title": "学校简介", "desc": "学校概览 - 学校简介"},
        {"path": "学校概览/燕郊特色.html", "title": "燕郊特色", "desc": "学校概览 - 燕郊特色"},
        {"path": "校园生活/体育课选择.html", "title": "体育课选择", "desc": "校园生活 - 体育课选择"},
        {"path": "入学指南/军训须知.html", "title": "军训须知", "desc": "入学指南 - 军训须知"},
        {"path": "入学指南/防骗指南.html", "title": "防骗指南", "desc": "入学指南 - 防骗指南"},
        {"path": "入学指南/报到流程.html", "title": "报到流程", "desc": "入学指南 - 报到流程"},
        {"path": "入学指南/来校路线.html", "title": "来校路线", "desc": "入学指南 - 来校路线"},
        {"path": "选课指南/推荐课程.html", "title": "推荐课程", "desc": "选课指南 - 推荐课程"},
        {"path": "选课指南/选课时间线.html", "title": "选课时间线", "desc": "选课指南 - 选课时间线"},
        {"path": "选课指南/选课流程.html", "title": "选课流程", "desc": "选课指南 - 选课流程"},
        {"path": "学分绩点/四六级.html", "title": "四六级", "desc": "学分绩点 - 四六级"},
        {"path": "学分绩点/奖学金与资助.html", "title": "奖学金与资助", "desc": "学分绩点 - 奖学金与资助：奖学金评定、基层就业学费补偿贷款代偿、学生资助平台"},
        {"path": "学分绩点/学分要求.html", "title": "学分要求", "desc": "学分绩点 - 学分要求"},
        {"path": "学分绩点/毕业条件.html", "title": "毕业条件", "desc": "学分绩点 - 毕业条件"},
        {"path": "学分绩点/绩点计算.html", "title": "绩点计算", "desc": "学分绩点 - 绩点计算"},
        {"path": "学分绩点/选修课.html", "title": "选修课", "desc": "学分绩点 - 选修课"},
        {"path": "校园生活/体测要求.html", "title": "体测要求", "desc": "校园生活 - 体测要求"},
        {"path": "校园生活/体育场馆开放时间.html", "title": "体育场馆开放时间", "desc": "校园生活 - 体育场馆开放时间（2026年9月）"},
        {"path": "校园生活/公交指南.html", "title": "公交指南", "desc": "校园生活 - 公交指南"},
        {"path": "校园生活/地铁指南.html", "title": "地铁指南", "desc": "校园生活 - 地铁指南"},
        {"path": "校园生活/学生组织.html", "title": "学生组织", "desc": "校园生活 - 学生组织"},
        {"path": "校园生活/宿舍篇.html", "title": "宿舍篇", "desc": "校园生活 - 宿舍篇"},
        {"path": "校园生活/常用电话.html", "title": "常用电话", "desc": "校园生活 - 常用电话"},
        {"path": "校园生活/心理健康.html", "title": "心理健康", "desc": "校园生活 - 心理健康"},
        {"path": "校园生活/校园地图.html", "title": "校园地图", "desc": "校园生活 - 校园地图"},
        {"path": "校园生活/食堂篇.html", "title": "食堂篇", "desc": "校园生活 - 食堂篇"},
        {"path": "校园生活/晚自习.html", "title": "晚自习", "desc": "校园生活 - 晚自习"},
        {"path": "校园生活/准军事化管理.html", "title": "准军事化管理", "desc": "校园生活 - 准军事化管理"},
        {"path": "校园生活/作息时间.html", "title": "作息时间", "desc": "校园生活 - 作息时间"},
        {"path": "校园生活/校历.html", "title": "校历", "desc": "校园生活 - 校历"},
        {"path": "校园生活/恋爱.html", "title": "恋爱", "desc": "校园生活 - 恋爱"},
        {"path": "学院与专业/应急技术与指挥学院/index.html", "title": "应急技术与指挥学院", "desc": "应急技术与指挥学院专业介绍"},
        {"path": "学院与专业/矿山安全学院/index.html", "title": "矿山安全学院", "desc": "矿山安全学院专业介绍"},
        {"path": "学院与专业/城市安全学院/index.html", "title": "城市安全学院", "desc": "城市安全学院专业介绍"},
        {"path": "学院与专业/地震工程与建筑安全学院/index.html", "title": "地震工程与建筑安全学院", "desc": "地震工程与建筑安全学院专业介绍"},
        {"path": "学院与专业/地震科学与技术学院/index.html", "title": "地震科学与技术学院", "desc": "地震科学与技术学院专业介绍"},
        {"path": "学院与专业/化工安全学院/index.html", "title": "化工安全学院", "desc": "化工安全学院专业介绍"},
        {"path": "学院与专业/环境与灾害治理学院/index.html", "title": "环境与灾害治理学院", "desc": "环境与灾害治理学院专业介绍"},
        {"path": "学院与专业/计算机与信息安全学院/index.html", "title": "计算机与信息安全学院", "desc": "计算机与信息安全学院专业介绍"},
        {"path": "学院与专业/应急通信与控制工程学院/index.html", "title": "应急通信与控制工程学院", "desc": "应急通信与控制工程学院专业介绍"},
        {"path": "学院与专业/应急装备学院/index.html", "title": "应急装备学院", "desc": "应急装备学院专业介绍"},
        {"path": "学院与专业/应急经济与物资保障学院/index.html", "title": "应急经济与物资保障学院", "desc": "应急经济与物资保障学院专业介绍"},
        {"path": "学院与专业/应急国际交流学院/index.html", "title": "应急国际交流学院", "desc": "应急国际交流学院专业介绍"},
        {"path": "学院与专业/应急救援训练中心/index.html", "title": "应急救援训练中心", "desc": "应急救援训练中心专业介绍"},
        {"path": "学院与专业/应急文化传播与法学院/index.html", "title": "应急文化传播与法学院", "desc": "应急文化传播与法学院专业介绍"},
        {"path": "学院与专业/理学院/index.html", "title": "理学院", "desc": "理学院专业介绍"},
        {"path": "学院与专业/防灾减灾工程学院/index.html", "title": "防灾减灾工程学院", "desc": "防灾减灾工程学院专业介绍"},
        {"path": "写在前面/index.html", "title": "写在前面", "desc": "欢迎来到应大Wiki"},
        {"path": "关于我们/index.html", "title": "关于我们", "desc": "贡献者与联系方式"},
        {"path": "常用链接/index.html", "title": "常用链接", "desc": "校内组织、学长学姐博客"},
        {"path": "常用链接/校内组织.html", "title": "校内组织", "desc": "实验室、战队与技术社群"},
        {"path": "常用链接/学长学姐博客.html", "title": "学长学姐博客", "desc": "校友技术博客汇总"},
        {"path": "常用链接/友情链接.html", "title": "友情链接", "desc": "与应大Wiki互链的站点"},
    ]
    for p in pages:
        p["url"] = site_url(p["path"])
        del p["path"]
    return pages


def write_search_index():
    """将搜索索引写入静态资源文件。"""
    ASSETS_DIR.mkdir(exist_ok=True)
    SEARCH_INDEX_FILE.write_text(
        json.dumps(build_search_entries(), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def build_html(md_path, force=False):
    """构建单个HTML文件"""
    # 如果是相对路径，先转换为绝对路径
    if not md_path.is_absolute():
        md_path = BASE_DIR / md_path

    html_path = md_path.with_suffix('.html')

    # 检查是否需要重新构建
    if not force and html_path.exists():
        if not is_file_changed(md_path):
            print(f"  跳过 (未变化): {md_path.name}")
            return False

    print(f"  构建: {md_path.name}")

    # 读取MD文件
    md_content = md_path.read_text(encoding='utf-8')

    # 提取标题（第一个#标题）
    title = md_path.stem
    for line in md_content.split('\n'):
        if line.strip().startswith('#'):
            title = line.strip().lstrip('#').strip()
            break

    # 转换为HTML
    page_path = md_path.with_suffix('.html').relative_to(DOCS_DIR).as_posix()
    content_html = absolutize_css_urls(
        absolutize_content_urls(md_to_html(md_content), page_path),
        page_path
    )

    # 读取模板
    template = (TEMPLATES_DIR / 'base.html').read_text(encoding='utf-8')

    # 替换变量
    html_output = template.replace('{{title}}', title)
    html_output = html_output.replace('{{content}}', content_html)
    html_output = html_output.replace('{{page_style}}', '')
    html_output = html_output.replace('{{page_scripts}}', '')

    # 写入HTML文件
    html_path.write_text(html_output, encoding='utf-8')

    # 更新缓存
    update_cache(md_path)

    return True


def is_file_changed(file_path):
    """检查文件是否已改变（模板、导航或构建器变更会使所有页面失效）"""
    if not CACHE_FILE.exists():
        return True

    cache = json.loads(CACHE_FILE.read_text(encoding='utf-8'))
    file_key = str(file_path.relative_to(BASE_DIR))

    if file_key not in cache:
        return True

    template_path = TEMPLATES_DIR / 'base.html'
    template_hash = hashlib.md5(template_path.read_bytes()).hexdigest()
    if cache[file_key].get('template_hash', '') != template_hash:
        return True
    navigation_hash = hashlib.md5(NAVIGATION_FILE.read_bytes()).hexdigest()
    if cache[file_key].get('navigation_hash', '') != navigation_hash:
        return True
    generator_hash = hashlib.md5(Path(__file__).read_bytes()).hexdigest()
    if cache[file_key].get('generator_hash', '') != generator_hash:
        return True

    # 计算文件哈希
    current_hash = hashlib.md5(file_path.read_bytes()).hexdigest()
    cached_hash = cache[file_key].get('hash', '')

    return current_hash != cached_hash


def update_cache(file_path):
    """更新文件缓存"""
    cache = {}
    if CACHE_FILE.exists():
        cache = json.loads(CACHE_FILE.read_text(encoding='utf-8'))

    file_key = str(file_path.relative_to(BASE_DIR))
    template_hash = hashlib.md5((TEMPLATES_DIR / 'base.html').read_bytes()).hexdigest()
    cache[file_key] = {
        'hash': hashlib.md5(file_path.read_bytes()).hexdigest(),
        'template_hash': template_hash,
        'navigation_hash': hashlib.md5(NAVIGATION_FILE.read_bytes()).hexdigest(),
        'generator_hash': hashlib.md5(Path(__file__).read_bytes()).hexdigest(),
        'timestamp': datetime.now().isoformat()
    }

    CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding='utf-8')


def load_cache():
    cache = {}
    if CACHE_FILE.exists():
        try:
            cache = json.loads(CACHE_FILE.read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            cache = {}
    return cache


def build_context_hashes():
    return {
        'template_hash': hashlib.md5((TEMPLATES_DIR / 'base.html').read_bytes()).hexdigest(),
        'navigation_hash': hashlib.md5(NAVIGATION_FILE.read_bytes()).hexdigest(),
        'generator_hash': hashlib.md5(Path(__file__).read_bytes()).hexdigest()
    }


def sync_standalone_html():
    """重新生成没有同名 md 源的 html 页面（板块首页 index.html、学院与专业等历史页面）。

    这些页面无法由 build_html 构建，模板更新后它们会一直停留在旧版样式上。
    做法：保留页面标题、正文、专属样式和专属脚本；侧边栏从
    navigation.json 重新生成，其余公共结构使用当前模板。
    """
    synced = 0
    cache = load_cache()
    context = build_context_hashes()
    cache_changed = False
    for html_path in DOCS_DIR.rglob('*.html'):
        if html_path.with_suffix('.md').exists():
            continue

        cache_key = f"html:{html_path.relative_to(BASE_DIR).as_posix()}"
        current_hash = hashlib.md5(html_path.read_bytes()).hexdigest()
        cached = cache.get(cache_key) or {}
        if (
            cached.get('hash') == current_hash
            and all(cached.get(key) == value for key, value in context.items())
        ):
            continue

        old = html_path.read_text(encoding='utf-8')

        title_m = re.search(r'<title>(.*?)</title>', old)
        content_open = old.find('<div class="markdown-section">')
        if not all([title_m, content_open != -1]):
            print(f"  跳过 (无法解析, 需人工处理): {html_path}")
            continue
        content_close = old.find('<!-- /markdown-section -->', content_open)
        if content_close == -1:
            anchor = old.find('twikoo-title', content_open)
            if anchor == -1:
                anchor = old.find('id="twikoo-comment"', content_open)
            content_close = old.rfind('</div>', 0, anchor) if anchor != -1 else old.rfind('</div>')
        if content_close == -1 or content_close <= content_open:
            print(f"  跳过 (无法定位正文, 需人工处理): {html_path}")
            continue
        page_path = html_path.relative_to(DOCS_DIR).as_posix()
        content = old[content_open + len('<div class="markdown-section">'):content_close].strip()
        content = absolutize_css_urls(
            absolutize_content_urls(content, page_path),
            page_path
        )
        title = title_m.group(1)
        if title.endswith(' - 应大Wiki'):
            title = title[:-len(' - 应大Wiki')]

        page_style = '\n'.join(
            re.findall(r'<style\s+data-page-style[^>]*>.*?</style>|<link\s+data-page-style[^>]*>', old, re.S | re.I)
        )
        page_style = absolutize_css_urls(
            page_style,
            page_path
        )
        page_scripts = '\n'.join(
            re.findall(r'<script\s+data-page-script[^>]*>.*?</script>', old, re.S | re.I)
        )

        template = (TEMPLATES_DIR / 'base.html').read_text(encoding='utf-8')
        html_output = template.replace('{{title}}', title)
        html_output = html_output.replace('{{content}}', content)
        html_output = html_output.replace('{{page_style}}', page_style)
        html_output = html_output.replace('{{page_scripts}}', page_scripts)

        if html_output != old:
            html_path.write_text(html_output, encoding='utf-8')
            synced += 1
            print(f"  重同步: {html_path.relative_to(BASE_DIR)}")
            current_hash = hashlib.md5(html_path.read_bytes()).hexdigest()

        cache[cache_key] = {
            'hash': current_hash,
            **context,
            'timestamp': datetime.now().isoformat()
        }
        cache_changed = True

    if cache_changed:
        CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding='utf-8')
    return synced


def build_all(force=False):
    """构建所有MD文件"""
    print("=" * 50)
    print("  开始构建...")
    print("=" * 50)

    md_files = list(DOCS_DIR.rglob('*.md'))
    print(f"找到 {len(md_files)} 个MD文件")

    built_count = 0
    skipped_count = 0
    load_sidebar_structure()
    write_search_index()

    for md_file in md_files:
        try:
            if build_html(md_file, force):
                built_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            print(f"  错误: {md_file.name} - {e}")

    print("=" * 50)
    print(f"  完成! 构建: {built_count}, 跳过: {skipped_count}")
    print("=" * 50)

    synced = sync_standalone_html()
    print(f"  孤儿页面重同步: {synced}")
    print("=" * 50)


def watch_files():
    """监听文件变化"""
    print("=" * 50)
    print("  监听文件变化 (按 Ctrl+C 停止)...")
    print("=" * 50)

    import time
    last_check = time.time()

    try:
        while True:
            time.sleep(1)
            current_time = time.time()
            template_changed = (TEMPLATES_DIR / 'base.html').stat().st_mtime > last_check
            navigation_changed = NAVIGATION_FILE.stat().st_mtime > last_check

            if template_changed or navigation_changed:
                reason = '模板' if template_changed else '侧边栏配置'
                print(f"\n检测到{reason}变化，全量重建")
                build_all(force=True)
                last_check = current_time
                continue

            # 检查MD文件变化
            for md_file in DOCS_DIR.rglob('*.md'):
                if md_file.stat().st_mtime > last_check:
                    print(f"\n检测到变化: {md_file.name}")
                    build_html(md_file, force=True)

            last_check = current_time
    except KeyboardInterrupt:
        print("\n停止监听")


def main():
    parser = argparse.ArgumentParser(description='应大Wiki MD转HTML构建脚本')
    parser.add_argument('files', nargs='*', help='要构建的MD文件路径')
    parser.add_argument('--force', '-f', action='store_true', help='强制重新构建所有文件')
    parser.add_argument('--watch', '-w', action='store_true', help='监听文件变化')
    parser.add_argument('--skip-recent', action='store_true', help='跳过 GitHub Deployments 更新')
    parser.add_argument('--update-recent', action='store_true', help='忽略缓存立即更新 GitHub Deployments')

    args = parser.parse_args()

    if not args.skip_recent:
        try:
            from update_recent import update_recent_updates
            update_recent_updates(
                max_age_seconds=0 if args.update_recent else 600,
                force=args.update_recent
            )
        except Exception as error:
            print(f"  最近更新数据刷新失败，继续使用现有文件: {error}")

    if args.watch:
        watch_files()
    elif args.files:
        # 构建指定文件
        for file_path in args.files:
            md_path = Path(file_path)
            if md_path.exists():
                build_html(md_path, force=True)
            else:
                print(f"文件不存在: {file_path}")
    else:
        # 构建所有文件
        build_all(args.force)


if __name__ == '__main__':
    main()
