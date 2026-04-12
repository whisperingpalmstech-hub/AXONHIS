import json
import os
import time
from deep_translator import GoogleTranslator

locales_dir = "frontend/src/i18n/locales"

# Map to Google Translator language codes
lang_map = {
    "ar": "ar", "de": "de", "es": "es", "fr": "fr",
    "hi": "hi", "ja": "ja", "mr": "mr", "pt": "pt",
    "ru": "ru", "zh": "zh-CN"
}

en_path = os.path.join(locales_dir, "en.json")
with open(en_path, "r", encoding="utf-8") as f:
    en_data = json.load(f)

for f_name in os.listdir(locales_dir):
    if f_name == "en.json" or not f_name.endswith(".json"): continue
    
    lang = f_name.replace(".json", "")
    if lang not in lang_map: continue
        
    target_lang = lang_map[lang]
    path = os.path.join(locales_dir, f_name)
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    prefix_check = f"[{lang.upper()}] "
    translator = GoogleTranslator(source='en', target=target_lang)
    
    changes = 0
    print(f"--- Processing Language: {lang} ---")

    for module_name, module_dict in en_data.items():
        if module_name not in data or not isinstance(data[module_name], dict):
            data[module_name] = {}
            
        for key, val_en in module_dict.items():
            if not val_en: continue
            
            current_val = data[module_name].get(key, "")
            
            # Identify if the string needs translation
            needs_translation = False
            if not current_val:
                needs_translation = True
            elif current_val == val_en:
                 # It's verbatim English
                 needs_translation = True
            elif current_val.startswith(prefix_check) or current_val.startswith("["):
                 # It has the placeholder prefix
                 needs_translation = True
                 
            if needs_translation:
                # Remove emojis for translation stability
                emoji_dict = {"🔴": "🔴", "🟠": "🟠", "🟡": "🟡", "🟢": "🟢", "🔵": "🔵"}
                emoji_prefix = ""
                clean_text = val_en
                # Check for standard prefixes
                if "[HI]" in clean_text: clean_text = clean_text.replace("[HI]", "").strip()
                if "[FR]" in clean_text: clean_text = clean_text.replace("[FR]", "").strip()
                
                for em in emoji_dict.values():
                    if clean_text.startswith(em + " "):
                        emoji_prefix = em + " "
                        clean_text = clean_text.replace(em + " ", "")
                        
                try:
                    res = translator.translate(clean_text)
                    if res and res != clean_text:
                        data[module_name][key] = emoji_prefix + res
                        changes += 1
                        if changes % 10 == 0:
                            print(f"{lang} translated {changes} strings...")
                except Exception as e:
                    print(f"Error on {clean_text}: {e}")
                    time.sleep(1) # Backoff

    if changes > 0:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"-> Successfully saved {changes} new translations to {lang}.json\n")
    else:
        print(f"-> {lang} is already up to date.\n")

print("Massive Translation Phase Complete!")
