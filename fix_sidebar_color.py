"""修改侧边栏和按钮背景色为 #002f82"""
from pathlib import Path
import re

BASE = Path(__file__).parent / 'docs'

REPLACEMENTS = [
    # wiki-sidebar 背景
    ('background: var(--paper-dark);', 'background: #002f82;'),
    # sidebar-title 边框和文字
    ('border-bottom: 1px solid var(--border);\n      margin-bottom: 8px;', 'border-bottom: 1px solid rgba(255,255,255,0.2);\n      margin-bottom: 8px;'),
    # 返回顶部按钮
    ('.back-to-top {\n      position: fixed;\n      bottom: 30px;\n      right: 30px;\n      width: 44px;\n      height: 44px;\n      border-radius: 50%;\n      background: var(--ink);',
     '.back-to-top {\n      position: fixed;\n      bottom: 30px;\n      right: 30px;\n      width: 44px;\n      height: 44px;\n      border-radius: 50%;\n      background: #002f82;'),
    # toc-toggle 按钮
    ('background: var(--ink);\n      color: var(--paper);\n      border: none;\n      font-size: 20px;\n      cursor: pointer;\n      z-index: 200;',
     'background: #002f82;\n      color: var(--paper);\n      border: none;\n      font-size: 20px;\n      cursor: pointer;\n      z-index: 200;'),
]

def fix_file(html_path):
    text = html_path.read_text(encoding='utf-8')
    original = text

    # 替换 wiki-sidebar 背景
    text = re.sub(
        r'(\.wiki-sidebar\s*\{[^}]*background:\s*)var\(--paper-dark\)',
        r'\1#002f82',
        text, flags=re.DOTALL
    )

    # 替换 sidebar-title border
    text = re.sub(
        r'(border-bottom:\s*1px solid\s*)var\(--border\);(\s*\n\s*margin-bottom:\s*8px;)',
        r'\1rgba(255,255,255,0.2);\2',
        text
    )

    # 替换 sidebar-link 相关颜色
    text = re.sub(
        r'(\.sidebar-link\s*\{[^}]*color:\s*)var\(--ink-light\)(\s*!important)',
        r'\1rgba(255,255,255,0.8)\2',
        text, flags=re.DOTALL
    )
    text = re.sub(
        r'(\.sidebar-link:hover\s*\{[^}]*background:\s*)var\(--paper-edge\)',
        r'\1rgba(255,255,255,0.1)',
        text, flags=re.DOTALL
    )
    text = re.sub(
        r'(\.sidebar-link:hover\s*\{[^}]*color:\s*)var\(--ink\)(\s*!important)',
        r'\1#fff\2',
        text, flags=re.DOTALL
    )
    text = re.sub(
        r'(\.sidebar-link:hover\s*\{[^}]*border-left-color:\s*)var\(--ink-faint\)',
        r'\1rgba(255,255,255,0.5)',
        text, flags=re.DOTALL
    )

    # sidebar-link.has-children
    text = re.sub(
        r'(\.sidebar-link\.has-children\s*\{[^}]*color:\s*)var\(--ink\)(\s*!important)',
        r'\1#fff\2',
        text, flags=re.DOTALL
    )

    # sidebar-link.has-children.active
    text = re.sub(
        r'(\.sidebar-link\.has-children\.active\s*\{[^}]*color:\s*)var\(--vermilion\)(\s*!important)',
        r'\1#ffd700\2',
        text, flags=re.DOTALL
    )
    text = re.sub(
        r'(\.sidebar-link\.has-children\.active\s*\{[^}]*border-left-color:\s*)var\(--vermilion\)',
        r'\1#ffd700',
        text, flags=re.DOTALL
    )
    text = re.sub(
        r'(\.sidebar-link\.has-children\.active\s*\{[^}]*background:\s*)rgba\(194,\s*54,\s*22,\s*0\.05\)',
        r'\1rgba(255, 215, 0, 0.1)',
        text, flags=re.DOTALL
    )

    # sidebar-children .sidebar-link
    text = re.sub(
        r'(\.sidebar-children \.sidebar-link\s*\{[^}]*color:\s*)var\(--ink-faint\)(\s*!important)',
        r'\1rgba(255,255,255,0.65)\2',
        text, flags=re.DOTALL
    )
    text = re.sub(
        r'(\.sidebar-children \.sidebar-link:hover\s*\{[^}]*color:\s*)var\(--ink\)(\s*!important)',
        r'\1#fff\2',
        text, flags=re.DOTALL
    )

    # sidebar-children border
    text = re.sub(
        r'(\.sidebar-children\s*\{[^}]*border-left:\s*1px solid\s*)var\(--border\)',
        r'\1rgba(255,255,255,0.2)',
        text, flags=re.DOTALL
    )

    # back-to-top 按钮背景
    text = re.sub(
        r'(\.back-to-top\s*\{[^}]*background:\s*)var\(--ink\)',
        r'\1#002f82',
        text, flags=re.DOTALL
    )
    text = re.sub(
        r'(\.back-to-top:hover\s*\{[^}]*background:\s*)var\(--vermilion\)',
        r'\1#0040b3',
        text, flags=re.DOTALL
    )

    # toc-toggle 按钮背景
    text = re.sub(
        r'(\.toc-toggle\s*\{[^}]*background:\s*)var\(--ink\)',
        r'\1#002f82',
        text, flags=re.DOTALL
    )

    # 移动端 wiki-sidebar
    text = re.sub(
        r'(\.wiki-sidebar\s*\{[^}]*box-shadow:\s*none;)(\s*\}\s*\n\s*\.wiki-sidebar\.open)',
        r'\1 background: #002f82;\2',
        text, flags=re.DOTALL
    )

    if text != original:
        html_path.write_text(text, encoding='utf-8')
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

print(f'\nDone! Updated {count} files.')
