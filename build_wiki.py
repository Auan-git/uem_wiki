"""
应大Wiki MD转HTML构建脚本
用法:
  python build_wiki.py              # 构建所有文件
  python build_wiki.py --watch      # 监听文件变化
  python build_wiki.py docs/校园生活/恋爱.md  # 构建单个文件
"""

import os
import re
import sys
import json
import hashlib
import argparse
from pathlib import Path
from datetime import datetime

# 修复 Windows 控制台编码
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent
DOCS_DIR = BASE_DIR / "docs"
TEMPLATES_DIR = BASE_DIR / "templates"
CACHE_FILE = BASE_DIR / ".build_cache.json"


def md_to_html(md_content):
    """将Markdown转换为HTML（支持表格、嵌套列表、行内格式全量转换）"""
    import re

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


def generate_sidebar(current_page, relative_depth):
    """生成侧边栏HTML"""
    # 定义侧边栏结构
    sidebar_structure = [
        {"name": "写在前面", "path": "写在前面/index.html"},
        {"name": "学校概览", "path": "学校概览/index.html", "children": [
            {"name": "周边配套", "path": "学校概览/周边配套.html"},
            {"name": "学校简介", "path": "学校概览/学校简介.html"},
            {"name": "燕郊特色", "path": "学校概览/燕郊特色.html"},
        ]},
        {"name": "入学指南", "path": "入学指南/index.html", "children": [
            {"name": "防骗指南", "path": "入学指南/防骗指南.html"},
            {"name": "军训须知", "path": "入学指南/军训须知.html"},
            {"name": "报到流程", "path": "入学指南/报到流程.html"},
            {"name": "来校路线", "path": "入学指南/来校路线.html"},
        ]},
        {"name": "选课指南", "path": "选课指南/index.html", "children": [
            {"name": "推荐课程", "path": "选课指南/推荐课程.html"},
            {"name": "选课时间线", "path": "选课指南/选课时间线.html"},
            {"name": "选课流程", "path": "选课指南/选课流程.html"},
        ]},
        {"name": "学分绩点", "path": "学分绩点/index.html", "children": [
            {"name": "四六级", "path": "学分绩点/四六级.html"},
            {"name": "奖学金与资助", "path": "学分绩点/奖学金与资助.html"},
            {"name": "学分要求", "path": "学分绩点/学分要求.html"},
            {"name": "毕业条件", "path": "学分绩点/毕业条件.html"},
            {"name": "绩点计算", "path": "学分绩点/绩点计算.html"},
            {"name": "选修课", "path": "学分绩点/选修课.html"},
        ]},
        {"name": "校园生活", "path": "校园生活/index.html", "children": [
            {"name": "体育课选择", "path": "校园生活/体育课选择.html"},
            {"name": "体测要求", "path": "校园生活/体测要求.html"},
            {"name": "公交指南", "path": "校园生活/公交指南.html"},
            {"name": "地铁指南", "path": "校园生活/地铁指南.html"},
            {"name": "学生组织", "path": "校园生活/学生组织.html"},
            {"name": "宿舍篇", "path": "校园生活/宿舍篇.html"},
            {"name": "常用电话", "path": "校园生活/常用电话.html"},
            {"name": "心理健康", "path": "校园生活/心理健康.html"},
            {"name": "校园地图", "path": "校园生活/校园地图.html"},
            {"name": "食堂篇", "path": "校园生活/食堂篇.html"},
            {"name": "晚自习", "path": "校园生活/晚自习.html"},
            {"name": "准军事化管理", "path": "校园生活/准军事化管理.html"},
            {"name": "作息时间", "path": "校园生活/作息时间.html"},
            {"name": "校历", "path": "校园生活/校历.html"},
            {"name": "恋爱", "path": "校园生活/恋爱.html"},
        ]},
        {"name": "学院与专业", "path": "学院与专业/index.html", "children": [
            {"name": "应急技术与指挥学院", "path": "学院与专业/应急技术与指挥学院/index.html"},
            {"name": "矿山安全学院", "path": "学院与专业/矿山安全学院/index.html"},
            {"name": "城市安全学院", "path": "学院与专业/城市安全学院/index.html"},
            {"name": "地震工程与建筑安全学院", "path": "学院与专业/地震工程与建筑安全学院/index.html"},
            {"name": "地震科学与技术学院", "path": "学院与专业/地震科学与技术学院/index.html"},
            {"name": "化工安全学院", "path": "学院与专业/化工安全学院/index.html"},
            {"name": "环境与灾害治理学院", "path": "学院与专业/环境与灾害治理学院/index.html"},
            {"name": "计算机与信息安全学院", "path": "学院与专业/计算机与信息安全学院/index.html"},
            {"name": "应急通信与控制工程学院", "path": "学院与专业/应急通信与控制工程学院/index.html"},
            {"name": "应急装备学院", "path": "学院与专业/应急装备学院/index.html"},
            {"name": "应急经济与物资保障学院", "path": "学院与专业/应急经济与物资保障学院/index.html"},
            {"name": "应急国际交流学院", "path": "学院与专业/应急国际交流学院/index.html"},
            {"name": "应急救援训练中心", "path": "学院与专业/应急救援训练中心/index.html"},
            {"name": "应急文化传播与法学院", "path": "学院与专业/应急文化传播与法学院/index.html"},
            {"name": "理学院", "path": "学院与专业/理学院/index.html"},
            {"name": "防灾减灾工程学院", "path": "学院与专业/防灾减灾工程学院/index.html"},
        ]},
        {"name": "关于我们", "path": "关于我们/index.html"},
        {"name": "常用链接", "path": "常用链接/index.html", "children": [
            {"name": "校内组织", "path": "常用链接/校内组织.html"},
            {"name": "学长学姐博客", "path": "常用链接/学长学姐博客.html"},
            {"name": "友情链接", "path": "常用链接/友情链接.html"},
        ]},
    ]

    html = '<ul class="sidebar-nav">\n'

    for item in sidebar_structure:
        is_active = item['path'] == current_page
        has_children = 'children' in item
        active_class = ' active' if is_active else ''
        children_class = ' has-children' if has_children else ''

        html += f'<li class="sidebar-item{active_class}">\n'
        html += f'<a href="{relative_depth}{item["path"]}" class="sidebar-link{children_class}{active_class}">{item["name"]}</a>\n'

        if has_children:
            html += '<ul class="sidebar-children">\n'
            for child in item['children']:
                child_active = child['path'] == current_page
                child_active_class = ' active' if child_active else ''
                html += f'<li><a href="{relative_depth}{child["path"]}" class="sidebar-link{child_active_class}">{child["name"]}</a></li>\n'
            html += '</ul>\n'

        html += '</li>\n'

    html += '</ul>'
    return html


