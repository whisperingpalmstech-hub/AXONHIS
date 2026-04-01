import json
import os

locales_dir = "frontend/src/i18n/locales"

# These are the ones missed in OT dict
hi_dict_ot = {
  "time": "समय",
  "patient": "मरीज",
  "surgery": "सर्जरी",
  "surgeon": "सर्जन",
  "room": "कमरा",
  "status": "स्थिति",
  "dailySurgicalSchedule": "दैनिक सर्जिकल अनुसूची",
  "otAvailabilityMatrix": "ओटी उपलब्धता मैट्रिक्स",
  "noSurgeries": "आज किसी सर्जरी की योजना नहीं है।",
  "noOtRooms": "कोई ओटी कमरे कॉन्फ़िगर नहीं किए गए हैं।",
  "laminarFlow": "लैमिनर फ्लो",
  "cArmEq": "सी-आर्म",
  "laserSuite": "लेजर सुइट",
  "blockOt": "ऑपरेटिंग थिएटर ब्लॉक करें",
  "selectLivePatient": "मरीज चुनें *",
  "corePatientRegistry": "— मुख्य रोगी रजिस्ट्री —",
  "selectOtRoom": "ओटी कमरा चुनें *",
  "availableSuites": "— उपलब्ध सुइट्स —",
  "primarySurgeon": "प्राथमिक सर्जन *",
  "egDrHouse": "उदा. डॉ. शर्मा",
  "surgeryProcedure": "सर्जरी प्रक्रिया *",
  "egAppendectomy": "उदा. अपेंडेक्टोमी",
  "cancel": "रद्द करें",
  "commitToBoard": "बोर्ड में प्रतिबद्ध करें",
  "surgeryScheduledSuccessfully": "सर्जरी सफलतापूर्वक निर्धारित",
  "scheduleError": "सर्जरी निर्धारित करने में विफल।",
  "seedRoomsError": "कमरे सेटअप करने में विफल।"
}

mr_dict_ot = {
  "time": "वेळ",
  "patient": "रुग्ण",
  "surgery": "शस्त्रक्रिया",
  "surgeon": "सर्जन",
  "room": "खोली",
  "status": "स्थिती",
  "dailySurgicalSchedule": "दैनिक सर्जिकल वेळापत्रक",
  "otAvailabilityMatrix": "ओटी उपलब्धता मॅट्रिक्स",
  "noSurgeries": "आज कोणत्याही शस्त्रक्रियेचे नियोजन नाही.",
  "noOtRooms": "कोणत्याही ओटी खोल्या कॉन्फिगर केलेल्या नाहीत.",
  "laminarFlow": "लॅमिनर प्रवाह",
  "cArmEq": "सी-आर्म",
  "laserSuite": "लेझर सूट",
  "blockOt": "ऑपरेटिंग थिएटर ब्लॉक करा",
  "selectLivePatient": "रुग्ण निवडा *",
  "corePatientRegistry": "— मुख्य रुग्ण नोंदणी —",
  "selectOtRoom": "ओटी खोली निवडा *",
  "availableSuites": "— उपलब्ध सूट्स —",
  "primarySurgeon": "प्राथमिक सर्जन *",
  "egDrHouse": "उदा. डॉ. जोशी",
  "surgeryProcedure": "शस्त्रक्रिया प्रक्रिया *",
  "egAppendectomy": "उदा. अपेंडेक्टोमी",
  "cancel": "रद्द करा",
  "commitToBoard": "बोर्डला सबमिट करा",
  "surgeryScheduledSuccessfully": "शस्त्रक्रिया यशस्वीरित्या निश्चित",
  "scheduleError": "शस्त्रक्रिया निश्चित करण्यात अयशस्वी.",
  "seedRoomsError": "खोल्या स्थापित करण्यात अयशस्वी."
}

for lang, locale_dict in [("hi", hi_dict_ot), ("mr", mr_dict_ot)]:
    path = os.path.join(locales_dir, f"{lang}.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if "ot" in data:
            for k, v in locale_dict.items():
                data["ot"][k] = v
                
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

print("OT table translations for HI/MR seamlessly applied.")
