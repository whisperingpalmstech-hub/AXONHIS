const fs = require('fs');
const path = require('path');

const NAV_DATA = {
  en: {
    dashboard: "Dashboard",
    patients: "Patients",
    patientRegistry: "Patient Registry",
    encounters: "Encounters",
    scheduling: "Scheduling",
    clinicalOps: "Clinical Workspace",
    rpiwWorkspace: "RPIW Workspace",
    tasks: "Tasks",
    clinicalOrders: "Orders",
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
  },
  es: {
    dashboard: "Panel de Control",
    patients: "Pacientes",
    patientRegistry: "Registro de Pacientes",
    encounters: "Consultas",
    scheduling: "Agenda",
    clinicalOps: "Espacio Clínico",
    rpiwWorkspace: "Espacio RPIW",
    tasks: "Tareas",
    clinicalOrders: "Órdenes",
    doctorDesk: "Escritorio Médico",
    opdVisits: "Consultas Externas",
    smartQueue: "Cola Inteligente",
    nursingTriage: "Triaje de Enfermería",
    emergencyRoom: "Urgencias (ER)",
    operationTheater: "Quirófano",
    ipdManagement: "Hospitalización",
    ipdAdmissions: "Admisiones",
    wardsAndBeds: "Gestión de Camas",
    ipdNursing: "Estación de Enfermería",
    ipdNursingVitals: "Signos Vitales",
    ipdDoctorDesk: "Rondas Médicas",
    ipdBilling: "Facturación IPD",
    ipdTransfers: "Traslados",
    ipdDischarge: "Alta Inteligente",
    visitorMlc: "Visitas y MLC",
    laboratory: "Diagnósticos",
    lisOrders: "Órdenes LIS",
    phlebotomy: "Flebotomía",
    sampleReceiving: "Recepción de Muestras",
    labProcessing: "Procesamiento Lab",
    analyzerHub: "Integración Analizadores",
    resultValidation: "Validación de Resultados",
    reportHandover: "Entrega de Informes",
    advancedDiagnostics: "Diagnóstico Avanzado",
    extendedLab: "Laboratorio Extendido",
    radiology: "Radiología",
    bloodBank: "Banco de Sangre",
    pharmacy: "Farmacia",
    rxWorklist: "Lista de Recetas",
    pharmacySales: "Ventas de Farmacia",
    ipMedicationIssue: "Dispensación Interna",
    pharmacyReturns: "Devoluciones",
    ipPharmacyReturns: "Devoluciones IPD",
    narcoticsVault: "Bóveda Narcóticos",
    inventoryIntelligence: "Inteligencia de Inventario",
    pharmacyCore: "Farmacia Core",
    pharmacyBilling: "Facturación y Cumplimiento",
    billing: "Finanzas y Facturación",
    billingMasters: "Maestros de Facturación",
    rcmBilling: "Gestión de Ingresos",
    administration: "Administración",
    users: "Usuarios",
    systemSettings: "Configuración",
    coreSystem: "Sistema Core",
    audit: "Logs de Auditoría",
    analytics: "Analítica e IA",
    biIntelligence: "Inteligencia BI",
    aiPlatform: "Plataforma IA",
    organizations: "Organizaciones (SaaS)",
    communication: "Comunicación"
  },
  fr: {
    dashboard: "Tableau de Bord",
    patients: "Patients",
    patientRegistry: "Registre des Patients",
    encounters: "Consultations",
    scheduling: "Planification",
    clinicalOps: "Espace Clinique",
    tasks: "Tâches",
    clinicalOrders: "Commandes",
    doctorDesk: "Bureau du Médecin",
    opdVisits: "Consultations Externes",
    emergencyRoom: "Urgences",
    operationTheater: "Bloc Opératoire",
    ipdManagement: "Hospitalisation",
    ipdAdmissions: "Admissions",
    wardsAndBeds: "Gestion des Lits",
    ipdNursing: "Station Infirmière",
    laboratory: "Diagnostics",
    pharmacy: "Pharmacie",
    billing: "Finance et Facturation",
    administration: "Administration",
    analytics: "Analytique et IA"
  }
  // I will fill others with English for now but ensure the structure is correct.
  // Actually, I should probably use a translation API or common terms for the rest.
  // But let's prioritize the 100% Spanish/Hindi/Marathi first since they are the focus.
};

const LANGUAGES = ['en', 'hi', 'mr', 'es', 'fr', 'de', 'ar', 'zh', 'ja', 'pt', 'ru'];

for (const lang of LANGUAGES) {
  const file = path.join(__dirname, `locales/${lang}.json`);
  if (!fs.existsSync(file)) continue;
  
  let data = JSON.parse(fs.readFileSync(file, 'utf8'));
  if (!data.nav) data.nav = {};
  
  const translations = NAV_DATA[lang] || {};
  
  // Apply translations, fallback to English if not present for this language
  for (const key in NAV_DATA.en) {
    data.nav[key] = translations[key] || data.nav[lang] || data.nav[key] || NAV_DATA.en[key];
  }
  
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
}
console.log("Global Navbar Translation Sync Complete.");
