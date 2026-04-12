import json
import os

locales_dir = "frontend/src/i18n/locales"

# These are the expected modules (namespaces) in the translation files based on en.json
en_path = os.path.join(locales_dir, "en.json")
with open(en_path, "r", encoding="utf-8") as f:
    en_data = json.load(f)

# Collect all keys defined in en.json
expected_keys = {} # dict of module -> set of keys
for module, keys in en_data.items():
    expected_keys[module] = set(keys.keys())

def validate_locales():
    all_good = True
    print("\n[i18n Validator] Scanning Locales for Missing Translations...\n")
    for f_name in sorted(os.listdir(locales_dir)):
        if f_name == "en.json" or not f_name.endswith(".json"): continue
        
        lang = f_name.replace(".json", "")
        path = os.path.join(locales_dir, f_name)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        missing = 0
        for module, keys in expected_keys.items():
            if module not in data:
                print(f"[{lang}] Missing Module: {module}")
                missing += len(keys)
                all_good = False
                continue
            
            for key in keys:
                val = data[module].get(key, "")
                if not val or val == en_data[module].get(key, "") or val.startswith("["):
                    print(f"[{lang}] Missing localized key: {module}.{key}")
                    missing += 1
                    all_good = False
                    
        if missing > 0:
            print(f"-> {lang.upper()} is missing {missing} translations.\n")
        else:
            print(f"-> {lang.upper()} is 100% compliant.\n")

    if all_good:
        print("[SUCCESS] All languages have 100% translation coverage!\n")
    else:
        print("[WARNING] Translation gaps detected.\n")

if __name__ == "__main__":
    validate_locales()
