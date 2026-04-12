import os
import re

locales_dir = "frontend/src/i18n/locales"

for f in os.listdir(locales_dir):
    if f.endswith(".json"):
        path = os.path.join(locales_dir, f)
        with open(path, "r", encoding="utf-8") as file:
            content = file.read()
        
        # We need to remove precisely lines that look like:
        # "encounters": "encounters",
        # "encounters": "मुलाकातें",
        # without removing "encounters": {
        
        # Regular expression breakdown:
        # ^\s*                     = start of line + whitespace
        # "encounters"             = the exact key
        # \s*:\s*                  = colon with optional whitespace
        # ".*"                     = any string (not an object)
        # ,?                       = optional comma
        # \s*$                     = optional whitespace + end of line
        
        new_content = re.sub(r'^\s*"encounters"\s*:\s*"[^"]*"\s*,?\s*$', '', content, flags=re.MULTILINE)
        
        if new_content != content:
            with open(path, "w", encoding="utf-8") as file:
                file.write(new_content)
            print(f"Fixed duplicate string in {f}")
        else:
            print(f"No match in {f}")
