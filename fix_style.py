import os
import re

def fix_style(html_content):
    # Remove markdown-section::after decorative circle
    html_content = re.sub(
        r'\.markdown-section::after\s*\{[^}]*\}',
        '',
        html_content
    )

    # Fix comment section margin
    html_content = re.sub(
        r'max-width:\s*620px;\s*margin:\s*60px\s*auto\s*0',
        'max-width: 620px; margin: 60px 0 0 20px',
        html_content
    )

    # Remove > :last-child::after decorative dots
    html_content = re.sub(
        r'\.markdown-section\s*>\s*:last-child::after\s*\{[^}]*\}',
        '',
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

                updated_content = fix_style(content)

                if updated_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    print(f'Fixed: {file_path}')
            except Exception as e:
                print(f'Error processing {file_path}: {e}')

print('Done!')
