const fs = require('fs');
const path = require('path');

const TRANSLATIONS = {
  hi: {
    ipd: { currentlyAccommodated: "वर्तमान में समायोजित", awaitingErOpdClearance: "ईआर/ओपीडी क्लीयरेंस की प्रतीक्षा", icuOccupancy: "आईसीयू ऑक्यूपेंसी", criticalCareBeds: "क्रिटिकल केयर बेड", patient: "मरीज़", attendingDoctor: "उपचार डॉक्टर", action: "कार्रवाई", noActiveAdmissionsCurrentlyTra: "वर्तमान में कोई सक्रिय प्रवेश ट्रैकिंग नहीं।", nursingFlowsheet: "नर्सिंग फ्लोशीट", requestTime: "अनुरोध का समय", diagnosisNotes: "निदान / नोट्स", noPendingAdmissionRequestsFrom: "ओपीडी/ईआर से कोई लंबित प्रवेश अनुरोध नहीं।", icu01IntensiveCare: "आईसीयू-01 (गहन चिकित्सा)", pvt205PrivateRoomSuite: "पीवीटी-205 (प्राइवेट रूम सुइट)", inpatientDepartment: "इनपेशेंट विभाग (आईपीडी)", admissionRequestsTab: "प्रवेश अनुरोध", admHash: "प्रवेश #", bedAllocatedStr: "बिस्तर आवंटित", generalWardStr: "जनरल वार्ड", assignedDr: "नियुक्त", triageStandard: "ट्रायज मानक", selectAvailableBedStar: "उपलब्ध बिस्तर चुनें *", dropdownSyncedWithBedMatrix: "— बिस्तर मैट्रिक्स के साथ सिंक —" },
    billing: { serviceCategory: "सेवा श्रेणी", quantity: "मात्रा", unitPrice: "इकाई मूल्य", collectDeposit: "जमा राशि लें", fileClaim: "दावा दायर करें", approveClaim: "दावा मंजूर करें", provider: "प्रदाता", preAuth: "पूर्व-प्राधिकरण", coverageLimit: "कवरेज सीमा", claimedAmount: "दावा किया गया", insurancePayable: "बीमा देय", patientPayable: "मरीज़ देय", depositsReceived: "प्राप्त जमा", paymentsReceived: "प्राप्त भुगतान", outstandingBalance: "बकाया शेष", fullySettled: "पूरी तरह से भुगतान किया गया", paymentMode: "भुगतान का प्रकार", referenceId: "संदर्भ आईडी", deposits: "जमा", estimates: "अनुमान", creditNotes: "क्रेडिट नोट्स", crossEvents: "क्रॉस इवेंट्स", loadingFinancialData: "आर्थिक डेटा लोड हो रहा है...", patient: "मरीज़", utilized: "उपयोग किया गया", balance: "शेष राशि" }
  },
  mr: {
    ipd: { currentlyAccommodated: "सध्याचे रुग्ण", awaitingErOpdClearance: "ER/OPD क्लिअरन्सची प्रतीक्षा", icuOccupancy: "ICU व्याप्ती", criticalCareBeds: "अतिदक्षता बेड", patient: "रुग्ण", attendingDoctor: "उपचार डॉक्टर", action: "कृती", noActiveAdmissionsCurrentlyTra: "सध्या कोणतेही सक्रिय प्रवेश ट्रॅकिंग नाही.", nursingFlowsheet: "नर्सिंग फ्लोशीट", requestTime: "विनंतीची वेळ", diagnosisNotes: "निदान / नोट्स", noPendingAdmissionRequestsFrom: "OPD/ER कडून प्रलंबित प्रवेश विनंती नाही.", icu01IntensiveCare: "ICU-01 (गहन चिकित्सा)", pvt205PrivateRoomSuite: "PVT-205 (प्रायव्हेट रूम सुट)", admissionRequestsTab: "प्रवेश विनंती", generalWardStr: "जनरल वॉर्ड", selectAvailableBedStar: "उपलब्ध बेड निवडा *" },
    billing: { serviceCategory: "सेवा प्रवर्ग", quantity: "प्रमाण", unitPrice: "दर", collectDeposit: "ठेव गोळा करा", fileClaim: "दावा दाखल करा", approveClaim: "मंजूर करा", preAuth: "पूर्व-मंजूरी", coverageLimit: "कवरेज मर्यादा", claimedAmount: "दावा केलेली रक्कम", depositsReceived: "प्राप्त ठेव", paymentsReceived: "प्राप्त पेमेंट", outstandingBalance: "शिल्लक थकीत", fullySettled: "पूर्ण सेटलमेंट", balance: "शिल्लक" }
  },
  es: {
    ipd: { currentlyAccommodated: "Actualmente acomodado", awaitingErOpdClearance: "Esperando autorización ER/OPD", icuOccupancy: "Ocupación de UCI", criticalCareBeds: "Camas de cuidados críticos", patient: "Paciente", attendingDoctor: "Médico tratante", action: "Acción", noActiveAdmissionsCurrentlyTra: "No hay ingresos activos en seguimiento.", nursingFlowsheet: "Hoja de flujo de enfermería", requestTime: "Hora de la solicitud", diagnosisNotes: "Notas de diagnóstico", noPendingAdmissionRequestsFrom: "No hay solicitudes de ingreso pendientes.", admissionRequestsTab: "Solicitudes de admisión" }
  }
};

const LANGUAGES = ['hi', 'mr', 'es', 'fr', 'de', 'ar', 'zh', 'ja', 'pt', 'ru'];

for (const lang of LANGUAGES) {
  const localeFile = path.join(__dirname, `locales/${lang}.json`);
  let data = JSON.parse(fs.readFileSync(localeFile, 'utf8'));
  const tr = TRANSLATIONS[lang] || {};
  for (const module in tr) {
    data[module] = { ...(data[module] || {}), ...tr[module] };
  }
  fs.writeFileSync(localeFile, JSON.stringify(data, null, 2) + '\n');
}
console.log("Updated major untranslated keys.");
