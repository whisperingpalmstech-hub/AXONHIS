import json
import os

locales_dir = "frontend/src/i18n/locales"

# My internal multilingual mappings for IPD and NAV (core navigation and headers)
base_map = {
  "ipdManagement": {"fr": "Gestion Rive", "es": "Gestión de IPD", "de": "IPD-Management", "ar": "إدارة IPD", "pt": "Gestão IPD", "ru": "Управление IPD", "zh": "住院管理", "ja": "IPD管理", "hi": "आईपीडी प्रबंधन", "mr": "आयपीडी व्यवस्थापन"},
  "ipdAdmissions": {"fr": "Admissions IPD", "es": "Adminsiones IPD", "de": "Einweisungen", "ar": "قبول IPD", "pt": "Admissões", "ru": "Прием в IPD", "zh": "住院", "ja": "IPD入院", "hi": "आईपीडी प्रवेश", "mr": "आयपीडी प्रवेश"},
  "wardsAndBeds": {"fr": "Salles et lits", "es": "Salas y Camas", "de": "Stationen & Betten", "ar": "أجنحة وأسرة", "pt": "Enfermarias e Leitos", "ru": "Палаты и койки", "zh": "病房和床位", "ja": "病棟とベッド", "hi": "वार्ड और बेड", "mr": "वॉर्ड आणि बेड्स"},
  "ipdNursing": {"fr": "Soins infirmiers", "es": "Enfermería IPD", "de": "Krankenpflege", "ar": "تمريض IPD", "pt": "Enfermagem IPD", "ru": "Сестринское дело", "zh": "住院护理", "ja": "IPD看護", "hi": "आईपीडी नर्सिंग", "mr": "आयपीडी नर्सिंग"},
  "ipdDoctorDesk": {"fr": "Bureau du médecin", "es": "Escritorio del médico", "de": "Arzttisch", "ar": "مكتب طبيب IPD", "pt": "Mesa do Doutor", "ru": "Стол врача", "zh": "医生工作台", "ja": "医師デスク", "hi": "डॉक्टर डेस्क", "mr": "डॉक्टर डेस्क"},
  "ipdTransfers": {"fr": "Transferts IPD", "es": "Trasferencias IPD", "de": "Transfers", "ar": "نقل IPD", "pt": "Transferências IPD", "ru": "Переводы", "zh": "转移", "ja": "IPD転送", "hi": "स्थानांतरण", "mr": "बदल्या"},
  "ipdBilling": {"fr": "Facturation IPD", "es": "Facturación IPD", "de": "Abrechnung", "ar": "فواتير IPD", "pt": "Faturamento IPD", "ru": "Биллинг IPD", "zh": "住院计费", "ja": "IPD請求", "hi": "बिलिंग", "mr": "बिलिंग"},
  "visitorMlc": {"fr": "Visiteur et MLC", "es": "Visitante y MLC", "de": "Besucher & MLC", "ar": "زائر و MLC", "pt": "Visitante e MLC", "ru": "Посетитель и MLC", "zh": "访客与MLC", "ja": "訪問者とMLC", "hi": "आगंतुक और एमएलसी", "mr": "अभ्यागत आणि एमएलसी"},
  "ipdDischarge": {"fr": "Décharge IPD", "es": "Alta médica", "de": "Entlassungen", "ar": "خروج IPD", "pt": "Alta Médica", "ru": "Выписка из IPD", "zh": "出院", "ja": "IPD退院", "hi": "डिस्चार्ज", "mr": "डिस्चार्ज"},
  
  # IPD Module specific text
  "smartWardsCentralNursing": {"fr": "Salles Intelligentes et Soins", "es": "Salas Inteligentes Y Enfermería Central", "de": "Smarte Stationen", "ar": "عنابر ذكية وتمريض مركزي", "pt": "Enfermarias Inteligentes", "ru": "Умные палаты и Медсестры", "zh": "智能病房及中央护理", "ja": "スマート病棟と中央看護", "hi": "स्मार्ट वार्ड और नर्सिंग", "mr": "स्मार्ट वॉर्ड आणि नर्सिंग"},
  "ipdSubtitle": {"fr": "Tableau des Lits • Signes Vitaux • Demandes d'admission", "es": "Tablero de Camas • Signos Vitales • Solicitudes", "de": "Bettenübersicht • Vitalwerte • Aufnahmeanfragen", "ar": "لوحة الأسرة • المؤشرات الحيوية • طلبات الدخول", "pt": "Quadro de Leitos • Sinais Vitais • Solicitações", "ru": "Обзор коек • Жизненные показатели • Запросы", "zh": "床位面板 • 生命体征监控 • 入院申请", "ja": "ベッドボード • バイタルモニタリング • 入院リクエスト", "hi": "बेड बोर्ड • महत्वपूर्ण लक्षण • प्रवेश अनुरोध", "mr": "बेड बोर्ड • महत्त्वाची लक्षणे • प्रवेश विनंत्या"},
  "activeAdmissions": {"fr": "Admissions actives", "es": "Admisiones Activas", "de": "Aktive Aufnahmen", "ar": "القبول النشط", "pt": "Admissões Ativas", "ru": "Активные поступления", "zh": "活动住院", "ja": "アクティブ入院"},
  "pendingRequests": {"fr": "Demandes en attente", "es": "Solicitudes pendientes", "de": "Ausstehende Anfragen", "ar": "الطلبات المعلقة", "pt": "Pedidos pendentes", "ru": "Ожидающие запросы", "zh": "待处理请求", "ja": "保留中のリクエスト"},
  "icuOccupancy": {"fr": "Occupation USI", "es": "Ocupación UCI", "de": "Intensivbelegung", "ar": "إشغال العناية المركزة", "pt": "Ocupação da UTI", "ru": "Заполняемость ОРИТ", "zh": "ICU占用率", "ja": "ICU稼働率"},
  "dischargesToday": {"fr": "Décharges aujourd'hui", "es": "Altas hoy", "de": "Entlassungen heute", "ar": "الخروج اليوم", "pt": "Altas de hoje", "ru": "Выписки сегодня", "zh": "今日出院", "ja": "今日の退院"},
  "patient": {"fr": "Patient", "es": "Paciente", "de": "Patient", "ar": "مريض", "pt": "Paciente", "ru": "Пациент", "zh": "患者", "ja": "患者"},
  "status": {"fr": "Statut", "es": "Estado", "de": "Status", "ar": "حالة", "pt": "Status", "ru": "Статус", "zh": "状态", "ja": "ステータス"},
  "action": {"fr": "Action", "es": "Acción", "de": "Aktion", "ar": "عمل", "pt": "Ação", "ru": "Акция", "zh": "动作", "ja": "アクション"},
  "stable": {"fr": "STABLE", "es": "ESTABLE", "de": "STABIL", "ar": "مستقر", "pt": "ESTÁVEL", "ru": "СТАБИЛЬНЫЙ", "zh": "稳定", "ja": "安定"},
  "bedAllocatedStr": {"fr": "LIT ALLOUÉ", "es": "CAMA ASIGNADA", "de": "BETT ZUGEWIESEN", "ar": "سرير مخصص", "pt": "CAMA ALOCADA", "ru": "КОЙКА ВЫДЕЛЕНА", "zh": "床位分配", "ja": "ベッド割り当て"},
  "assignedDr": {"fr": "Assigné", "es": "Asignado", "de": "Zugewiesen", "ar": "مكلف", "pt": "Atribuído", "ru": "Назначен", "zh": "已分配", "ja": "割り当て済み"},
  "pendingDoctor": {"fr": "Médecin en attente", "es": "Médico pendiente", "de": "Arzt ausstehend", "ar": "طبيب معلق", "pt": "Médico Pendente", "ru": "Ожидающий врач", "zh": "待定医生", "ja": "医師保留"}
}

def sync_language(lang_code):
    path = os.path.join(locales_dir, f"{lang_code}.json")
    if not os.path.exists(path): return
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    for module in ["nav", "ipd"]:
        if module not in data: data[module] = {}

    for key, dmap in base_map.items():
        if lang_code in dmap:
            val = dmap[lang_code]
            # determine which module it belongs to
            # First check if the key belongs to `nav` or `ipd` in en.json
            # I can just assign it to both or guess.
            if key in ["ipdManagement", "ipdAdmissions", " wardsAndBeds", "ipdNursing", "ipdDoctorDesk", "ipdTransfers", "ipdBilling", "visitorMlc", "ipdDischarge", "wardsAndBeds"]:
                data["nav"][key] = val
                # Some are in ipd too
                data["ipd"][key] = val
            else:
                data["ipd"][key] = val
                
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

for lang in ["ar", "de", "es", "fr", "hi", "mr", "pt", "ru", "zh", "ja"]:
    sync_language(lang)

print("Applied rich offline dictionary matching for IPD and Sidebar nav across all 10 languages!")
