import os
import re

def fix_overlap(html_content):
    # Fix markdown-section max-width to avoid overlap with TOC
    # Change from 860px to 620px and add margin-right
    html_content = re.sub(
        r'\.markdown-section\s*\{[^}]*max-width:\s*860px',
        '.markdown-section {\n  max-width: 620px; margin: 0; margin-left: 40px; margin-right: 240px',
        html_content
    )

    # Also fix the comment section if it has max-width: 780px
    html_content = re.sub(
        r'max-width:\s*780px',
        'max-width: 620px',
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

                updated_content = fix_overlap(content)

                if updated_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    print(f'Fixed: {file_path}')
            except Exception as e:
                print(f'Error processing {file_path}: {e}')

print('Done!')
