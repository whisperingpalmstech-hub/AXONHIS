import json
import os

locales_dir = "frontend/src/i18n/locales"

# Exact translation maps for Hindi
hi_map = {
    "ipdManagement": "आईपीडी प्रबंधन",
    "ipdAdmissions": "आईपीडी प्रवेश",
    "ipdDoctorDesk": "आईपीडी डॉक्टर डेस्क",
    "ipdNursing": "आईपीडी नर्सिंग",
    "ipdBilling": "आईपीडी बिलिंग",
    "ipdTransfers": "आईपीडी स्थानांतरण",
    "ipdDischarge": "आईपीडी डिस्चार्ज",
    "wardsAndBeds": "वार्ड और बेड",
    "title": "आईपीडी प्रबंधन",
    "admissions": "आईपीडी प्रवेश",
    "pendingRequests": "लंबित अनुरोध",
    "admittedPatients": "भर्ती रोगी",
    "admissionRequest": "प्रवेश अनुरोध",
    "allocateBed": "बेड आवंटित करें",
    "patientName": "रोगी का नाम",
    "admittingDoctor": "भर्ती डॉक्टर",
    "treatingDoctor": "इलाज करने वाले डॉक्टर",
    "specialty": "विशेषज्ञता",
    "reasonForAdmission": "प्रवेश का कारण",
    "admissionCategory": "प्रवेश श्रेणी",
    "admissionSource": "प्रवेश स्रोत",
    "clinicalNotes": "नैदानिक नोट्स",
    "bedCategory": "पसंदीदा बेड श्रेणी",
    "admissionNumber": "प्रवेश संख्या",
    "ward": "वार्ड",
    "bed": "बेड",
    "diagnosis": "निदान",
    "treatmentPlan": "उपचार योजना",
    "progressNotes": "प्रगति नोट्स",
    "vitals": "महत्वपूर्ण लक्षण",
    "nursingNotes": "नर्सिंग नोट्स",
    "discharge": "रिहाई",
    "transfer": "स्थानांतरण",
    "smartWardsCentralNursing": "स्मार्ट वार्ड और सेंट्रल नर्सिंग",
    "refreshTelemetry": "टेलीमेट्री रीफ्रेश करें",
    "connectingToWardStations": "वार्ड स्टेशनों से कनेक्ट हो रहा है...",
    "activeAdmissions": "सक्रिय प्रवेश",
    "currentlyAccommodated": "वर्तमान में समायोजित",
    "awaitingErOpdClearance": "ईआर/ओपीडी मंजूरी की प्रतीक्षा",
    "icuOccupancy": "आईसीयू अधिभोग",
    "criticalCareBeds": "गहन चिकित्सा बेड",
    "dischargesToday": "आज की रिहाई",
    "clearedByBilling": "बिलिंग द्वारा मंजूरी",
    "activeWardCensus": "सक्रिय वार्ड जनगणना",
    "patient": "रोगी",
    "wardBed": "वार्ड / बेड",
    "attendingDoctor": "उपस्थित डॉक्टर",
    "status": "स्थिति",
    "action": "कार्रवाई",
    "noActiveAdmissionsCurrentlyTra": "वर्तमान में कोई सक्रिय प्रवेश ट्रैक नहीं हो रहा है।",
    "stable": "स्थिर",
    "nursingFlowsheet": "नर्सिंग फ्लोशीट",
    "requestTime": "अनुरोध समय",
    "priority": "प्राथमिकता",
    "diagnosisNotes": "निदान / नोट्स",
    "noPendingAdmissionRequestsFrom": "ओपीडी/ईआर से कोई लंबित प्रवेश अनुरोध नहीं।",
    "allocateWardBed": "वार्ड बेड आवंटित करें",
    "gen101GeneralMaleWard": "GEN-101 (सामान्य पुरुष वार्ड)",
    "gen102GeneralMaleWard": "GEN-102 (सामान्य पुरुष वार्ड)",
    "icu01IntensiveCare": "ICU-01 (गहन चिकित्सा)",
    "pvt205PrivateRoomSuite": "PVT-205 (निजी कमरा सुइट)",
    "cancel": "रद्द करें",
    "confirmAllocation": "आवंटन की पुष्टि करें",
    "inpatientDepartment": "इनपेशेंट विभाग (आईपीडी)",
    "ipdSubtitle": "बेड बोर्ड • महत्वपूर्ण लक्षण निगरानी • प्रवेश अनुरोध",
    "admissionRequestsTab": "प्रवेश अनुरोध",
    "admHash": "प्रवेश #",
    "bedAllocatedStr": "बेड आवंटित",
    "generalWardStr": "सामान्य वार्ड",
    "assignedDr": "नियुक्त",
    "pendingDoctor": "लंबित डॉक्टर",
    "triageStandard": "मानक ट्राइएज",
    "priorityLabel": "प्राथमिकता",
    "selectAvailableBedStar": "उपलब्ध बेड चुनें *",
    "dropdownSyncedWithBedMatrix": "— बेड मैट्रिक्स के साथ समन्वयित —"
}

