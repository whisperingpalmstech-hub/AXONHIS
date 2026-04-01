const fs = require('fs');
const path = require('path');

const TRANSLATIONS = {
  hi: {
    bloodBank: { coldStorage: "कोल्ड स्टोरेज इन्वेंट्री", transfusionOrders: "ट्रांसफ्यूजन ऑर्डर", donorRegistry: "डोनर रजिस्ट्री", registerDonor: "नया डोनर पंजीकृत करें", volume: "वॉल्यूम", rhFactor: "आरएच फैक्टर" },
    radiology: { modality: "मोडेलिटी", bodyPart: "शरीर का हिस्सा", findings: "निष्कर्ष", impression: "प्रभाव" },
    wards: { capacity: "क्षमता", roomNumber: "कमरा नंबर", bedStatus: "ब्रेड की स्थिति", available: "उपलब्ध", occupied: "भरा हुआ", wardBedManagement: "वार्ड और बिस्तर प्रबंधन", totalCapacity: "कुल क्षमता", bedInventory: "बिस्तर सूची", johnDoe: "जॉन डो", surgicalHistory: "सर्जिकल इतिहास", surgery: "सर्जरी", medicine: "दवा", icu: "आईसीयू", emergency: "आपातकालीन" },
    encounters: { statusScheduled: "शेड्यूल्ड", statusInProgress: "प्रगति में", statusCompleted: "पूर्ण", opOutPatient: "ओपी (बाह्य रोगी)", ipInPatient: "आईपी (आंतरिक रोगी)", erEmergency: "ईआर (आपातकालीन)", cardiology: "कार्डियोलॉजी", orthopedics: "ऑर्थोपेडिक्स", pediatrics: "पीडियाट्रिक्स", neurology: "न्यूरोलॉजी", gynecology: "गाइनेकोलॉजी", psychiatry: "साइकियाट्री" },
    er: { resuscitation: "पुनर्जीवन", acuteCare: "तीव्र देखभाल", fastTrack: "फास्ट ट्रैक", pediatrics: "पीडियाट्रिक्स", observation: "अवलोकन", nurse: "नर्स", labTech: "लैब टेक", pharmacist: "फार्मासिस्ट", startTask: "कार्य शुरू करें", completeTask: "कार्य पूर्ण करें" },
    tasks: {collectSpecimen: "नमूना संग्रह", processLabTest: "प्रयोगशाला प्रशंसकरण", dispenseMedication: "दवा वितरण", administerMedication: "दवा प्रशासन", vitalMonitoring: "महत्वपूर्ण निगरानी" },
    orders: { medicationOrder: "दवा ऑर्डर", labOrder: "लैब ऑर्डर", radiologyOrder: "रेडियोलॉजी ऑर्डर", routine: "नियमित", urgent: "तत्काल", stat: "अति तत्काल" }
  },
  mr: {
    bloodBank: { coldStorage: "कोल्ड स्टोरेज साठा", donorRegistry: "डोनर नोंदणी", registerDonor: "नवीन डोनर नोंदणी" },
    radiology: { modality: "मोडालिटी", findings: "निष्कर्ष", impression: "प्रभाव" },
    wards: { capacity: "क्षमता", available: "उपलब्ध", occupied: "भरलेले", icu: "आयसीयू", emergency: "आपातकालीन" },
    encounters: { statusScheduled: "नियोजित", statusInProgress: "प्रगतीपथावर", statusCompleted: "पूर्ण" }
  }
};

const LANGUAGES = ['hi', 'mr'];

for (const lang of LANGUAGES) {
  const localeFile = path.join(__dirname, `locales/${lang}.json`);
  let data = JSON.parse(fs.readFileSync(localeFile, 'utf8'));
  const tr = TRANSLATIONS[lang] || {};
  for (const module in tr) {
    data[module] = { ...(data[module] || {}), ...tr[module] };
  }
  fs.writeFileSync(localeFile, JSON.stringify(data, null, 2) + '\n');
}
console.log("Updated Hindi and Marathi medical terms.");
