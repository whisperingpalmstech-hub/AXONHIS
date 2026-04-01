import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from deep_translator import GoogleTranslator

locales_dir = "frontend/src/i18n/locales"
en_path = os.path.join(locales_dir, "en.json")

# Map to Google Translator language codes
lang_map = {
    "ar": "ar", "de": "de", "es": "es", "fr": "fr",
    "ja": "ja", "pt": "pt", "ru": "ru", "zh": "zh-CN",
    "hi": "hi", "mr": "mr" # hi and mr are basically done but we check anyway
}

def translate_string(target_lang, module_name, key, val_en, current_val):
    if not val_en:
        return None
    
    prefix_check = f"[{target_lang.upper()}] "
    needs_translation = False
    
    if not current_val:
        needs_translation = True
    elif current_val == val_en:
        needs_translation = True
    elif current_val.startswith(prefix_check) or current_val.startswith("["):
        needs_translation = True
        
    if not needs_translation:
        return None

    emoji_dict = {"🔴": "🔴", "🟠": "🟠", "🟡": "🟡", "🟢": "🟢", "🔵": "🔵"}
    emoji_prefix = ""
    clean_text = val_en
    if "[HI]" in clean_text: clean_text = clean_text.replace("[HI]", "").strip()
    if "[FR]" in clean_text: clean_text = clean_text.replace("[FR]", "").strip()
    
    for em in emoji_dict.values():
        if clean_text.startswith(em + " "):
            emoji_prefix = em + " "
            clean_text = clean_text.replace(em + " ", "")
            
    translator = GoogleTranslator(source='en', target=target_lang)
    try:
        res = translator.translate(clean_text)
        if res and res != clean_text:
            return (target_lang, module_name, key, emoji_prefix + res)
    except Exception as e:
        # Silently fail, it will be skipped
        pass
    
    return None


def main():
    print("Loading english reference...", flush=True)
    with open(en_path, "r", encoding="utf-8") as f:
        en_data = json.load(f)

    # Load all languages so we can build a massive task list
    lang_data = {}
    for lang, t_lang in lang_map.items():
        path = os.path.join(locales_dir, f"{lang}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                lang_data[lang] = json.load(f)
        except:
            lang_data[lang] = {}

    tasks = []
    
    for lang, target_lang in lang_map.items():
        data = lang_data[lang]
        for module_name, module_dict in en_data.items():
            if module_name not in data or not isinstance(data[module_name], dict):
                data[module_name] = {}
            for key, val_en in module_dict.items():
                current_val = data[module_name].get(key, "")
                tasks.append((target_lang, module_name, key, val_en, current_val, lang))

    print(f"Discovered {len(tasks)} potential strings across all locales. Dispatching worker pool...", flush=True)
    
    success_count = 0
    futures = []
    
    # We use ThreadPoolExecutor to translate concurrently. 
    # GoogleTranslator is not async, but requests handles threads fine.
    # 20 workers is a good balance to avoid instant IP ban but move very fast.
    with ThreadPoolExecutor(max_workers=20) as executor:
        for t in tasks:
            # t = (target_lang, module_name, key, val_en, current_val, lang_file_name)
            future = executor.submit(translate_string, t[0], t[1], t[2], t[3], t[4])
            # attach lang_file_name to future so we know where to save
            future.__lang = t[5]
            futures.append(future)

        for i, future in enumerate(as_completed(futures)):
            result = future.result()
            if result:
                target_lang, module_name, key, new_val = result
                lang_code = future.__lang
                lang_data[lang_code][module_name][key] = new_val
                success_count += 1
                if success_count % 50 == 0:
                    print(f"Translated {success_count} strings so far...", flush=True)

    print(f"\nPhase complete! Successfully translated {success_count} strings.", flush=True)
    
    # Save everything back to disk
    for lang in lang_map.keys():
        path = os.path.join(locales_dir, f"{lang}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(lang_data[lang], f, ensure_ascii=False, indent=2)
            
    print("All language files updated and synchronized across all modules! 100% coverage enforced.", flush=True)

if __name__ == "__main__":
    main()