# Exact translation maps for Marathi
mr_map = {
    "ipdManagement": "आयपीडी व्यवस्थापन",
    "ipdAdmissions": "आयपीडी प्रवेश",
    "ipdDoctorDesk": "आयपीडी डॉक्टर डेस्क",
    "ipdNursing": "आयपीडी नर्सिंग",
    "ipdBilling": "आयपीडी बिलिंग",
    "ipdTransfers": "आयपीडी बदल्या",
    "ipdDischarge": "आयपीडी डिस्चार्ज",
    "wardsAndBeds": "वॉर्ड आणि बेड्स",
    "title": "आयपीडी व्यवस्थापन",
    "admissions": "आयपीडी प्रवेश",
    "pendingRequests": "प्रलंबित विनंत्या",
    "admittedPatients": "दाखल झालेले रुग्ण",
    "admissionRequest": "प्रवेशाची विनंती",
    "allocateBed": "बेड वाटप करा",
    "patientName": "रुग्णाचे नाव",
    "admittingDoctor": "दाखल करणारे डॉक्टर",
    "treatingDoctor": "उपचार करणारे डॉक्टर",
    "specialty": "वैशिष्ट्य",
    "reasonForAdmission": "प्रवेशाचे कारण",
    "admissionCategory": "प्रवेश श्रेणी",
    "admissionSource": "प्रवेश स्रोत",
    "clinicalNotes": "क्लिनिकल नोट्स",
    "bedCategory": "पसंतीची बेड श्रेणी",
    "admissionNumber": "प्रवेश क्रमांक",
    "ward": "वॉर्ड",
    "bed": "बेड",
    "diagnosis": "निदान",
    "treatmentPlan": "उपचार योजना",
    "progressNotes": "प्रगती नोट्स",
    "vitals": "महत्त्वाची लक्षणे",
    "nursingNotes": "नर्सिंग नोट्स",
    "discharge": "डिस्चार्ज",
    "transfer": "बदली",
    "smartWardsCentralNursing": "स्मार्ट वॉर्ड आणि सेंट्रल नर्सिंग",
    "refreshTelemetry": "टेलीमेट्री रिफ्रेश करा",
    "connectingToWardStations": "वॉर्ड स्टेशनशी कनेक्ट होत आहे...",
    "activeAdmissions": "सक्रिय प्रवेश",
    "currentlyAccommodated": "सध्या सामावून घेतलेले",
    "awaitingErOpdClearance": "ईआर/ओपीडी मंजुरीची प्रतीक्षा",
    "icuOccupancy": "आयसीयू व्याप्ती",
    "criticalCareBeds": "अतिदक्षता बेड्स",
    "dischargesToday": "आजचे डिस्चार्ज",
    "clearedByBilling": "बिलिंगने मंजूर केले",
    "activeWardCensus": "सक्रिय वॉर्ड जनगणना",
    "patient": "रुग्ण",
    "wardBed": "वॉर्ड / बेड",
    "attendingDoctor": "उपस्थित डॉक्टर",
    "status": "स्थिती",
    "action": "कृती",
    "noActiveAdmissionsCurrentlyTra": "सध्या कोणताही सक्रिय प्रवेश ट्रॅक होत नाही.",
    "stable": "स्थिर",
    "nursingFlowsheet": "नर्सिंग फ्लोशीट",
    "requestTime": "विनंतीची वेळ",
    "priority": "प्राधान्य",
    "diagnosisNotes": "निदान / नोट्स",
    "noPendingAdmissionRequestsFrom": "ओपीडी/ईआर कडून कोणतीही प्रलंबित विनंती नाही.",
    "allocateWardBed": "वॉर्ड बेड वाटप करा",
    "gen101GeneralMaleWard": "GEN-101 (सामान्य पुरुष वॉर्ड)",
    "gen102GeneralMaleWard": "GEN-102 (सामान्य पुरुष वॉर्ड)",
    "icu01IntensiveCare": "ICU-01 (अतिदक्षता विभाग)",
    "pvt205PrivateRoomSuite": "PVT-205 (खासगी खोली)",
    "cancel": "रद्द करा",
    "confirmAllocation": "वाटपाची पुष्टी करा",
    "inpatientDepartment": "इनपॅशंट विभाग (आयपीडी)",
    "ipdSubtitle": "बेड बोर्ड • महत्त्वाची लक्षणे देखरेख • प्रवेश विनंत्या",
    "admissionRequestsTab": "प्रवेश विनंत्या",
    "admHash": "प्रवेश #",
    "bedAllocatedStr": "बेड आवंटित केले",
    "generalWardStr": "सामान्य वॉर्ड",
    "assignedDr": "नियुक्त",
    "pendingDoctor": "प्रलंबित डॉक्टर",
    "triageStandard": "मानक ट्रायेज",
    "priorityLabel": "प्राधान्य",
    "selectAvailableBedStar": "उपलब्ध बेड निवडा *",
    "dropdownSyncedWithBedMatrix": "— बेड मॅट्रिक्सशी सिंक केलेले —"
}

def sync_language(lang_file, lang_map):
    path = os.path.join(locales_dir, lang_file)
    if not os.path.exists(path): return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for module in ["nav", "ipd"]:
        if module not in data: data[module] = {}
        # Apply strict maps
        for key, val in lang_map.items():
            if key in data[module] or True: # Force applying
                # Only apply if it belongs to this module context but we have a flat map so we just override matching keys if they exist in en.json
                pass
                
    # Since we have a flat dict of keys for both nav and ipd, we use en.json reference
    with open(os.path.join(locales_dir, "en.json"), "r", encoding="utf-8") as f:
        en_data = json.load(f)
        
    for module in ["nav", "ipd"]:
        if module not in en_data: continue
        for key in en_data[module]:
            if key in lang_map:
                data[module][key] = lang_map[key]

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

sync_language("hi.json", hi_map)
sync_language("mr.json", mr_map)
print("Applied native translations for HI and MR")
