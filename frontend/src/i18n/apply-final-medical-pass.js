const fs = require('fs');
const path = require('path');

const TRANSLATIONS = {
  hi: {
    smartQueue: { orchestrator: "प्रादेशिक कतार आयोजक", signage: "डिजिटल साइनेज", wayfinding: "डिजिटल मार्ग खोज", crowdAi: "भीड़ विश्लेषण (AI)", engineActive: "कतार इंजन सक्रिय", target: "लक्ष्य", length: "लंबाई", bestRoom: "सर्वोत्तम कक्ष", nowServing: "अब सेवा दे रहे हैं", nextInQueue: "कतार में अगला", estWait: "अनुमानित प्रतीक्षा", min: "मिनट", emptyQueue: "कतार खाली है" },
    ot: { operatingTheatre: "ऑपरेशन थियेटर (OT)", surgeonCommandCenter: "सर्जन कमांड सेंटर", scheduleSurgery: "सर्जरी शेड्यूल करें", todaysSurgeries: "आज की सर्जरी", inProgress: "प्रगति में", surgeon: "सर्जन", room: "कमरा", appendectomy: "एपेंडेक्टोमी", primarySurgeon: "प्राथमिक सर्जन *", surgeryProcedure: "सर्जरी प्रक्रिया *" },
    ipdDischarge: { dischargePlan: "डिस्चार्ज योजना", billingCleared: "बिलिंग क्लियर", mediationReconciled: "दवा मिलान", summaryGenerated: "डिस्चार्ज सारांश जेनरेट किया गया", completeDischarge: "डिस्चार्ज पूर्ण करें", lama: "एलएएमए (सलाह के खिलाफ छोड़ा)", expired: "मृत", referred: "रेफर किया गया" },
    narcotics: { narcoticsVault: "नारकोटिक्स वॉल्ट", controlledSubstances: "नियंत्रित पदार्थ", dualVerification: "दोहरी सत्यापन आवश्यक", chainOfCustody: "चेन ऑफ कस्टडी", approve: "स्वीकार करें", reject: "अस्वीकार करें" },
    nursingVitals: { pulseRate: "पल्स रेट", respiratoryRate: "श्वसन दर", bpSystolic: "बीपी सिस्टोलिक", painScore: "दर्द स्कोर", fallRisk: "गिरने का जोखिम", pressureUlcer: "प्रेशर अल्सर", familyHistory: "पारिवारिक इतिहास" },
    audit: { systemAuditLogs: "सिस्टम ऑडिट लॉग", timestamp: "समय", severity: "गंभीरता", exportLogs: "लॉग निर्यात करें" }
  },
  mr: {
    smartQueue: { orchestrator: "रांग व्यवस्थापक", signage: "डिजिटल साईन", nextInQueue: "रांगेत पुढील", emptyQueue: "रांग रिकामी आहे" },
    ot: { operatingTheatre: "शस्त्रक्रिया गृह (OT)", surgeon: "सर्जन", inProgress: "प्रगतीपथावर" },
    ipdDischarge: { dischargePlan: "डिस्चार्ज योजना", billingCleared: "बिलिंग क्लियर", completeDischarge: "डिस्चार्ज पूर्ण करा" },
    narcotics: { narcoticsVault: "नार्कोटिक्स वॉल्ट", controlledSubstances: "नियंत्रित पदार्थ", approve: "मंजूर करा", reject: "नाकारा" }
  }
};

const LANGUAGES = ['hi', 'mr'];

for (const lang of LANGUAGES) {
  const file = path.join(__dirname, `locales/${lang}.json`);
  let data = JSON.parse(fs.readFileSync(file, 'utf8'));
  const tr = TRANSLATIONS[lang] || {};
  for (const module in tr) {
    data[module] = { ...(data[module] || {}), ...tr[module] };
  }
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
}
console.log("Final medical modules pass finished.");
