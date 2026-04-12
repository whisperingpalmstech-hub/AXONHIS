const fs = require('fs');
const path = require('path');

const TRANSLATIONS = {
  hi: {
    er: { emergencyDepartment: "आपातकालीन विभाग", critical: "आपातकालीन", bedsAvailable: "बेड उपलब्ध", mlcCases: "एमएलसी मामले", arrival: "आगमन", policeStation: "थाना", fir: "एफआईआर", vitalSigns: "महत्वपूर्ण लक्षण", bpSys: "बीपी सिस", pulse: "पल्स", pain010: "दर्द (0-10)", triageNotes: "ट्रायज नोट्स", registerPatient: "मरीज़ पंजीकृत करें" },
    tasks: { nurse: "नर्स", doctor: "डॉक्टर", pharmacist: "फार्मासिस्ट", startTask: "कार्य शुरू करें", completeTask: "कार्य पूर्ण करें", executionNotes: "निष्पादन नोट्स", cancel: "रद्द करें", due: "देय", role: "भूमिका" },
    orders: { orderItems: "ऑर्डर आइटम", orderType: "ऑर्डर प्रकार", patient: "मरीज़", encounter: "परामर्श", back: "वापस", next: "अगला", submitOrder: "ऑर्डर सबमिट करें" }
  },
  mr: {
    er: { emergencyDepartment: "आपत्कालीन विभाग", critical: "अतिदक्षता", bedsAvailable: "बेड उपलब्ध", mlcCases: "MLC प्रकरणे", arrival: "आगमन", policeStation: "पोलीस स्टेशन", fir: "एफआयआर", registerPatient: "रुग्ण नोंदणी" },
    tasks: { nurse: "नर्स", doctor: "डॉक्टर", pharmacist: "फार्मासिस्ट", startTask: "काम सुरू करा", completeTask: "काम पूर्ण करा", cancel: "रद्द करा" },
    orders: { orderType: "ऑर्डर प्रकार", patient: "रुग्ण", encounter: "भेट", submitOrder: "ऑर्डर सबमिट करा" }
  },
  es: {
    er: { emergencyDepartment: "Servicio de Urgencias", critical: "Urgente", bedsAvailable: "Camas Disponibles", mlcCases: "Casos Legales", arrival: "Llegada", fir: "Denuncia", registerPatient: "Registrar Paciente" },
    tasks: { nurse: "Enfermera", doctor: "Doctor", pharmacist: "Farmacéutico", startTask: "Iniciar Tarea", completeTask: "Completar Tarea", cancel: "Cancelar" },
    orders: { orderType: "Tipo de Pedido", patient: "Paciente", encounter: "Consulta", submitOrder: "Enviar Pedido" }
  }
  // Simplified for this pass
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
