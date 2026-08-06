import os
import re

def fix_margin(html_content):
    # Fix markdown-section margin
    html_content = re.sub(
        r'\.markdown-section\s*\{[^}]*margin:\s*0;\s*margin-left:\s*40px;\s*margin-right:\s*240px;\s*margin:\s*0\s*auto;',
        '.markdown-section {\n  max-width: 620px; margin: 0; margin-left: 20px; margin-right: 240px;',
        html_content
    )

    # Also fix comment section margin
    html_content = re.sub(
        r'max-width:\s*620px;\s*margin:\s*60px\s*0\s*0\s*40px',
        'max-width: 620px; margin: 60px 0 0 20px',
        html_content
    )

    return html_content

# Process all HTML files in docs
docs_dir = 'docs'
for root, dirs, files in os.walk(docs_dir):
    for file in files:
        if file.endswith('.html'):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                updated_content = fix_margin(content)

                if updated_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    print(f'Fixed: {file_path}')
            except Exception as e:
                print(f'Error processing {file_path}: {e}')

print('Done!')
