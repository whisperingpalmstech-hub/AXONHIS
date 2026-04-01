const fs = require('fs');
const path = require('path');

const NEW_KEYS = {
  hi: {
    patients: {
      countryDefault: "भारत",
      modeManual: "नियमावली (Manual)",
      modeManualDesc: "चरण-दर-चरण फ़ॉर्म",
      modeAI: "AI निर्देशित",
      modeAIDesc: "AI प्रश्न पूछता है",
      modeVoice: "आवाज़",
      modeVoiceDesc: "आवाज़ आदेश",
      modeIDScan: "आईडी स्कैन",
      modeIDScanDesc: "ओसीआर दस्तावेज़ स्कैन",
      modeFace: "फेस चेक-इन",
      modeFaceDesc: "बायोमेट्रिक",
      selectGender: "लिंग चुनें",
      cardNumber: "कार्ड नंबर"
    }
  },
  mr: {
    patients: {
      countryDefault: "भारत",
      modeManual: "मॅन्युअल",
      modeManualDesc: "चरण-दर-चरण फॉर्म",
      modeAI: "AI मार्गदर्शित",
      modeAIDesc: "AI प्रश्न विचारतो",
      modeVoice: "आवाज",
      modeVoiceDesc: "आवाज आज्ञा",
      modeIDScan: "ID स्कॅन",
      modeIDScanDesc: "OCR दस्तऐवज स्कॅन",
      modeFace: "फेस चेक-इन",
      modeFaceDesc: "बायोमेट्रिक",
      selectGender: "लिंग निवडा",
      cardNumber: "कार्ड नंबर"
    }
  },
  es: {
    patients: {
      countryDefault: "España",
      modeManual: "Manual",
      modeManualDesc: "Formulario paso a paso",
      modeAI: "Guiado por AI",
      modeAIDesc: "AI hace preguntas",
      modeVoice: "Voz",
      modeVoiceDesc: "Comandos de voz",
      modeIDScan: "Escaneo de ID",
      modeIDScanDesc: "Escaneo OCR de documentos",
      modeFace: "Check-in facial",
      modeFaceDesc: "Biométrico",
      selectGender: "Seleccionar género",
      cardNumber: "Número de tarjeta"
    }
  },
  fr: {
    patients: {
       countryDefault: "France",
       modeManual: "Manuel",
       modeManualDesc: "Formulaire étape par étape",
       modeAI: "Guidé par IA",
       modeAIDesc: "L'IA pose des questions",
       modeVoice: "Voix",
       modeVoiceDesc: "Commandes vocales",
       modeIDScan: "Scan d'ID",
       modeIDScanDesc: "Scan OCR de documents",
       modeFace: "Check-in facial",
       modeFaceDesc: "Biométrique",
       selectGender: "Sélectionnez le sexe",
       cardNumber: "Numéro de carte"
    }
  },
  ar: {
    patients: {
       countryDefault: "المملكة العربية السعودية",
       modeManual: "يدوي",
       modeManualDesc: "نموذج خطوة بخطوة",
       modeAI: "مسترشد بالذكاء الاصطناعي",
       modeAIDesc: "الذكاء الاصطناعي يطرح الأسئلة",
       modeVoice: "صوت",
       modeVoiceDesc: "أوامر صوتية",
       modeIDScan: "مسح الهوية",
       modeIDScanDesc: "مسح المستندات OCR",
       modeFace: "تسجيل الوصول بالوجه",
       modeFaceDesc: "بيومتري",
       selectGender: "اختر الجنس",
       cardNumber: "رقم البطاقة"
    }
  }
};

const LANGUAGES = ['hi', 'mr', 'es', 'fr', 'ar', 'de', 'zh', 'ja', 'pt', 'ru'];
const en = JSON.parse(fs.readFileSync(path.join(__dirname, 'locales/en.json'), 'utf8'));

for (const lang of LANGUAGES) {
  const file = path.join(__dirname, `locales/${lang}.json`);
  let data = JSON.parse(fs.readFileSync(file, 'utf8'));
  const translations = NEW_KEYS[lang] || {};
  
  // Ensure patients module exists
  if (!data.patients) data.patients = {};
  
  // Keys to sync from EN
  const keysToSync = [
    'countryDefault', 'modeManual', 'modeManualDesc', 'modeAI', 'modeAIDesc', 
    'modeVoice', 'modeVoiceDesc', 'modeIDScan', 'modeIDScanDesc', 
    'modeFace', 'modeFaceDesc', 'selectGender', 'cardNumber'
  ];

  for (const key of keysToSync) {
    if (translations.patients && translations.patients[key]) {
      data.patients[key] = translations.patients[key];
    } else if (en.patients[key]) {
      // Use English as fallback to maintain structure
      data.patients[key] = en.patients[key];
    }
  }
  
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
}
console.log("Updated all relevant languages with Patient Registration registration keys.");
