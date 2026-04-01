import json
import os
import time
import urllib.request
import urllib.parse
import re

locales_dir = "frontend/src/i18n/locales"

# These are the target namespaces
targets = ["ipd", "nav"]

lang_map = {
    "ar": "ar", "de": "de", "es": "es", "fr": "fr",
    "hi": "hi", "ja": "ja", "mr": "mr", "pt": "pt",
    "ru": "ru", "zh": "zh-CN"
}

def translate_fast(text, target_lang):
    if not text: return text
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl={target_lang}&dt=t&q={urllib.parse.quote(text)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            res = json.loads(response.read())
            # Google free API returns [[["translated text", "original text", ...]]]
            ans = "".join([i[0] for i in res[0]])
            return ans
    except Exception as e:
        print("Error translating:", text, e)
    return text

def translate_system():
    en_path = os.path.join(locales_dir, "en.json")
    with open(en_path, "r", encoding="utf-8") as f:
        en_data = json.load(f)

    for f_name in os.listdir(locales_dir):
        if f_name == "en.json" or not f_name.endswith(".json"): continue

        lang = f_name.replace(".json", "")
        if lang not in lang_map: continue
            
        target_lang = lang_map[lang]
        path = os.path.join(locales_dir, f_name)
        
        with open(path, "r", encoding="utf-8") as f: data = json.load(f)

        changed = False

        for module_name in targets:
            if module_name not in en_data: continue
            module_dict = en_data[module_name]
            if module_name not in data or not isinstance(data[module_name], dict):
                data[module_name] = {}
            
            for key, val_en in module_dict.items():
                current_val = data[module_name].get(key, "")
                
                # Check if it lacks a real translation (same as English or has [LANG] prefix)
                if not current_val or current_val == val_en or current_val.startswith("["):
                    # We won't re-translate Hindi or Marathi if they are already native, but checking equality or bracket is enough.
                    # Since Hindi/Marathi are already done natively, their value won't be == val_en, it will skip!
                    
                    # Strip emojis safely for API
                    emoji_dict = {"🔴": "🔴", "🟠": "🟠", "🟡": "🟡", "🟢": "🟢", "🔵": "🔵"}
                    emoji_prefix = ""
                    clean_text = val_en
                    for em in emoji_dict.values():
                        if clean_text.startswith(em + " "):
                            emoji_prefix = em + " "
                            clean_text = clean_text.replace(em + " ", "")
                    
                    ans = translate_fast(clean_text, target_lang)
                    
                    if ans and ans != clean_text:
                        data[module_name][key] = emoji_prefix + ans
                        changed = True

        if changed:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved {lang}.json")

if __name__ == "__main__":
    translate_system()
    print("Done generating ultra-fast translations for IPD & NAV!")
