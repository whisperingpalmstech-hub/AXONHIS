const fs = require('fs');
const path = require('path');

const NAV_DATA = {
  en: {
    dashboard: "Dashboard", patients: "Patients", patientRegistry: "Patient Registry",
    encounters: "Encounters", scheduling: "Scheduling", clinicalOps: "Clinical Workspace",
    rpiwWorkspace: "RPIW Workspace", tasks: "Tasks", clinicalOrders: "Orders",
    doctorDesk: "Doctor Desk", opdVisits: "Outpatient (OPD)",
    emergencyRoom: "Emergency (ER)", operationTheater: "Operating Theatre",
    ipdManagement: "Inpatient (IPD)", ipdAdmissions: "Admissions",
    wardsAndBeds: "Ward Board", ipdNursing: "Nursing Station",
    ipdNursingVitals: "Nursing Vitals", ipdDoctorDesk: "Doctor Rounds",
    ipdBilling: "IPD Billing", ipdTransfers: "Bed Transfers",
    ipdDischarge: "Smart Discharge", laboratory: "Diagnostics",
    pharmacy: "Pharmacy", billing: "Finance & Billing",
    administration: "Administration", analytics: "Analytics & AI", languageLabel: "LANGUAGE"
  },
  es: {
    dashboard: "Panel de Control", patients: "Pacientes", patientRegistry: "Registro de Pacientes",
    encounters: "Consultas", scheduling: "Agenda", clinicalOps: "Área Clínica",
    rpiwWorkspace: "Espacio RPIW", tasks: "Tareas", clinicalOrders: "Órdenes",
    doctorDesk: "Escritorio Médico", opdVisits: "Consultas Externas",
    emergencyRoom: "Urgencias (ER)", operationTheater: "Quirófano",
    ipdManagement: "Hospitalización", ipdAdmissions: "Admisiones",
    wardsAndBeds: "Gestión de Camas", ipdNursing: "Estación de Enfermería",
    ipdNursingVitals: "Signos Vitales", ipdDoctorDesk: "Rondas Médicas",
    ipdBilling: "Facturación IPD", ipdTransfers: "Traslados",
    ipdDischarge: "Alta Inteligente", laboratory: "Diagnósticos",
    pharmacy: "Farmacia", billing: "Finanzas y Facturación",
    administration: "Administración", analytics: "Analítica e IA", languageLabel: "IDIOMA"
  },
  hi: {
    dashboard: "डैशबोर्ड", patients: "मरीज़", patientRegistry: "मरीज़ रजिस्ट्री",
    encounters: "एन्काउंटर", scheduling: "शेड्यूलिंग", clinicalOps: "नैदानिक कार्यस्थल",
    tasks: "कार्य", clinicalOrders: "ऑर्डर", doctorDesk: "डॉक्टर डेस्क",
    opdVisits: "ओपीडी (OPD)", emergencyRoom: "आपातकालीन (ER)",
    ipdManagement: "आईपीडी (IPD)", ipdAdmissions: "आईपीडी प्रवेश",
    wardsAndBeds: "वार्ड और बेड", ipdNursing: "नर्सिंग स्टेशन",
    laboratory: "प्रयोगशाला", pharmacy: "औषधालय", administration: "प्रशासन", languageLabel: "भाषा"
  },
  mr: {
    dashboard: "डॅशबोर्ड", patients: "रुग्ण", patientRegistry: "रुग्ण नोंदणी",
    encounters: "एन्काउंटर", scheduling: "शेड्युलिंग", clinicalOps: "क्लिनिकल वर्कस्पेस",
    tasks: "कार्ये", clinicalOrders: "ऑर्डर्स", doctorDesk: "डॉक्टर डेस्क",
    opdVisits: "ओपीडी (OPD)", emergencyRoom: "आपातकालीन",
    ipdManagement: "आयपीडी व्यवस्थापन", ipdAdmissions: "आयपीडी प्रवेश",
    wardsAndBeds: "वॉर्ड आणि बेड", ipdNursing: "आयपीडी नर्सिंग",
    laboratory: "प्रयोगशाळा", pharmacy: "औषधालय", administration: "प्रशासन", languageLabel: "भाषा"
  }
};

const LANGUAGES = ['en', 'hi', 'mr', 'es', 'fr', 'de', 'ar', 'zh', 'ja', 'pt', 'ru'];

for (const lang of LANGUAGES) {
  const file = path.join(__dirname, `locales/${lang}.json`);
  if (!fs.existsSync(file)) continue;
  
  let data = JSON.parse(fs.readFileSync(file, 'utf8'));
  if (!data.nav) data.nav = {};
  
  const translations = NAV_DATA[lang] || {};
  
  for (const key in NAV_DATA.en) {
    // FORCE OVERWRITE with correct data if available, or English fallback
    data.nav[key] = translations[key] || NAV_DATA.en[key];
  }
  
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
}
console.log("Forced Global Nav Override Complete.");
