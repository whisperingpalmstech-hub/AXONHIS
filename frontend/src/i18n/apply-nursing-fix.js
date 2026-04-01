const fs = require('fs');
const path = require('path');

const NURSING_IPD_MAP = {
  en: {
    nursingIpd: {
      title: "Nursing IPD Management",
      subtitle: "IPD Patient Acceptance, Coversheets & Nursing Documentation",
      totalWorklist: "Total Worklist",
      pendingAcceptance: "Pending Acceptance",
      accepted: "Accepted",
      critical: "Critical",
      tabWorklist: "Admission Worklist",
      tabCoversheets: "Accepted Patients",
      tabNotes: "Nursing Notes",
      colAdmNo: "Admission No",
      colUHID: "Patient UHID",
      colBed: "Bed / Ward",
      colAdmittingDoctor: "Admitting Doctor",
      colTime: "Admission Time",
      colStatus: "Status",
      colActions: "Actions",
      acceptPatient: "Accept Patient",
      confirmAcceptance: "Confirm Acceptance",
      addNote: "Add Nursing Note",
      noteType: "Note Type",
      clinicalNote: "Clinical Note",
      saveNote: "Save Note",
      assignCare: "Assign Nursing Care",
      staffAssigned: "Staff Assigned Successfully"
    }
  },
  hi: {
    nursingIpd: {
      title: "नर्सिंग IPD प्रबंधन",
      subtitle: "IPD मरीज़ स्वीकृति, कवरशीट और नर्सिंग दस्तावेज़ीकरण",
      totalWorklist: "कुल कार्यसूची",
      pendingAcceptance: "स्वीकृति लंबित",
      accepted: "स्वीकार कर लिया",
      critical: "गंभीर",
      tabWorklist: "प्रवेश कार्यसूची",
      tabCoversheets: "स्वीकृत मरीज़",
      tabNotes: "नर्सिंग नोट्स",
      colAdmNo: "प्रवेश संख्या",
      colUHID: "मरीज़ UHID",
      colBed: "बेड / वार्ड",
      colAdmittingDoctor: "भर्ती करने वाले डॉक्टर",
      colTime: "प्रवेश का समय",
      colStatus: "स्थिति",
      colActions: "कार्रवाई",
      acceptPatient: "मरीज़ स्वीकार करें",
      confirmAcceptance: "स्वीकृति की पुष्टि करें",
      addNote: "नर्सिंग नोट जोड़ें",
      noteType: "नोट प्रकार",
      clinicalNote: "नैदानिक नोट",
      saveNote: "नोट सहेजें",
      assignCare: "नर्सिंग देखभाल असाइन करें",
      staffAssigned: "स्टाफ सफलतापूर्वक असाइन किया गया"
    }
  },
  mr: {
    nursingIpd: {
      title: "नर्सिंग IPD व्यवस्थापन",
      subtitle: "IPD रुग्ण स्वीकृती, कव्हरशीट आणि नर्सिंग दस्तऐवजीकरण",
      totalWorklist: "एकूण कार्यसूची",
      pendingAcceptance: "स्वीकृती प्रलंबित",
      accepted: "स्वीकारले",
      critical: "गंभीर",
      tabWorklist: "प्रवेश कार्यसूची",
      tabCoversheets: "स्वीकृत रुग्ण",
      tabNotes: "नर्सिंग नोट्स",
      colAdmNo: "प्रवेश क्रमांक",
      colUHID: "रुग्ण UHID",
      colBed: "बेड / वॉर्ड",
      colAdmittingDoctor: "भर्ती करणारे डॉक्टर",
      colTime: "प्रवेशाची वेळ",
      colStatus: "स्थिती",
      colActions: "क्रिया",
      acceptPatient: "रुग्ण स्वीकारा",
      confirmAcceptance: "स्वीकृतीची पुष्टी करा",
      addNote: "नर्सिंग नोट जोडा",
      noteType: "नोट प्रकार",
      clinicalNote: "क्लिनिकल नोट",
      saveNote: "नोट जतन करा",
      assignCare: "नर्सिंग केअर असाइन करा",
      staffAssigned: "कर्मचारी यशस्वीरित्या नियुक्त केले"
    }
  }
};
// I will also add basic keys for others to avoid raw keys
const OTHERS = ['es', 'fr', 'de', 'ar', 'zh', 'ja', 'pt', 'ru'];

const LANGUAGES = ['en', 'hi', 'mr', ...OTHERS];

for (const lang of LANGUAGES) {
  const file = path.join(__dirname, `locales/${lang}.json`);
  let data = JSON.parse(fs.readFileSync(file, 'utf8'));
  
  if (NURSING_IPD_MAP[lang]) {
      data.nursingIpd = NURSING_IPD_MAP[lang].nursingIpd;
  } else {
      // English fallback keys to avoid raw key rendering
      data.nursingIpd = NURSING_IPD_MAP.en.nursingIpd;
  }
  
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
}
console.log("Applied Nursing IPD translations and fixed raw key issues.");
