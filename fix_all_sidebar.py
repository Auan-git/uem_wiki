"""修复所有页面侧边栏，显示全部16个学院"""
from pathlib import Path
import re

BASE = Path(__file__).parent / 'docs'

COLLEGES = [
    "应急技术与指挥学院",
    "矿山安全学院",
    "城市安全学院",
    "地震工程与建筑安全学院",
    "地震科学与技术学院",
    "化工安全学院",
    "环境与灾害治理学院",
    "计算机与信息安全学院",
    "应急通信与控制工程学院",
    "应急装备学院",
    "应急经济与物资保障学院",
    "应急国际交流学院",
    "应急救援训练中心",
    "应急文化传播与法学院",
    "理学院",
    "防灾减灾工程学院",
]

def get_prefix(html_path):
    """根据文件位置计算路径前缀"""
    rel = html_path.relative_to(BASE)
    depth = len(rel.parts) - 1  # 排除文件名
    return '../' * depth

def build_college_list(prefix):
    """构建完整学院列表HTML"""
    lines = []
    for name in COLLEGES:
        lines.append(f'<li><a href="{prefix}学院与专业/{name}/index.html" class="sidebar-link">{name}</a></li>')
    return '\n'.join(lines)

def fix_file(html_path):
    text = html_path.read_text(encoding='utf-8')
    prefix = get_prefix(html_path)

    # 匹配学院与专业的sidebar区块
    pattern = r'(<li class="sidebar-item[^"]*">\s*<a href="[^"]*学院与专业/index\.html"[^>]*>.*?</a>\s*<ul class="sidebar-children">)(.*?)(</ul>\s*</li>)'

    def replacer(m):
        open_tag = m.group(1)
        close_tag = m.group(3)
        college_list = build_college_list(prefix)
        return open_tag + '\n' + college_list + '\n' + close_tag

    new_text = re.sub(pattern, replacer, text, flags=re.DOTALL)

    if new_text != text:
        html_path.write_text(new_text, encoding='utf-8')
        return True
    return False

count = 0
for html_file in sorted(BASE.rglob('*.html')):
    try:
        if fix_file(html_file):
            count += 1
            print(f'  OK {html_file.relative_to(BASE)}')
    except Exception as e:
        print(f'  ERR {html_file.relative_to(BASE)}: {e}')

print(f'\nDone! Fixed {count} files.')
