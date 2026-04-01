import os
import json
import re

sidebar_file = "frontend/src/components/ui/Sidebar.tsx"
locales_dir = "frontend/src/i18n/locales"

# The missing mappings we are adding
missing_mappings = {
    "RPIW Workspace": "nav.rpiwWorkspace",
    "Tasks": "nav.tasks",
    "Orders": "nav.clinicalOrders",
    "Visitor & MLC": "nav.visitorMlc",
    "Sample Receiving": "nav.sampleReceiving",
    "Analyzer Hub": "nav.analyzerHub",
    "Report Handover": "nav.reportHandover",
    "Advanced Diagnostics": "nav.advancedDiagnostics",
    "Extended Lab Services": "nav.extendedLab",
    "Rx Worklist": "nav.rxWorklist",
    "IP Medication Issue": "nav.ipMedicationIssue",
    "Returns": "nav.pharmacyReturns",
    "IP Returns": "nav.ipPharmacyReturns",
    "Narcotics Vault": "nav.narcoticsVault",
    "Inventory Intelligence": "nav.inventoryIntelligence",
    "Organizations (SaaS)": "nav.organizations",
    "Core System": "nav.coreSystem",
    "Communication": "nav.communication",
    "BI Intelligence": "nav.biIntelligence",
    "AI Platform": "nav.aiPlatform"
}

# The english display names for the missing strings
english_values = {
    "rpiwWorkspace": "RPIW Workspace",
    "tasks": "Tasks",
    "clinicalOrders": "Orders",
    "visitorMlc": "Visitor & MLC",
    "sampleReceiving": "Sample Receiving",
    "analyzerHub": "Analyzer Hub",
    "reportHandover": "Report Handover",
    "advancedDiagnostics": "Advanced Diagnostics",
    "extendedLab": "Extended Lab Services",
    "rxWorklist": "Rx Worklist",
    "ipMedicationIssue": "IP Medication Issue",
    "pharmacyReturns": "Returns",
    "ipPharmacyReturns": "IP Returns",
    "narcoticsVault": "Narcotics Vault",
    "inventoryIntelligence": "Inventory Intelligence",
    "organizations": "Organizations (SaaS)",
    "coreSystem": "Core System",
    "communication": "Communication",
    "biIntelligence": "BI Intelligence",
    "aiPlatform": "AI Platform"
}

hindi_values = {
    "rpiwWorkspace": "आरपीआईडब्ल्यू कार्यक्षेत्र (RPIW)",
    "tasks": "कार्य",
    "clinicalOrders": "आदेश (Orders)",
    "visitorMlc": "आगंतुक और एमएलसी",
    "sampleReceiving": "नमूना प्राप्ति",
    "analyzerHub": "एनालाइजर हब",
    "reportHandover": "रिपोर्ट सौंपना",
    "advancedDiagnostics": "उन्नत निदान",
    "extendedLab": "विस्तारित लैब",
    "rxWorklist": "आरएक्स वर्कलिस्ट",
    "ipMedicationIssue": "आईपीडी दवा जारी",
    "pharmacyReturns": "दवा वापसी",
    "ipPharmacyReturns": "आईपीडी वापसी",
    "narcoticsVault": "नारकोटिक्स वॉल्ट",
    "inventoryIntelligence": "इन्वेंटरी इंटेलिजेंस",
    "organizations": "संस्थान (SaaS)",
    "coreSystem": "कोर सिस्टम",
    "communication": "संचार",
    "biIntelligence": "बीआई इंटेलिजेंस",
    "aiPlatform": "एआई प्लेटफॉर्म"
}

marathi_values = {
    "rpiwWorkspace": "आरपीआयडब्ल्यू कार्यक्षेत्र (RPIW)",
    "tasks": "कार्ये",
    "clinicalOrders": "ऑर्डर्स",
    "visitorMlc": "भेट देणारे आणि एमएलसी",
    "sampleReceiving": "नमुना प्राप्ती",
    "analyzerHub": "अ‍ॅनालायझर हब",
    "reportHandover": "रिपोर्ट हस्तांतरण",
    "advancedDiagnostics": "प्रगत निदान",
    "extendedLab": "विस्तारित लॅब",
    "rxWorklist": "आरएक्स वर्कलिस्ट",
    "ipMedicationIssue": "आयपीडी औषध वाटप",
    "pharmacyReturns": "फार्मसी परतावा",
    "ipPharmacyReturns": "आयपीडी परतावा",
    "narcoticsVault": "नार्कोटिक्स वॉल्ट",
    "inventoryIntelligence": "इन्व्हेंटरी इंटेलिजन्स",
    "organizations": "संस्था (SaaS)",
    "coreSystem": "कोर सिस्टम",
    "communication": "संवाद",
    "biIntelligence": "बीआय इंटेलिजन्स",
    "aiPlatform": "एआय प्लॅटफॉर्म"
}

# 1. Update Sidebar.tsx
with open(sidebar_file, "r", encoding="utf-8") as f:
    sidebar_code = f.read()

# Find the end of LABEL_I18N_MAP
match = re.search(r'const LABEL_I18N_MAP: Record<string, string> = {([\s\S]*?)};', sidebar_code)
if match:
    existing_map = match.group(1)
    
    # Add new mappings if they don't exist
    new_map_entries = []
    for k, v in missing_mappings.items():
        if f'"{k}"' not in existing_map:
            new_map_entries.append(f'  "{k}": "{v}",')
    
    if new_map_entries:
        insert_text = "\n" + "\n".join(new_map_entries) + "\n"
        sidebar_code = sidebar_code.replace(match.group(0), f'const LABEL_I18N_MAP: Record<string, string> = {{{existing_map}{insert_text}}};')
        
        with open(sidebar_file, "w", encoding="utf-8") as f:
            f.write(sidebar_code)
        print("Updated Sidebar.tsx LABEL_I18N_MAP.")


# 2. Update all locale JSON files
for file_name in os.listdir(locales_dir):
    if not file_name.endswith(".json"): continue
    
    lang_code = file_name.split(".")[0]
    file_path = os.path.join(locales_dir, file_name)
    
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue
    
    if "nav" not in data:
        data["nav"] = {}
        
    for key, en_val in english_values.items():
        if key not in data["nav"]:
            if lang_code == "en":
                data["nav"][key] = en_val
            elif lang_code == "hi" and key in hindi_values:
                data["nav"][key] = hindi_values[key]
            elif lang_code == "mr" and key in marathi_values:
                data["nav"][key] = marathi_values[key]
            else:
                data["nav"][key] = en_val  # Fallback to english
                
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"Updated {file_name}")

