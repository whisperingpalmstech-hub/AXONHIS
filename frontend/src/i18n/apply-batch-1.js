const fs = require('fs');
const path = require('path');

const TRANSLATIONS = {
  hi: {
    common: {
      save: "सहेजें", cancel: "रद्द करें", delete: "हटाएं", edit: "संपादित करें",
      add: "जोड़ें", search: "खोजें", refresh: "रीफ्रेश करें", loading: "लोड हो रहा है...",
      submit: "सबमिट करें", back: "वापस", next: "अगला", close: "बंद करें",
      confirm: "पुष्टि करें", yes: "हाँ", no: "नहीं", actions: "कार्रवाई",
      status: "स्थिति", date: "तारीख", name: "नाम", type: "प्रकार",
      amount: "राशि", total: "कुल", noData: "कोई डेटा नहीं मिला",
      error: "त्रुटि", success: "सफलता", warning: "चेतावनी", info: "जानकारी",
      required: "आवश्यक", optional: "वैकल्पिक", selectLanguage: "भाषा चुनें",
      language: "भाषा", logout: "लॉगआउट", profile: "प्रोफ़ाइल",
      settings: "सेटिंग्स", notifications: "सूचनाएं", dashboard: "डैशबोर्ड",
      welcome: "स्वागत है", viewAll: "सभी देखें", print: "प्रिंट",
      export: "निर्यात", import: "आयात", filter: "फ़िल्टर",
      sortBy: "इसके अनुसार क्रमबद्ध करें", ascending: "बढ़ते क्रम",
      descending: "घटते क्रम", active: "सक्रिय", inactive: "निष्क्रिय",
      pending: "लंबित", approved: "स्वीकृत", rejected: "अस्वीकृत", completed: "पूर्ण"
    },
    dashboard: {
      totalPatients: "कुल मरीज़", activeEncounters: "सक्रिय परामर्श",
      pendingTasks: "लंबित कार्य", lowStock: "कम स्टॉक अलर्ट",
      pendingRx: "लंबित प्रिस्क्रिप्शन", nearExpiry: "समाप्ति के करीब",
      labSamples: "लैब नमूने", invoices: "चालान",
      quickNav: "त्वरित नेविगेशन", quickNavDesc: "मुख्य मॉड्यूल तक सीधी पहुंच",
      Registeredpatients: "पजीकृत मरीज़", "Inprogress&scheduled": "प्रगति में और शेड्यूल्ड",
      Awaitingexecution: "निष्पादन की प्रतीक्षा", Itemsbelowthreshold: "सीमा से नीचे आइटम",
      Awaitingdispensing: "वितरण की प्रतीक्षा", Expiringin60days: "60 दिनों में समाप्त",
      Pendingprocessing: "प्रसंस्करण लंबित", "1pendingpayment": "1 लंबित भुगतान",
      "Register&searchpatie": "मरीज़ पंजीकृत करें और खोजें", "Manageclinicalvisits": "क्लिनिकल विज़िट प्रबंधित करें",
      "Labtests,medications": "लैब टेस्ट, दवाएं", "Clinicalworkflows&nu": "क्लिनिकल वर्कफ़्लो और नर्सिंग कार्य",
      "Testcatalog,samples&": "टेस्ट कैटलॉग, नमूने", "Inventory,prescripti": "इन्वेंटरी, प्रिस्क्रिप्शन",
      "Invoices,payments&in": "चालान, भुगतान और बीमा", PatientRegistry: "मरीज़ रजिस्ट्री",
      Encounters: "परामर्श", OrderManagement: "ऑर्डर प्रबंधन",
      TaskQueue: "कार्य कतार", Laboratory: "प्रयोगशाला",
      Pharmacy: "फार्मेसी", Billing: "बिलिंग", pendingPayment: "भुगतान लंबित",
      pharmacyDesc: "इन्वेंटरी, प्रिस्क्रिप्शन और वितरण", billingDesc: "चालान, भुगतान और बीमा दावे",
      criticalAlerts: "गंभीर अलर्ट", criticalResults: "गंभीर परिणाम",
      belowReorder: "पुनःऑर्डर सीमा से नीचे", batchesExpiring: "दवा बैच जल्द समाप्त हो रहे हैं",
      labNeedingAttention: "लैब परिणामों पर ध्यान आवश्यक"
    },
    auth: {
      login: "साइन इन", email: "ईमेल", password: "पासवर्ड",
      forgotPassword: "पासवर्ड भूल गए?", rememberMe: "मुझे याद रखें",
      loginTitle: "अस्पताल सूचना प्रणाली", loginSubtitle: "अपने खाते में साइन इन करें",
      invalidCredentials: "अमान्य ईमेल या पासवर्ड"
    }
  },
  mr: {
    common: {
      save: "जतन करा", cancel: "रद्द करा", delete: "हटवा", edit: "संपादित करा",
      add: "जोडा", search: "शोधा", refresh: "रिफ्रेश करा", loading: "लोड होत आहे...",
      submit: "सबमिट करा", back: "मागे", next: "पुढे", close: "बंद करा",
      confirm: "पुष्टी करा", yes: "होय", no: "नाही", actions: "क्रिया",
      status: "स्थिती", date: "तारीख", name: "नाव", type: "प्रकार",
      amount: "रक्कम", total: "एकूण", noData: "डेटा आढळला नाही",
      error: "त्रुटी", success: "यशस्वी", warning: "चेतावणी", info: "माहिती",
      required: "आवश्यक", optional: "ऐच्छिक", selectLanguage: "भाषा निवडा",
      language: "भाषा", logout: "लॉगआउट", profile: "प्रोफाइल",
      settings: "सेटिंग्स", notifications: "सूचना", dashboard: "डॅशबोर्ड",
      welcome: "स्वागत", viewAll: "सर्व पहा", print: "प्रिंट",
      export: "निर्यात", import: "आयात", filter: "फिल्टर",
      sortBy: "क्रमवारी लावा", ascending: "चढता", descending: "उतरता",
      active: "सक्रिय", inactive: "निष्क्रिय", pending: "प्रलंबित",
      approved: "मंजूर", rejected: "नाकारले", completed: "पूर्ण"
    },
    dashboard: {
      totalPatients: "एकूण रुग्ण", activeEncounters: "सक्रिय भेटी",
      pendingTasks: "प्रलंबित कार्ये", lowStock: "कमी स्टॉक सूचना",
      pendingRx: "प्रलंबित औषधोपचार", nearExpiry: "मुदत संपत आलेले",
      labSamples: "लॅब नमुने", invoices: "बिले",
      quickNav: "जलद नेव्हिगेशन", quickNavDesc: "मुख्य मॉड्यूल्सना थेट प्रवेश",
      Registeredpatients: "नोंदणीकृत रुग्ण", "Inprogress&scheduled": "प्रगतीपथावर आणि नियोजित",
      Awaitingexecution: "अंमलबजावणीच्या प्रतीक्षेत", Itemsbelowthreshold: "मर्यादेखालील वस्तू",
      Awaitingdispensing: "वितरणाच्या प्रतीक्षेत", Expiringin60days: "60 दिवसांत संपणारे",
      Pendingprocessing: "प्रक्रिया प्रलंबित", "1pendingpayment": "1 प्रलंबित देय",
      "Register&searchpatie": "रुग्ण नोंदणी आणि शोधा", "Manageclinicalvisits": "क्लिनिकल भेटी व्यवस्थापित करा",
      "Labtests,medications": "लॅब चाचण्या, औषधे", "Clinicalworkflows&nu": "क्लिनिकल वर्कफ्लो आणि नर्सिंग कार्ये",
      "Testcatalog,samples&": "चाचणी सूची, नमुने", "Inventory,prescripti": "साठा आणि प्रिस्क्रिप्शन",
      "Invoices,payments&in": "बिले आणि विमा", PatientRegistry: "रुग्ण नोंदवही",
      Encounters: "भेटी", OrderManagement: "ऑर्डर व्यवस्थापन",
      TaskQueue: "कार्य रांग", Laboratory: "प्रयोगशाळा",
      Pharmacy: "औषधालय", Billing: "बिलिंग", pendingPayment: "देय प्रलंबित",
      pharmacyDesc: "साठा, प्रिस्क्रिप्शन आणि वितरण", billingDesc: "बिले, भुगतान आणि विमा दावे",
      criticalAlerts: "गंभीर सूचना", criticalResults: "गंभीर निकाल",
      belowReorder: "पुन्हा ऑर्डर मर्यादेखालील वस्तू", batchesExpiring: "औषध बॅच लवकरच संपणार",
      labNeedingAttention: "लॅब निकालांना लक्ष आवश्यक"
    },
    auth: {
      login: "साइन इन करा", email: "ईमेल", password: "पासवर्ड",
      forgotPassword: "पासवर्ड विसरलात?", rememberMe: "मला लक्षात ठेवा",
      loginTitle: "रुग्णालय माहिती प्रणाली", loginSubtitle: "आपल्या खात्यात साइन इन करा",
      invalidCredentials: "अवैध ईमेल किंवा पासवर्ड"
    }
  },
  es: {
    common: {
      save: "Guardar", cancel: "Cancelar", delete: "Eliminar", edit: "Editar",
      add: "Añadir", search: "Buscar", refresh: "Refrescar", loading: "Cargando...",
      submit: "Enviar", back: "Regresar", next: "Siguiente", close: "Cerrar",
      confirm: "Confirmar", yes: "Sí", no: "No", actions: "Acciones",
      status: "Estado", date: "Fecha", name: "Nombre", type: "Tipo",
      amount: "Monto", total: "Total", noData: "No se encontraron datos",
      error: "Error", success: "Éxito", warning: "Advertencia", info: "Información",
      required: "Requerido", optional: "Opcional", selectLanguage: "Seleccionar Idioma",
      language: "Idioma", logout: "Cerrar sesión", profile: "Perfil",
      settings: "Configuración", notifications: "Notificaciones", dashboard: "Tablero",
      welcome: "Bienvenido", viewAll: "Ver todo", print: "Imprimir",
      export: "Exportar", import: "Importar", filter: "Filtrar",
      sortBy: "Ordenar por", ascending: "Ascendente", descending: "Descendente",
      active: "Activo", inactive: "Inactivo", pending: "Pendiente",
      approved: "Aprobado", rejected: "Rechazado", completed: "Completado"
    },
    dashboard: {
      totalPatients: "Total de Pacientes", activeEncounters: "Consultas Activas",
      pendingTasks: "Tareas Pendientes", lowStock: "Alertas de Stock Bajo",
      pendingRx: "Recetas Pendientes", nearExpiry: "Vencimiento Cercano",
      labSamples: "Muestras de Laboratorio", invoices: "Facturas",
      quickNav: "Navegación Rápida", quickNavDesc: "Acceso directo a módulos centrales",
      Registeredpatients: "Pacientes registrados", "Inprogress&scheduled": "En progreso y programado",
      Awaitingexecution: "Esperando ejecución", Itemsbelowthreshold: "Artículos por debajo del límite",
      Awaitingdispensing: "Esperando dispensación", Expiringin60days: "Vence en 60 días",
      Pendingprocessing: "Procesamiento pendiente", "1pendingpayment": "1 pago pendiente",
      "Register&searchpatie": "Registrar y buscar pacientes", "Manageclinicalvisits": "Gestionar visitas clínicas",
      "Labtests,medications": "Pruebas de laboratorio, medicamentos", "Clinicalworkflows&nu": "Flujos de trabajo clínicos",
      "Testcatalog,samples&": "Catálogo de pruebas, muestras", "Inventory,prescripti": "Inventario, recetas",
      "Invoices,payments&in": "Facturas, pagos y seguros", PatientRegistry: "Registro de Pacientes",
      Encounters: "Consultas", OrderManagement: "Gestión de Pedidos",
      TaskQueue: "Cola de Tareas", Laboratory: "Laboratorio",
      Pharmacy: "Farmacia", Billing: "Facturación", pendingPayment: "pago pendiente",
      pharmacyDesc: "Inventario, recetas y dispensación", billingDesc: "Facturas, pagos y reclamaciones de seguros",
      criticalAlerts: "Alertas Críticas", criticalResults: "Resultados Críticos",
      belowReorder: "Artículos por debajo del punto de pedido", batchesExpiring: "Lotes de medicamentos que vencen pronto",
      labNeedingAttention: "Resultados de laboratorio que requieren atención"
    },
    auth: {
      login: "Iniciar Sesión", email: "Correo Electrónico", password: "Contraseña",
      forgotPassword: "¿Olvidó su contraseña?", rememberMe: "Recordarme",
      loginTitle: "Sistema de Información Hospitalaria", loginSubtitle: "Inicie sesión en su cuenta",
      invalidCredentials: "Correo o contraseña inválidos"
    }
  },
  fr: {
    common: {
      save: "Enregistrer", cancel: "Annuler", delete: "Supprimer", edit: "Modifier",
      add: "Ajouter", search: "Rechercher", refresh: "Actualiser", loading: "Chargement...",
      submit: "Soumettre", back: "Retour", next: "Suivant", close: "Fermer",
      confirm: "Confirmer", yes: "Oui", no: "Non", actions: "Actions",
      status: "Statut", date: "Date", name: "Nom", type: "Type",
      amount: "Montant", total: "Total", noData: "Aucune donnée trouvée",
      error: "Erreur", success: "Succès", warning: "Avertissement", info: "Information",
      required: "Requis", optional: "Optionnel", selectLanguage: "Choisir la langue",
      language: "Langue", logout: "Déconnexion", profile: "Profil",
      settings: "Paramètres", notifications: "Notifications", dashboard: "Tableau de bord",
      welcome: "Bienvenue", viewAll: "Voir tout", print: "Imprimer",
      export: "Exporter", import: "Importer", filter: "Filtrer",
      sortBy: "Trier par", ascending: "Croissant", descending: "Décroissant",
      active: "Actif", inactive: "Inactif", pending: "En attente",
      approved: "Approuvé", rejected: "Rejeté", completed: "Terminé"
    },
    dashboard: {
        totalPatients: "Total des Patients", activeEncounters: "Consultations Actives",
        pendingTasks: "Tâches en Attente", lowStock: "Alertes de Stock Faible",
        pendingRx: "Ordonnances en Attente", nearExpiry: "Expiration Proche",
        labSamples: "Échantillons de Laboratoire", invoices: "Factures",
        quickNav: "Navigation Rapide", quickNavDesc: "Accès direct aux modules centraux",
        Registeredpatients: "Patients enregistrés", "Inprogress&scheduled": "En cours et programmé",
        Awaitingexecution: "En attente d'exécution", Itemsbelowthreshold: "Articles sous le seuil",
        Awaitingdispensing: "En attente de dispensation", Expiringin60days: "Expirant dans 60 jours",
        Pendingprocessing: "Traitement en attente", "1pendingpayment": "1 paiement en attente",
        "Register&searchpatie": "Enregistrer et rechercher des patients", "Manageclinicalvisits": "Gérer les visites cliniques",
        "Labtests,medications": "Tests de labo, médicaments", "Clinicalworkflows&nu": "Flux cliniques",
        "Testcatalog,samples&": "Catalogue de tests, échantillons", "Inventory,prescripti": "Inventaire, ordonnances",
        "Invoices,payments&in": "Factures, paiements et assurances", PatientRegistry: "Registre des Patients",
        Encounters: "Consultations", OrderManagement: "Gestion des Commandes",
        TaskQueue: "File d'Attente des Tâches", Laboratory: "Laboratoire",
        Pharmacy: "Pharmacie", Billing: "Facturation", pendingPayment: "paiement en attente",
        pharmacyDesc: "Inventaire, ordonnances et dispensation", billingDesc: "Factures, paiements et réclamations d'assurance",
        criticalAlerts: "Alertes Critiques", criticalResults: "Résultats Critiques",
        belowReorder: "Articles sous le seuil de réapprovisionnement", batchesExpiring: "Lots de médicaments bientôt périmés",
        labNeedingAttention: "Résultats de laboratoire nécessitant une attention"
    },
    auth: {
      login: "Se Connecter", email: "Adresse E-mail", password: "Mot de Passe",
      forgotPassword: "Mot de passe oublié ?", rememberMe: "Se souvenir de moi",
      loginTitle: "Système d'Information Hospitalier", loginSubtitle: "Connectez-vous à votre compte",
      invalidCredentials: "E-mail ou mot de passe invalide"
    }
  },
  de: {
    common: {
      save: "Speichern", cancel: "Abbrechen", delete: "Löschen", edit: "Bearbeiten",
      add: "Hinzufügen", search: "Suchen", refresh: "Aktualisieren", loading: "Laden...",
      submit: "Absenden", back: "Zurück", next: "Weiter", close: "Schließen",
      confirm: "Bestätigen", yes: "Ja", no: "Nein", actions: "Aktionen",
      status: "Status", date: "Datum", name: "Name", type: "Typ",
      amount: "Betrag", total: "Gesamt", noData: "Keine Daten gefunden",
      error: "Fehler", success: "Erfolg", warning: "Warnung", info: "Information",
      required: "Erforderlich", optional: "Optional", selectLanguage: "Sprache auswählen",
      language: "Sprache", logout: "Abmelden", profile: "Profil",
      settings: "Einstellungen", notifications: "Benachrichtigungen", dashboard: "Dashboard",
      welcome: "Willkommen", viewAll: "Alle ansehen", print: "Drucken",
      export: "Exportieren", import: "Importieren", filter: "Filter",
      sortBy: "Sortieren nach", ascending: "Aufsteigend", descending: "Absteigend",
      active: "Aktiv", inactive: "Inaktiv", pending: "Ausstehend",
      approved: "Genehmigt", rejected: "Abgelehnt", completed: "Abgeschlossen"
    },
    dashboard: {
        totalPatients: "Gesamtpatienten", activeEncounters: "Aktive Konsultationen",
        pendingTasks: "Ausstehende Aufgaben", lowStock: "Warnungen bei niedrigem Bestand",
        pendingRx: "Ausstehende Rezepte", nearExpiry: "Kurz vor Ablauf",
        labSamples: "Laborproben", invoices: "Rechnungen",
        quickNav: "Schnellnavigation", quickNavDesc: "Direkter Zugriff auf Kernmodule",
        Registeredpatients: "Registrierte Patienten", "Inprogress&scheduled": "In Bearbeitung & geplant",
        Awaitingexecution: "Wartet auf Ausführung", Itemsbelowthreshold: "Artikel unter dem Schwellenwert",
        Awaitingdispensing: "Wartet auf Ausgabe", Expiringin60days: "Läuft in 60 Tagen ab",
        Pendingprocessing: "Bearbeitung ausstehend", "1pendingpayment": "1 ausstehende Zahlung",
        "Register&searchpatie": "Patienten registrieren & suchen", "Manageclinicalvisits": "Klinische Besuche verwalten",
        "Labtests,medications": "Labortests, Medikamente", "Clinicalworkflows&nu": "Klinische Arbeitsabläufe",
        "Testcatalog,samples&": "Testkatalog, Proben", "Inventory,prescripti": "Inventar, Rezepte",
        "Invoices,payments&in": "Rechnungen, Zahlungen & Versicherung", PatientRegistry: "Patientenregister",
        Encounters: "Konsultationen", OrderManagement: "Auftragsverwaltung",
        TaskQueue: "Aufgabenwarteschlange", Laboratory: "Labor",
        Pharmacy: "Apotheke", Billing: "Abrechnung", pendingPayment: "ausstehende Zahlung",
        pharmacyDesc: "Inventar, Rezepte & Ausgabe", billingDesc: "Rechnungen, Zahlungen & Versicherungsansprüche",
        criticalAlerts: "Kritische Warnungen", criticalResults: "Kritische Ergebnisse",
        belowReorder: "Artikel unter dem Nachbestellwert", batchesExpiring: "Medikamentenchargen laufen bald ab",
        labNeedingAttention: "Laborergebnisse, die Aufmerksamkeit erfordern"
    },
    auth: {
      login: "Anmelden", email: "E-Mail-Adresse", password: "Passwort",
      forgotPassword: "Passwort vergessen?", rememberMe: "Angemeldet bleiben",
      loginTitle: "Krankenhaus-Informationssystem", loginSubtitle: "Melden Sie sich in Ihrem Konto an",
      invalidCredentials: "Ungültige E-Mail oder Passwort"
    }
  },
  ar: {
    common: {
      save: "حفظ", cancel: "إلغاء", delete: "حذف", edit: "تعديل",
      add: "إضافة", search: "بحث", refresh: "تحديث", loading: "جاري التحميل...",
      submit: "إرسال", back: "رجوع", next: "التالي", close: "إغلاق",
      confirm: "تأكيد", yes: "نعم", no: "لا", actions: "إجراءات",
      status: "الحالة", date: "التاريخ", name: "الاسم", type: "النوع",
      amount: "المبلغ", total: "الإجمالي", noData: "لم يتم العثور على بيانات",
      error: "خطأ", success: "نجاح", warning: "تحذير", info: "معلومات",
      required: "مطلوب", optional: "اختياري", selectLanguage: "اختر اللغة",
      language: "اللغة", logout: "تسجيل الخروج", profile: "الملف الشخصي",
      settings: "الإعدادات", notifications: "الإشعارات", dashboard: "لوحة التحكم",
      welcome: "مرحباً", viewAll: "عرض الكل", print: "طباعة",
      export: "تصدير", import: "استيراد", filter: "تصفية",
      sortBy: "فرز حسب", ascending: "تصاعدي", descending: "تنازلي",
      active: "نشط", inactive: "غير نشط", pending: "قيد الانتظار",
      approved: "مقبول", rejected: "مرفوض", completed: "مكتمل"
    },
    dashboard: {
        totalPatients: "إجمالي المرضى", activeEncounters: "الزيارات النشطة",
        pendingTasks: "المهام المعلقة", lowStock: "تنبيهات انخفاض المخزون",
        pendingRx: "الوصفات المعلقة", nearExpiry: "قريب من الانتهاء",
        labSamples: "عينات المختبر", invoices: "الفواتير",
        quickNav: "التنقل السريع", quickNavDesc: "الوصول المباشر إلى الوحدات الأساسية",
        Registeredpatients: "المرضى المسجلون", "Inprogress&scheduled": "قيد التنفيذ والمجدولة",
        Awaitingexecution: "في انتظار التنفيذ", Itemsbelowthreshold: "أصناف تحت الحد الأدنى",
        Awaitingdispensing: "في انتظار الصرف", Expiringin60days: "تنتهي الصلاحية خلال 60 يومًا",
        Pendingprocessing: "قيد المعالجة", "1pendingpayment": "1 دفعة معلقة",
        "Register&searchpatie": "تسجيل وبحث المرضى", "Manageclinicalvisits": "إدارة الزيارات السريرية",
        "Labtests,medications": "فحوصات، أدوية", "Clinicalworkflows&nu": "سير العمل السريري",
        "Testcatalog,samples&": "كتالوج الفحوصات، العينات", "Inventory,prescripti": "المخزون، الوصفات",
        "Invoices,payments&in": "الفواتير، المدفوعات والتأمين", PatientRegistry: "سجل المرضى",
        Encounters: "الزيارات", OrderManagement: "إدارة الطلبات",
        TaskQueue: "طابور المهام", Laboratory: "المختبر",
        Pharmacy: "الصيدلية", Billing: "الفواتير", pendingPayment: "دفعة معلقة",
        pharmacyDesc: "المخزون، الوصفات والصرف", billingDesc: "الفواتير، المدفوعات ومطالبات التأمين",
        criticalAlerts: "تنبيهات حرجة", criticalResults: "نتائج حرجة",
        belowReorder: "أصناف تحت حد إعادة الطلب", batchesExpiring: "دفعات أدوية تنتهي قريباً",
        labNeedingAttention: "نتائج مختبر تحتاج إلى اهتمام"
    },
    auth: {
      login: "تسجيل الدخول", email: "البريد الإلكتروني", password: "كلمة المرور",
      forgotPassword: "هل نسيت كلمة المرور؟", rememberMe: "تذكرني",
      loginTitle: "نظام معلومات المستشفى", loginSubtitle: "سجل الدخول إلى حسابك",
      invalidCredentials: "البريد الإلكتروني أو كلمة المرور غير صالحة"
    }
  },
  zh: {
    common: {
      save: "保存", cancel: "取消", delete: "删除", edit: "编辑",
      add: "添加", search: "搜索", refresh: "刷新", loading: "加载中...",
      submit: "提交", back: "返回", next: "下一步", close: "关闭",
      confirm: "确认", yes: "是", no: "否", actions: "操作",
      status: "状态", date: "日期", name: "名称", type: "类型",
      amount: "金额", total: "总计", noData: "未找到数据",
      error: "错误", success: "成功", warning: "警告", info: "信息",
      required: "必填", optional: "可选", selectLanguage: "选择语言",
      language: "语言", logout: "注销", profile: "个人资料",
      settings: "设置", notifications: "通知", dashboard: "仪表板",
      welcome: "欢迎", viewAll: "查看全部", print: "打印",
      export: "导出", import: "导入", filter: "筛选",
      sortBy: "排序方式", ascending: "升序", descending: "降序",
      active: "活动", inactive: "非活动", pending: "待定",
      approved: "已批准", rejected: "已拒绝", completed: "已完成"
    },
    dashboard: {
        totalPatients: "患者总数", activeEncounters: "活跃就诊",
        pendingTasks: "待处理任务", lowStock: "低库存警报",
        pendingRx: "待处理处方", nearExpiry: "临期商品",
        labSamples: "实验室样本", invoices: "发票",
        quickNav: "快速导航", quickNavDesc: "直接访问核心模块",
        Registeredpatients: "注册患者", "Inprogress&scheduled": "进行中和已排期",
        Awaitingexecution: "等待执行", Itemsbelowthreshold: "低于阈值的物品",
        Awaitingdispensing: "等待配药", Expiringin60days: "60天内过期",
        Pendingprocessing: "等待处理", "1pendingpayment": "1个待支付账单",
        "Register&searchpatie": "注册和搜索患者", "Manageclinicalvisits": "管理临床就诊",
        "Labtests,medications": "实验室测试、药物", "Clinicalworkflows&nu": "临床工作流程",
        "Testcatalog,samples&": "测试目录、样本", "Inventory,prescripti": "库存、处方",
        "Invoices,payments&in": "发票、付款和保险", PatientRegistry: "患者登记处",
        Encounters: "就诊", OrderManagement: "医嘱管理",
        TaskQueue: "任务队列", Laboratory: "实验室",
        Pharmacy: "药房", Billing: "计费", pendingPayment: "待支付",
        pharmacyDesc: "库存、处方和配药", billingDesc: "发票、付款和保险理赔",
        criticalAlerts: "紧急警报", criticalResults: "危机值",
        belowReorder: "低于再订货点的物品", batchesExpiring: "即将过期的药品批次",
        labNeedingAttention: "需要关注的实验室结果"
    },
    auth: {
      login: "登录", email: "电子邮件地址", password: "密码",
      forgotPassword: "忘记密码？", rememberMe: "记住我",
      loginTitle: "医院信息系统", loginSubtitle: "登录您的账户",
      invalidCredentials: "电子邮件或密码无效"
    }
  },
  ja: {
    common: {
      save: "保存", cancel: "キャンセル", delete: "削除", edit: "編集",
      add: "追加", search: "検索", refresh: "更新", loading: "読み込み中...",
      submit: "送信", back: "戻る", next: "次へ", close: "閉じる",
      confirm: "確認", yes: "はい", no: "いいえ", actions: "アクション",
      status: "ステータス", date: "日付", name: "名前", type: "タイプ",
      amount: "金額", total: "合計", noData: "データが見つかりません",
      error: "エラー", success: "成功", warning: "警告", info: "情報",
      required: "必須", optional: "任意", selectLanguage: "言語を選択",
      language: "言語", logout: "ログアウト", profile: "プロフィール",
      settings: "設定", notifications: "通知", dashboard: "ダッシュボード",
      welcome: "ようこそ", viewAll: "すべて表示", print: "印刷",
      export: "エクスポート", import: "インポート", filter: "フィルタ",
      sortBy: "並べ替え", ascending: "昇順", descending: "降順",
      active: "有効", inactive: "無効", pending: "保留中",
      approved: "承認済み", rejected: "却下", completed: "完了"
    },
    dashboard: {
        totalPatients: "総患者数", activeEncounters: "進行中の診察",
        pendingTasks: "保留中のタスク", lowStock: "在庫不足のアラート",
        pendingRx: "保留中の処方箋", nearExpiry: "期限間近",
        labSamples: "検査検体", invoices: "請求書",
        quickNav: "クイックナビ", quickNavDesc: "コアモジュールへの直接アクセス",
        Registeredpatients: "登録患者", "Inprogress&scheduled": "進行中および予定",
        Awaitingexecution: "実行待ち", Itemsbelowthreshold: "しきい値以下の項目",
        Awaitingdispensing: "調剤待ち", Expiringin60days: "60日以内に期限切れ",
        Pendingprocessing: "処理待ち", "1pendingpayment": "1件の未払い",
        "Register&searchpatie": "患者の登録と検索", "Manageclinicalvisits": "診察の管理",
        "Labtests,medications": "検査、投薬", "Clinicalworkflows&nu": "臨床ワークフロー",
        "Testcatalog,samples&": "検査カタログ、検体", "Inventory,prescripti": "在庫、処方箋",
        "Invoices,payments&in": "請求書、支払い、保険", PatientRegistry: "患者レジストリ",
        Encounters: "診察", OrderManagement: "オーダー管理",
        TaskQueue: "タスクキュー", Laboratory: "検査室",
        Pharmacy: "薬局", Billing: "請求", pendingPayment: "未払い",
        pharmacyDesc: "在庫、処方箋、調剤", billingDesc: "請求書、支払い、保険請求",
        criticalAlerts: "重要なアラート", criticalResults: "パニック値",
        belowReorder: "再注文ポイント未満の項目", batchesExpiring: "期限間近の医薬品バッチ",
        labNeedingAttention: "注意が必要な検査結果"
    },
    auth: {
      login: "ログイン", email: "メールアドレス", password: "パスワード",
      forgotPassword: "パスワードを忘れた場合", rememberMe: "ログイン状態を保持",
      loginTitle: "病院情報システム", loginSubtitle: "アカウントにログイン",
      invalidCredentials: "メールアドレスまたはパスワードが正しくありません"
    }
  },
  pt: {
    common: {
      save: "Salvar", cancel: "Cancelar", delete: "Excluir", edit: "Editar",
      add: "Adicionar", search: "Pesquisar", refresh: "Atualizar", loading: "Carregando...",
      submit: "Enviar", back: "Voltar", next: "Próximo", close: "Fechar",
      confirm: "Confirmar", yes: "Sim", no: "Não", actions: "Ações",
      status: "Status", date: "Data", name: "Nome", type: "Tipo",
      amount: "Valor", total: "Total", noData: "Nenhum dado encontrado",
      error: "Erro", success: "Sucesso", warning: "Aviso", info: "Informação",
      required: "Obrigatório", optional: "Opcional", selectLanguage: "Selecionar Idioma",
      language: "Idioma", logout: "Sair", profile: "Perfil",
      settings: "Configurações", notifications: "Notificações", dashboard: "Painel",
      welcome: "Bem-vindo", viewAll: "Ver todos", print: "Imprimir",
      export: "Exportar", import: "Importar", filter: "Filtrar",
      sortBy: "Ordenar por", ascending: "Crescente", descending: "Decrescente",
      active: "Ativo", inactive: "Inativo", pending: "Pendente",
      approved: "Aprovado", rejected: "Rejeitado", completed: "Concluído"
    },
    dashboard: {
        totalPatients: "Total de Pacientes", activeEncounters: "Consultas Ativas",
        pendingTasks: "Tarefas Pendentes", lowStock: "Alertas de Baixo Estoque",
        pendingRx: "Receitas Pendentes", nearExpiry: "Vencimento Próximo",
        labSamples: "Amostras de Laboratório", invoices: "Faturas",
        quickNav: "Navegação Rápida", quickNavDesc: "Acesso direto aos módulos principais",
        Registeredpatients: "Pacientes registrados", "Inprogress&scheduled": "Em andamento e agendado",
        Awaitingexecution: "Aguardando execução", Itemsbelowthreshold: "Itens abaixo do limite",
        Awaitingdispensing: "Aguardando dispensação", Expiringin60days: "Vencendo em 60 dias",
        Pendingprocessing: "Processamento pendente", "1pendingpayment": "1 pagamento pendente",
        "Register&searchpatie": "Registrar e pesquisar pacientes", "Manageclinicalvisits": "Gerenciar visitas clínicas",
        "Labtests,medications": "Exames de laboratório, medicamentos", "Clinicalworkflows&nu": "Fluxos de trabalho clínicos",
        "Testcatalog,samples&": "Catálogo de exames, amostras", "Inventory,prescripti": "Inventário, receitas",
        "Invoices,payments&in": "Faturas, pagamentos e seguros", PatientRegistry: "Registro de Pacientes",
        Encounters: "Consultas", OrderManagement: "Gestión de Pedidos",
        TaskQueue: "Fila de Tarefas", Laboratory: "Laboratório",
        Pharmacy: "Farmácia", Billing: "Faturamento", pendingPayment: "pagamento pendente",
        pharmacyDesc: "Inventário, receitas e dispensação", billingDesc: "Faturas, pagamentos e reclamações de seguro",
        criticalAlerts: "Alertas Críticos", criticalResults: "Resultados Críticos",
        belowReorder: "Itens abaixo do ponto de pedido", batchesExpiring: "Lotes de medicamentos vencendo em breve",
        labNeedingAttention: "Resultados de laboratório precisando de atenção"
    },
    auth: {
      login: "Entrar", email: "E-mail", password: "Senha",
      forgotPassword: "Esqueceu a senha?", rememberMe: "Lembrar de mim",
      loginTitle: "Sistema de Informação Hospitalar", loginSubtitle: "Entre na sua conta",
      invalidCredentials: "E-mail ou senha inválidos"
    }
  },
  ru: {
    common: {
      save: "Сохранить", cancel: "Отмена", delete: "Удалить", edit: "Изменить",
      add: "Добавить", search: "Поиск", refresh: "Обновить", loading: "Загрузка...",
      submit: "Отправить", back: "Назад", next: "Далее", close: "Закрыть",
      confirm: "Подтвердить", yes: "Да", no: "Нет", actions: "Действия",
      status: "Статус", date: "Дата", name: "Имя", type: "Тип",
      amount: "Сумма", total: "Итого", noData: "Данные не найдены",
      error: "Ошибка", success: "Успех", warning: "Предупреждение", info: "Информация",
      required: "Обязательно", optional: "Необязательно", selectLanguage: "Выбрать язык",
      language: "Язык", logout: "Выйти", profile: "Профиль",
      settings: "Настройки", notifications: "Уведомления", dashboard: "Панель управления",
      welcome: "Добро пожаловать", viewAll: "Посмотреть все", print: "Печать",
      export: "Экспорт", import: "Импорт", filter: "Фильтр",
      sortBy: "Сортировать по", ascending: "По возрастанию", descending: "По убыванию",
      active: "Активен", inactive: "Неактивен", pending: "В ожидании",
      approved: "Одобрено", rejected: "Отклонено", completed: "Завершено"
    },
    dashboard: {
        totalPatients: "Всего пациентов", activeEncounters: "Активные приемы",
        pendingTasks: "Ожидающие задачи", lowStock: "Низкий уровень запасов",
        pendingRx: "Ожидающие рецепты", nearExpiry: "Близкий срок годности",
        labSamples: "Лабораторные образцы", invoices: "Счета",
        quickNav: "Быстрая навигация", quickNavDesc: "Прямой доступ к основным модулям",
        Registeredpatients: "Зарегистрированные пациенты", "Inprogress&scheduled": "В процессе и запланировано",
        Awaitingexecution: "Ожидание выполнения", Itemsbelowthreshold: "Товары ниже порогового значения",
        Awaitingdispensing: "Ожидание выдачи", Expiringin60days: "Истекает в течение 60 дней",
        Pendingprocessing: "Ожидание обработки", "1pendingpayment": "1 ожидает оплаты",
        "Register&searchpatie": "Регистрация и поиск пациентов", "Manageclinicalvisits": "Управление клиническими визитами",
        "Labtests,medications": "Лабораторные тесты, лекарства", "Clinicalworkflows&nu": "Клинические рабочие процессы",
        "Testcatalog,samples&": "Каталог тестов, образцы", "Inventory,prescripti": "Инвентарь, рецепты",
        "Invoices,payments&in": "Счета, платежи и страхование", PatientRegistry: "Реестр Пациентов",
        Encounters: "Приемы", OrderManagement: "Управление Заказами",
        TaskQueue: "Очередь Задач", Laboratory: "Лаборатория",
        Pharmacy: "Аптека", Billing: "Биллинг", pendingPayment: "ожидает оплаты",
        pharmacyDesc: "Инвентарь, рецепты и выдача", billingDesc: "Счета, платежи и страховые претензии",
        criticalAlerts: "Критические оповещения", criticalResults: "Критические результаты",
        belowReorder: "Товары ниже точки перезаказа", batchesExpiring: "Скоро истекают партии лекарств",
        labNeedingAttention: "Результаты анализов, требующие внимания"
    },
    auth: {
      login: "Войти", email: "Электронная почта", password: "Пароль",
      forgotPassword: "Забыли пароль?", rememberMe: "Запомнить меня",
      loginTitle: "Больничная информационная система", loginSubtitle: "Войдите в свой аккаунт",
      invalidCredentials: "Неверный адрес электронной почты или пароль"
    }
  }
};

const LANGUAGES = ['hi', 'mr', 'es', 'fr', 'de', 'ar', 'zh', 'ja', 'pt', 'ru'];

for (const lang of LANGUAGES) {
  const localeFile = path.join(__dirname, `locales/${lang}.json`);
  let data = {};
  if (fs.existsSync(localeFile)) {
    data = JSON.parse(fs.readFileSync(localeFile, 'utf8'));
  }
  
  const tr = TRANSLATIONS[lang];
  if (tr) {
    for (const module in tr) {
      data[module] = { ...(data[module] || {}), ...tr[module] };
    }
    fs.writeFileSync(localeFile, JSON.stringify(data, null, 2) + '\n');
    console.log(`Updated ${lang}.json for common, dashboard, auth`);
  }
}
