const fs = require('fs');
const path = require('path');

const TRANSLATIONS = {
  hi: {
    ipd: { title: "आईपीडी प्रबंधन", admissions: "आईपीडी प्रवेश", pendingRequests: "लंबित अनुरोध", admittedPatients: "प्रवेशित मरीज़", admissionRequest: "प्रवेश अनुरोध", allocateBed: "बेड आवंटित करें", patientName: "मरीज़ का नाम", admittingDoctor: "प्रवेश डॉक्टर", treatingDoctor: "उपचार डॉक्टर", specialty: "विशेषता", reasonForAdmission: "प्रवेश का कारण", admissionCategory: "प्रवेश श्रेणी", admissionSource: "प्रवेश स्रोत", clinicalNotes: "नैदानिक नोट्स", bedCategory: "पसंदीदा बेड श्रेणी", admissionNumber: "प्रवेश नंबर", ward: "वार्ड", bed: "बेड", diagnosis: "निदान", treatmentPlan: "उपचार योजना", progressNotes: "प्रगति नोट्स", vitals: "वाइटल्स", nursingNotes: "नर्सिंग नोट्स", discharge: "डिस्चार्ज", transfer: "स्थानांतरण", stable: "स्थिर", priority: "प्राथमिकता" },
    billing: { title: "आईपीडी बिलिंग और निपटान", subtitle: "मरीज़ शुल्क, जमा, बीमा और अंतिम निपटान प्रबंधित करें।", activePatients: "सक्रिय मरीज़", settledDischarged: "निपटाया / डिस्चार्ज", manageBill: "बिल प्रबंधित करें", billingDetails: "बिलिंग विवरण", serviceCharges: "मदवार सेवाएं और शुल्क", addService: "सेवा जोड़ें", advanceDeposits: "अग्रिम जमा", insuranceClaims: "बीमा और टीपीए दावे", grossCharges: "कुल शुल्क", discount: "छूट", netAmount: "कुल राशि", refundDue: "रिफंड देय" }
  },
  mr: {
    ipd: { title: "आयपीडी व्यवस्थापन", admissions: "आयपीडी प्रवेश", pendingRequests: "प्रलंबित विनंत्या", admittedPatients: "दाखल रुग्ण", admissionRequest: "प्रवेश विनंती", allocateBed: "बेड वाटप करा", patientName: "रुग्णाचे नाव", admittingDoctor: "प्रवेश डॉक्टर", treatingDoctor: "उपचार डॉक्टर", specialty: "विशेषता", reasonForAdmission: "प्रवेशाचे कारण", diagnosis: "निदान", treatmentPlan: "उपचार योजना", progressNotes: "प्रगती नोट्स", vitals: "वाइटल्स", nursingNotes: "नर्सिंग नोट्स", discharge: "डिस्चार्ज", transfer: "बदली", stable: "स्थिर", priority: "प्राधान्य" },
    billing: { title: "आयपीडी बिलिंग आणि सेटलमेंट", subtitle: "रुग्ण शुल्क, ठेव, आणि अंतिम सेटलमेंट व्यवस्थापित करा.", activePatients: "सक्रिय रुग्ण", settledDischarged: "सेटल / डिस्चार्ज", manageBill: "बिल व्यवस्थापित करा", billingDetails: "बिलिंग तपशील", serviceCharges: "सेवा आणि शुल्क", addService: "सेवा जोडा", advanceDeposits: "आगाऊ ठेव", grossCharges: "एकूण शुल्क", discount: "सवलत", netAmount: "निव्वळ रक्कम", refundDue: "परतावा देय" }
  },
  es: {
    ipd: { title: "Gestión de IPD", admissions: "Admisiones IPD", pendingRequests: "Solicitudes Pendientes", admittedPatients: "Pacientes Admitidos", admissionRequest: "Solicitud de Admisión", allocateBed: "Asignar Cama", patientName: "Nombre del Paciente", admittingDoctor: "Médico de Admisión", treatingDoctor: "Médico Tratante", specialty: "Especialidad", reasonForAdmission: "Razón de Admisión", diagnosis: "Diagnóstico", treatmentPlan: "Plan de Tratamiento", progressNotes: "Notas de Progreso", vitals: "Signos Vitales", nursingNotes: "Notas de Enfermería", discharge: "Alta", transfer: "Traslado", stable: "ESTABLE", priority: "Prioridad" },
    billing: { title: "Facturación y Liquidación IPD", subtitle: "Gestionar cargos de pacientes, depósitos, seguros y liquidaciones finales.", activePatients: "Pacientes Activos", settledDischarged: "Liquidado / Alta", manageBill: "Gestionar Factura", billingDetails: "Detalles de Facturación", serviceCharges: "Servicios y Cargos Detallados", addService: "Añadir Servicio", advanceDeposits: "Depósitos Anticipados", grossCharges: "Cargos Brutos Totales", discount: "Descuento Fijo", netAmount: "Monto Neto", refundDue: "Reembolso Pendiente" }
  },
  fr: {
    ipd: { title: "Gestion IPD", admissions: "Admissions IPD", pendingRequests: "Demandes en Attente", admittedPatients: "Patients Admis", admissionRequest: "Demande d'Admission", allocateBed: "Allouer un Lit", patientName: "Nom du Patient", admittingDoctor: "Médecin d'Admission", treatingDoctor: "Médecin Traitant", specialty: "Spécialité", reasonForAdmission: "Raison de l'Admission", diagnosis: "Diagnostic", treatmentPlan: "Plan de Traitement", progressNotes: "Notes d'Évolution", vitals: "Signes Vitaux", nursingNotes: "Notes Infirmières", discharge: "Sortie", transfer: "Transfert", stable: "STABLE", priority: "Priorité" },
    billing: { title: "Facturation & Règlement IPD", subtitle: "Gérer les frais des patients, les dépôts, l'assurance et les règlements finaux.", activePatients: "Patients Actifs", settledDischarged: "Réglé / Sorti", manageBill: "Gérer la Facture", billingDetails: "Détails de Facturation", serviceCharges: "Services & Frais Détaillés", addService: "Ajouter un Service", advanceDeposits: "Acomptes", grossCharges: "Frais Bruts Totaux", discount: "Remise Fixe", netAmount: "Montant Net", refundDue: "Remboursement Dû" }
  },
  de: {
    ipd: { title: "Stationäre Verwaltung", admissions: "Aufnahmen", pendingRequests: "Ausstehende Anfragen", admittedPatients: "Stationäre Patienten", admissionRequest: "Aufnahmeantrag", allocateBed: "Bett zuweisen", patientName: "Patientenname", admittingDoctor: "Aufnehmender Arzt", treatingDoctor: "Behandelnder Arzt", specialty: "Fachbereich", reasonForAdmission: "Aufnahmegrund", diagnosis: "Diagnose", treatmentPlan: "Behandlungsplan", progressNotes: "Verlaufsnotizen", vitals: "Vitalparameter", nursingNotes: "Pflegenotizen", discharge: "Entlassung", transfer: "Verlegung", stable: "STABIL", priority: "Priorität" },
    billing: { title: "Stationäre Abrechnung & Abwicklung", subtitle: "Patientengebühren, Depotzahlungen, Versicherungen und Endabrechnungen verwalten.", activePatients: "Aktive Patienten", settledDischarged: "Abgerechnet / Entlassen", manageBill: "Rechnung verwalten", billingDetails: "Abrechnungsdetails", serviceCharges: "Einzelne Leistungen & Gebühren", addService: "Leistung hinzufügen", advanceDeposits: "Vorauszahlungen", grossCharges: "Gesamtgebühren", discount: "Rabatt", netAmount: "Nettobetrag", refundDue: "Rückerstattung fällig" }
  },
  ar: {
    ipd: { title: "إدارة قسم التنويم", admissions: "دخول المرضى", pendingRequests: "الطلبات المعلقة", admittedPatients: "المرضى المنومون", admissionRequest: "طلب تنويم", allocateBed: "تخصيص سرير", patientName: "اسم المريض", admittingDoctor: "طبيب الدخول", treatingDoctor: "الطبيب المعالج", specialty: "التخصص", reasonForAdmission: "سبب التنويم", diagnosis: "التشخيص", treatmentPlan: "خطة العلاج", progressNotes: "ملاحظات التطور", vitals: "العلامات الحيوية", nursingNotes: "ملاحظات التمريض", discharge: "خروج", transfer: "تحويل", stable: "مستقر", priority: "الأولوية" },
    billing: { title: "فواتير وتسوية التنويم", subtitle: "إدارة رسوم المرضى والودائع والتأمين والتسويات النهائية.", activePatients: "المرضى النشطون", settledDischarged: "تمت التسوية / خرج", manageBill: "إدارة الفاتورة", billingDetails: "تفاصيل الفاتورة", serviceCharges: "الخدمات والرسوم التفصيلية", addService: "إضافة خدمة", advanceDeposits: "الودائع المقدمة", grossCharges: "إجمالي الرسوم", discount: "خصم ثابت", netAmount: "المبلغ الصافي", refundDue: "مستحق الاسترداد" }
  },
  zh: {
    ipd: { title: "住院管理", admissions: "住院登记", pendingRequests: "待处理请求", admittedPatients: "住院患者", admissionRequest: "住院申请", allocateBed: "分配床位", patientName: "患者姓名", admittingDoctor: "主治医生", treatingDoctor: "主治医生", specialty: "科室", reasonForAdmission: "入院原因", diagnosis: "诊断", treatmentPlan: "治疗计划", progressNotes: "病程记录", vitals: "生命体征", nursingNotes: "护理记录", discharge: "出院", transfer: "转院", stable: "稳定", priority: "优先级" },
    billing: { title: "住院计费与结算", subtitle: "管理患者费用、押金、保险和最终结算。", activePatients: "在院患者", settledDischarged: "已结算 / 已出院", manageBill: "管理账单", billingDetails: "计费详情", serviceCharges: "服务项目与费用", addService: "添加服务", advanceDeposits: "预交金", grossCharges: "费用总计", discount: "折扣", netAmount: "净额", refundDue: "应退金额" }
  },
  ja: {
    ipd: { title: "入院管理", admissions: "入院手続き", pendingRequests: "保留中のリクエスト", admittedPatients: "入院患者", admissionRequest: "入院リクエスト", allocateBed: "ベッド割り当て", patientName: "患者名", admittingDoctor: "入院時医師", treatingDoctor: "担当医", specialty: "専門", reasonForAdmission: "入院理由", diagnosis: "診断", treatmentPlan: "治療計画", progressNotes: "経過記録", vitals: "バイタルサイン", nursingNotes: "看護記録", discharge: "退院", transfer: "転院", stable: "安定", priority: "優先順位" },
    billing: { title: "入院請求と決済", subtitle: "患者の費用、預かり金、保険、最終決済を管理します。", activePatients: "入院中の患者", settledDischarged: "決済済み / 退院", manageBill: "請求書の管理", billingDetails: "請求詳細", serviceCharges: "サービスおよび料金の詳細", addService: "サービスの追加", advanceDeposits: "預かり金", grossCharges: "請求総額", discount: "割引", netAmount: "純支払額", refundDue: "返金予定額" }
  },
  pt: {
    ipd: { title: "Gestão de IPD", admissions: "Admissões IPD", pendingRequests: "Solicitações Pendentes", admittedPatients: "Pacientes Admitidos", admissionRequest: "Solicitação de Admissão", allocateBed: "Alocar Cama", patientName: "Nome do Paciente", admittingDoctor: "Médico de Admissão", treatingDoctor: "Médico Assistente", specialty: "Especialidade", reasonForAdmission: "Motivo de Admissão", diagnosis: "Diagnóstico", treatmentPlan: "Plano de Tratamento", progressNotes: "Notas de Evolução", vitals: "Sinais Vitais", nursingNotes: "Notas de Enfermagem", discharge: "Alta", transfer: "Transferência", stable: "ESTÁVEL", priority: "Prioridade" },
    billing: { title: "Faturamento e Liquidação IPD", subtitle: "Gerir encargos de pacientes, depósitos, seguros e liquidação final.", activePatients: "Pacientes Ativos", settledDischarged: "Liquidado / Alta", manageBill: "Gerenciar Conta", billingDetails: "Detalhes de Faturamento", serviceCharges: "Serviços e Encargos Detalhados", addService: "Adicionar Serviço", advanceDeposits: "Depósitos Antecipados", grossCharges: "Total Bruto", discount: "Desconto Fixo", netAmount: "Valor Líquido", refundDue: "Reembolso Devido" }
  },
  ru: {
    ipd: { title: "Управление стационаром", admissions: "Госпитализация", pendingRequests: "Ожидающие запросы", admittedPatients: "Стационарные пациенты", admissionRequest: "Запрос на госпитализацию", allocateBed: "Выделить койку", patientName: "Имя пациента", admittingDoctor: "Врач при приеме", treatingDoctor: "Лечащий врач", specialty: "Специальность", reasonForAdmission: "Причина госпитализации", diagnosis: "Диагноз", treatmentPlan: "План лечения", progressNotes: "Дневниковые записи", vitals: "Жизненные показатели", nursingNotes: "Сестринские записи", discharge: "Выписка", transfer: "Перевод", stable: "СТАБИЛЬНО", priority: "Приоритет" },
    billing: { title: "Биллинг стационара и поселения", subtitle: "Управление счетами пациентов, депозитами, страховками и окончательными расчетами.", activePatients: "Активные пациенты", settledDischarged: "Рассчитан / Выписан", manageBill: "Управление счетом", billingDetails: "Детали биллинга", serviceCharges: "Детализированные услуги и сборы", addService: "Добавить услугу", advanceDeposits: "Авансовые депозиты", grossCharges: "Общая сумма", discount: "Скидка", netAmount: "Чистая сумма", refundDue: "К возврату" }
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
    console.log(`Updated ${lang}.json for ipd, billing (Batch 3)`);
  }
}
