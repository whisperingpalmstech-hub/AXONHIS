const fs = require('fs');
const path = require('path');

const DICTIONARY = {
  hi: {
    dashboard: "डैशबोर्ड", patients: "मरीज़", encounters: "परामर्श", tasks: "कार्य", billing: "बिलिंग",
    pharmacy: "फार्मेसी", inventory: "इन्वेंट्री", laboratory: "प्रयोगशाला", radiology: "रेडियोलॉजी",
    bloodBank: "ब्लड बैंक", administration: "प्रशासन", analytics: "एनालिटिक्स", users: "उपयोगकर्ता",
    settings: "सेटिंग्स", profile: "प्रोफ़ाइल", logout: "लॉगआउट", welcome: "स्वागत है",
    totalPatients: "कुल मरीज़", activeEncounters: "सक्रिय परामर्श", pendingTasks: "लंबित कार्य",
    revenue: "राजस्व", high: "उच्च", low: "निम्न", critical: "गंभीर", normal: "सामान्य",
    urgent: "तत्काल", stat: "अति तत्काल", registration: "पंजीकरण", registrationSuccess: "पंजीकरण सफल!",
    firstName: "पहला नाम", lastName: "अंतिम नाम", birthDate: "जन्म तिथि", gender: "लिंग",
    male: "पुरुष", female: "महिला", other: "अन्य", phone: "फ़ोन", email: "ईमेल", address: "पता",
    city: "शहर", state: "राज्य", country: "देश", bloodGroup: "रक्त समूह", allergy: "एलर्जी",
    complaint: "शिकायत", diagnosis: "निदान", summary: "सारांश", prescription: "प्रिस्क्रिप्शन",
    medication: "दवा", dosage: "खुराक", frequency: "आवृत्ति", duration: "अवधि", route: "मार्ग",
    appointment: "अपॉइंटमेंट", schedule: "शेड्यूल", time: "समय", date: "तारीख", room: "कमरा",
    bed: "बस्तर", ward: "वार्ड", admission: "प्रवेश", discharge: "डिस्चार्ज", transfer: "स्थानांतरण",
    result: "परिणाम", specimen: "नमूना", collected: "संग्रहीत", received: "प्राप्त",
    validate: "सत्यापित", reject: "अस्वीकार", price: "कीमत", amount: "राशि", discount: "छूट",
    total: "कुल", balance: "शेष", status: "स्थिति", action: "कार्रवाई", view: "देखें",
    edit: "संपादित करें", delete: "हटाएं", save: "सहेजें", cancel: "रद्द करें", submit: "सबमिट करें"
  },
  mr: {
    dashboard: "डॅशबोर्ड", patients: "रुग्ण", encounters: "भेटी", tasks: "कार्ये",
    pharmacy: "औषधालय", laboratory: "प्रयोगशाळा", bloodBank: "रक्तपेढी",
    registration: "नोंदणी", firstName: "पहिले नाव", lastName: "आडनाव",
    gender: "लिंग", male: "पुरुष", female: "स्त्री", other: "इतर", phone: "फोन",
    email: "ईमेल", address: "पत्ता", city: "शहर", state: "राज्य", country: "देश",
    summary: "सारांश", prescription: "प्रिस्क्रिप्शन", medication: "औषध",
    appointment: "अपॉइंटमेंट", schedule: "वेळापत्रक", room: "खोली", bed: "बेड",
    ward: "वॉर्ड", admission: "प्रवेश", discharge: "डिस्चार्ज", status: "स्थिती",
    action: "कृती", view: "पहा", save: "जतन करा", submit: "सादर करा"
  }
};

const LANGUAGES = ['hi', 'mr', 'es', 'fr', 'de', 'ar', 'zh', 'ja', 'pt', 'ru'];
const en = JSON.parse(fs.readFileSync(path.join(__dirname, 'locales/en.json'), 'utf8'));

for (const lang of LANGUAGES) {
  const file = path.join(__dirname, `locales/${lang}.json`);
  let data = JSON.parse(fs.readFileSync(file, 'utf8'));
  const dict = DICTIONARY[lang] || {};

  for (const module in en) {
    if (!data[module]) data[module] = {};
    for (const key in en[module]) {
      // If we have a specific dictionary translation, use it
      if (dict[key]) {
        data[module][key] = dict[key];
      }
    }
  }
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
}
console.log("Applied final cross-language dictionary sync.");
