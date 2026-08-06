import os
import re

def fix_comment(html_content):
    # Fix comment section inline style
    html_content = re.sub(
        r'<div style="max-width:\s*620px;margin:0\s*auto;padding:0\s*20px;">',
        '<div style="max-width: 620px; margin: 60px 0 0 20px; padding: 0;">',
        html_content
    )

    return html_content

# Process only 学院与专业 files
docs_dir = 'docs/学院与专业'
for root, dirs, files in os.walk(docs_dir):
    for file in files:
        if file.endswith('.html'):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                updated_content = fix_comment(content)

                if updated_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    print(f'Fixed: {file_path}')
            except Exception as e:
                print(f'Error processing {file_path}: {e}')

print('Done!')
