import json
import os
import time
import urllib.request
import urllib.parse

locales_dir = "frontend/src/i18n/locales"
en_path = os.path.join(locales_dir, "en.json")

# New explicit IPD keys
new_ipd_keys = {
    "inpatientDepartment": "Inpatient Department (IPD)",
    "ipdSubtitle": "Bed Board • Vitals Monitoring • Admission Requests",
    "admissionRequestsTab": "Admission Requests",
    "admHash": "Adm #",
    "bedAllocatedStr": "BED ALLOCATED",
    "generalWardStr": "GENERAL WARD",
    "assignedDr": "Assigned",
    "pendingDoctor": "Pending Doctor",
    "triageStandard": "Triage Standard",
    "priorityLabel": "Priority",
    "selectAvailableBedStar": "Select Available Bed *",
    "dropdownSyncedWithBedMatrix": "— Dropdown synced with Bed Matrix —"
}

lang_map = {
    "ar": "ar", "de": "de", "es": "es", "fr": "fr",
    "hi": "hi", "ja": "ja", "mr": "mr", "pt": "pt",
    "ru": "ru", "zh": "zh-CN"
}

prefixes = {
    "ar": "[AR] ", "de": "[DE] ", "es": "[ES] ", "fr": "[FR] ", 
    "hi": "[HI] ", "ja": "[JA] ", "mr": "[MR] ", "pt": "[PT] ", 
    "ru": "[RU] ", "zh": "[ZH] "
}

def translate(text, target_lang):
    if not text: return text
    url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(text)}&langpair=en|{target_lang}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read())
            if res.get("responseStatus") == 200:
                return res["responseData"]["translatedText"]
    except Exception as e:
        print("Error:", e)
    return text

def translate_system():
    with open(en_path, "r", encoding="utf-8") as f:
        en_data = json.load(f)

    if "ipd" not in en_data: en_data["ipd"] = {}
    for k, v in new_ipd_keys.items(): en_data["ipd"][k] = v
    with open(en_path, "w", encoding="utf-8") as f:
        json.dump(en_data, f, ensure_ascii=False, indent=2)

    for f_name in os.listdir(locales_dir):
        if f_name == "en.json" or not f_name.endswith(".json"): continue

        lang = f_name.replace(".json", "")
        if lang not in lang_map: continue
            
        target_lang = lang_map[lang]
        prefix = prefixes.get(lang, f"[{lang.upper()}] ")
        path = os.path.join(locales_dir, f_name)
        
        with open(path, "r", encoding="utf-8") as f: data = json.load(f)

        changed = False

        for module_name in ["ipd", "nav"]:
            if module_name not in en_data: continue
            module_dict = en_data[module_name]
            if module_name not in data or not isinstance(data[module_name], dict):
                data[module_name] = {}
            
            for key, val_en in module_dict.items():
                current_val = data[module_name].get(key, "")
                
                if not current_val or current_val.startswith(prefix) or current_val == val_en:
                    # Strip emojis safely
                    emoji_dict = {"🔴": "🔴", "🟠": "🟠", "🟡": "🟡", "🟢": "🟢", "🔵": "🔵"}
                    emoji_prefix = ""
                    clean_text = val_en
                    for em in emoji_dict.values():
                        if clean_text.startswith(em + " "):
                            emoji_prefix = em + " "
                            clean_text = clean_text.replace(em + " ", "")
                    
                    print(f"Translating {lang} -> '{clean_text}'")
                    ans = translate(clean_text, target_lang)
                    
                    if ans and ans != clean_text and "[MYMEMORY WARNING]" not in ans:
                        data[module_name][key] = emoji_prefix + ans
                        changed = True
                    else:
                        print("Failed/Unchanged")
                    time.sleep(0.3)

        if changed:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved {lang}.json")

if __name__ == "__main__":
    translate_system()
    print("Done generating true translations for IPD & NAV!")
