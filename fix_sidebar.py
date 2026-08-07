import os
import re

COLLEGES = [
    "应急技术与指挥学院", "矿山安全学院", "地震科学与技术学院",
    "城市安全学院", "防灾减灾工程学院", "化工安全学院",
    "环境与灾害治理学院", "地震工程与建筑安全学院", "应急装备学院",
    "应急通信与控制工程学院", "计算机与信息安全学院", "应急经济与物资保障学院",
    "应急文化传播与法学院", "应急国际交流学院", "应急救援训练中心", "理学院"
]

def make_college_sidebar(prefix):
    items = '\n'.join(f'<li><a href="{prefix}学院与专业/{c}/index.html" class="sidebar-link">{c}</a></li>' for c in COLLEGES)
    return f'''<li class="sidebar-item">
<a href="{prefix}学院与专业/index.html" class="sidebar-link has-children">学院与专业</a>
<ul class="sidebar-children">
{items}
</ul>
</li>'''

def fix_sidebar(html_content, file_path):
    # Determine prefix based on file depth
    rel = os.path.relpath(file_path, 'docs').replace('\\', '/')
    depth = rel.count('/')
    prefix = '../' * depth if depth > 0 else '../'

    new_sidebar = make_college_sidebar(prefix)

    # Find the start of the 学院与专业 sidebar section
    # Look for the pattern: <li class="sidebar-item..."> followed by a link to 学院与专业
    start_pattern = r'<li class="sidebar-item(?:\s+active)?">\s*<a href="[^"]*学院与专业/index\.html"[^>]*>学院与专业</a>'
    start_match = re.search(start_pattern, html_content)

    if not start_match:
        return False

    # Find the end of the section by counting nested ul/li tags
    start_pos = start_match.start()
    depth = 0
    pos = start_pos
    found_first_ul = False

    while pos < len(html_content):
        if html_content[pos:pos+3] == '<ul':
            depth += 1
            found_first_ul = True
        elif html_content[pos:pos+5] == '</ul>':
            depth -= 1
            if found_first_ul and depth == 0:
                # Find the closing </li>
                end_li = html_content.find('</li>', pos)
                if end_li != -1:
                    end_pos = end_li + 5
                    html_content = html_content[:start_pos] + new_sidebar + html_content[end_pos:]
                    return True
                break
        pos += 1

    return False

# Process all HTML files
docs_dir = 'docs'
updated = 0
for root, dirs, files in os.walk(docs_dir):
    for file in files:
        if file.endswith('.html'):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                if fix_sidebar(content, file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    updated += 1
                    print(f'Updated: {file_path}')
            except Exception as e:
                print(f'Error: {file_path}: {e}')

print(f'\nDone! Updated {updated} files.')
