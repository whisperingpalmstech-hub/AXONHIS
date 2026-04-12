const fs = require('fs');
const path = require('path');

const TRANSLATIONS = {
  hi: {
    bloodBank: { title: "केंद्रीय ब्लड बैंक", subtitle: "क्रॉस-मैचिंग • इन्वेंट्री ट्रैकिंग • डोनर रजिस्ट्री", newDonation: "नया रक्तदान", coldStorage: "कोल्ड स्टोरेज इन्वेंट्री", transfusionOrders: "ट्रांसफ्यूजन ऑर्डर", donorRegistry: "डोनर रजिस्ट्री", registerDonor: "नया डोनर पंजीकृत करें", bloodType: "रक्त का प्रकार", component: "घटक", volume: "वॉल्यूम", expiryDate: "समाप्ति तिथि", rhFactor: "आरएच फैक्टर" },
    pharmacy: { title: "फार्मेसी", prescriptions: "प्रिस्क्रिप्शन", inventory: "फार्मेसी इन्वेंट्री", dispense: "दवा वितरण", drugName: "दवा का नाम", dosage: "खुराक", frequency: "आवृत्ति", duration: "अवधि", stockLevel: "स्टॉक स्तर", batchNumber: "बैच नंबर", lowStockAlerts: "कम स्टॉक अलर्ट", dispensedToday: "आज वितरित" },
    lab: { title: "प्रयोगशाला", orders: "लैब ऑर्डर", processing: "लैब प्रशंसकरण", results: "परिणाम", validation: "परिणाम सत्यापन", testName: "परीक्षण का नाम", specimen: "नमूना", orderedBy: "ऑर्डर किसके द्वारा", resultValue: "परिणाम मूल्य", referenceRange: "संदर्भ सीमा", abnormal: "असामान्य", alert: "अलर्ट" }
  },
  mr: {
    bloodBank: { title: "रक्तपेढी", subtitle: "इन्व्हेंटरी ट्रॅकिंग • डोनर नोंदणी", newDonation: "नवीन रक्तदान", coldStorage: "कोल्ड स्टोरेज साठा", transfusionOrders: "ट्रान्सफ्यूजन ऑर्डर्स", donorRegistry: "डोनर नोंदणी", registerDonor: "नवीन डोनर नोंदणी", bloodType: "रक्तगट", component: "घटक", volume: "आकारमान", expiryDate: "मुदत संपण्याची तारीख", rhFactor: "आरएच फॅक्टर" },
    pharmacy: { title: "औषधालय", prescriptions: "प्रिस्क्रिप्शन", inventory: "औषध साठा", dispense: "औषध वितरण", drugName: "औषधाचे नाव", dosage: "डोस", frequency: "वारंवारता", duration: "कालावधी", stockLevel: "साठा पातळी", batchNumber: "बॅच नंबर", lowStockAlerts: "कमी साठा सूचना", dispensedToday: "आज वितरित" },
    lab: { title: "प्रयोगशाला", orders: "लॅब ऑर्डर्स", processing: "लॅब प्रक्रिया", results: "निकाल", validation: "निकाल पडताळणी", testName: "चाचणीचे नाव", specimen: "नमुना", orderedBy: "कोणी मागवले", resultValue: "निकाल मूल्य", referenceRange: "संदर्भ मर्यादा", abnormal: "असामान्य", alert: "सूचना" }
  },
  es: {
    bloodBank: { title: "Banco de Sangre Central", subtitle: "Pruebas Cruzadas • Seguimiento de Inventario • Registro de Donantes", newDonation: "Nueva Donación de Sangre", coldStorage: "Inventario en Almacenamiento en Frío", transfusionOrders: "Pedidos de Transfusión", donorRegistry: "Registro de Donantes", registerDonor: "Registrar Nuevo Donante", bloodType: "Tipo de Sangre", component: "Componente", volume: "Volumen", expiryDate: "Fecha de Vencimiento", rhFactor: "Factor Rh" },
    pharmacy: { title: "Farmacia", prescriptions: "Recetas", inventory: "Inventario de Farmacia", dispense: "Dispensar", drugName: "Nombre del Medicamento", dosage: "Dosis", frequency: "Frecuencia", duration: "Duración", stockLevel: "Nivel de Stock", batchNumber: "Nº de Lote", lowStockAlerts: "Alertas de Stock Bajo", dispensedToday: "Dispensado Hoy" },
    lab: { title: "Laboratorio", orders: "Pedidos de Laboratorio", processing: "Procesamiento", results: "Resultados", validation: "Validación de Resultados", testName: "Nombre de la Prueba", specimen: "Espécimen", orderedBy: "Pedido Por", resultValue: "Valor del Resultado", referenceRange: "Rango de Referencia", abnormal: "Anormal", alert: "ALERTA" }
  },
  fr: {
    bloodBank: { title: "Banque de Sang Centrale", subtitle: "Tests Croisés • Suivi d'Inventaire • Registre des Donneurs", newDonation: "Nouveau Don de Sang", coldStorage: "Inventaire de Stockage à Froid", transfusionOrders: "Commandes de Transfusion", donorRegistry: "Registre des Donneurs", registerDonor: "Enregistrer un Nouveau Donneur", bloodType: "Groupe Sanguin", component: "Composant", volume: "Volume", expiryDate: "Date d'Expiration", rhFactor: "Facteur Rh" },
    pharmacy: { title: "Pharmacie", prescriptions: "Ordonnances", inventory: "Inventaire de Pharmacie", dispense: "Distribuer", drugName: "Nom du Médicament", dosage: "Dosage", frequency: "Fréquence", duration: "Durée", stockLevel: "Niveau de Stock", batchNumber: "N° de Lot", lowStockAlerts: "Alertes de Stock Bas", dispensedToday: "Distribué Aujourd'hui" },
    lab: { title: "Laboratoire", orders: "Commandes de Laboratoire", processing: "Traitement", results: "Résultats", validation: "Validation de Résultats", testName: "Nom du Test", specimen: "Spécimen", orderedBy: "Commandé Par", resultValue: "Valeur du Résultat", referenceRange: "Plage de Référence", abnormal: "Anormal", alert: "ALERTE" }
  },
  de: {
    bloodBank: { title: "Zentrale Blutbank", subtitle: "Kreuzprobe • Inventarverfolgung • Spenderregister", newDonation: "Neue Blutspende", coldStorage: "Kühllagerinventar", transfusionOrders: "Transfusionsaufträge", donorRegistry: "Spenderregister", registerDonor: "Neuen Spender registrieren", bloodType: "Blutgruppe", component: "Komponente", volume: "Volumen", expiryDate: "Ablaufdatum", rhFactor: "Rh-Faktor" },
    pharmacy: { title: "Apotheke", prescriptions: "Rezepte", inventory: "Apothekeninventar", dispense: "Ausgabe", drugName: "Arzneimittelname", dosage: "Dosierung", frequency: "Häufigkeit", duration: "Dauer", stockLevel: "Lagerbestand", batchNumber: "Chargennummer", lowStockAlerts: "Warnungen bei niedrigem Bestand", dispensedToday: "Heute ausgegeben" },
    lab: { title: "Labor", orders: "Laboraufträge", processing: "Bearbeitung", results: "Ergebnisse", validation: "Validierung der Ergebnisse", testName: "Testname", specimen: "Probe", orderedBy: "Bestellt von", resultValue: "Ergebniswert", referenceRange: "Referenzbereich", abnormal: "Abnormal", alert: "ALARM" }
  },
  ar: {
    bloodBank: { title: "بنك الدم المركزي", subtitle: "مطابقة الدم • تتبع المخزون • سجل المانحين", newDonation: "تبرع جديد بالدم", coldStorage: "مخزون التخزين البارد", transfusionOrders: "طلبات نقل الدم", donorRegistry: "سجل المتبرعين", registerDonor: "تسجيل متبرع جديد", bloodType: "فصيلة الدم", component: "المكون", volume: "الحجم", expiryDate: "تاريخ الانتهاء", rhFactor: "عامل الريسوس" },
    pharmacy: { title: "الصيدلية", prescriptions: "الوصفات الطبية", inventory: "مخزون الصيدلية", dispense: "صرف الدواء", drugName: "اسم الدواء", dosage: "الجرعة", frequency: "التكرار", duration: "المدة", stockLevel: "مستوى المخزون", batchNumber: "رقم الدفعة", lowStockAlerts: "تنبيهات انخفاض المخزون", dispensedToday: "تم صرفها اليوم" },
    lab: { title: "المختبر", orders: "طلبات المختبر", processing: "المعالجة", results: "النتائج", validation: "تحقق من النتائج", testName: "اسم الفحص", specimen: "العينة", orderedBy: "طلب بواسطة", resultValue: "قيمة النتيجة", referenceRange: "النطاق المرجعي", abnormal: "غير طبيعي", alert: "تنبيه" }
  },
  zh: {
    bloodBank: { title: "中心血库", subtitle: "配型 • 库存跟踪 • 献血者登记处", newDonation: "新献血", coldStorage: "冷库库存", transfusionOrders: "输血医嘱", donorRegistry: "献血者登记处", registerDonor: "注册新献血者", bloodType: "血型", component: "成分", volume: "体积", expiryDate: "失效日期", rhFactor: "Rh因子" },
    pharmacy: { title: "药房", prescriptions: "处方", inventory: "药房库存", dispense: "配药", drugName: "药品名称", dosage: "剂量", frequency: "频率", duration: "持续时间", stockLevel: "库存水平", batchNumber: "批号", lowStockAlerts: "低库存警报", dispensedToday: "今日已配药" },
    lab: { title: "实验室", orders: "实验室医嘱", processing: "处理中", results: "结果", validation: "结果验证", testName: "测试名称", specimen: "标本", orderedBy: "下达者", resultValue: "结果值", referenceRange: "参考范围", abnormal: "异常", alert: "警报" }
  },
  ja: {
    bloodBank: { title: "中央血液銀行", subtitle: "交差試験 • 在庫管理 • ドナー登録", newDonation: "新規献血", coldStorage: "コールドストレージ在庫", transfusionOrders: "輸血オーダー", donorRegistry: "ドナー登録", registerDonor: "新規ドナー登録", bloodType: "血液型", component: "成分", volume: "量", expiryDate: "有効期限", rhFactor: "Rh因子" },
    pharmacy: { title: "薬局", prescriptions: "処方箋", inventory: "薬局在庫", dispense: "調剤", drugName: "医薬品名", dosage: "用量", frequency: "頻度", duration: "期間", stockLevel: "在庫レベル", batchNumber: "バッチ番号", lowStockAlerts: "在庫不足のアラート", dispensedToday: "本日の調剤分" },
    lab: { title: "検査室", orders: "検査オーダー", processing: "処理中", results: "結果", validation: "結果の承認", testName: "検査名", specimen: "検体", orderedBy: "依頼者", resultValue: "結果値", referenceRange: "基準値範囲", abnormal: "異常", alert: "アラート" }
  },
  pt: {
    bloodBank: { title: "Banco de Sangue Central", subtitle: "Compatibilidade • Rastreio de Stock • Registo de Dadores", newDonation: "Nova Doação de Sangue", coldStorage: "Inventário de Armazenamento a Frio", transfusionOrders: "Pedidos de Transfusão", donorRegistry: "Registo de Dadores", registerDonor: "Registar Novo Dadore", bloodType: "Tipo de Sangue", component: "Componente", volume: "Volume", expiryDate: "Data de Validade", rhFactor: "Factor Rh" },
    pharmacy: { title: "Farmácia", prescriptions: "Receitas", inventory: "Inventário de Farmácia", dispense: "Dispensar", drugName: "Nome do Medicamento", dosage: "Dosagem", frequency: "Frequência", duration: "Duração", stockLevel: "Nível de Stock", batchNumber: "Nº do Lote", lowStockAlerts: "Alertas de Baixo Stock", dispensedToday: "Dispensado Hoje" },
    lab: { title: "Laboratório", orders: "Pedidos de Laboratório", processing: "Processamento", results: "Resultados", validation: "Validação de Resultados", testName: "Nome do Exame", specimen: "Amostra", orderedBy: "Pedido Por", resultValue: "Valor do Resultado", referenceRange: "Intervalo de Referência", abnormal: "Anormal", alert: "ALERTA" }
  },
  ru: {
    bloodBank: { title: "Центральный банк крови", subtitle: "Перекрестная проба • Отслеживание запасов • Реестр доноров", newDonation: "Новое донорство", coldStorage: "Запасы в холодильнике", transfusionOrders: "Заказы на переливание", donorRegistry: "Реестр доноров", registerDonor: "Зарегистрировать донора", bloodType: "Группа крови", component: "Компонент", volume: "Объем", expiryDate: "Срок годности", rhFactor: "Rh-фактор" },
    pharmacy: { title: "Аптека", prescriptions: "Рецепты", inventory: "Инвентарь аптеки", dispense: "Выдать", drugName: "Название лекарства", dosage: "Дозировка", frequency: "Частота", duration: "Продолжительность", stockLevel: "Уровень запасов", batchNumber: "Номер партии", lowStockAlerts: "Оповещения о низких запасах", dispensedToday: "Выдано сегодня" },
    lab: { title: "Лаборатория", orders: "Заказы на анализы", processing: "Обработка", results: "Результаты", validation: "Валидация результатов", testName: "Название теста", specimen: "Образец", orderedBy: "Заказано", resultValue: "Значение результата", referenceRange: "Референсный диапазон", abnormal: "Аномально", alert: "ОПОВЕЩЕНИЕ" }
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
    console.log(`Updated ${lang}.json for bloodBank, pharmacy, lab (Batch 4)`);
  }
}
