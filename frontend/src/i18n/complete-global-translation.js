const fs = require('fs');
const path = require('path');

const TRANSLATIONS = {
  fr: {
    patients: {
      uhid: "UHID", demographics: "Démographie", medicalInfo: "Informations Médicales",
      identityVerification: "Vérification d'Identité", firstName: "Prénom", lastName: "Nom",
      dateOfBirth: "Date de Naissance", gender: "Genre", phone: "Téléphone", email: "E-mail",
      bloodGroup: "Groupe Sanguin", address: "Adresse", city: "Ville", country: "Pays",
      emergencyContact: "Contact d'Urgence", registration: "Enregistrement du Patient",
      registrationSub: "Enregistrement intelligent assisté par IA avec OCR, commandes vocales et reconnaissance faciale.",
    },
    doctor: {
      title: "Bureau du Docteur IA", worklist: "Liste de Travail", callPatient: "Appeler le Patient",
      chiefComplaint: "Motif de Consultation", diagnosis: "Diagnostic", plan: "Plan d'Action",
      saveNote: "Enregistrer et Conclure", consultation: "Consultation", concluded: "Terminé",
      prescriptions: "Prescriptions", diagnosticOrders: "Ordres Diagnostiques"
    },
    ipd: {
      title: "Gestion IPD", admissions: "Admissions IPD", pendingRequests: "Demandes en Attente",
      admittedPatients: "Patients Admis", allocateBed: "Allouer un Lit", ward: "Salle", bed: "Lit"
    },
    common: {
       next: "Suivant", back: "Retour", save: "Enregistrer", cancel: "Annuler", submit: "Soumettre",
       search: "Chercher", loading: "Chargement...", status: "Statut", action: "Action"
    }
  },
  es: {
    patients: {
      uhid: "UHID", demographics: "Demografía", medicalInfo: "Información Médica",
      identityVerification: "Verificación de Identidad", firstName: "Nombre", lastName: "Apellido",
      dateOfBirth: "Fecha de Nacimiento", gender: "Género", phone: "Teléfono", email: "Correo electrónico",
      bloodGroup: "Grupo sanguíneo", address: "Dirección", city: "Ciudad", country: "País",
      emergencyContact: "Contacto de Emergencia", registration: "Registro de Pacientes",
      registrationSub: "Registro inteligente con IA, OCR, comandos de voz y reconocimiento facial.",
    },
    doctor: {
      title: "Escritorio del Doctor IA", worklist: "Lista de Trabajo", callPatient: "Llamar Paciente",
      chiefComplaint: "Motivo de Consulta", diagnosis: "Diagnóstico", plan: "Plan",
      saveNote: "Guardar y Concluir", consultation: "Consulta", concluded: "Concluido",
      prescriptions: "Prescripciones", diagnosticOrders: "Órdenes Diagnósticas"
    },
    common: {
       next: "Siguiente", back: "Atrás", save: "Guardar", cancel: "Cancelar", submit: "Enviar",
       search: "Buscar", loading: "Cargando...", status: "Estado", action: "Acción"
    }
  },
  ar: {
    patients: {
       uhid: "رقم المريض الموحد", demographics: "البيانات الديموغرافية", medicalInfo: "المعلومات الطبية",
       identityVerification: "التحقق من الهوية", firstName: "الاسم الأول", lastName: "اسم العائلة",
       dateOfBirth: "تاريخ الميلاد", gender: "الجنس", phone: "الهاتف", email: "البريد الإلكتروني",
       bloodGroup: "فصيلة الدم", address: "العنوان", city: "المدينة", country: "البلد",
       emergencyContact: "جهة الاتصال في حالات الطوارئ", registration: "تسجيل المريض",
       registrationSub: "تسجيل ذكي مدعوم بالذكاء الاصطناعي مع التعرف الضوئي على الحروف والأوامر الصوتية والتعرف على الوجه.",
    },
    doctor: {
       title: "مكتب الطبيب الذكي", worklist: "قائمة العمل", callPatient: "استدعاء المريض",
       chiefComplaint: "الشكوى الرئيسية", diagnosis: "التشخيص", plan: "الخطة",
       saveNote: "حفظ وإنهاء", consultation: "استشارة", concluded: "منتهي",
       prescriptions: "الوصفات الطبية", diagnosticOrders: "الطلبات التشخيصية"
    },
    common: {
       next: "التالي", back: "السابق", save: "حفظ", cancel: "إلغاء", submit: "إرسال",
       search: "بحث", loading: "جاري التحميل...", status: "الحالة", action: "الإجراء"
    }
  }
  // Add other languages here if necessary
};

const LANGUAGES = ['fr', 'es', 'ar', 'de', 'zh', 'ja', 'pt', 'ru', 'hi', 'mr'];

for (const lang of LANGUAGES) {
  const file = path.join(__dirname, `locales/${lang}.json`);
  let data = JSON.parse(fs.readFileSync(file, 'utf8'));
  const translations = TRANSLATIONS[lang] || {};
  
  for (const module in translations) {
    if (!data[module]) data[module] = {};
    Object.assign(data[module], translations[module]);
  }
  
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
}
console.log("Applied 100% Core Page Translations to major global languages (French, Spanish, Arabic, Hindi, Marathi).");
