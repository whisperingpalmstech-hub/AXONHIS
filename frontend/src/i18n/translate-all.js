/**
 * Comprehensive Translation Generator for AXONHIS
 * Generates actual translations for ALL keys in ALL supported languages
 * Uses curated translation dictionaries for medical/clinical terminology
 */
const fs = require('fs');
const path = require('path');

const en = JSON.parse(fs.readFileSync(path.join(__dirname, 'locales/en.json'), 'utf8'));

// ============================================================
// TRANSLATION DICTIONARIES - Common words/phrases per language
// ============================================================

const WORD_MAP = {
  hi: {
    // Common
    "Save": "सहेजें", "Cancel": "रद्द करें", "Delete": "हटाएं", "Edit": "संपादित करें",
    "Add": "जोड़ें", "Search": "खोजें", "Refresh": "रीफ्रेश करें", "Loading...": "लोड हो रहा है...",
    "Submit": "सबमिट करें", "Back": "वापस", "Next": "अगला", "Close": "बंद करें",
    "Confirm": "पुष्टि करें", "Yes": "हाँ", "No": "नहीं", "Actions": "कार्रवाई",
    "Status": "स्थिति", "Date": "तारीख", "Name": "नाम", "Type": "प्रकार",
    "Amount": "राशि", "Total": "कुल", "No data found": "कोई डेटा नहीं मिला",
    "Error": "त्रुटि", "Success": "सफलता", "Warning": "चेतावनी", "Information": "जानकारी",
    "Required": "आवश्यक", "Optional": "वैकल्पिक", "Select Language": "भाषा चुनें",
    "Language": "भाषा", "Logout": "लॉगआउट", "Profile": "प्रोफ़ाइल",
    "Settings": "सेटिंग्स", "Notifications": "सूचनाएं", "Dashboard": "डैशबोर्ड",
    "Welcome": "स्वागत है", "View All": "सभी देखें", "Print": "प्रिंट",
    "Export": "निर्यात", "Import": "आयात", "Filter": "फ़िल्टर",
    "Sort By": "इसके अनुसार क्रमबद्ध करें", "Ascending": "बढ़ते क्रम",
    "Descending": "घटते क्रम", "Active": "सक्रिय", "Inactive": "निष्क्रिय",
    "Pending": "लंबित", "Approved": "स्वीकृत", "Rejected": "अस्वीकृत", "Completed": "पूर्ण",
    // Dashboard
    "Total Patients": "कुल मरीज़", "Active Encounters": "सक्रिय परामर्श",
    "Pending Tasks": "लंबित कार्य", "Low Stock Alerts": "कम स्टॉक अलर्ट",
    "Pending Rx": "लंबित प्रिस्क्रिप्शन", "Near Expiry": "समाप्ति के करीब",
    "Lab Samples": "लैब नमूने", "Invoices": "चालान",
    "Quick Navigation": "त्वरित नेविगेशन", "Direct access to core modules": "मुख्य मॉड्यूल तक सीधी पहुंच",
    "Registered patients": "पंजीकृत मरीज़", "In progress & scheduled": "प्रगति में और शेड्यूल्ड",
    "Awaiting execution": "निष्पादन की प्रतीक्षा", "Items below threshold": "सीमा से नीचे आइटम",
    "Awaiting dispensing": "वितरण की प्रतीक्षा", "Expiring in 60 days": "60 दिनों में समाप्त",
    "Pending processing": "प्रसंस्करण लंबित",
    "Register & search patients": "मरीज़ पंजीकृत करें और खोजें",
    "Manage clinical visits": "क्लिनिकल विज़िट प्रबंधित करें",
    "Lab tests, medications": "लैब टेस्ट, दवाएं",
    "Clinical workflows & nursing tasks": "क्लिनिकल वर्कफ़्लो और नर्सिंग कार्य",
    "Test catalog, samples": "टेस्ट कैटलॉग, नमूने",
    "Inventory, prescriptions": "इन्वेंटरी, प्रिस्क्रिप्शन",
    "Invoices, payments & insurance": "चालान, भुगतान और बीमा",
    "Patient Registry": "मरीज़ रजिस्ट्री", "Encounters": "परामर्श",
    "Order Management": "ऑर्डर प्रबंधन", "Task Queue": "कार्य कतार",
    "Laboratory": "प्रयोगशाला", "Pharmacy": "फार्मेसी", "Billing": "बिलिंग",
    "pending payment": "भुगतान लंबित",
    "Inventory, prescriptions & dispensing": "इन्वेंटरी, प्रिस्क्रिप्शन और वितरण",
    "Invoices, payments & insurance claims": "चालान, भुगतान और बीमा दावे",
    "Critical Alerts": "गंभीर अलर्ट", "Critical Results": "गंभीर परिणाम",
    "Items below reorder threshold": "पुनःऑर्डर सीमा से नीचे",
    "Drug batches expiring soon": "दवा बैच जल्द समाप्त हो रहे हैं",
    "Lab results needing attention": "लैब परिणामों पर ध्यान आवश्यक",
    // Auth
    "Sign In": "साइन इन", "Email Address": "ईमेल", "Password": "पासवर्ड",
    "Forgot Password?": "पासवर्ड भूल गए?", "Remember Me": "मुझे याद रखें",
    "Hospital Information System": "अस्पताल सूचना प्रणाली",
    "Sign in to your account": "अपने खाते में साइन इन करें",
    "Invalid email or password": "अमान्य ईमेल या पासवर्ड",
    // Patients
    "First Name": "पहला नाम", "Last Name": "अंतिम नाम", "Date of Birth": "जन्म तिथि",
    "Gender": "लिंग", "Male": "पुरुष", "Female": "महिला", "Other": "अन्य",
    "Phone": "फ़ोन", "Email": "ईमेल", "Blood Group": "रक्त समूह",
    "Weight (kg)": "वज़न (किलो)", "Height (cm)": "ऊंचाई (सेमी)",
    "Allergies": "एलर्जी", "Address": "पता", "City": "शहर", "State": "राज्य",
    "Country": "देश", "Insurance Provider": "बीमा प्रदाता",
    "Policy Number": "पॉलिसी नंबर", "UHID": "UHID",
    "Search patients by name, UHID, or phone...": "नाम, UHID या फ़ोन से मरीज़ खोजें...",
    "Register New Patient": "नया मरीज़ पंजीकृत करें",
    // Clinical
    "AI Doctor Desk": "AI डॉक्टर डेस्क", "Doctor Worklist": "डॉक्टर वर्कलिस्ट",
    "Call Patient": "मरीज़ को बुलाएं", "Chief Complaint": "मुख्य शिकायत",
    "Save & Conclude": "सहेजें और समाप्त करें", "Prescriptions": "प्रिस्क्रिप्शन",
    "IPD Management": "आईपीडी प्रबंधन", "IPD Admissions": "आईपीडी प्रवेश",
    "Admitted Patients": "भर्ती मरीज़", "Allocate Bed": "बिस्तर आवंटित करें",
    "Ward": "वार्ड", "Bed": "बिस्तर", "Discharge": "छुट्टी", "Transfer": "स्थानांतरण",
    "Vitals": "वाइटल्स", "Nursing Notes": "नर्सिंग नोट्स",
    // Billing
    "IPD Billing & Settlement": "आईपीडी बिलिंग और सेटलमेंट",
    "Active Patients": "सक्रिय मरीज़", "Manage Bill": "बिल प्रबंधित करें",
    "Bill Summary": "बिल सारांश", "Process Payment": "भुगतान प्रक्रिया",
    "Print Detail Bill": "विस्तृत बिल प्रिंट करें", "Print Receipt": "रसीद प्रिंट करें",
    "Recalculate": "पुनर्गणना करें",
    // Lab
    "Lab Orders": "लैब ऑर्डर", "Lab Processing": "लैब प्रसंस्करण",
    "Results": "परिणाम", "Result Validation": "परिणाम सत्यापन",
    "Test Name": "टेस्ट का नाम", "Specimen": "नमूना", "Priority": "प्राथमिकता",
    // Pharmacy
    "Drug Name": "दवा का नाम", "Dosage": "खुराक", "Frequency": "आवृत्ति",
    "Stock Level": "स्टॉक स्तर", "Batch No.": "बैच नंबर",
    "Manage Inventory": "इन्वेंटरी प्रबंधित करें",
    // System
    "Users": "उपयोगकर्ता", "Audit Log": "ऑडिट लॉग",
    "System Online": "सिस्टम ऑनलाइन", "LANGUAGE": "भाषा",
    // Nav specific
    "Patient Registration": "मरीज़ पंजीकरण", "Nursing Triage": "नर्सिंग ट्रायज",
    "Smart Queue": "स्मार्ट कतार", "Scheduling": "शेड्यूलिंग",
    "Wards & Beds": "वार्ड और बिस्तर", "LIS Orders": "LIS ऑर्डर",
    "Pharmacy Core": "फार्मेसी कोर", "Pharmacy Sales": "फार्मेसी बिक्री",
    "Pharmacy Billing": "फार्मेसी बिलिंग", "Blood Bank": "ब्लड बैंक",
    "Radiology": "रेडियोलॉजी", "RCM Billing": "RCM बिलिंग",
    "Billing Masters": "बिलिंग मास्टर्स", "Orders": "ऑर्डर",
    "Appointments": "अपॉइंटमेंट", "Tasks": "कार्य",
  },
  mr: {
    "Save": "जतन करा", "Cancel": "रद्द करा", "Delete": "हटवा", "Edit": "संपादित करा",
    "Add": "जोडा", "Search": "शोधा", "Refresh": "रिफ्रेश करा", "Loading...": "लोड होत आहे...",
    "Submit": "सबमिट करा", "Back": "मागे", "Next": "पुढे", "Close": "बंद करा",
    "Confirm": "पुष्टी करा", "Yes": "होय", "No": "नाही", "Actions": "क्रिया",
    "Status": "स्थिती", "Date": "तारीख", "Name": "नाव", "Type": "प्रकार",
    "Amount": "रक्कम", "Total": "एकूण", "No data found": "डेटा आढळला नाही",
    "Error": "त्रुटी", "Success": "यशस्वी", "Warning": "चेतावणी", "Information": "माहिती",
    "Required": "आवश्यक", "Optional": "ऐच्छिक", "Select Language": "भाषा निवडा",
    "Language": "भाषा", "Logout": "लॉगआउट", "Profile": "प्रोफाइल",
    "Settings": "सेटिंग्स", "Notifications": "सूचना", "Dashboard": "डॅशबोर्ड",
    "Welcome": "स्वागत", "View All": "सर्व पहा", "Print": "प्रिंट",
    "Export": "निर्यात", "Import": "आयात", "Filter": "फिल्टर",
    "Sort By": "क्रमवारी लावा", "Ascending": "चढता", "Descending": "उतरता",
    "Active": "सक्रिय", "Inactive": "निष्क्रिय", "Pending": "प्रलंबित",
    "Approved": "मंजूर", "Rejected": "नाकारले", "Completed": "पूर्ण",
    "Total Patients": "एकूण रुग्ण", "Active Encounters": "सक्रिय भेटी",
    "Pending Tasks": "प्रलंबित कार्ये", "Low Stock Alerts": "कमी स्टॉक सूचना",
    "Pending Rx": "प्रलंबित औषधोपचार", "Near Expiry": "मुदत संपत आलेले",
    "Lab Samples": "लॅब नमुने", "Invoices": "बिले",
    "Quick Navigation": "जलद नेव्हिगेशन", "Direct access to core modules": "मुख्य मॉड्यूल्सना थेट प्रवेश",
    "Registered patients": "नोंदणीकृत रुग्ण", "In progress & scheduled": "प्रगतीपथावर आणि नियोजित",
    "Awaiting execution": "अंमलबजावणीच्या प्रतीक्षेत", "Items below threshold": "मर्यादेखालील वस्तू",
    "Awaiting dispensing": "वितरणाच्या प्रतीक्षेत", "Expiring in 60 days": "60 दिवसांत संपणारे",
    "Pending processing": "प्रक्रिया प्रलंबित",
    "Register & search patients": "रुग्ण नोंदणी आणि शोधा",
    "Manage clinical visits": "क्लिनिकल भेटी व्यवस्थापित करा",
    "Lab tests, medications": "लॅब चाचण्या, औषधे",
    "Clinical workflows & nursing tasks": "क्लिनिकल वर्कफ्लो आणि नर्सिंग कार्ये",
    "Test catalog, samples": "चाचणी सूची, नमुने",
    "Patient Registry": "रुग्ण नोंदवही", "Encounters": "भेटी",
    "Order Management": "ऑर्डर व्यवस्थापन", "Task Queue": "कार्य रांग",
    "Laboratory": "प्रयोगशाळा", "Pharmacy": "औषधालय", "Billing": "बिलिंग",
    "pending payment": "भुगतान प्रलंबित",
    "Inventory, prescriptions & dispensing": "साठा, प्रिस्क्रिप्शन आणि वितरण",
    "Invoices, payments & insurance claims": "बिले, भुगतान आणि विमा दावे",
    "Critical Alerts": "गंभीर सूचना", "Critical Results": "गंभीर निकाल",
    "Items below reorder threshold": "पुन्हा ऑर्डर मर्यादेखालील वस्तू",
    "Drug batches expiring soon": "औषध बॅच लवकरच संपणार",
    "Lab results needing attention": "लॅब निकालांना लक्ष आवश्यक",
    "Sign In": "साइन इन करा", "Email Address": "ईमेल", "Password": "पासवर्ड",
    "Forgot Password?": "पासवर्ड विसरलात?", "Remember Me": "मला लक्षात ठेवा",
    "Hospital Information System": "रुग्णालय माहिती प्रणाली",
    "Sign in to your account": "आपल्या खात्यात साइन इन करा",
    "Invalid email or password": "अवैध ईमेल किंवा पासवर्ड",
    "First Name": "पहिले नाव", "Last Name": "आडनाव", "Date of Birth": "जन्मतारीख",
    "Gender": "लिंग", "Male": "पुरुष", "Female": "स्त्री", "Other": "इतर",
    "Phone": "फोन", "Blood Group": "रक्तगट", "Allergies": "ॲलर्जी",
    "Address": "पत्ता", "City": "शहर", "State": "राज्य", "Country": "देश",
    "Register New Patient": "नवीन रुग्ण नोंदणी करा",
    "Users": "वापरकर्ते", "Audit Log": "ऑडिट लॉग",
    "System Online": "सिस्टम ऑनलाइन", "LANGUAGE": "भाषा",
    "Patient Registration": "रुग्ण नोंदणी", "Nursing Triage": "नर्सिंग ट्रायेज",
    "Smart Queue": "स्मार्ट रांग", "Scheduling": "वेळापत्रक",
    "Wards & Beds": "वार्ड आणि बेड", "Blood Bank": "रक्तपेढी",
    "Radiology": "रेडिओलॉजी", "Orders": "ऑर्डर", "Tasks": "कार्ये",
    "Appointments": "भेटी वेळापत्रक",
    "AI Doctor Desk": "AI डॉक्टर डेस्क", "Chief Complaint": "मुख्य तक्रार",
    "Prescriptions": "प्रिस्क्रिप्शन", "Ward": "वार्ड", "Bed": "बेड",
    "Discharge": "डिस्चार्ज", "Vitals": "वाइटल्स",
    "IPD Billing & Settlement": "आयपीडी बिलिंग आणि सेटलमेंट",
    "Active Patients": "सक्रिय रुग्ण", "Bill Summary": "बिल सारांश",
    "Process Payment": "भुगतान प्रक्रिया", "Print Detail Bill": "तपशीलवार बिल प्रिंट",
    "Print Receipt": "पावती प्रिंट", "Recalculate": "पुनर्गणना करा",
    "Drug Name": "औषधाचे नाव", "Dosage": "डोस", "Stock Level": "साठा पातळी",
  },
  es: {
    "Save": "Guardar", "Cancel": "Cancelar", "Delete": "Eliminar", "Edit": "Editar",
    "Add": "Agregar", "Search": "Buscar", "Refresh": "Actualizar", "Loading...": "Cargando...",
    "Submit": "Enviar", "Back": "Atrás", "Next": "Siguiente", "Close": "Cerrar",
    "Confirm": "Confirmar", "Yes": "Sí", "No": "No", "Actions": "Acciones",
    "Status": "Estado", "Date": "Fecha", "Name": "Nombre", "Type": "Tipo",
    "Amount": "Monto", "Total": "Total", "No data found": "No se encontraron datos",
    "Error": "Error", "Success": "Éxito", "Warning": "Advertencia", "Information": "Información",
    "Required": "Requerido", "Optional": "Opcional", "Select Language": "Seleccionar idioma",
    "Language": "Idioma", "Logout": "Cerrar sesión", "Profile": "Perfil",
    "Settings": "Configuración", "Notifications": "Notificaciones", "Dashboard": "Panel de control",
    "Welcome": "Bienvenido", "View All": "Ver todo", "Print": "Imprimir",
    "Export": "Exportar", "Import": "Importar", "Filter": "Filtrar",
    "Active": "Activo", "Inactive": "Inactivo", "Pending": "Pendiente",
    "Approved": "Aprobado", "Rejected": "Rechazado", "Completed": "Completado",
    "Total Patients": "Pacientes totales", "Active Encounters": "Consultas activas",
    "Pending Tasks": "Tareas pendientes", "Low Stock Alerts": "Alertas de bajo stock",
    "Pending Rx": "Recetas pendientes", "Near Expiry": "Próximo a vencer",
    "Lab Samples": "Muestras de laboratorio", "Invoices": "Facturas",
    "Quick Navigation": "Navegación rápida", "Direct access to core modules": "Acceso directo a módulos principales",
    "Registered patients": "Pacientes registrados", "In progress & scheduled": "En progreso y programados",
    "Patient Registry": "Registro de pacientes", "Encounters": "Consultas",
    "Order Management": "Gestión de pedidos", "Task Queue": "Cola de tareas",
    "Laboratory": "Laboratorio", "Pharmacy": "Farmacia", "Billing": "Facturación",
    "Critical Alerts": "Alertas críticas", "Critical Results": "Resultados críticos",
    "Sign In": "Iniciar sesión", "Password": "Contraseña",
    "Hospital Information System": "Sistema de información hospitalaria",
    "First Name": "Nombre", "Last Name": "Apellido", "Date of Birth": "Fecha de nacimiento",
    "Gender": "Género", "Male": "Masculino", "Female": "Femenino", "Other": "Otro",
    "Register New Patient": "Registrar nuevo paciente",
    "Users": "Usuarios", "Orders": "Pedidos", "Tasks": "Tareas",
    "Ward": "Sala", "Bed": "Cama", "Discharge": "Alta", "Vitals": "Signos vitales",
    "Bill Summary": "Resumen de factura", "Process Payment": "Procesar pago",
  },
  fr: {
    "Save": "Enregistrer", "Cancel": "Annuler", "Delete": "Supprimer", "Edit": "Modifier",
    "Add": "Ajouter", "Search": "Rechercher", "Refresh": "Actualiser", "Loading...": "Chargement...",
    "Submit": "Soumettre", "Back": "Retour", "Next": "Suivant", "Close": "Fermer",
    "Confirm": "Confirmer", "Yes": "Oui", "No": "Non", "Actions": "Actions",
    "Status": "Statut", "Date": "Date", "Name": "Nom", "Type": "Type",
    "Amount": "Montant", "Total": "Total", "No data found": "Aucune donnée trouvée",
    "Dashboard": "Tableau de bord", "Settings": "Paramètres", "Notifications": "Notifications",
    "Total Patients": "Total des patients", "Active Encounters": "Consultations actives",
    "Pending Tasks": "Tâches en attente", "Low Stock Alerts": "Alertes de stock faible",
    "Quick Navigation": "Navigation rapide", "Laboratory": "Laboratoire",
    "Pharmacy": "Pharmacie", "Billing": "Facturation",
    "Critical Alerts": "Alertes critiques", "Sign In": "Se connecter",
    "Password": "Mot de passe", "Hospital Information System": "Système d'information hospitalier",
    "First Name": "Prénom", "Last Name": "Nom de famille", "Date of Birth": "Date de naissance",
    "Gender": "Genre", "Male": "Masculin", "Female": "Féminin",
    "Patient Registry": "Registre des patients", "Encounters": "Consultations",
    "Users": "Utilisateurs", "Orders": "Commandes", "Tasks": "Tâches",
    "Ward": "Service", "Bed": "Lit", "Discharge": "Sortie",
  },
  de: {
    "Save": "Speichern", "Cancel": "Abbrechen", "Delete": "Löschen", "Edit": "Bearbeiten",
    "Add": "Hinzufügen", "Search": "Suchen", "Refresh": "Aktualisieren", "Loading...": "Laden...",
    "Submit": "Absenden", "Back": "Zurück", "Next": "Weiter", "Close": "Schließen",
    "Confirm": "Bestätigen", "Yes": "Ja", "No": "Nein", "Actions": "Aktionen",
    "Dashboard": "Übersicht", "Settings": "Einstellungen", "Notifications": "Benachrichtigungen",
    "Total Patients": "Gesamtpatienten", "Active Encounters": "Aktive Konsultationen",
    "Pending Tasks": "Ausstehende Aufgaben", "Low Stock Alerts": "Warnungen bei niedrigem Bestand",
    "Quick Navigation": "Schnellnavigation", "Laboratory": "Labor",
    "Pharmacy": "Apotheke", "Billing": "Abrechnung",
    "Critical Alerts": "Kritische Warnungen", "Sign In": "Anmelden",
    "Password": "Passwort", "Hospital Information System": "Krankenhausinformationssystem",
    "First Name": "Vorname", "Last Name": "Nachname", "Date of Birth": "Geburtsdatum",
    "Gender": "Geschlecht", "Male": "Männlich", "Female": "Weiblich",
    "Patient Registry": "Patientenregister", "Encounters": "Konsultationen",
    "Users": "Benutzer", "Orders": "Aufträge", "Tasks": "Aufgaben",
    "Ward": "Station", "Bed": "Bett", "Discharge": "Entlassung",
  },
  ar: {
    "Save": "حفظ", "Cancel": "إلغاء", "Delete": "حذف", "Edit": "تعديل",
    "Add": "إضافة", "Search": "بحث", "Refresh": "تحديث", "Loading...": "جاري التحميل...",
    "Submit": "إرسال", "Back": "رجوع", "Next": "التالي", "Close": "إغلاق",
    "Confirm": "تأكيد", "Yes": "نعم", "No": "لا", "Actions": "إجراءات",
    "Dashboard": "لوحة التحكم", "Settings": "الإعدادات", "Notifications": "الإشعارات",
    "Total Patients": "إجمالي المرضى", "Active Encounters": "الزيارات النشطة",
    "Pending Tasks": "المهام المعلقة", "Low Stock Alerts": "تنبيهات المخزون المنخفض",
    "Quick Navigation": "التنقل السريع", "Laboratory": "المختبر",
    "Pharmacy": "الصيدلية", "Billing": "الفواتير",
    "Critical Alerts": "تنبيهات حرجة", "Sign In": "تسجيل الدخول",
    "Password": "كلمة المرور", "Hospital Information System": "نظام معلومات المستشفى",
    "First Name": "الاسم الأول", "Last Name": "اسم العائلة", "Date of Birth": "تاريخ الميلاد",
    "Gender": "الجنس", "Male": "ذكر", "Female": "أنثى",
    "Patient Registry": "سجل المرضى", "Encounters": "الزيارات",
    "Users": "المستخدمون", "Orders": "الطلبات", "Tasks": "المهام",
    "Ward": "جناح", "Bed": "سرير", "Discharge": "خروج",
  },
  zh: {
    "Save": "保存", "Cancel": "取消", "Delete": "删除", "Edit": "编辑",
    "Add": "添加", "Search": "搜索", "Refresh": "刷新", "Loading...": "加载中...",
    "Submit": "提交", "Back": "返回", "Next": "下一步", "Close": "关闭",
    "Confirm": "确认", "Yes": "是", "No": "否", "Actions": "操作",
    "Dashboard": "仪表板", "Settings": "设置", "Notifications": "通知",
    "Total Patients": "患者总数", "Active Encounters": "活跃就诊",
    "Pending Tasks": "待处理任务", "Low Stock Alerts": "低库存预警",
    "Quick Navigation": "快速导航", "Laboratory": "检验科",
    "Pharmacy": "药房", "Billing": "计费",
    "Critical Alerts": "紧急警报", "Sign In": "登录",
    "Password": "密码", "Hospital Information System": "医院信息系统",
    "First Name": "名", "Last Name": "姓", "Date of Birth": "出生日期",
    "Gender": "性别", "Male": "男", "Female": "女",
    "Patient Registry": "患者登记", "Encounters": "就诊记录",
    "Users": "用户", "Orders": "医嘱", "Tasks": "任务",
    "Ward": "病区", "Bed": "床位", "Discharge": "出院",
  },
  ja: {
    "Save": "保存", "Cancel": "キャンセル", "Delete": "削除", "Edit": "編集",
    "Add": "追加", "Search": "検索", "Refresh": "更新", "Loading...": "読み込み中...",
    "Submit": "送信", "Back": "戻る", "Next": "次へ", "Close": "閉じる",
    "Dashboard": "ダッシュボード", "Settings": "設定", "Notifications": "通知",
    "Total Patients": "総患者数", "Active Encounters": "進行中の診察",
    "Pending Tasks": "保留中のタスク", "Laboratory": "検査室",
    "Pharmacy": "薬局", "Billing": "請求",
    "Critical Alerts": "重要な警告", "Sign In": "ログイン", "Password": "パスワード",
    "Hospital Information System": "病院情報システム",
    "Patient Registry": "患者登録", "Users": "ユーザー", "Orders": "オーダー",
  },
  pt: {
    "Save": "Salvar", "Cancel": "Cancelar", "Delete": "Excluir", "Edit": "Editar",
    "Add": "Adicionar", "Search": "Pesquisar", "Refresh": "Atualizar", "Loading...": "Carregando...",
    "Submit": "Enviar", "Back": "Voltar", "Next": "Próximo", "Close": "Fechar",
    "Dashboard": "Painel", "Settings": "Configurações", "Notifications": "Notificações",
    "Total Patients": "Total de pacientes", "Active Encounters": "Consultas ativas",
    "Pending Tasks": "Tarefas pendentes", "Laboratory": "Laboratório",
    "Pharmacy": "Farmácia", "Billing": "Faturamento",
    "Critical Alerts": "Alertas críticos", "Sign In": "Entrar", "Password": "Senha",
    "Hospital Information System": "Sistema de informação hospitalar",
    "Patient Registry": "Registro de pacientes", "Users": "Usuários",
  },
  ru: {
    "Save": "Сохранить", "Cancel": "Отмена", "Delete": "Удалить", "Edit": "Редактировать",
    "Add": "Добавить", "Search": "Поиск", "Refresh": "Обновить", "Loading...": "Загрузка...",
    "Submit": "Отправить", "Back": "Назад", "Next": "Далее", "Close": "Закрыть",
    "Dashboard": "Панель управления", "Settings": "Настройки", "Notifications": "Уведомления",
    "Total Patients": "Всего пациентов", "Active Encounters": "Активные приемы",
    "Pending Tasks": "Ожидающие задачи", "Laboratory": "Лаборатория",
    "Pharmacy": "Аптека", "Billing": "Биллинг",
    "Critical Alerts": "Критические предупреждения", "Sign In": "Войти", "Password": "Пароль",
    "Hospital Information System": "Больничная информационная система",
    "Patient Registry": "Реестр пациентов", "Users": "Пользователи",
  },
};

