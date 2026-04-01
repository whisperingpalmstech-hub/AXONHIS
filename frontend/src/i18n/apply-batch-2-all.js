const fs = require('fs');
const path = require('path');

const TRANSLATIONS = {
  hi: {
    nav: {
      dashboard: "डैशबोर्ड", patients: "मरीज़ प्रबंधन", patientRegistry: "मरीज़ रजिस्ट्री",
      patientRegistration: "मरीज़ पंजीकरण", clinicalOps: "क्लिनिकल संचालन",
      doctorDesk: "डॉक्टर डेस्क", nursingTriage: "नर्सिंग ट्रायज",
      smartQueue: "स्मार्ट कतार", opdVisits: "ओपीडी विज़िट",
      scheduling: "शेड्यूलिंग", ipdManagement: "आईपीडी प्रबंधन",
      ipdAdmissions: "आईपीडी प्रवेश", ipdDoctorDesk: "आईपीडी डॉक्टर डेस्क",
      ipdNursing: "आईपीडी नर्सिंग", ipdBilling: "आईपीडी बिलिंग",
      ipdTransfers: "आईपीडी स्थानांतरण", ipdDischarge: "आईपीडी डिस्चार्ज",
      wardsAndBeds: "वार्ड और बेड", laboratory: "प्रयोगशाला",
      lisOrders: "LIS ऑर्डर", labProcessing: "लैब प्रशंसकरण",
      resultValidation: "परिणाम सत्यापन", pharmacy: "फार्मेसी",
      pharmacyCore: "फार्मेसी कोर", pharmacySales: "फार्मेसी बिक्री",
      pharmacyBilling: "फार्मेसी बिलिंग", bloodBank: "ब्लड बैंक",
      radiology: "रेडियोलॉजी", billing: "बिलिंग और आरसीएम",
      ipdBillingNav: "आईपीडी बिलिंग", rcmBilling: "आरसीएम बिलिंग",
      billingMasters: "बिलिंग मास्टर्स", emergencyRoom: "आपातकालीन कक्ष",
      operationTheater: "ऑपरेशन थियेटर", administration: "प्रशासन",
      users: "उपयोगकर्ता", systemSettings: "सिस्टम सेटिंग्स",
      analytics: "एनालिटिक्स", audit: "ऑडिट लॉग",
      rpiwWorkspace: "RPIW वर्कस्पेस", tasks: "कार्य",
      clinicalOrders: "ऑर्डर", visitorMlc: "विजिटर और एमएलसी",
      sampleReceiving: "सैंपल रिसीविंग", analyzerHub: "एनालाइजर हब",
      reportHandover: "रिपोर्ट हैंडओवर", advancedDiagnostics: "उन्नत निदान",
      extendedLab: "विस्तारित लैब सेवाएं", rxWorklist: "प्रिस्क्रिप्शन वर्कलिस्ट",
      ipMedicationIssue: "आईपी दवा वितरण", pharmacyReturns: "रिटर्न",
      ipPharmacyReturns: "आईपी रिटर्न", narcoticsVault: "नारकोटिक्स वॉल्ट",
      inventoryIntelligence: "इन्वेंट्री इंटेलिजेंस", organizations: "संगठन (SaaS)",
      coreSystem: "कोर सिस्टम", communication: "संचार",
      biIntelligence: "BI इंटेलिजेंस", aiPlatform: "AI प्लेटफॉर्म",
      encounters: "परामर्श", orders: "ऑर्डर",
      appointments: "अपॉइंटमेंट", pharmacySalesNav: "फार्मेसी बिक्री",
      ipdOrdersNav: "ऑर्डर", ipdNursingVitals: "नर्सिंग वाइटल्स",
      ipdDoctorRounds: "डॉक्टर राउंड्स", ipdBedTransfers: "बेड ट्रांसफर",
      ipdSmartDischarge: "आईपीडी डिस्चार्ज", phlebotomy: "फ्लेबोटोमी",
      sampleReceivingCentral: "सैंपल रिसीविंग", labProcessingWorkflow: "लैब प्रशंसकरण",
      analyzerHubNav: "एनालाइजर हब", validationDesk: "सत्यापन डेस्क",
      reportHandoverNav: "रिपोर्ट हैंडओवर", advancedDiagnosticsNav: "उन्नत निदान",
      extendedLabNav: "विस्तारित लैब सेवाएं", narcoticsVaultNav: "नारकोटिक्स वॉल्ट",
      ipMedicationIssueNav: "आईपी दवा वितरण", ipReturnsNav: "आईपी रिटर्न",
      returnsNav: "रिटर्न", inventoryIntelligenceNav: "इन्वेंट्री इंटेलिजेंस",
      pharmacyCoreNav: "फार्मेसी कोर", billingComplianceNav: "बिलिंग और अनुपालन",
      organizationsNav: "संगठन (SaaS)", systemOnline: "सिस्टम ऑनलाइन",
      languageLabel: "भाषा"
    },
    patients: {
      title: "मरीज़ रजिस्ट्री", manageRecords: "मरीज़ रिकॉर्ड और पहचान प्रबंधित करें।",
      registration: "एंटरप्राइज़ मरीज़ पंजीकरण",
      registrationSub: "AI-संचालित स्मार्ट पंजीकरण।",
      firstName: "पहला नाम", lastName: "अंतिम नाम", dateOfBirth: "जन्म तिथि",
      gender: "लिंग", male: "पुरुष", female: "महिला", other: "अन्य",
      phone: "फ़ोन", email: "ईमेल", bloodGroup: "रक्त समूह",
      weight: "वज़न (किग्रा)", height: "ऊंचाई (सेमी)", allergies: "एलर्जी",
      address: "पता", pincode: "पिनकोड", city: "शहर", state: "राज्य",
      country: "देश", emergencyContact: "आपातकालीन संपर्क",
      emergencyPhone: "आपातकालीन फ़ोन", idType: "आईडी प्रकार",
      idNumber: "दस्तावेज़ संख्या", insuranceProvider: "बीमा प्रदाता",
      policyNumber: "पॉलिसी नंबर", chiefComplaint: "मुख्य शिकायत",
      reasonForVisit: "विज़िट का कारण", uhid: "UHID",
      searchPatients: "मरीज़ खोजें...",
      registerNew: "नया मरीज़ पंजीकृत करें", viewProfile: "मरीज़ प्रोफ़ाइल देखें",
      demographics: "जनसांख्यिकी", medicalInfo: "चिकित्सा जानकारी",
      identityVerification: "पहचान सत्यापन", insurance: "बीमा",
      consentNotification: "सूचनाएं", registrationSuccess: "पंजीकरण सफल!",
      healthCardReady: "स्वास्थ्य कार्ड तैयार"
    }
  },
  mr: {
    nav: {
      dashboard: "डॅशबोर्ड", patients: "रुग्ण व्यवस्थापन", patientRegistry: "रुग्ण नोंदवही",
      patientRegistration: "रुग्ण नोंदणी", clinicalOps: "क्लिनिकल कार्यसंचालन",
      doctorDesk: "डॉक्टर डेस्क", nursingTriage: "नर्सिंग ट्रायज",
      smartQueue: "स्मार्ट रांग", opdVisits: "ओपीडी भेटी",
      scheduling: "वेळापत्रक", ipdManagement: "आयपीडी व्यवस्थापन",
      ipdAdmissions: "IPD प्रवेश", ipdDoctorDesk: "IPD डॉक्टर डेस्क",
      ipdNursing: "IPD नर्सिंग", ipdBilling: "IPD बिलिंग",
      ipdTransfers: "IPD बदल्या", ipdDischarge: "IPD डिस्चार्ज",
      wardsAndBeds: "वॉर्ड आणि बेड", laboratory: "प्रयोगशाळा",
      lisOrders: "LIS ऑर्डर्स", labProcessing: "लॅब प्रक्रिया",
      resultValidation: "निकाल पडताळणी", pharmacy: "औषधालय",
      pharmacyCore: "फार्मसी कोअर", pharmacySales: "फार्मसी विक्री",
      pharmacyBilling: "फार्मसी बिलिंग", bloodBank: "रक्तपेढी",
      radiology: "रेडिओलॉजी", billing: "बिलिंग आणि आरसीएम",
      ipdBillingNav: "IPD बिलिंग", rcmBilling: "आरसीएम बिलिंग",
      billingMasters: "बिलिंग मास्टर्स", emergencyRoom: "आपत्कालीन कक्ष",
      operationTheater: "शस्त्रक्रिया गृह", administration: "प्रशासन",
      users: "वापरकर्ते", systemSettings: "सिस्टम सेटिंग्ज",
      analytics: "एनालिटिक्स", audit: "ऑडिट लॉग",
      rpiwWorkspace: "RPIW वर्कस्पेस", tasks: "कार्ये",
      clinicalOrders: "ऑर्डर्स", visitorMlc: "विजिटर आणि एमएलसी",
      sampleReceiving: "नमुना पावती", analyzerHub: "ॲनालायजर हब",
      reportHandover: "रिपोर्ट हँडओव्हर", advancedDiagnostics: "प्रगत निदान",
      extendedLab: "विस्तारित लॅब सेवा", rxWorklist: "Rx वर्कलिस्ट",
      ipMedicationIssue: "IP औषध वितरण", pharmacyReturns: "परतावा",
      ipPharmacyReturns: "IP परतावा", narcoticsVault: "नार्कोटिक्स वॉल्ट",
      inventoryIntelligence: "इन्व्हेंटरी इंटेलिजन्स", organizations: "संस्था (SaaS)",
      coreSystem: "कोअर सिस्टम", communication: "संवाद",
      biIntelligence: "BI इंटेलिजन्स", aiPlatform: "AI प्लॅ特फॉर्म",
      encounters: "भेटी", orders: "ऑर्डर्स",
      appointments: "अपॉइंटमेंट्स", pharmacySalesNav: "फार्मसी विक्री",
      ipdOrdersNav: "ऑर्डर्स", ipdNursingVitals: "नर्सिंग वाइटल्स",
      ipdDoctorRounds: "डॉक्टर राऊंड्स", ipdBedTransfers: "बेड ट्रान्सफर",
      ipdSmartDischarge: "IPD डिस्चार्ज", phlebotomy: "फ्लेबोटोमी",
      sampleReceivingCentral: "नमुना पावती", labProcessingWorkflow: "लॅब प्रक्रिया",
      analyzerHubNav: "ॲनालायजर हब", validationDesk: "पडताळणी डेस्क",
      reportHandoverNav: "रिपोर्ट हँडओव्हर", advancedDiagnosticsNav: "प्रगत निदान",
      extendedLabNav: "विस्तारित लॅब सेवा", narcoticsVaultNav: "नार्कोटिक्स वॉल्ट",
      ipMedicationIssueNav: "IP औषध वितरण", ipReturnsNav: "IP परतावा",
      returnsNav: "परतावा", inventoryIntelligenceNav: "इन्व्हेंटरी इंटेलिजन्स",
      pharmacyCoreNav: "फार्मसी कोअर", billingComplianceNav: "बिलिंग आणि अनुपालन",
      organizationsNav: "संस्था (SaaS)", systemOnline: "सिस्टम ऑनलाइन",
      languageLabel: "भाषा"
    },
    patients: {
      title: "रुग्ण नोंदवही", manageRecords: "रुग्ण रेकॉर्ड व्यवस्थापित करा.",
      registration: "रुग्ण नोंदणी",
      firstName: "पहिले नाव", lastName: "आडनाव", dateOfBirth: "जन्मतारीख",
      gender: "लिंग", male: "पुरुष", female: "स्त्री", other: "इतर",
      phone: "फोन", email: "ईमेल", bloodGroup: "रक्तगट",
      address: "पत्ता", pincode: "पिनकोड", city: "शहर", state: "राज्य",
      country: "देश", emergencyContact: "तातडीचा संपर्क"
    }
  },
  es: {
    nav: {
      dashboard: "Tablero", patients: "Gestión de Pacientes", patientRegistry: "Registro de Pacientes",
      patientRegistration: "Registro de Pacientes", clinicalOps: "Operaciones Clínicas",
      doctorDesk: "Escritorio del Doctor", nursingTriage: "Triaje de Enfermería",
      smartQueue: "Cola Inteligente", opdVisits: "Visitas Ambulatorias",
      scheduling: "Programación", ipdManagement: "Gestión de IPD",
      ipdAdmissions: "Admisiones IPD", ipdDoctorDesk: "Escritorio Médico IPD",
      ipdNursing: "Enfermería IPD", ipdBilling: "Facturación IPD",
      ipdTransfers: "Traslados IPD", ipdDischarge: "Alta IPD",
      wardsAndBeds: "Salas y Camas", laboratory: "Laboratorio",
      lisOrders: "Pedidos LIS", labProcessing: "Procesamiento de Laboratorio",
      resultValidation: "Validación de Resultados", pharmacy: "Farmacia",
      pharmacyCore: "Núcleo de Farmacia", pharmacySales: "Ventas de Farmacia",
      pharmacyBilling: "Facturación de Farmacia", bloodBank: "Banco de Sangre",
      radiology: "Radiología", billing: "Facturación y RCM",
      ipdBillingNav: "Facturación IPD", rcmBilling: "Facturación RCM",
      billingMasters: "Maestros de Facturación", emergencyRoom: "Sala de Emergencias",
      operationTheater: "Quirófano", administration: "Administración",
      analytics: "Analítica", audit: "Registro de Auditoría",
      tasks: "Tareas", clinicalOrders: "Pedidos",
      encounters: "Encuentros", orders: "Pedidos",
      appointments: "Citas", pharmacySalesNav: "Ventas de Farmacia",
      systemOnline: "Sistema en Línea", languageLabel: "IDIOMA"
    },
    patients: {
      title: "Registro de Pacientes", manageRecords: "Gestionar expedientes e identidades de pacientes.",
      registration: "Registro de Pacientes de Empresa",
      firstName: "Nombre", lastName: "Apellido", dateOfBirth: "Fecha de Nacimiento",
      gender: "Género", male: "Masculino", female: "Femenino", phone: "Teléfono",
      email: "Correo", address: "Dirección", city: "Ciudad", country: "País"
    }
  },
  fr: {
    nav: {
      dashboard: "Tableau de bord", patients: "Gestion des Patients", patientRegistry: "Registre des Patients",
      patientRegistration: "Inscription des Patients", clinicalOps: "Opérations Cliniques",
      doctorDesk: "Bureau du Médecin", nursingTriage: "Tri Infirmier",
      smartQueue: "File d'attente Intelligente", opdVisits: "Visites Ambulatoires",
      scheduling: "Planification", ipdManagement: "Gestion IPD",
      ipdAdmissions: "Admissions IPD", ipdDoctorDesk: "Bureau Médical IPD",
      ipdNursing: "Soins Infirmiers IPD", ipdBilling: "Facturation IPD",
      ipdTransfers: "Transferts IPD", ipdDischarge: "Sortie IPD",
      wardsAndBeds: "Salles et Lits", laboratory: "Laboratoire",
      pharmacy: "Pharmacie", bloodBank: "Banque de Sang",
      radiology: "Radiologie", billing: "Facturation & RCM",
      emergencyRoom: "Urgences", operationTheater: "Bloc Opératoire",
      administration: "Administration", analytics: "Analytique",
      encounters: "Rencontres", orders: "Commandes",
      appointments: "Rendez-vous", systemOnline: "Système en Ligne",
      languageLabel: "LANGUE"
    },
    patients: {
      title: "Registre des Patients", manageRecords: "Gérer les dossiers et identités des patients.",
      registration: "Enregistrement des Patients Enterprise",
      firstName: "Prénom", lastName: "Nom", dateOfBirth: "Date de Naissance",
      gender: "Genre", male: "Homme", female: "Femme", phone: "Téléphone",
      email: "E-mail", address: "Adresse", city: "Ville", country: "Pays"
    }
  },
  de: {
    nav: {
      dashboard: "Dashboard", patients: "Patientenverwaltung", patientRegistry: "Patientenregister",
      patientRegistration: "Patientenregistrierung", clinicalOps: "Klinischer Betrieb",
      doctorDesk: "Arzt-Arbeitsplatz", nursingTriage: "Pflegetriage",
      smartQueue: "Intelligente Warteschlange", opdVisits: "Ambulante Besuche",
      scheduling: "Terminplanung", ipdManagement: "Stationäre Verwaltung",
      ipdAdmissions: "IPD-Aufnahmen", ipdDoctorDesk: "IPD-Arzt-Arbeitsplatz",
      ipdNursing: "IPD-Pflege", ipdBilling: "IPD-Abrechnung",
      wardsAndBeds: "Stationen & Betten", laboratory: "Labor",
      pharmacy: "Apotheke", bloodBank: "Blutbank",
      radiology: "Radiologie", billing: "Abrechnung & RCM",
      emergencyRoom: "Notaufnahme", operationTheater: "Operationssaal",
      administration: "Verwaltung", analytics: "Analytik",
      encounters: "Begegnungen", orders: "Aufträge",
      appointments: "Termine", systemOnline: "System Online",
      languageLabel: "SPRACHE"
    },
    patients: {
      title: "Patientenregister", manageRecords: "Patientenakten und Identitäten verwalten.",
      registration: "Unternehmens-Patientenregistrierung",
      firstName: "Vorname", lastName: "Nachname", dateOfBirth: "Geburtsdatum",
      gender: "Geschlecht", male: "Männlich", female: "Weiblich", phone: "Telefon",
      email: "E-Mail", address: "Adresse", city: "Stadt", country: "Land"
    }
  },
  ar: {
    nav: {
      dashboard: "لوحة التحكم", patients: "إدارة المرضى", patientRegistry: "سجل المرضى",
      patientRegistration: "تسجيل المرضى", clinicalOps: "العمليات السريرية",
      doctorDesk: "مكتب الطبيب", nursingTriage: "فرز التمريض",
      smartQueue: "الطابور الذكي", opdVisits: "زيارات العيادات الخارجية",
      scheduling: "الجدولة", ipdManagement: "إدارة قسم التنويم",
      ipdAdmissions: "دخول المرضى", ipdDoctorDesk: "مكتب طبيب التنويم",
      ipdNursing: "تمريض قسم التنويم", ipdBilling: "فواتير التنويم",
      wardsAndBeds: "الأجنحة والأسرة", laboratory: "المختبر",
      pharmacy: "الصيدلية", bloodBank: "بنك الدم",
      radiology: "الأشعة", billing: "الفواتير و RCM",
      emergencyRoom: "غرفة الطوارئ", operationTheater: "غرفة العمليات",
      administration: "الإدارة", analytics: "التحليلات",
      encounters: "الزيارات", orders: "الطلبات",
      appointments: "المواعيد", systemOnline: "النظام متصل",
      languageLabel: "اللغة"
    },
    patients: {
      title: "سجل المرضى", manageRecords: "إدارة سجلات المرضى وهوياتهم.",
      registration: "تسجيل المرضى للمؤسسات",
      firstName: "الاسم الأول", lastName: "اسم العائلة", dateOfBirth: "تاريخ الميلاد",
      gender: "الجنس", male: "ذكر", female: "أنثى", phone: "الهاتف",
      email: "البريد الإلكتروني", address: "العنوان", city: "المدينة", country: "الدولة"
    }
  },
  zh: {
    nav: {
      dashboard: "仪表板", patients: "患者管理", patientRegistry: "患者登记处",
      patientRegistration: "患者注册", clinicalOps: "临床业务",
      doctorDesk: "医生工作站", nursingTriage: "护理分诊",
      smartQueue: "智能队列", opdVisits: "门诊采集",
      scheduling: "排程", ipdManagement: "住院管理",
      ipdAdmissions: "住院登记", ipdDoctorDesk: "住院医生工作站",
      ipdNursing: "住院护理", ipdBilling: "住院计费",
      wardsAndBeds: "病房与床位", laboratory: "实验室",
      pharmacy: "药房", bloodBank: "血库",
      radiology: "放射科", billing: "计费与RCM",
      emergencyRoom: "急诊室", operationTheater: "手术室",
      administration: "行政管理", analytics: "分析",
      encounters: "就诊", orders: "医嘱",
      appointments: "预约", systemOnline: "系统在线",
      languageLabel: "语言"
    },
    patients: {
      title: "患者登记处", manageRecords: "管理患者档案和身份。",
      registration: "企业患者注册",
      firstName: "名", lastName: "姓", dateOfBirth: "出生日期",
      gender: "性别", male: "男", female: "女", phone: "电话",
      email: "电子邮件", address: "地址", city: "城市", country: "国家"
    }
  },
  ja: {
    nav: {
      dashboard: "ダッシュボード", patients: "患者管理", patientRegistry: "患者レジストリ",
      patientRegistration: "患者登録", clinicalOps: "臨床業務",
      doctorDesk: "医師用デスク", nursingTriage: "看護トリアージ",
      smartQueue: "スマート待機列", opdVisits: "外来診察",
      scheduling: "スケジューリング", ipdManagement: "入院管理",
      ipdAdmissions: "入院手続き", ipdDoctorDesk: "入院医師デスク",
      ipdNursing: "入院看護", ipdBilling: "入院会計",
      wardsAndBeds: "病棟・ベッド", laboratory: "検査室",
      pharmacy: "薬局", bloodBank: "血液銀行",
      radiology: "放射線科", billing: "請求・RCM",
      emergencyRoom: "救急室", operationTheater: "手術室",
      administration: "管理", analytics: "分析",
      encounters: "診察", orders: "オーダー",
      appointments: "予約", systemOnline: "システム稼働中",
      languageLabel: "言語"
    },
    patients: {
      title: "患者レジストリ", manageRecords: "患者の記録と身元を管理します。",
      registration: "エンタープライズ患者登録",
      firstName: "名", lastName: "姓", dateOfBirth: "生年月日",
      gender: "性別", male: "男性", female: "女性", phone: "電話番号",
      email: "メール", address: "住所", city: "市区町村", country: "国"
    }
  },
  pt: {
    nav: {
      dashboard: "Painel", patients: "Gestão de Pacientes", patientRegistry: "Registro de Pacientes",
      patientRegistration: "Registro de Paciente", clinicalOps: "Operações Clínicas",
      doctorDesk: "Mesa do Médico", nursingTriage: "Triagem de Enfermagem",
      smartQueue: "Fila Inteligente", opdVisits: "Visitas de Ambulatório",
      scheduling: "Agendamento", ipdManagement: "Gestão de IPD",
      ipdAdmissions: "Admissões IPD", ipdDoctorDesk: "Mesa Médica IPD",
      ipdNursing: "Enfermagem IPD", ipdBilling: "Faturamento IPD",
      wardsAndBeds: "Enfermarias e Camas", laboratory: "Laboratório",
      pharmacy: "Farmácia", bloodBank: "Banco de Sangue",
      radiology: "Radiologia", billing: "Faturamento e RCM",
      emergencyRoom: "Pronto Socorro", operationTheater: "Centro Cirúrgico",
      administration: "Administração", analytics: "Analítica",
      encounters: "Atendimentos", orders: "Pedidos",
      appointments: "Consultas", systemOnline: "Sistema Online",
      languageLabel: "IDIOMA"
    },
    patients: {
      title: "Registro de Pacientes", manageRecords: "Gerir registos e identidades de pacientes.",
      registration: "Registro de Pacientes Corporativo",
      firstName: "Nome", lastName: "Sobrenome", dateOfBirth: "Data de Nascimento",
      gender: "Gênero", male: "Masculino", female: "Feminino", phone: "Telefone",
      email: "E-mail", address: "Endereço", city: "Cidade", country: "País"
    }
  },
  ru: {
    nav: {
      dashboard: "Панель управления", patients: "Управление Пациентами", patientRegistry: "Реестр Пациентов",
      patientRegistration: "Регистрация Пациентов", clinicalOps: "Клинические Операции",
      doctorDesk: "Рабочее место врача", nursingTriage: "Сестринская сортировка",
      smartQueue: "Умная очередь", opdVisits: "Амбулаторные визиты",
      scheduling: "Планирование", ipdManagement: "Управление стационаром",
      ipdAdmissions: "Госпитализация", ipdDoctorDesk: "Место врача стационара",
      ipdNursing: "Сестринское дело стационар", ipdBilling: "Биллинг стационар",
      wardsAndBeds: "Палаты и койки", laboratory: "Лаборатория",
      pharmacy: "Аптека", bloodBank: "Банк крови",
      radiology: "Радиология", billing: "Биллинг и RCM",
      emergencyRoom: "Отделение неотложной помощи", operationTheater: "Операционная",
      administration: "Администрирование", analytics: "Аналитика",
      encounters: "Приемы", orders: "Заказы",
      appointments: "Записи", systemOnline: "Система в сети",
      languageLabel: "ЯЗЫК"
    },
    patients: {
      title: "Реестр Пациентов", manageRecords: "Управление картами и данными пациентов.",
      registration: "Корпоративная регистрация пациентов",
      firstName: "Имя", lastName: "Фамилия", dateOfBirth: "Дата рождения",
      gender: "Пол", male: "Мужской", female: "Женский", phone: "Телефон",
      email: "Электронная почта", address: "Адрес", city: "Город", country: "Страна"
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
    console.log(`Updated ${lang}.json for nav, patients (Full Set)`);
  }
}
