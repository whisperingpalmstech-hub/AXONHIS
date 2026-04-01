const fs = require('fs');
const path = require('path');

const NAV_FIX = {
  en: {
    nav: {
      dashboard: "Dashboard",
      patients: "Patients",
      patientManagement: "Patient Management",
      patientRegistry: "Patient Registry",
      encounters: "Encounters",
      scheduling: "Scheduling",
      clinicalOps: "Clinical Workspace",
      rpiwWorkspace: "RPIW Workspace",
      tasks: "Tasks",
      orders: "Orders",
      clinicalOrders: "Clinical Orders",
      doctorDesk: "Doctor Desk",
      opdVisits: "Outpatient (OPD)",
      smartQueue: "Smart Queue",
      nursingTriage: "Nursing Triage",
      emergencyRoom: "Emergency (ER)",
      operationTheater: "Operating Theatre",
      ipdManagement: "Inpatient (IPD)",
      ipdAdmissions: "Admissions",
      wardsAndBeds: "Ward Board",
      ipdNursing: "Nursing Station",
      ipdNursingVitals: "Nursing Vitals",
      ipdDoctorDesk: "Doctor Rounds",
      ipdBilling: "IPD Billing",
      ipdTransfers: "Bed Transfers",
      ipdDischarge: "Smart Discharge",
      visitorMlc: "Visitor & MLC",
      laboratory: "Diagnostics",
      lisOrders: "LIS Orders",
      phlebotomy: "Phlebotomy",
      sampleReceiving: "Sample Receiving",
      labProcessing: "Lab Processing",
      analyzerHub: "Analyzer Hub",
      resultValidation: "Validation Desk",
      reportHandover: "Report Handover",
      advancedDiagnostics: "Advanced Diagnostics",
      extendedLab: "Extended Lab Services",
      radiology: "Radiology",
      bloodBank: "Blood Bank",
      pharmacy: "Pharmacy",
      rxWorklist: "Rx Worklist",
      pharmacySales: "Walk-in Sales",
      ipMedicationIssue: "IP Medication Issue",
      pharmacyReturns: "Returns",
      ipPharmacyReturns: "IP Returns",
      narcoticsVault: "Narcotics Vault",
      inventoryIntelligence: "Inventory Intelligence",
      pharmacyCore: "Pharmacy Core",
      pharmacyBilling: "Billing & Compliance",
      billing: "Finance & Billing",
      billingMasters: "Billing Masters",
      rcmBilling: "RCM Billing",
      administration: "Administration",
      users: "Users",
      systemSettings: "System Settings",
      coreSystem: "Core System",
      audit: "Audit Logs",
      analytics: "Analytics & AI",
      biIntelligence: "BI Intelligence",
      aiPlatform: "AI Platform",
      organizations: "Organizations (SaaS)",
      communication: "Communication"
    }
  },
  hi: {
    nav: {
      dashboard: "डैशबोर्ड",
      patients: "मरीज़",
      patientRegistry: "मरीज़ रजिस्ट्री",
      encounters: "Encounter",
      scheduling: "शेड्यूलिंग",
      clinicalOps: "नैदानिक कार्यस्थल",
      rpiwWorkspace: "RPIW वर्कस्पेस",
      tasks: "कार्य",
      orders: "ऑर्डर",
      doctorDesk: "डॉक्टर डेस्क",
      opdVisits: "ओपीडी (OPD)",
      smartQueue: "स्मार्ट कतार",
      nursingTriage: "नर्सिंग ट्राइएज",
      emergencyRoom: "आपातकालीन (ER)",
      operationTheater: "ऑपरेशन थिएटर",
      ipdManagement: "आईपीडी (IPD)",
      ipdAdmissions: "आईपीडी प्रवेश",
      wardsAndBeds: "वार्ड और बेड",
      ipdNursing: "नर्सिंग स्टेशन",
      ipdNursingVitals: "नर्सिंग महत्वपूर्ण संकेत",
      ipdDoctorDesk: "डॉक्टर राउंड",
      ipdBilling: "आईपीडी बिलिंग",
      ipdTransfers: "बेड स्थानांतरण",
      ipdDischarge: "स्मार्ट डिस्चार्ज"
    }
  },
  mr: {
    nav: {
      dashboard: "डॅशबोर्ड",
      patients: "रुग्ण",
      patientRegistry: "रुग्ण नोंदणी",
      encounters: "एन्काउंटर",
      scheduling: "शेड्युलिंग",
      clinicalOps: "क्लिनिकल वर्कस्पेस",
      rpiwWorkspace: "RPIW वर्कस्पेस",
      tasks: "कार्ये",
      orders: "ऑर्डर्स",
      doctorDesk: "डॉक्टर डेस्क",
      opdVisits: "ओपीडी (OPD)",
      smartQueue: "स्मार्ट रांग",
      nursingTriage: "नर्सिंग ट्रायज",
      emergencyRoom: "आपातकालीन कक्ष",
      operationTheater: "शस्त्रक्रिया गृह (OT)",
      ipdManagement: "आयपीडी व्यवस्थापन",
      ipdAdmissions: "IPD प्रवेश",
      wardsAndBeds: "वॉर्ड आणि बेड",
      ipdNursing: "IPD नर्सिंग",
      ipdNursingVitals: "नर्सिंग व्हायटल्स",
      ipdDoctorDesk: "IPD डॉक्टर डेस्क",
      ipdBilling: "आयपीडी बिलिंग",
      ipdTransfers: "बेड बदल्या",
      ipdDischarge: "स्मार्ट डिस्चार्ज",
      laboratory: "प्रयोगशाळा",
      pharmacy: "औषधालय"
    }
  }
};

const LANGUAGES = ['en', 'hi', 'mr', 'es', 'fr', 'de', 'ar', 'zh', 'ja', 'pt', 'ru'];

for (const lang of LANGUAGES) {
  const file = path.join(__dirname, `locales/${lang}.json`);
  let data = JSON.parse(fs.readFileSync(file, 'utf8'));
  
  if (!data.nav) data.nav = {};
  
  const translations = NAV_FIX[lang] ? NAV_FIX[lang].nav : NAV_FIX.en.nav;
  
  // Fill all keys from English to ensure no raw keys
  for (const key in NAV_FIX.en.nav) {
    data.nav[key] = translations[key] || data.nav[key] || NAV_FIX.en.nav[key];
  }
  
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
}
console.log("Global Sidebar Key synchronization complete.");
