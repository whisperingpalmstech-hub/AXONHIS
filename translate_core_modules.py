import os
import re
import json

TARGET_FILES = [
    "frontend/src/app/dashboard/opd-visits/page.tsx",
    "frontend/src/app/dashboard/er/page.tsx",
    "frontend/src/app/dashboard/pharmacy/page.tsx",
    "frontend/src/app/dashboard/lab/page.tsx",
    "frontend/src/app/dashboard/billing/page.tsx",
    "frontend/src/app/dashboard/tasks/page.tsx",
    "frontend/src/app/dashboard/orders/page.tsx",
    "frontend/src/app/dashboard/encounters/page.tsx",
    "frontend/src/app/dashboard/ipd/page.tsx",
    "frontend/src/app/dashboard/wards/page.tsx",
]

EN_JSON_PATH = "frontend/src/i18n/locales/en.json"

def to_camel_case(text):
    s = re.sub(r'[^a-zA-Z0-9]', ' ', text).strip()
    parts = s.split()
    if not parts:
        return ""
    return parts[0].lower() + ''.join(p.capitalize() for p in parts[1:])

def load_en_json():
    with open(EN_JSON_PATH, "r") as f:
        return json.load(f)

def save_en_json(data):
    with open(EN_JSON_PATH, "w") as f:
        json.dump(data, f, indent=2)

def process_file(filepath, en_data):
    if not os.path.exists(filepath):
        return False

    with open(filepath, "r") as f:
        content = f.read()

    # Determine namespace
    module_name = filepath.split("/")[-2]
    module_name = to_camel_case(module_name)
    
    if module_name not in en_data:
        en_data[module_name] = {}

    modified = False

    # Regex targeting EXACTLY: >Something< or > Something < but NOT containing '{' or '}' or '<' or '>'
    # It must contain at least one word character.
    pattern = re.compile(r'>\s*([A-Z][a-zA-Z0-9\s,\.\-&!/\(\)\[\]]+?)\s*<')

    def replace_match(match):
        nonlocal modified
        text = match.group(1).strip()

        if not text or len(text) < 2 or "var(--" in text or "{" in text or "}" in text:
            return match.group(0)

        # Skip code-like words
        if text in ["return", "import", "from", "const", "let", "function", "export", "default"]:
            return match.group(0)

        key = to_camel_case(text)
        if len(key) > 30:
            key = key[:30]
        if not key:
            return match.group(0)

        en_data[module_name][key] = text
        modified = True
        return f'>{{t("{module_name}.{key}")}}<'

    new_content = pattern.sub(replace_match, content)

    # Inject useTranslation
    if modified and 'useTranslation' not in new_content:
        # Add import statement
        if '"use client";' in new_content:
            new_content = new_content.replace('"use client";', '"use client";\nimport { useTranslation } from "@/i18n";', 1)
        
        # Add const { t } = useTranslation();
        component_match = re.search(r'(export default function [a-zA-Z0-9_]+\([^\)]*\)\s*\{)', new_content)
        if component_match:
            insertion_point = component_match.end()
            new_content = new_content[:insertion_point] + '\n  const { t } = useTranslation();' + new_content[insertion_point:]

    if modified:
        with open(filepath, "w") as f:
            f.write(new_content)
            
    return modified

def main():
    os.chdir("/home/sujeetnew/Downloads/AXONHIS")
    en_data = load_en_json()
    files_processed = 0

    for f in TARGET_FILES:
        if process_file(f, en_data):
            files_processed += 1

    save_en_json(en_data)
    print(f"Processed {files_processed} core modules successfully.")

if __name__ == "__main__":
    main()
