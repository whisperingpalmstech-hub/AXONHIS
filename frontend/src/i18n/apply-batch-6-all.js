const fs = require('fs');
const path = require('path');

const TRANSLATIONS = {
  hi: {
    admin: { title: "प्रशासन", users: "उपयोगकर्ता प्रबंधन", languageManagement: "भाषा प्रबंधन", addLanguage: "भाषा जोड़ें", coverage: "कवरेज", ltr: "बाएं से दाएं", rtl: "दाएं से बाएं" },
    validation: { required: "यह फ़ील्ड आवश्यक है", invalidEmail: "अमान्य ईमेल पता", invalidPhone: "अमान्य फ़ोन नंबर" },
    opdVisits: { opdVisitIntelligence: "ओपीडी विज़िट इंटेलिजेंस", patient: "मरीज़", confirmed: "पुष्टि की गई", aiFindings: "AI निष्कर्ष", symptoms: "लक्षण", visitId: "विज़िट आईडी", queueIsEmpty: "कतार खाली है" },
    er: { emergencyDepartment: "आपातकालीन विभाग", critical: "आपातकालीन (क्रिटिकल)", bedsAvailable: "बेड उपलब्ध", mlcCases: "एमएलसी मामले", zoneOccupancy: "जोन ऑक्यूपेंसी", arrival: "आगमन", policeStation: "थाना" }
  },
  mr: {
    admin: { title: "प्रशासन", users: "वापरकर्ता व्यवस्थापन", languageManagement: "भाषा व्यवस्थापन", addLanguage: "भाषा जोडा", coverage: "व्याप्ती" },
    validation: { required: "हे क्षेत्र भरणे आवश्यक आहे", invalidEmail: "अवैध ईमेल पत्ता" },
    opdVisits: { opdVisitIntelligence: "ओपीडी भेट इंटेलिजन्स", patient: "रुग्ण", confirmed: "निश्चित", visitId: "भेट आयडी", queueIsEmpty: "रांग रिकामी आहे" },
    er: { emergencyDepartment: "आपत्कालीन विभाग", critical: "अतिदक्षता", bedsAvailable: "बेड उपलब्ध", mlcCases: "MLC प्रकरणे", arrival: "आगमन", policeStation: "पोलीस स्टेशन" }
  },
  es: {
    admin: { title: "Administración", users: "Gestión de Usuarios", languageManagement: "Gestión de Idiomas", addLanguage: "Añadir Idioma", coverage: "Cobertura" },
    validation: { required: "Este campo es obligatorio", invalidEmail: "Correo electrónico inválido" },
    opdVisits: { opdVisitIntelligence: "Inteligencia de Visitas Ambulatorias", patient: "Paciente", confirmed: "Confirmado", visitId: "ID de Visita", queueIsEmpty: "La cola está vacía" },
    er: { emergencyDepartment: "Departamento de Emergencias", critical: "Crítico", bedsAvailable: "Camas Disponibles", mlcCases: "Casos MLC", arrival: "Llegada" }
  },
  fr: {
    admin: { title: "Administration", users: "Gestion des Utilisateurs", languageManagement: "Gestion des Langues", addLanguage: "Ajouter une Langue", coverage: "Couverture" },
    validation: { required: "Ce champ est obligatoire", invalidEmail: "Adresse e-mail invalide" },
    opdVisits: { opdVisitIntelligence: "Intelligence des Visites Ambulatoires", patient: "Patient", confirmed: "Confirmé", visitId: "ID de Visite", queueIsEmpty: "La file d'attente est vide" },
    er: { emergencyDepartment: "Service des Urgences", critical: "Critique", bedsAvailable: "Lits Disponibles", mlcCases: "Cas MLC", arrival: "Arrivée" }
  },
  de: {
    admin: { title: "Administration", users: "Benutzerverwaltung", languageManagement: "Sprachverwaltung", addLanguage: "Sprache hinzufügen", coverage: "Abdeckung" },
    validation: { required: "Dieses Feld ist ein Pflichtfeld", invalidEmail: "Ungültige E-Mail-Adresse" },
    opdVisits: { opdVisitIntelligence: "Ambulante Besuchsintelligenz", patient: "Patient", confirmed: "Bestätigt", visitId: "Besuchs-ID", queueIsEmpty: "Warteschlange ist leer" },
    er: { emergencyDepartment: "Notfallabteilung", critical: "Kritisch", bedsAvailable: "Verfügbare Betten", mlcCases: "MLC-Fälle", arrival: "Ankunft" }
  },
  ar: {
    admin: { title: "الإدارة", users: "إدارة المستخدمين", languageManagement: "إدارة اللغات", addLanguage: "إضافة لغة", coverage: "التغطية", ltr: "من اليسار إلى اليمين", rtl: "من اليمين إلى اليسار" },
    validation: { required: "هذا الحقل مطلوب", invalidEmail: "بريد إلكتروني غير صالح" },
    opdVisits: { opdVisitIntelligence: "ذكاء زيارات العيادات الخارجية", patient: "المريض", confirmed: "مؤكد", visitId: "رقم الزيارة", queueIsEmpty: "الطابور فارغ" },
    er: { emergencyDepartment: "قسم الطوارئ", critical: "حرج", bedsAvailable: "أسرة متاحة", mlcCases: "حالات MLC", arrival: "الوصول" }
  },
  zh: {
    admin: { title: "行政管理", users: "用户管理", languageManagement: "语言管理", addLanguage: "添加语言", coverage: "覆盖率" },
    validation: { required: "此字段为必填项", invalidEmail: "电子邮件地址无效" },
    opdVisits: { opdVisitIntelligence: "门诊智能咨询", patient: "患者", confirmed: "已确认", visitId: "就诊ID", queueIsEmpty: "队列为空" },
    er: { emergencyDepartment: "急诊部", critical: "危机", bedsAvailable: "可用床位", mlcCases: "司法案件(MLC)", arrival: "送达" }
  },
  ja: {
    admin: { title: "管理", users: "ユーザー管理", languageManagement: "言語管理", addLanguage: "言語の追加", coverage: "網羅率" },
    validation: { required: "この項目は必須です", invalidEmail: "無効なメールアドレスです" },
    opdVisits: { opdVisitIntelligence: "インテリジェント外来診察", patient: "患者", confirmed: "確定", visitId: "診察ID", queueIsEmpty: "待機列はありません" },
    er: { emergencyDepartment: "救急科", critical: "重症", bedsAvailable: "空きベッド", mlcCases: "警察届出案件(MLC)", arrival: "到着" }
  },
  pt: {
    admin: { title: "Administração", users: "Gestão de Usuários", languageManagement: "Gestão de Idiomas", addLanguage: "Adicionar Idioma", coverage: "Cobertura" },
    validation: { required: "Este campo é obrigatório", invalidEmail: "E-mail inválido" },
    opdVisits: { opdVisitIntelligence: "Inteligência de Visitas de Ambulatório", patient: "Paciente", confirmed: "Confirmado", visitId: "ID da Visita", queueIsEmpty: "A fila está vazia" },
    er: { emergencyDepartment: "Pronto Socorro", critical: "Crítico", bedsAvailable: "Camas Disponíveis", mlcCases: "Casos MLC", arrival: "Chegada" }
  },
  ru: {
    admin: { title: "Администрирование", users: "Управление пользователями", languageManagement: "Управление языками", addLanguage: "Добавить язык", coverage: "Покрытие" },
    validation: { required: "Это поле обязательно к заполнению", invalidEmail: "Неверный адрес электронной почты" },
    opdVisits: { opdVisitIntelligence: "Амбулаторная аналитика", patient: "Пациент", confirmed: "Подтверждено", visitId: "ID визита", queueIsEmpty: "Очередь пуста" },
    er: { emergencyDepartment: "Отделение экстренной помощи", critical: "Критический", bedsAvailable: "Доступно коек", mlcCases: "Судебно-медицинские случаи (MLC)", arrival: "Прибытие" }
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
    console.log(`Updated ${lang}.json for admin, validation, opdVisits, er (Batch 6)`);
  }
}
