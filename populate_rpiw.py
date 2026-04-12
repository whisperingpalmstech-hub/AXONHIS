import json
import os

locales_dir = "frontend/src/i18n/locales"

translations = {
    "en": {
        "doctorWorkspace": "Doctor Workspace",
        "nurseWorkspace": "Nurse Workspace",
        "phlebotomistWorkspace": "Phlebotomist Workspace",
        "subtitle": "Role-Based Patient Interaction Workspace (RPIW)",
        "userId": "User ID",
        "department": "Department",
        "activeSession": "Active Session",
        "generalMedicine": "General Medicine",
        "online": "Online",
        "workflowsTitle": "Workflows",
        "permissionsTitle": "Permissions",
        "workflow": "Workflow",
        "activeWorkflowSubtitle": "Active clinical workflow panel",
        "route": "Route",
        "linkedPanelInfo": "This panel is linked to the {role} workspace module.",
        "syncInfo": "Ensuring live data synchronization with AxonHIS Core.",
        "welcomeTo": "Welcome to",
        "selectWorkflowToStart": "Select a workflow from the left panel to get started",
        "recentActivity": "Recent Activity",
        "noActivityRecord": "No activity recorded yet. Actions performed in the workspace will appear here.",
        "sessionStats": "Session Stats",
        "workflowsAvailable": "Workflows Available",
        "activePermissions": "Active Permissions",
        "uiComponents": "UI Components",
        "activityLogs": "Activity Logs",
        "rbacStatus": "RBAC Status",
        "accessControlActive": "Access Control Active",
        "auditLoggingEnabled": "Audit Logging Enabled",
        "encryptedSession": "Encrypted Session"
    },
    "hi": {
        "doctorWorkspace": "डॉक्टर कार्यक्षेत्र",
        "nurseWorkspace": "नर्स कार्यक्षेत्र",
        "phlebotomistWorkspace": "फलेबोटोमिस्ट कार्यक्षेत्र",
        "subtitle": "भूमिका-आधारित रोगी सहभागिता कार्यक्षेत्र (RPIW)",
        "userId": "उपयोगकर्ता आईडी",
        "department": "विभाग",
        "activeSession": "सक्रिय सत्र",
        "generalMedicine": "सामान्य चिकित्सा",
        "online": "ऑनलाइन",
        "workflowsTitle": "कार्यप्रवाह",
        "permissionsTitle": "अनुमतियाँ",
        "workflow": "कार्यप्रवाह",
        "activeWorkflowSubtitle": "सक्रिय नैदानिक कार्यप्रवाह पैनल",
        "route": "मार्ग",
        "linkedPanelInfo": "यह पैनल {role} कार्यक्षेत्र से जुड़ा है।",
        "syncInfo": "AxonHIS कोर के साथ लाइव डेटा सुनिश्चित करना।",
        "welcomeTo": "स्वागत है",
        "selectWorkflowToStart": "शुरू करने के लिए बाएं पैनल से एक चुनें",
        "recentActivity": "हाल की गतिविधि",
        "noActivityRecord": "कोई गतिविधि दर्ज नहीं की गई।",
        "sessionStats": "सत्र के आँकड़े",
        "workflowsAvailable": "उपलब्ध कार्यप्रवाह",
        "activePermissions": "सक्रिय अनुमतियाँ",
        "uiComponents": "यूआई अवयव",
        "activityLogs": "गतिविधि लॉग",
        "rbacStatus": "RBAC स्थिति",
        "accessControlActive": "पहुंच नियंत्रण सक्रिय",
        "auditLoggingEnabled": "ऑडिट लॉगिंग सक्षम",
        "encryptedSession": "एन्क्रिप्टेड सत्र"
    },
    "mr": {
        "doctorWorkspace": "डॉक्टर कार्यक्षेत्र",
        "nurseWorkspace": "नर्स कार्यक्षेत्र",
        "phlebotomistWorkspace": "फ्लेबोटोमिस्ट कार्यक्षेत्र",
        "subtitle": "भूमिका-आधारित रुग्ण संवाद कार्यक्षेत्र (RPIW)",
        "userId": "वापरकर्ता आयडी",
        "department": "विभाग",
        "activeSession": "सक्रिय सत्र",
        "generalMedicine": "सामान्य चिकित्सा",
        "online": "ऑनलाइन",
        "workflowsTitle": "कार्यप्रवाह",
        "permissionsTitle": "परवानग्या",
        "workflow": "कार्यप्रवाह",
        "activeWorkflowSubtitle": "सक्रिय वैद्यकीय कार्यप्रवाह पॅनेल",
        "route": "मार्ग",
        "linkedPanelInfo": "हे पॅनेल {role} कार्यक्षेत्राशी जोडलेले आहे.",
        "syncInfo": "AxonHIS कोरसह थेट डेटा सुनिश्चित करणे.",
        "welcomeTo": "स्वागत आहे",
        "selectWorkflowToStart": "सुरू करण्यासाठी डाव्या पॅनेलमधून निवडा",
        "recentActivity": "अलीकडील क्रियाकलाप",
        "noActivityRecord": "अद्याप कोणताही क्रियाकलाप नाही.",
        "sessionStats": "सत्र आकडेवारी",
        "workflowsAvailable": "उपलब्ध कार्यप्रवाह",
        "activePermissions": "सक्रिय परवानग्या",
        "uiComponents": "यूआय घटक",
        "activityLogs": "अॅक्टिव्हिटी लॉग",
        "rbacStatus": "RBAC स्थिती",
        "accessControlActive": "अॅक्सेस कंट्रोल सक्रिय",
        "auditLoggingEnabled": "ऑडिट लॉगिंग सुरू",
        "encryptedSession": "एन्क्रिप्टेड सत्र"
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
            
        data["rpiw"] = final_translations
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Updated rpiw {file_path}")
