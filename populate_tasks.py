import json
import os

locales_dir = "frontend/src/i18n/locales"

translations = {
    "en": {
        "searchPlaceholder": "Search tasks by patient or description...",
        "allStatuses": "All Statuses",
        "allRoles": "All Roles",
        "nurseRole": "Nurse",
        "labtechRole": "Lab Tech",
        "radiologytechRole": "Radiology Tech",
        "pharmacistRole": "Pharmacist",
        "doctorRole": "Doctor",
        "anyRole": "Any",
        "allCaughtUp": "All Caught Up!",
        "noActiveTasksAssigned": "You have no active tasks assigned to you right now.",
        "noTasksFoundQueue": "No tasks found in the queue matching your filters.",
        "patient": "Patient",
        "role": "Role",
        "created": "Created",
        "due": "Due",
        "recurring": "Recurring",
        "everyXMins": "Every {x} mins",
        "completedByUser": "Completed by user",
        "cancelledStatusMsg": "Cancelled",
        "executionNotesPlaceholder": "e.g., Patient tolerated procedure well. Sample collected from left arm.",
        "confirmCompletion": "Confirm Completion",
        "status_PENDING": "Pending",
        "status_ASSIGNED": "Assigned",
        "status_IN_PROGRESS": "In Progress",
        "status_COMPLETED": "Completed",
        "status_CANCELLED": "Cancelled",
        "type_COLLECT_SPECIMEN": "Sample Collection",
        "type_PROCESS_LAB_TEST": "Lab Processing",
        "type_DISPENSE_MEDICATION": "Dispense Med",
        "type_ADMINISTER_MEDICATION": "Administer Med",
        "type_PERFORM_IMAGING": "Imaging Prep",
        "type_PERFORM_PROCEDURE": "Procedure Assist",
        "type_VITAL_MONITORING": "Vitals",
        "type_NURSING_ASSESSMENT": "Nursing",
        "type_PREPARE_DISCHARGE": "Discharge",
        "type_GENERIC": "General Task"
    },
    "hi": {
        "searchPlaceholder": "रोगी या विवरण द्वारा कार्य खोजें...",
        "allStatuses": "सभी स्थितियां",
        "allRoles": "सभी भूमिकाएं",
        "nurseRole": "नर्स",
        "labtechRole": "लैब टेक",
        "radiologytechRole": "रेडियोलॉजी टेक",
        "pharmacistRole": "फार्मासिस्ट",
        "doctorRole": "डॉक्टर",
        "anyRole": "कोई भी",
        "allCaughtUp": "सभी कार्य पूर्ण!",
        "noActiveTasksAssigned": "अभी आपके पास कोई सक्रिय कार्य नहीं है।",
        "noTasksFoundQueue": "आपके फ़िल्टर से मेल खाने वाले कतार में कोई कार्य नहीं मिला।",
        "patient": "मरीज",
        "role": "भूमिका",
        "created": "निर्मित",
        "due": "देय",
        "recurring": "आवर्ती",
        "everyXMins": "हर {x} मिनट",
        "completedByUser": "उपयोगकर्ता द्वारा पूरा किया गया",
        "cancelledStatusMsg": "रद्द",
        "executionNotesPlaceholder": "उदाहरण: रोगी ने प्रक्रिया को अच्छी तरह सहन किया। बाएं हाथ से नमूना एकत्र किया गया।",
        "confirmCompletion": "पूर्णता की पुष्टि करें",
        "status_PENDING": "लंबित",
        "status_ASSIGNED": "सौंपा गया",
        "status_IN_PROGRESS": "प्रगति में",
        "status_COMPLETED": "पूरा हो गया",
        "status_CANCELLED": "रद्द",
        "type_COLLECT_SPECIMEN": "नमूना संग्रह",
        "type_PROCESS_LAB_TEST": "लैब प्रसंस्करण",
        "type_DISPENSE_MEDICATION": "दवा वितरण",
        "type_ADMINISTER_MEDICATION": "दवा प्रशासन",
        "type_PERFORM_IMAGING": "इमेजिंग तैयारी",
        "type_PERFORM_PROCEDURE": "प्रक्रिया सहायता",
        "type_VITAL_MONITORING": "नब्ज",
        "type_NURSING_ASSESSMENT": "नर्सिंग",
        "type_PREPARE_DISCHARGE": "छुट्टी",
        "type_GENERIC": "सामान्य कार्य"
    },
    "mr": {
        "searchPlaceholder": "रुग्ण किंवा वर्णनानुसार कार्ये शोधा...",
        "allStatuses": "सर्व स्थिती",
        "allRoles": "सर्व भूमिका",
        "nurseRole": "परिचारिका",
        "labtechRole": "लॅब टेक",
        "radiologytechRole": "रेडिओलॉजी टेक",
        "pharmacistRole": "फार्मासिस्ट",
        "doctorRole": "डॉक्टर",
        "anyRole": "कोणतेही",
        "allCaughtUp": "सर्व कार्ये पूर्ण!",
        "noActiveTasksAssigned": "सध्या तुमच्याकडे कोणतेही सक्रिय कार्य नाही.",
        "noTasksFoundQueue": "तुमच्या फिल्टरशी जुळणारी रांगेत कोणतीही कार्ये आढळली नाहीत.",
        "patient": "रुग्ण",
        "role": "भूमिका",
        "created": "तयार केले",
        "due": "देय",
        "recurring": "आवर्ती",
        "everyXMins": "दर {x} मिनिटे",
        "completedByUser": "वापरकर्त्याद्वारे पूर्ण केले",
        "cancelledStatusMsg": "रद्द केले",
        "executionNotesPlaceholder": "उदा., रुग्णाने प्रक्रियेस चांगला प्रतिसाद दिला. डाव्या हातातून नमुना गोळा केला.",
        "confirmCompletion": "पूर्णतेची पुष्टी करा",
        "status_PENDING": "प्रलंबित",
        "status_ASSIGNED": "नियुक्त केले",
        "status_IN_PROGRESS": "प्रगतीपथावर",
        "status_COMPLETED": "पूर्ण झाले",
        "status_CANCELLED": "रद्द",
        "type_COLLECT_SPECIMEN": "नमुना संकलन",
        "type_PROCESS_LAB_TEST": "लॅब प्रक्रिया",
        "type_DISPENSE_MEDICATION": "औषध वितरण",
        "type_ADMINISTER_MEDICATION": "औषध प्रशासन",
        "type_PERFORM_IMAGING": "इमेजिंग तयारी",
        "type_PERFORM_PROCEDURE": "प्रक्रिया सहाय्य",
        "type_VITAL_MONITORING": "महत्त्वाची लक्षणे",
        "type_NURSING_ASSESSMENT": "नर्सिंग",
        "type_PREPARE_DISCHARGE": "डिस्चार्ज",
        "type_GENERIC": "सामान्य कार्य"
    }
}

for lang_code in ['en', 'hi', 'mr', 'ar', 'es', 'fr', 'pt', 'de', 'ru', 'zh', 'ja']:
    file_path = os.path.join(locales_dir, f"{lang_code}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except:
                data = {}
        
        final_translations = translations["en"].copy()
        if lang_code in translations:
            final_translations.update(translations[lang_code])
            
        if "tasks" not in data:
            data["tasks"] = {}
        
        data["tasks"].update(final_translations)
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Updated tasks in {file_path}")
