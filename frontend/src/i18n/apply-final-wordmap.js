const fs = require('fs');
const path = require('path');

const WORD_MAP = {
  hi: {
    uhid: "UHID", noDepositsRecordedYet: "अभी तक कोई जमा राशि दर्ज नहीं की गई",
    admissionEstimates: "प्रवेश अनुमान", noEstimatesCreatedYet: "अभी तक कोई अनुमान नहीं बनाया गया",
    insurancePreAuthorizations: "बीमा पूर्व-प्राधिकरण", requested: "अनुरोधित",
    noPreAuthorizations: "कोई पूर्व-प्राधिकरण नहीं", crossModuleIntegrationEvents: "क्रॉस-मोड्यूल एकीकरण विवरण",
    moduleConnectivityMap: "मोड्यूल कनेक्टिविटी मैप", donorId: "डोनर आईडी",
    crossmatchAllocate: "क्रॉस-मैच और आवंटित करें", freezerEmpty: "फ्रीज़र खाली है",
    noActiveRequests: "कोई सक्रिय अनुरोध नहीं", noDonors: "कोई डोनर नहीं",
    units: "इकाइयां", eligibility: "पात्रता", contactNumber: "संपर्क नंबर",
    reorderLevel: "पुनःआदेश स्तर", realTimeOverviewOfDispensaryOp: "डिस्पेंसरी संचालन का रीयल-टाइम अवलोकन",
    noPendingPrescriptions: "कोई लंबित प्रिस्क्रिप्शन नहीं", criticalInventoryAlerts: "क्रिटिकल इन्वेंट्री अलर्ट",
    noInventoryAlerts: "कोई इन्वेंट्री अलर्ट नहीं", lowStockAlert: "कम स्टॉक अलर्ट",
    critical: "गंभीर", drugId: "दवा आईडी", batch: "बैच",
    testCategories: "परीक्षण श्रेणियां", recentSamples: "हालिया नमूने",
    receive: "प्राप्त करें", process: "संसाधित करें", noSamplesYetSamplesAreCreatedW: "अभी तक कोई नमूना नहीं।",
    allCategories: "सभी श्रेणियां", addTest: "परीक्षण जोड़ें",
    normalLimits: "सामान्य सीमा", criticalLimits: "गंभीर सीमा", price: "कीमत",
    collected: "संग्रहीत", received: "प्राप्त", processInAnalyzer: "एनालाइज़र में संसाधित करें",
    enterResult: "परिणाम दर्ज करें", noSamplesFound: "कोई नमूना नहीं मिला",
    validate: "सत्यापित करें", reject: "अस्वीकार करें", allResultsValidated: "सभी परिणाम सत्यापित!",
    noPendingValidationsAtThisTime: "अभी कोई लंबित सत्यापन नहीं है।", addLabTest: "लैब टेस्ट जोड़ें",
    testCode: "टेस्ट कोड", category: "श्रेणी", unit: "इकाई",
    normalLow: "सामान्य निम्न", normalHigh: "सामान्य उच्च", criticalLow: "गंभीर निम्न",
    criticalHigh: "गंभीर उच्च", createTest: "परीक्षण बनाएं", enterLabResult: "लैब परिणाम दर्ज करें",
    sampleBarcode: "सैंपल बारकोड", selectTest: "परीक्षण चुनें", resultValueText: "परिणाम मूल्य (पाठ)",
    notesRemarks: "नोट्स / टिप्पणी", department: "विभाग", bedCode: "बेड कोड",
    monitorHospitalOccupancyAndMan: "अस्पताल ऑक्यूपेंसी की निगरानी और प्रबंधन", beds: "बेड",
    addBed: "बेड जोड़ें", noWardsDefinedYetStartByCreati: "अभी तक कोई वार्ड परिभाषित नहीं।",
    addMultipleBeds: "एकाधिक बेड जोड़ें", bedInfo: "बेड की जानकारी", currentOccupant: "वर्तमान निवासी",
    selectDept: "विभाग चुनें", discard: "खारिज करें", general: "सामान्य",
    semiPrivate: "सेमी-प्राइवेट", private: "प्राइवेट", createRoom: "कमरा बनाएं",
    addSingleBed: "एक बेड जोड़ें", selectRoom: "कमरा चुनें", bedNumber: "बेड नंबर",
    prefix: "उपसर्ग", count: "गणना", roomsLayout: "कमरे और लेआउट",
    addRoom: "कमरा जोड़ें", occupancyRate: "ऑक्यूपेंसी दर", selectPatient: "मरीज़ चुनें",
    selectEncounter: "परामर्श चुनें", pleaseSelectAPatientFirstToSee: "परामर्श देखने के लिए पहले मरीज़ चुनें",
    bedsCanOnlyBeAssignedToPatient: "बेड केवल सक्रिय परामर्श वाले मरीज़ों को दिए जा सकते हैं।",
    loadingEncounters: "परामर्श लोड हो रहा है...", noEncountersFound: "कोई परामर्श नहीं मिला",
    clickToStart: "शुरू करने के लिए 'नया परामर्श' चुनें।", encounterId: "ENCOUNTER ID",
    type: "प्रकार", status: "स्थिति", date: "तारीख", action: "कार्रवाई",
    newEncounter: "नया परामर्श", loadingPatients: "मरीज़ लोड हो रहे हैं...",
    noPatientsFound: "कोई मरीज़ नहीं मिला।", followUp: "अनुवर्ती", teleconsultation: "टेलीकंसल्टेशन"
  },
  mr: {
    uhid: "UHID", noDepositsRecordedYet: "अद्याप कोणतीही ठेव नोंदवलेली नाही",
    admissionEstimates: "प्रवेश अंदाज", noEstimatesCreatedYet: "अद्याप कोणतेही अंदाज तयार केलेले नाहीत",
    insurancePreAuthorizations: "विमा पूर्व-मंजुरी", requested: "विनंती केली",
    noPreAuthorizations: "कोणतीही पूर्व-मंजुरी नाही", donorId: "डोनर आयडी",
    freezerEmpty: "फ्रीझर रिकामा आहे", noActiveRequests: "कोणतीही सक्रिय विनंती नाही",
    noDonors: "कोणतेही डोनर नाहीत", units: "युनिट्स", eligibility: "पात्रता",
    contactNumber: "संपर्क क्रमांक", reorderLevel: "पुन्हा ऑर्डर पातळी",
    noPendingPrescriptions: "कोणतीही प्रलंबित प्रिस्क्रिप्शन नाहीत",
    criticalInventoryAlerts: "गंभीर साठा सूचना", noInventoryAlerts: "कोणतीही साठा सूचना नाही",
    lowStockAlert: "कमी साठा सूचना", critical: "गंभीर", batch: "बॅच",
    receive: "प्राप्त करा", process: "संसाधित करा", allCategories: "सर्व प्रवर्ग",
    addTest: "चाचणी जोडा", price: "किंमत", collected: "संकलित",
    received: "प्राप्त", enterResult: "निकाल नोंदवा", noSamplesFound: "नमुने आढळले नाहीत",
    validate: "पडताळणी करा", reject: "नाकारा", addLabTest: "लॅब चाचणी जोडा",
    testCode: "चाचणी कोड", unit: "युनिट", createTest: "चाचणी तयार करा",
    department: "विभाग", bedCode: "बेड कोड", beds: "बेड", addBed: "बेड जोडा",
    selectDept: "विभाग निवडा", discard: "रद्द करा", general: "सामान्य",
    private: "खाजगी", createRoom: "खोली तयार करा", prefix: "उपसर्ग",
    count: "संख्या", addRoom: "खोली जोडा", selectPatient: "रुग्ण निवडा",
    noEncountersFound: "भेटी आढळल्या नाहीत", type: "प्रकार", status: "स्थिती",
    date: "तारीख", action: "कृती", newEncounter: "नवीन भेट"
  }
};

const LANGUAGES = ['hi', 'mr', 'es', 'fr', 'de', 'ar', 'zh', 'ja', 'pt', 'ru'];
const en = JSON.parse(fs.readFileSync(path.join(__dirname, 'locales/en.json'), 'utf8'));

for (const lang of LANGUAGES) {
  const localeFile = path.join(__dirname, `locales/${lang}.json`);
  let data = JSON.parse(fs.readFileSync(localeFile, 'utf8'));
  const tr = WORD_MAP[lang] || {};
  
  for (const module in en) {
    if (!data[module]) data[module] = {};
    for (const key in en[module]) {
      if (tr[key]) {
        data[module][key] = tr[key];
      }
    }
  }
  fs.writeFileSync(localeFile, JSON.stringify(data, null, 2) + '\n');
}
console.log("Applied final cross-module word map.");
