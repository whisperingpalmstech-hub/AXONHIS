import json
import os

locales_dir = "frontend/src/i18n/locales"

zone_dict_en = {
    "zoneResuscitation": "Resuscitation",
    "zoneAcuteCare": "Acute Care",
    "zoneFastTrack": "Fast Track",
    "zonePediatrics": "Pediatrics",
    "zoneObservation": "Observation"
}

hi_dict = {
    "emergencyDepartment": "आपातकालीन विभाग",
    "totalActive": "कुल सक्रिय",
    "critical": "गंभीर",
    "awaitingTriage": "ट्राइएज की प्रतीक्षा",
    "bedsAvailable": "उपलब्ध बेड",
    "mlcCases": "एमएलसी केस",
    "zoneOccupancy": "क्षेत्र अधिभोग",
    "commandCenter": "कमांड सेंटर",
    "patientList": "रोगी सूची",
    "triageQueue": "ट्राइएज कतार",
    "bedMap": "बेड मैप",
    "mlcCasesTab": "एमएलसी मामले",
    "seedBeds": "बेड सेटअप करें",
    "registerErPatient": "ईआर रोगी पंजीकरण",
    "digitalCommandCenter": "डिजिटल कमांड सेंटर • ट्राइएज • बेड मैप • एमएलसी",
    "erPatientFlow": "ईआर रोगी प्रवाह",
    "reg": "पंजीकरण",
    "triageEsi": "ट्राइएज (ईएसआई)",
    "bedAssign": "बेड आवंटन",
    "tx": "इलाज",
    "disposition": "निपटान",
    "dischargeAdmit": "डिस्चार्ज/प्रवेश",
    # Zones
    "zoneResuscitation": "पुनर्जीवन",
    "zoneAcuteCare": "तीव्र देखभाल",
    "zoneFastTrack": "फास्ट ट्रैक",
    "zonePediatrics": "बाल रोग",
    "zoneObservation": "अवलोकन",
    # OT Module
    "operatingTheatre": "ऑपरेशन थियेटर (OT)",
    "surgeonCommandCenter": "सर्जन कमांड सेंटर",
    "otSubtitle": "सर्जरी अनुसूची • ओटी स्थिति",
    "constructOtRooms": "ओटी कमरे बनाएँ",
    "scheduleSurgery": "सर्जरी निर्धारित करें",
    "checkingOt": "ओटी उपलब्धता की जांच कर रहा है...",
    "totalRooms": "कुल कमरे",
    "available": "उपलब्ध",
    "todaysSurgeries": "आज की सर्जरी",
    "inProgress": "प्रगति पर",
    "completed": "पूरा हुआ"
}

mr_dict = {
    "emergencyDepartment": "आपत्कालीन विभाग",
    "totalActive": "एकूण सक्रिय",
    "critical": "गंभीर",
    "awaitingTriage": "ट्रायेजची प्रतीक्षा",
    "bedsAvailable": "उपलब्ध बेड्स",
    "mlcCases": "एमएलसी केसेस",
    "zoneOccupancy": "झोन व्याप्ती",
    "commandCenter": "कमांड सेंटर",
    "patientList": "रुग्ण यादी",
    "triageQueue": "ट्रायेज रांग",
    "bedMap": "बेड नकाशा",
    "mlcCasesTab": "एमएलसी केसेस",
    "seedBeds": "बेड सेटअप करा",
    "registerErPatient": "ईआर रुग्ण नोंदणी",
    # Zones
    "zoneResuscitation": "पुनरुज्जीवन",
    "zoneAcuteCare": "त्वरित काळजी",
    "zoneFastTrack": "फास्ट ट्रॅक",
    "zonePediatrics": "बालरोग",
    "zoneObservation": "निरीक्षण",
    # OT Module
    "operatingTheatre": "ऑपरेशन थिएटर (OT)",
    "surgeonCommandCenter": "सर्जन कमांड सेंटर",
    "otSubtitle": "शस्त्रक्रिया वेळापत्रक • ओटी स्थिती",
    "constructOtRooms": "ओटी खोल्या तयार करा",
    "scheduleSurgery": "शस्त्रक्रिया निश्चित करा",
    "totalRooms": "एकूण खोल्या",
    "available": "उपलब्ध",
    "todaysSurgeries": "आजच्या शस्त्रक्रिया",
    "inProgress": "प्रगतीवर",
    "completed": "पूर्ण झाले"
}

prefixes = {
    "hi": "[HI] ", "mr": "[MR] ", "ar": "[AR] ", "es": "[ES] ", "fr": "[FR] ", "pt": "[PT] ",
    "de": "[DE] ", "ru": "[RU] ", "zh": "[ZH] ", "ja": "[JA] "
}

en_path = os.path.join(locales_dir, "en.json")
with open(en_path, "r", encoding="utf-8") as f:
    en_data = json.load(f)

# Inject zones to EN first
if "er" not in en_data:
    en_data["er"] = {}
for k, v in zone_dict_en.items():
    en_data["er"][k] = v

with open(en_path, "w", encoding="utf-8") as f:
    json.dump(en_data, f, ensure_ascii=False, indent=2)

for f_name in os.listdir(locales_dir):
    if f_name == "en.json" or not f_name.endswith(".json"):
        continue

    lang = f_name.replace(".json", "")
    prefix = prefixes.get(lang, f"[{lang.upper()}] ")
    path = os.path.join(locales_dir, f_name)
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for module_name, module_dict in en_data.items():
        if module_name not in data or not isinstance(data[module_name], dict):
            data[module_name] = {}
        
        if isinstance(module_dict, dict):
            for key, val_en in module_dict.items():
                if key not in data[module_name]:
                    if lang == "hi" and key in hi_dict:
                        data[module_name][key] = hi_dict[key]
                    elif lang == "mr" and key in mr_dict:
                        data[module_name][key] = mr_dict[key]
                    else:
                        data[module_name][key] = prefix + val_en
                else:
                    current_val = data[module_name][key]
                    if lang == "hi" and key in hi_dict and current_val.startswith("[HI]"):
                         data[module_name][key] = hi_dict[key]
                    elif lang == "mr" and key in mr_dict and current_val.startswith("[MR]"):
                         data[module_name][key] = mr_dict[key]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

print("Synchronized all strings natively and applied translations across locales!")
