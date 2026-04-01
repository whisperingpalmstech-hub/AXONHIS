const fs = require('fs');
const path = require('path');

const TRANSLATIONS = {
  hi: {
    radiology: { title: "रेडियोलॉजी", orders: "रेडियोलॉजी ऑर्डर", modality: "मोडेलिटी", bodyPart: "शरीर का हिस्सा", findings: "निष्कर्ष", impression: "प्रभाव" },
    wards: { title: "वार्ड और बेड प्रबंधन", wardName: "वार्ड का नाम", floor: "मंजिल", capacity: "क्षमता", roomNumber: "कमरा नंबर", bedStatus: "बेड की स्थिति", available: "उपलब्ध", occupied: "भरा हुआ", cleaning: "सफाई", maintenance: "रखरखाव", jd: "जेडी", johnDoe: "जॉन डो", unassigned: "अनारक्षित" },
    encounters: { title: "आज के परामर्श", subtitle: "क्लिनिकल परामर्श और प्रवेश प्रबंधित करें।", newQuickEncounter: "त्वरित नया परामर्श", searchPlaceholder: "खोजें...", statusScheduled: "शेड्यूल्ड", statusInProgress: "प्रगति में", statusCompleted: "पूर्ण", workspace: "वर्कस्पेस", encounterType: "परामर्श प्रकार", opOutPatient: "ओपी (आउट-पेशेंट)", ipInPatient: "आईपी (इन-पेशेंट)", erEmergency: "ईआर (इमरजेंसी)" }
  },
  mr: {
    radiology: { title: "रेडिओलॉजी", orders: "रेडिओलॉजी ऑर्डर्स", modality: "मोडालिटी", bodyPart: "शरीराचा भाग", findings: "निष्कर्ष", impression: "इम्प्रेसन" },
    wards: { title: "वॉर्ड आणि बेड व्यवस्थापन", wardName: "वॉर्डचे नाव", floor: "मजला", capacity: "क्षमता", roomNumber: "खोली क्रमांक", bedStatus: "बेडची स्थिती", available: "उपलब्ध", occupied: "भरलेले", cleaning: "स्वच्छता", maintenance: "देखभाल", unassigned: "नेमणूक नाही" },
    encounters: { title: "आजच्या भेटी", subtitle: "क्लिनिकल भेटी आणि प्रवेश व्यवस्थापित करा.", newQuickEncounter: "नवीन झटपट भेट", statusScheduled: "नियोजित", statusInProgress: "प्रगतीपथावर", statusCompleted: "पूर्ण", opOutPatient: "ओपी (बाह्यरुग्ण)", ipInPatient: "आयपी (दाखल रुग्ण)", erEmergency: "ईआर (आपत्कालीन)" }
  },
  es: {
    radiology: { title: "Radiología", orders: "Pedidos de Radiología", modality: "Modalidad", bodyPart: "Parte del Cuerpo", findings: "Hallazgos", impression: "Impresión" },
    wards: { title: "Gestión de Salas y Camas", wardName: "Nombre de la Sala", floor: "Piso", capacity: "Capacidad", roomNumber: "Número de Habitación", bedStatus: "Estado de la Cama", available: "Disponible", occupied: "Ocupada", cleaning: "Limpieza", maintenance: "Mantenimiento" },
    encounters: { title: "Encuentros de Hoy", subtitle: "Gestionar consultas clínicas y admisiones.", newQuickEncounter: "Nuevo Encuentro Rápido", statusScheduled: "Programado", statusInProgress: "En Curso", statusCompleted: "Completado", opOutPatient: "Pacientes Externos", ipInPatient: "Pacientes Internos", erEmergency: "Urgencias" }
  },
  fr: {
    radiology: { title: "Radiologie", orders: "Commandes de Radiologie", modality: "Modalité", bodyPart: "Partie du Corps", findings: "Résultats", impression: "Impression" },
    wards: { title: "Gestion des Salles et Lits", wardName: "Nom de la Salle", floor: "Étage", capacity: "Capacité", roomNumber: "Numéro de Chambre", bedStatus: "État du Lit", available: "Disponible", occupied: "Occupé", cleaning: "Nettoyage", maintenance: "Entretien" },
    encounters: { title: "Rencontres d'Aujourd'hui", subtitle: "Gérer les consultations cliniques et les admissions.", newQuickEncounter: "Nouvelle Rencontre Rapide", statusScheduled: "Programmé", statusInProgress: "En cours", statusCompleted: "Terminé", opOutPatient: "Consultation Externe", ipInPatient: "Hospitalisation", erEmergency: "Urgences" }
  },
  de: {
    radiology: { title: "Radiologie", orders: "Radiologie-Aufträge", modality: "Modalität", bodyPart: "Körperteil", findings: "Befunde", impression: "Beurteilung" },
    wards: { title: "Stationen & Bettenverwaltung", wardName: "Stationsname", floor: "Etage", capacity: "Kapazität", roomNumber: "Zimmernummer", bedStatus: "Bettenstatus", available: "Verfügbar", occupied: "Belegt", cleaning: "Reinigung", maintenance: "Wartung" },
    encounters: { title: "Heutige Begegnungen", subtitle: "Klinische Konsultationen und Aufnahmen verwalten.", newQuickEncounter: "Neuer Schnellbesuch", statusScheduled: "Geplant", statusInProgress: "In Bearbeitung", statusCompleted: "Abgeschlossen", opOutPatient: "Ambulant", ipInPatient: "Stationär", erEmergency: "Notfall" }
  },
  ar: {
    radiology: { title: "الأشعة", orders: "طلبات الأشعة", modality: "الوسيلة", bodyPart: "جزء الجسم", findings: "النتائج", impression: "الانطباع" },
    wards: { title: "إدارة الأجنحة والأسرة", wardName: "اسم الجناح", floor: "الطابق", capacity: "السعة", roomNumber: "رقم الغرفة", bedStatus: "حالة السرير", available: "متاح", occupied: "مشغول", cleaning: "تنظيف", maintenance: "صيانة" },
    encounters: { title: "زيارات اليوم", subtitle: "إدارة الاستشارات السريرية والدخول.", newQuickEncounter: "زيارة سريعة جديدة", statusScheduled: "مجدول", statusInProgress: "قيد التنفيذ", statusCompleted: "مكتمل", opOutPatient: "عيادات خارجية", ipInPatient: "تنويم مرضى", erEmergency: "طوارئ" }
  },
  zh: {
    radiology: { title: "放射科", orders: "放射科医嘱", modality: "成像方式", bodyPart: "身体部位", findings: "检查结果", impression: "检查印象" },
    wards: { title: "病房与床位管理", wardName: "病房名称", floor: "楼层", capacity: "容量", roomNumber: "房间号", bedStatus: "床位状态", available: "可用", occupied: "占用", cleaning: "清洁中", maintenance: "维修中" },
    encounters: { title: "今日就诊", subtitle: "管理临床咨询和住院。", newQuickEncounter: "新建快速就诊", statusScheduled: "已排期", statusInProgress: "进行中", statusCompleted: "已完成", opOutPatient: "门诊", ipInPatient: "住院", erEmergency: "急诊" }
  },
  ja: {
    radiology: { title: "放射線科", orders: "放射線科オーダー", modality: "方式", bodyPart: "部位", findings: "所見", impression: "診断" },
    wards: { title: "病棟・ベッド管理", wardName: "病棟名", floor: "階", capacity: "収容人数", roomNumber: "部屋番号", bedStatus: "ベッドの状態", available: "空き", occupied: "使用中", cleaning: "清掃中", maintenance: "点検中" },
    encounters: { title: "本日の診察", subtitle: "臨床診察と入院の管理。", newQuickEncounter: "新規クイック診察", statusScheduled: "予約済み", statusInProgress: "進行中", statusCompleted: "完了", opOutPatient: "外来", ipInPatient: "入院", erEmergency: "救急" }
  },
  pt: {
    radiology: { title: "Radiologia", orders: "Pedidos de Radiologia", modality: "Modalidade", bodyPart: "Parte do Corpo", findings: "Achados", impression: "Impressão" },
    wards: { title: "Gestão de Enfermarias e Camas", wardName: "Nome da Ala", floor: "Andar", capacity: "Capacidade", roomNumber: "Número do Quarto", bedStatus: "Estado da Cama", available: "Disponível", occupied: "Ocupado", cleaning: "Limpeza", maintenance: "Manutenção" },
    encounters: { title: "Atendimentos de Hoje", subtitle: "Gerir consultas e admissões clínicas.", newQuickEncounter: "Novo Atendimento Rápido", statusScheduled: "Agendado", statusInProgress: "Em curso", statusCompleted: "Concluído", opOutPatient: "Ambulatório", ipInPatient: "Internação", erEmergency: "Pronto Socorro" }
  },
  ru: {
    radiology: { title: "Радиология", orders: "Заказы на радиологию", modality: "Метод", bodyPart: "Часть тела", findings: "Результаты", impression: "Заключение" },
    wards: { title: "Управление палатами и койками", wardName: "Название палаты", floor: "Этаж", capacity: "Вместимость", roomNumber: "Номер комнаты", bedStatus: "Статус койки", available: "Свободно", occupied: "Занято", cleaning: "Уборка", maintenance: "Обслуживание" },
    encounters: { title: "Приемы на сегодня", subtitle: "Управление клиническими консультациями и госпитализацией.", newQuickEncounter: "Новый быстрый прием", statusScheduled: "Запланировано", statusInProgress: "В процессе", statusCompleted: "Завершено", opOutPatient: "Амбулаторный", ipInPatient: "Стационарный", erEmergency: "Экстренный" }
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
    console.log(`Updated ${lang}.json for radiology, wards, encounters (Batch 5)`);
  }
}
