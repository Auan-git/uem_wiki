"""
应大Wiki MD转HTML构建脚本
用法:
  python build_wiki.py              # 构建所有文件
  python build_wiki.py --watch      # 监听文件变化
  python build_wiki.py docs/校园生活/恋爱.md  # 构建单个文件
"""

import os
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
    """将Markdown转换为HTML"""
    lines = md_content.split('\n')
    html_lines = []
    in_list = False
    in_ordered_list = False
    in_blockquote = False
    in_code_block = False
    code_content = []

    for line in lines:
        stripped = line.strip()

        # 代码块
        if stripped.startswith('```'):
            if in_code_block:
                html_lines.append('<pre><code>' + '\n'.join(code_content) + '</code></pre>')
                in_code_block = False
                code_content = []
            else:
                in_code_block = True
            continue

        if in_code_block:
            code_content.append(line)
            continue

        # 空行
        if not stripped:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            if in_ordered_list:
                html_lines.append('</ol>')
                in_ordered_list = False
            if in_blockquote:
                html_lines.append('</blockquote>')
                in_blockquote = False
            continue

        # 标题
        if stripped.startswith('#'):
            level = len(stripped) - len(stripped.lstrip('#'))
            text = stripped[level:].strip()
            html_lines.append(f'<h{level}>{text}</h{level}>')
            continue

        # 引用
        if stripped.startswith('>'):
            if not in_blockquote:
                html_lines.append('<blockquote>')
                in_blockquote = True
            text = stripped[1:].strip()
            html_lines.append(f'<p>{text}</p>')
            continue

        # 无序列表
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            text = stripped[2:].strip()
            html_lines.append(f'<li>{text}</li>')
            continue

        # 有序列表
        if len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in '.)' and stripped[2] == ' ':
            if not in_ordered_list:
                html_lines.append('<ol>')
                in_ordered_list = True
            text = stripped[3:].strip()
            html_lines.append(f'<li>{text}</li>')
            continue

        # 关闭列表
        if in_list and not stripped.startswith('- ') and not stripped.startswith('* '):
            html_lines.append('</ul>')
            in_list = False
        if in_ordered_list and not (len(stripped) > 2 and stripped[0].isdigit() and stripped[1] in '.)' and stripped[2] == ' '):
            html_lines.append('</ol>')
            in_ordered_list = False

        # 关闭引用
        if in_blockquote and not stripped.startswith('>'):
            html_lines.append('</blockquote>')
            in_blockquote = False

        # 水平线
        if stripped in ('---', '***', '___'):
            html_lines.append('<hr>')
            continue

        # 普通段落
        # 处理图片 ![alt](url)
        import re
        text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" style="max-width:100%;border-radius:4px;">', stripped)

        # 处理链接 [text](url)
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

        # 处理粗体和斜体
        text = text.replace('**', '<strong>', 1).replace('**', '</strong>', 1)
        text = text.replace('*', '<em>', 1).replace('*', '</em>', 1)

        # 处理行内代码
        if '`' in text:
            parts = text.split('`')
            text = ''
            for i, part in enumerate(parts):
                if i % 2 == 0:
                    text += part
                else:
                    text += f'<code>{part}</code>'

        html_lines.append(f'<p>{text}</p>')

    # 关闭未关闭的标签
    if in_list:
        html_lines.append('</ul>')
    if in_ordered_list:
        html_lines.append('</ol>')
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
            {"name": "奖学金", "path": "学分绩点/奖学金.html"},
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