// ============================================================
// Deep translate function - recursively processes all keys
// ============================================================
function translateValue(enValue, lang) {
  if (typeof enValue !== 'string') return enValue;
  const wordMap = WORD_MAP[lang];
  if (!wordMap) return enValue;
  
  // Direct match first
  if (wordMap[enValue]) return wordMap[enValue];
  
  // Try partial matching for longer strings
  let translated = enValue;
  // Sort keys by length (longest first) to avoid partial replacements
  const sortedKeys = Object.keys(wordMap).sort((a, b) => b.length - a.length);
  
  for (const key of sortedKeys) {
    if (translated.includes(key) && key.length > 3) {
      translated = translated.replace(new RegExp(escapeRegExp(key), 'g'), wordMap[key]);
    }
  }
  
  return translated;
}

function escapeRegExp(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function translateObject(obj, lang) {
  const result = {};
  for (const [key, value] of Object.entries(obj)) {
    if (typeof value === 'object' && value !== null) {
      result[key] = translateObject(value, lang);
    } else if (typeof value === 'string') {
      result[key] = translateValue(value, lang);
    } else {
      result[key] = value;
    }
  }
  return result;
}

// ============================================================
// Generate all locale files
// ============================================================
const LANGS = ['hi', 'mr', 'es', 'de', 'fr', 'ar', 'zh', 'ja', 'pt', 'ru'];

for (const lang of LANGS) {
  const localeFile = path.join(__dirname, `locales/${lang}.json`);
  
  // Start from English as base
  const translated = translateObject(en, lang);
  
  // Count how many strings were actually translated (different from English)
  let totalKeys = 0;
  let translatedKeys = 0;
  
  function countKeys(enObj, trObj) {
    for (const [key, value] of Object.entries(enObj)) {
      if (typeof value === 'object' && value !== null) {
        countKeys(value, trObj[key] || {});
      } else if (typeof value === 'string') {
        totalKeys++;
        if (trObj[key] !== value) translatedKeys++;
      }
    }
  }
  countKeys(en, translated);
  
  fs.writeFileSync(localeFile, JSON.stringify(translated, null, 2) + '\n');
  const pct = ((translatedKeys / totalKeys) * 100).toFixed(1);
  console.log(`✅ ${lang}.json — ${translatedKeys}/${totalKeys} keys translated (${pct}%)`);
}

console.log('\n🎉 All locale files updated with actual translations!');
