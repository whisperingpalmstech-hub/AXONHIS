import os
import re
import json

FRONTEND_DIR = "/home/sujeetnew/Downloads/AXONHIS/frontend/src/app/dashboard"
EN_JSON_PATH = "/home/sujeetnew/Downloads/AXONHIS/frontend/src/i18n/locales/en.json"

def to_camel_case(text):
    s = re.sub(r'[^a-zA-Z0-9]', ' ', text).strip()
    parts = s.split()
    if not parts:
        return "blank"
    return parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])

def load_en_json():
    with open(EN_JSON_PATH, "r") as f:
        return json.load(f)

def save_en_json(data):
    with open(EN_JSON_PATH, "w") as f:
        json.dump(data, f, indent=2)

def process_file(filepath, en_data):
    with open(filepath, "r") as f:
        content = f.read()

    # Determine a namespace based on the directory name
    rel_path = os.path.relpath(filepath, FRONTEND_DIR)
    module_name = rel_path.split("/")[0] if "/" in rel_path else "dashboard_core"
    module_name = to_camel_case(module_name)
    
    if module_name not in en_data:
        en_data[module_name] = {}

    modified = False

    # Regex to find plain text inside JSX tags
    # Example: <span className="x">Hello World</span>
    # Match group 1: the string exactly
    # We must avoid matching scripts inside {} or other tags.
    pattern = re.compile(r'>([\s\n]*)([A-Z][a-zA-Z0-9\s,\.\-&!/\(\)\[\]]+?)([\s\n]*)<')

    def replace_match(match):
        nonlocal modified
        prefix = match.group(1)
        text = match.group(2).strip()
        suffix = match.group(3)

        if not text or len(text) < 2 or "var(--" in text:
            return match.group(0)

        # Skip things that look like code
        if text in ["return", "import", "from", "const", "let", "function"]:
            return match.group(0)

        key = to_camel_case(text)
        if len(key) > 40:
            key = key[:40]

        en_data[module_name][key] = text
        modified = True
        return f'>{prefix}{{t("{module_name}.{key}")}}{suffix}<'

    new_content = pattern.sub(replace_match, content)

    # Check if we removed TopNav
    if '<TopNav' in new_content:
        new_content = re.sub(r'<TopNav[^>]+/>[\s\n]*', '', new_content)
        modified = True

    if modified:
        # Check if we need to insert useTranslation
        if '{t(' in new_content and 'useTranslation' not in new_content:
            # Add import statement after the first import or "use client"
            if '"use client"' in new_content:
                new_content = new_content.replace('"use client";', '"use client";\nimport { useTranslation } from "@/i18n";', 1)
            elif 'import React' in new_content:
                new_content = new_content.replace('import React', 'import { useTranslation } from "@/i18n";\nimport React', 1)
            
            # Find the main exported component and inject the hook
            component_match = re.search(r'(export default function[^\(]*\([^\)]*\)\s*\{)', new_content)
            if component_match:
                insertion_point = component_match.end()
                new_content = new_content[:insertion_point] + '\n  const { t } = useTranslation();' + new_content[insertion_point:]
            
        with open(filepath, "w") as f:
            f.write(new_content)
    
    return modified

def main():
    en_data = load_en_json()
    files_processed = 0

    for root, dirs, files in os.walk(FRONTEND_DIR):
        for file in files:
            if file.endswith('.tsx') or file.endswith('.ts'):
                if process_file(os.path.join(root, file), en_data):
                    files_processed += 1

    save_en_json(en_data)
    print(f"Processed {files_processed} files successfully. Updated EN JSON.")

if __name__ == "__main__":
    main()