def generate_search_data(relative_depth='../'):
    """生成搜索数据；relative_depth 为当前页到 docs/ 的相对前缀"""
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
        p["url"] = relative_depth + p["path"]
        del p["path"]
    return json.dumps(pages, ensure_ascii=False, indent=2)


def calculate_relative_depth(md_path):
    """计算从MD文件到根目录的相对深度"""
    # 如果是相对路径，先转换为绝对路径
    if not md_path.is_absolute():
        md_path = BASE_DIR / md_path
    relative_path = md_path.relative_to(DOCS_DIR)
    depth = len(relative_path.parts) - 1
    return '../' * depth


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
    content_html = md_to_html(md_content)

    # 生成侧边栏
    relative_depth = calculate_relative_depth(md_path)
    current_page = md_path.relative_to(DOCS_DIR).as_posix()
    sidebar_html = generate_sidebar(current_page, relative_depth)

    # 生成搜索数据（按当前页深度生成相对 URL）
    search_data = generate_search_data(relative_depth)

    # 读取模板
    template = (TEMPLATES_DIR / 'base.html').read_text(encoding='utf-8')

    # 站点根相对当前页：docs/ 下深度 depth → 需再上一级到仓库根
    depth = len(md_path.relative_to(DOCS_DIR).parts) - 1
    base_url = '/'.join(['..'] * (depth + 1))

    # 替换变量
    html_output = template.replace('{{title}}', title)
    html_output = html_output.replace('{{content}}', content_html)
    html_output = html_output.replace('{{sidebar}}', sidebar_html)
    html_output = html_output.replace('{{search_data}}', search_data)
    html_output = html_output.replace('{{base_url}}', base_url)

    # 写入HTML文件
    html_path.write_text(html_output, encoding='utf-8')

    # 更新缓存
    update_cache(md_path)

    return True


def is_file_changed(file_path):
    """检查文件是否已改变（模板 base.html 变更会使所有页面失效）"""
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
        'timestamp': datetime.now().isoformat()
    }

    CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding='utf-8')


def sync_standalone_html():
    """重新生成没有同名 md 源的 html 页面（板块首页 index.html、学院与专业等历史页面）。

    这些页面无法由 build_html 构建，模板更新后它们会一直停留在旧版样式上。
    做法：保留页面自身的标题、侧边栏、搜索数据、正文，其余部分（CSS/JS/导航结构）
    全部用当前模板重新生成。
    """
    synced = 0
    for html_path in DOCS_DIR.rglob('*.html'):
        if html_path.with_suffix('.md').exists():
            continue
        old = html_path.read_text(encoding='utf-8')

        nav_open = '<nav class="wiki-sidebar" id="wikiSidebar">'
        title_m = re.search(r'<title>(.*?)</title>', old)
        sidebar_m = re.search(re.escape(nav_open) + r'\n(.*?)\s*</nav>', old, re.S)
        pages_m = re.search(r'const pages = (\[.*?\]);', old, re.S)
        brand_m = re.search(r'<a href="(.*?)/index.html" class="nav-brand">', old)
        content_open = old.find('<div class="markdown-section">')
        if not all([title_m, sidebar_m, pages_m, brand_m, content_open != -1]):
            print(f"  跳过 (无法解析, 需人工处理): {html_path}")
            continue
        anchor = old.find('twikoo-title', content_open)
        if anchor == -1:
            anchor = old.find('id="twikoo-comment"', content_open)
        content_close = old.rfind('</div>', 0, anchor) if anchor != -1 else old.rfind('</div>')
        if content_close == -1 or content_close <= content_open:
            print(f"  跳过 (无法定位正文, 需人工处理): {html_path}")
            continue
        content = old[content_open + len('<div class="markdown-section">'):content_close].strip()
        title = title_m.group(1)
        if title.endswith(' - 应大Wiki'):
            title = title[:-len(' - 应大Wiki')]

        template = (TEMPLATES_DIR / 'base.html').read_text(encoding='utf-8')
        html_output = template.replace('{{title}}', title)
        html_output = html_output.replace('{{content}}', content)
        html_output = html_output.replace('{{sidebar}}', sidebar_m.group(1))
        html_output = html_output.replace('{{search_data}}', pages_m.group(1))
        html_output = html_output.replace('{{base_url}}', brand_m.group(1))

        if html_output != old:
            html_path.write_text(html_output, encoding='utf-8')
            synced += 1
            print(f"  重同步: {html_path.relative_to(BASE_DIR)}")
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

    args = parser.parse_args()

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
