const fs = require('fs');
const path = require('path');

const CORE_MAP = {
  ar: {
     nav: { dashboard: "لوحة القيادة", patients: "إدارة المرضى", doctorDesk: "مكتب الطبيب", laboratory: "المختبر", pharmacy: "الصيدلية", billing: "الفواتير", settings: "الإعدادات" },
     common: { save: "حفظ", cancel: "إلغاء", delete: "حذف", search: "بحث", next: "التالي", back: "السابق" }
  },
  zh: {
     nav: { dashboard: "仪表板", patients: "患者管理", doctorDesk: "医生工作台", laboratory: "实验室", pharmacy: "药房", billing: "计费", settings: "设置" },
     common: { save: "保存", cancel: "取消", delete: "删除", search: "搜索", next: "下一步", back: "返回" }
  },
  ja: {
     nav: { dashboard: "ダッシュボード", patients: "患者管理", doctorDesk: "医師のデスク", laboratory: "実験室", pharmacy: "薬局", billing: "請求", settings: "設定" },
     common: { save: "保存", cancel: "キャンセル", delete: "削除", search: "検索", next: "次へ", back: "戻る" }
  },
  ru: {
     nav: { dashboard: "Панель управления", patients: "Управление пациентами", doctorDesk: "Рабочий стол врача", laboratory: "Лаборатория", pharmacy: "Аптека", billing: "Биллинг", settings: "Настройки" },
     common: { save: "Сохранить", cancel: "Отмена", delete: "Удалить", search: "Поиск", next: "Далее", back: "Назад" }
  },
  de: {
     nav: { dashboard: "Dashboard", patients: "Patientenverwaltung", doctorDesk: "Arzt-Desk", laboratory: "Labor", pharmacy: "Apotheke", billing: "Abrechnung", settings: "Einstellungen" },
     common: { save: "Speichern", cancel: "Abbrechen", delete: "Löschen", search: "Suche", next: "Weiter", back: "Zurück" }
  },
  pt: {
     nav: { dashboard: "Painel", patients: "Gestão de Pacientes", doctorDesk: "Mesa do Médico", laboratory: "Laboratório", pharmacy: "Farmácia", billing: "Faturamento", settings: "Configurações" },
     common: { save: "Salvar", cancel: "Cancelar", delete: "Excluir", search: "Pesquisar", next: "Próximo", back: "Voltar" }
  }
};

const LANGUAGES = ['hi', 'mr', 'es', 'fr', 'ar', 'de', 'zh', 'ja', 'pt', 'ru'];
const en = JSON.parse(fs.readFileSync(path.join(__dirname, 'locales/en.json'), 'utf8'));

for (const lang of LANGUAGES) {
  const file = path.join(__dirname, `locales/${lang}.json`);
  let data = JSON.parse(fs.readFileSync(file, 'utf8'));
  const translations = CORE_MAP[lang] || {};
  
  for (const module in translations) {
    if (!data[module]) data[module] = {};
    Object.assign(data[module], translations[module]);
  }
  
  // Fill any empty strings with English placeholders
  for (const m in en) {
      if (!data[m]) data[m] = {};
      for (const k in en[m]) {
          if (!data[m][k]) data[m][k] = en[m][k];
      }
  }
  
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
}
console.log("Global Core Sync Finished for all 10 non-English languages.");
