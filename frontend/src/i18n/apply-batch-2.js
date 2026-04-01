const fs = require('fs');
const path = require('path');

const TRANSLATIONS = {
  hi: {
    nav: {
      dashboard: "डैशबोर्ड", patients: "मरीज़ प्रबंधन", patientRegistry: "मरीज़ रजिस्ट्री",
      patientRegistration: "मरीज़ पंजीकरण", clinicalOps: "क्लिनिकल संचालन",
      doctorDesk: "डॉक्टर डेस्क", nursingTriage: "नर्सिंग ट्रायज",
      smartQueue: "स्मार्ट कतार", opdVisits: "ओपीडी विज़िट",
      scheduling: "शेड्यूलिंग", ipdManagement: "आईपीडी प्रबंधन",
      ipdAdmissions: "आईपीडी प्रवेश", ipdDoctorDesk: "आईपीडी डॉक्टर डेस्क",
      ipdNursing: "आईपीडी नर्सिंग", ipdBilling: "आईपीडी बिलिंग",
      ipdTransfers: "आईपीडी स्थानांतरण", ipdDischarge: "आईपीडी डिस्चार्ज",
      wardsAndBeds: "वार्ड और बेड", laboratory: "प्रयोगशाला",
      lisOrders: "LIS ऑर्डर", labProcessing: "लैब प्रशंसकरण",
      resultValidation: "परिणाम सत्यापन", pharmacy: "फार्मेसी",
      pharmacyCore: "फार्मेसी कोर", pharmacySales: "फार्मेसी बिक्री",
      pharmacyBilling: "फार्मेसी बिलिंग", bloodBank: "ब्लड बैंक",
      radiology: "रेडियोलॉजी", billing: "बिलिंग और आरसीएम",
      ipdBillingNav: "आईपीडी बिलिंग", rcmBilling: "आरसीएम बिलिंग",
      billingMasters: "बिलिंग मास्टर्स", emergencyRoom: "आपातकालीन कक्ष",
      operationTheater: "ऑपरेशन थियेटर", administration: "प्रशासन",
      users: "उपयोगकर्ता", systemSettings: "सिस्टम सेटिंग्स",
      analytics: "एनालिटिक्स", audit: "ऑडिट लॉग",
      rpiwWorkspace: "RPIW वर्कस्पेस", tasks: "कार्य",
      clinicalOrders: "ऑर्डर", visitorMlc: "विजिटर और एमएलसी",
      sampleReceiving: "सैंपल रिसीविंग", analyzerHub: "एनालाइजर हब",
      reportHandover: "रिपोर्ट हैंडओवर", advancedDiagnostics: "उन्नत निदान",
      extendedLab: "विस्तारित लैब सेवाएं", rxWorklist: "प्रिस्क्रिप्शन वर्कलिस्ट",
      ipMedicationIssue: "आईपी दवा वितरण", pharmacyReturns: "रिटर्न",
      ipPharmacyReturns: "आईपी रिटर्न", narcoticsVault: "नारकोटिक्स वॉल्ट",
      inventoryIntelligence: "इन्वेंट्री इंटेलिजेंस", organizations: "संगठन (SaaS)",
      coreSystem: "कोर सिस्टम", communication: "संचार",
      biIntelligence: "BI इंटेलिजेंस", aiPlatform: "AI प्लेटफॉर्म",
      encounters: "परामर्श", orders: "ऑर्डर",
      appointments: "अपॉइंटमेंट", pharmacySalesNav: "फार्मेसी बिक्री",
      ipdOrdersNav: "ऑर्डर", ipdNursingVitals: "नर्सिंग वाइटल्स",
      ipdDoctorRounds: "डॉक्टर राउंड्स", ipdBedTransfers: "बेड ट्रांसफर",
      ipdSmartDischarge: "आईपीडी डिस्चार्ज", phlebotomy: "फ्लेबोटोमी",
      sampleReceivingCentral: "सैंपल रिसीविंग", labProcessingWorkflow: "लैब प्रशंसकरण",
      analyzerHubNav: "एनालाइजर हब", validationDesk: "सत्यापन डेस्क",
      reportHandoverNav: "रिपोर्ट हैंडओवर", advancedDiagnosticsNav: "उन्नत निदान",
      extendedLabNav: "विस्तारित लैब सेवाएं", narcoticsVaultNav: "नारकोटिक्स वॉल्ट",
      ipMedicationIssueNav: "आईपी दवा वितरण", ipReturnsNav: "आईपी रिटर्न",
      returnsNav: "रिटर्न", inventoryIntelligenceNav: "इन्वेंट्री इंटेलिजेंस",
      pharmacyCoreNav: "फार्मेसी कोर", billingComplianceNav: "बिलिंग और अनुपालन",
      organizationsNav: "संगठन (SaaS)", systemOnline: "सिस्टम ऑनलाइन",
      languageLabel: "भाषा"
    },
    patients: {
      title: "मरीज़ रजिस्ट्री", manageRecords: "मरीज़ रिकॉर्ड और पहचान प्रबंधित करें।",
      registration: "एंटरप्राइज़ मरीज़ पंजीकरण",
      registrationSub: "OCR, वॉयस कमांड, फेस रिकग्निशन और डुप्लीकेट डिटेक्शन के साथ AI-संचालित स्मार्ट पंजीकरण।",
      firstName: "पहला नाम", lastName: "अंतिम नाम", dateOfBirth: "जन्म तिथि",
      gender: "लिंग", male: "पुरुष", female: "महिला", other: "अन्य",
      phone: "फ़ोन", email: "ईमेल", bloodGroup: "रक्त समूह",
      weight: "वज़न (किग्रा)", height: "ऊंचाई (सेमी)", allergies: "एलर्जी",
      address: "पता", pincode: "पिनकोड", city: "शहर", state: "राज्य",
      country: "देश", emergencyContact: "आपातकालीन संपर्क",
      emergencyPhone: "आपातकालीन फ़ोन", idType: "आईडी प्रकार",
      idNumber: "दस्तावेज़ संख्या", insuranceProvider: "बीमा प्रदाता",
      policyNumber: "पॉलिसी नंबर", chiefComplaint: "मुख्य शिकायत",
      reasonForVisit: "विज़िट का कारण", uhid: "UHID",
      searchPatients: "नाम, UHID या फ़ोन द्वारा मरीज़ खोजें...",
      registerNew: "नया मरीज़ पंजीकृत करें", viewProfile: "मरीज़ प्रोफ़ाइल देखें",
      demographics: "जनसांख्यिकी", medicalInfo: "चिकित्सा जानकारी",
      identityVerification: "पहचान सत्यापन", insurance: "बीमा",
      consentNotification: "सूचनाएं", registrationSuccess: "पंजीकरण सफल!",
      healthCardReady: "स्वास्थ्य कार्ड तैयार"
    },
    doctor: {
      title: "AI डॉक्टर डेस्क", subtitle: "इंटेलिजेंट EMR, AI स्क्राइबिंग, और नैदानिक निर्णय समर्थन।",
      worklist: "डॉक्टर वर्कलिस्ट", callPatient: "मरीज़ को बुलाएं",
      seedQueue: "कतार में जोड़ें", chiefComplaint: "मुख्य शिकायत",
      historyPresentIllness: "वर्तमान बीमारी का इतिहास", plan: "योजना",
      saveNote: "सहेजें और निष्कर्ष निकालें", aiSuggestions: "AI सुझाव",
      runAI: "AI डायग्नोस्टिक चलाएं", prescriptions: "प्रिस्क्रिप्शन",
      diagnosticOrders: "नैदानिक आदेश", recommendAdmission: "IPD प्रवेश की अनुशंसा करें",
      currentHealth: "वर्तमान स्वास्थ्य स्थिति", medications: "दवाएं / देने के लिए खुराक",
      planOfAction: "कार्य योजना", consultation: "परामर्श",
      inConsultation: "परामर्श में", waiting: "प्रतीक्षा",
      concluded: "निष्कर्ष निकाला", clinicalTimeline: "नैदानिक समयरेखा"
    }
  },
  mr: {
    nav: {
      dashboard: "डॅशबोर्ड", patients: "रुग्ण व्यवस्थापन", patientRegistry: "रुग्ण नोंदवही",
      patientRegistration: "रुग्ण नोंदणी", clinicalOps: "क्लिनिकल कार्यसंचालन",
      doctorDesk: "डॉक्टर डेस्क", nursingTriage: "नर्सिंग ट्रायज",
      smartQueue: "स्मार्ट रांग", opdVisits: "ओपीडी भेटी",
      scheduling: "वेळापत्रक", ipdManagement: "आयपीडी व्यवस्थापन",
      ipdAdmissions: "IPD प्रवेश", ipdDoctorDesk: "IPD डॉक्टर डेस्क",
      ipdNursing: "IPD नर्सिंग", ipdBilling: "IPD बिलिंग",
      ipdTransfers: "IPD बदल्या", ipdDischarge: "IPD डिस्चार्ज",
      wardsAndBeds: "वॉर्ड आणि बेड", laboratory: "प्रयोगशाळा",
      lisOrders: "LIS ऑर्डर्स", labProcessing: "लॅब प्रक्रिया",
      resultValidation: "निकाल पडताळणी", pharmacy: "औषधालय",
      pharmacyCore: "फार्मसी कोअर", pharmacySales: "फार्मसी विक्री",
      pharmacyBilling: "फार्मसी बिलिंग", bloodBank: "रक्तपेढी",
      radiology: "रेडिओलॉजी", billing: "बिलिंग आणि आरसीएम",
      ipdBillingNav: "IPD बिलिंग", rcmBilling: "आरसीएम बिलिंग",
      billingMasters: "बिलिंग मास्टर्स", emergencyRoom: "आपत्कालीन कक्ष",
      operationTheater: "शस्त्रक्रिया गृह", administration: "प्रशासन",
      users: "वापरकर्ते", systemSettings: "सिस्टम सेटिंग्ज",
      analytics: "एनालिटिक्स", audit: "ऑडिट लॉग",
      rpiwWorkspace: "RPIW वर्कस्पेस", tasks: "कार्ये",
      clinicalOrders: "ऑर्डर्स", visitorMlc: "विजिटर आणि एमएलसी",
      sampleReceiving: "नमुना पावती", analyzerHub: "ॲनालायजर हब",
      reportHandover: "रिपोर्ट हँडओव्हर", advancedDiagnostics: "प्रगत निदान",
      extendedLab: "विस्तारित लॅब सेवा", rxWorklist: "Rx वर्कलिस्ट",
      ipMedicationIssue: "IP औषध वितरण", pharmacyReturns: "परतावा",
      ipPharmacyReturns: "IP परतावा", narcoticsVault: "नार्कोटिक्स वॉल्ट",
      inventoryIntelligence: "इन्व्हेंटरी इंटेलिजन्स", organizations: "संस्था (SaaS)",
      coreSystem: "कोअर सिस्टम", communication: "संवाद",
      biIntelligence: "BI इंटेलिजन्स", aiPlatform: "AI प्लॅटफॉर्म",
      encounters: "भेटी", orders: "ऑर्डर्स",
      appointments: "अपॉइंटमेंट्स", pharmacySalesNav: "फार्मसी विक्री",
      ipdOrdersNav: "ऑर्डर्स", ipdNursingVitals: "नर्सिंग वाइटल्स",
      ipdDoctorRounds: "डॉक्टर राऊंड्स", ipdBedTransfers: "बेड ट्रान्सफर",
      ipdSmartDischarge: "IPD डिस्चार्ज", phlebotomy: "फ्लेबोटोमी",
      sampleReceivingCentral: "नमुना पावती", labProcessingWorkflow: "लॅब प्रक्रिया",
      analyzerHubNav: "ॲनालायजर हब", validationDesk: "पडताळणी डेस्क",
      reportHandoverNav: "रिपोर्ट हँडओव्हर", advancedDiagnosticsNav: "प्रगत निदान",
      extendedLabNav: "विस्तारित लॅब सेवा", narcoticsVaultNav: "नार्कोटिक्स वॉल्ट",
      ipMedicationIssueNav: "IP औषध वितरण", ipReturnsNav: "IP परतावा",
      returnsNav: "परतावा", inventoryIntelligenceNav: "इन्व्हेंटरी इंटेलिजन्स",
      pharmacyCoreNav: "फार्मसी कोअर", billingComplianceNav: "बिलिंग आणि अनुपालन",
      organizationsNav: "संस्था (SaaS)", systemOnline: "सिस्टम ऑनलाइन",
      languageLabel: "भाषा"
    },
    patients: {
      title: "रुग्ण नोंदवही", manageRecords: "रुग्ण रेकॉर्ड आणि ओळख व्यवस्थापित करा.",
      registration: "एंटरप्राइझ रुग्ण नोंदणी",
      registrationSub: "OCR, व्हॉइस कमांड, फेस रिकग्निशन आणि डुप्लिकेट डिटेक्शनसह AI-आधारित स्मार्ट नोंदणी.",
      firstName: "पहिले नाव", lastName: "आडनाव", dateOfBirth: "जन्मतारीख",
      gender: "लिंग", male: "पुरुष", female: "स्त्री", other: "इतर",
      phone: "फोन", email: "ईमेल", bloodGroup: "रक्तगट",
      weight: "वजन (किलो)", height: "उंची (सेमी)", allergies: "ॲलर्जी",
      address: "पत्ता", pincode: "पिनकोड", city: "शहर", state: "राज्य",
      country: "देश", emergencyContact: "तातडीचा संपर्क",
      emergencyPhone: "तातडीचा फोन", idType: "ओळखपत्राचा प्रकार",
      idNumber: "दस्तऐवज क्रमांक", insuranceProvider: "विमा कंपनी",
      policyNumber: "पॉलिसी क्रमांक", chiefComplaint: "मुख्य तक्रार",
      reasonForVisit: "भेटीचे कारण", uhid: "UHID",
      searchPatients: "नाव, UHID किंवा फोनद्वारे रुग्ण शोधा...",
      registerNew: "नवीन रुग्ण नोंदणी करा", viewProfile: "रुग्ण प्रोफाइल पहा",
      demographics: "लोकसंख्याशास्त्र", medicalInfo: "वैद्यकीय माहिती",
      identityVerification: "ओळख पडताळणी", insurance: "विमा",
      consentNotification: "सूचना", registrationSuccess: "नोंदणी यशस्वी!",
      healthCardReady: "हेल्थ कार्ड तयार आहे"
    },
    doctor: {
      title: "AI डॉक्टर डेस्क", subtitle: "इंटेलिजेंट EMR, AI स्क्राइबिंग आणि क्लिनिकल निर्णय समर्थन.",
      worklist: "डॉक्टर वर्कलिस्ट", callPatient: "रुग्णास बोलवा",
      seedQueue: "रांगेत जोडा", chiefComplaint: "मुख्य तक्रार",
      historyPresentIllness: "सध्याच्या आजाराचा इतिहास", plan: "योजना",
      saveNote: "जतन करा आणि निष्कर्ष काढा", aiSuggestions: "AI सूचना",
      runAI: "AI डायग्नोस्टिक चालवा", prescriptions: "प्रिस्क्रिप्शन",
      diagnosticOrders: "निदान ऑर्डर्स", recommendAdmission: "IPD प्रवेशाची शिफारस करा",
      currentHealth: "सध्याची आरोग्य स्थिती", medications: "औषधे / देण्याचे डोस",
      planOfAction: "कृती आराखडा", consultation: "सल्ला",
      inConsultation: "सल्लामसलत सुरू", waiting: "प्रतिक्षा",
      concluded: "निष्कर्ष संपला", clinicalTimeline: "क्लिनिकल टाइमलाइन"
    }
  }
};

const LANGUAGES = ['hi', 'mr']; // and others, but starting with these

for (const lang of LANGUAGES) {
  const localeFile = path.join(__dirname, `locales/${lang}.json`);
  let data = {};
  if (fs.existsSync(localeFile)) {
    data = JSON.parse(fs.readFileSync(localeFile, 'utf8'));
  }
  
  const tr = TRANSLATIONS[lang];
  if (tr) {
    for (const module in tr) {
      data[module] = { ...(data[module] || {}), ...tr[module] };
    }
    fs.writeFileSync(localeFile, JSON.stringify(data, null, 2) + '\n');
    console.log(`Updated ${lang}.json for nav, patients, doctor`);
  }
}