def generate_search_data():
    """生成搜索数据"""
    # 定义页面列表
    pages = [
        {"url": "../学校概览/周边配套.html", "title": "周边配套", "desc": "学校概览 - 周边配套"},
        {"url": "../学校概览/学校简介.html", "title": "学校简介", "desc": "学校概览 - 学校简介"},
        {"url": "../学校概览/燕郊特色.html", "title": "燕郊特色", "desc": "学校概览 - 燕郊特色"},
        {"url": "../校园生活/体育课选择.html", "title": "体育课选择", "desc": "校园生活 - 体育课选择"},
        {"url": "../入学指南/军训须知.html", "title": "军训须知", "desc": "入学指南 - 军训须知"},
        {"url": "../入学指南/防骗指南.html", "title": "防骗指南", "desc": "入学指南 - 防骗指南"},
        {"url": "../入学指南/报到流程.html", "title": "报到流程", "desc": "入学指南 - 报到流程"},
        {"url": "../入学指南/来校路线.html", "title": "来校路线", "desc": "入学指南 - 来校路线"},
        {"url": "../选课指南/推荐课程.html", "title": "推荐课程", "desc": "选课指南 - 推荐课程"},
        {"url": "../选课指南/选课时间线.html", "title": "选课时间线", "desc": "选课指南 - 选课时间线"},
        {"url": "../选课指南/选课流程.html", "title": "选课流程", "desc": "选课指南 - 选课流程"},
        {"url": "../学分绩点/四六级.html", "title": "四六级", "desc": "学分绩点 - 四六级"},
        {"url": "../学分绩点/奖学金.html", "title": "奖学金", "desc": "学分绩点 - 奖学金"},
        {"url": "../学分绩点/学分要求.html", "title": "学分要求", "desc": "学分绩点 - 学分要求"},
        {"url": "../学分绩点/毕业条件.html", "title": "毕业条件", "desc": "学分绩点 - 毕业条件"},
        {"url": "../学分绩点/绩点计算.html", "title": "绩点计算", "desc": "学分绩点 - 绩点计算"},
        {"url": "../学分绩点/选修课.html", "title": "选修课", "desc": "学分绩点 - 选修课"},
        {"url": "../校园生活/体测要求.html", "title": "体测要求", "desc": "校园生活 - 体测要求"},
        {"url": "../校园生活/公交指南.html", "title": "公交指南", "desc": "校园生活 - 公交指南"},
        {"url": "../校园生活/地铁指南.html", "title": "地铁指南", "desc": "校园生活 - 地铁指南"},
        {"url": "../校园生活/学生组织.html", "title": "学生组织", "desc": "校园生活 - 学生组织"},
        {"url": "../校园生活/宿舍篇.html", "title": "宿舍篇", "desc": "校园生活 - 宿舍篇"},
        {"url": "../校园生活/常用电话.html", "title": "常用电话", "desc": "校园生活 - 常用电话"},
        {"url": "../校园生活/心理健康.html", "title": "心理健康", "desc": "校园生活 - 心理健康"},
        {"url": "../校园生活/校园地图.html", "title": "校园地图", "desc": "校园生活 - 校园地图"},
        {"url": "../校园生活/食堂篇.html", "title": "食堂篇", "desc": "校园生活 - 食堂篇"},
        {"url": "../校园生活/晚自习.html", "title": "晚自习", "desc": "校园生活 - 晚自习"},
        {"url": "../校园生活/准军事化管理.html", "title": "准军事化管理", "desc": "校园生活 - 准军事化管理"},
        {"url": "../校园生活/作息时间.html", "title": "作息时间", "desc": "校园生活 - 作息时间"},
        {"url": "../校园生活/校历.html", "title": "校历", "desc": "校园生活 - 校历"},
        {"url": "../校园生活/恋爱.html", "title": "恋爱", "desc": "校园生活 - 恋爱"},
        {"url": "../学院与专业/应急技术与指挥学院/index.html", "title": "应急技术与指挥学院", "desc": "应急技术与指挥学院专业介绍"},
        {"url": "../学院与专业/矿山安全学院/index.html", "title": "矿山安全学院", "desc": "矿山安全学院专业介绍"},
        {"url": "../学院与专业/城市安全学院/index.html", "title": "城市安全学院", "desc": "城市安全学院专业介绍"},
        {"url": "../学院与专业/地震工程与建筑安全学院/index.html", "title": "地震工程与建筑安全学院", "desc": "地震工程与建筑安全学院专业介绍"},
        {"url": "../学院与专业/地震科学与技术学院/index.html", "title": "地震科学与技术学院", "desc": "地震科学与技术学院专业介绍"},
        {"url": "../学院与专业/化工安全学院/index.html", "title": "化工安全学院", "desc": "化工安全学院专业介绍"},
        {"url": "../学院与专业/环境与灾害治理学院/index.html", "title": "环境与灾害治理学院", "desc": "环境与灾害治理学院专业介绍"},
        {"url": "../学院与专业/计算机与信息安全学院/index.html", "title": "计算机与信息安全学院", "desc": "计算机与信息安全学院专业介绍"},
        {"url": "../学院与专业/应急通信与控制工程学院/index.html", "title": "应急通信与控制工程学院", "desc": "应急通信与控制工程学院专业介绍"},
        {"url": "../学院与专业/应急装备学院/index.html", "title": "应急装备学院", "desc": "应急装备学院专业介绍"},
        {"url": "../学院与专业/应急经济与物资保障学院/index.html", "title": "应急经济与物资保障学院", "desc": "应急经济与物资保障学院专业介绍"},
        {"url": "../学院与专业/应急国际交流学院/index.html", "title": "应急国际交流学院", "desc": "应急国际交流学院专业介绍"},
        {"url": "../学院与专业/应急救援训练中心/index.html", "title": "应急救援训练中心", "desc": "应急救援训练中心专业介绍"},
        {"url": "../学院与专业/应急文化传播与法学院/index.html", "title": "应急文化传播与法学院", "desc": "应急文化传播与法学院专业介绍"},
        {"url": "../学院与专业/理学院/index.html", "title": "理学院", "desc": "理学院专业介绍"},
        {"url": "../学院与专业/防灾减灾工程学院/index.html", "title": "防灾减灾工程学院", "desc": "防灾减灾工程学院专业介绍"},
    ]

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

    # 生成搜索数据
    search_data = generate_search_data()

    # 读取模板
    template = (TEMPLATES_DIR / 'base.html').read_text(encoding='utf-8')

    # 替换变量
    html_output = template.replace('{{title}}', title)
    html_output = html_output.replace('{{content}}', content_html)
    html_output = html_output.replace('{{sidebar}}', sidebar_html)
    html_output = html_output.replace('{{search_data}}', search_data)
    html_output = html_output.replace('{{base_url}}', '.')

    # 写入HTML文件
    html_path.write_text(html_output, encoding='utf-8')

    # 更新缓存
    update_cache(md_path)

    return True


def is_file_changed(file_path):
    """检查文件是否已改变"""
    if not CACHE_FILE.exists():
        return True

    cache = json.loads(CACHE_FILE.read_text(encoding='utf-8'))
    file_key = str(file_path.relative_to(BASE_DIR))

    if file_key not in cache:
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
    cache[file_key] = {
        'hash': hashlib.md5(file_path.read_bytes()).hexdigest(),
        'timestamp': datetime.now().isoformat()
    }

    CACHE_FILE.write_text(json.dumps(cache, indent=2), encoding='utf-8')


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
