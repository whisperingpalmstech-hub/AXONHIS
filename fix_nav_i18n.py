import json
import os
import re

locales_dir = "frontend/src/i18n/locales"

nav_translations = {
    "en": {"encounters": "Encounters", "orders": "Orders", "doctorDesk": "Doctor Desk", "appointments": "Appointments", "clinicalOps": "Clinical Operations"},
    "hi": {"encounters": "मुलाकातें", "orders": "आदेश", "doctorDesk": "डॉक्टर डेस्क", "appointments": "नियुक्तियाँ", "clinicalOps": "नैदानिक ​​संचालन"},
    "mr": {"encounters": "भेटी", "orders": "आदेश", "doctorDesk": "डॉक्टर डेस्क", "appointments": "भेटीची वेळ", "clinicalOps": "क्लिनिकल ऑपरेशन्स"},
}

for f in os.listdir(locales_dir):
    if f.endswith(".json"):
        path = os.path.join(locales_dir, f)
        
        # We need to clean up potential duplicate string keys the safe way:
        # We will parse with json, which keeps the last key. Since the objects were 
        # ADDED AFTER the strings in our past scripts, json.load will correctly load the dict 
        # instead of the string!
        # Then, if we just json.dump it back out, it will naturally clean up the duplicate string keys!
        
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
                
            lang = f.split(".")[0]
            t_data = nav_translations.get(lang, nav_translations["en"])
            
            if "nav" not in data:
                data["nav"] = {}
                
            for k, v in t_data.items():
                if k not in data["nav"]:
                    data["nav"][k] = v
                    
            with open(path, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            print(f"Cleaned and restored {f}")
        except Exception as e:
            print(f"Error processing {f}: {e}")
