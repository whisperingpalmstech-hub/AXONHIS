import json
import os
import glob
from pathlib import Path

# Provide a small dictionary of translations for the 10 avatar strings across all requested languages.
# (I am providing approximate translations to get it fully functionally correct for the user right now).
translations = {
    "Tap to speak": {
        "en": "Tap to speak", "hi": "बोलने के लिए टैप करें", "mr": "बोलण्यासाठी टॅप करा",
        "es": "Toque para hablar", "fr": "Appuyez pour parler", "de": "Tippen zum Sprechen",
        "ar": "انقر للتحدث", "zh": "点击说话", "ja": "タップして話す", "pt": "Toque para falar", "ru": "Нажмите, чтобы говорить"
    },
    "Listening...": {
        "en": "Listening...", "hi": "सुन रहा हूँ...", "mr": "ऐकत आहे...",
        "es": "Escuchando...", "fr": "Écoute...", "de": "Zuhören...",
        "ar": "استماع...", "zh": "聆听中...", "ja": "聞いています...", "pt": "Ouvindo...", "ru": "Слушаю..."
    },
    "Processing...": {
        "en": "Processing...", "hi": "प्रसंस्करण...", "mr": "प्रक्रिया करत आहे...",
        "es": "Procesando...", "fr": "Traitement...", "de": "Bearbeitung...",
        "ar": "جاري المعالجة...", "zh": "处理中...", "ja": "処理中...", "pt": "Processando...", "ru": "Обработка..."
    },
    "Speaking...": {
        "en": "Speaking...", "hi": "बोल रहा हूँ...", "mr": "बोलत आहे...",
        "es": "Hablando...", "fr": "Parlant...", "de": "Sprechen...",
        "ar": "تتحدث...", "zh": "说话中...", "ja": "話しています...", "pt": "Falando...", "ru": "Говорю..."
    },
    "Register": {
        "en": "Register", "hi": "पंजीकरण", "mr": "नोंदणी",
        "es": "Registrar", "fr": "S'inscrire", "de": "Registrieren",
        "ar": "تسجيل", "zh": "注册", "ja": "登録", "pt": "Registrar", "ru": "Регистрация"
    },
    "Appointment": {
        "en": "Appointment", "hi": "नियुक्ति", "mr": "नियुक्ती",
        "es": "Cita", "fr": "Rendez-vous", "de": "Termin",
        "ar": "موعد", "zh": "预约", "ja": "予約", "pt": "Consulta", "ru": "Запись"
    },
    "Symptoms": {
        "en": "Symptoms", "hi": "लक्षण", "mr": "लक्षणे",
        "es": "Síntomas", "fr": "Symptômes", "de": "Symptome",
        "ar": "أعراض", "zh": "症状", "ja": "症状", "pt": "Sintomas", "ru": "Симптомы"
    },
    "Billing": {
        "en": "Billing", "hi": "बिलिंग", "mr": "बिलिंग",
        "es": "Facturación", "fr": "Facturation", "de": "Abrechnung",
        "ar": "فواتير", "zh": "账单", "ja": "請求", "pt": "Faturamento", "ru": "Счета"
    },
    "Lab Test": {
        "en": "Lab Test", "hi": "प्रयोगशाला परीक्षण", "mr": "लॅब चाचणी",
        "es": "Prueba de lab", "fr": "Test de labo", "de": "Labortest",
        "ar": "فحص مختبر", "zh": "实验室检查", "ja": "臨床検査", "pt": "Exame de lab", "ru": "Анализы"
    },
    "Discharge": {
        "en": "Discharge", "hi": "छुट्टी", "mr": "डिस्चार्ज",
        "es": "Alta", "fr": "Sortie", "de": "Entlassung",
        "ar": "تخريج", "zh": "出院", "ja": "退院", "pt": "Alta", "ru": "Выписка"
    },
    "Directions": {
        "en": "Directions", "hi": "दिशा-निर्देश", "mr": "दिशानिर्देश",
        "es": "Direcciones", "fr": "Itinéraire", "de": "Wegbeschreibung",
        "ar": "اتجاهات", "zh": "导航", "ja": "行き方", "pt": "Direções", "ru": "Маршрут"
    },
    "Live Conversation": {
        "en": "Live Conversation", "hi": "जीवंत बातचीत", "mr": "थेट संवाद",
        "es": "Chat en vivo", "fr": "Conversation en direct", "de": "Live-Unterhaltung",
        "ar": "المحادثة الحية", "zh": "实时对话", "ja": "ライブ会話", "pt": "Conversa ao vivo", "ru": "Живая беседа"
    },
    "{count} messages": {
        "en": "{count} messages", "hi": "{count} संदेश", "mr": "{count} संदेश",
        "es": "{count} mensajes", "fr": "{count} messages", "de": "{count} Nachrichten",
        "ar": "{count} رسائل", "zh": "{count} 条消息", "ja": "{count} 件のメッセージ", "pt": "{count} mensagens", "ru": "{count} сообщений"
    },
    "Virtual Avatar": {
        "en": "Virtual Avatar", "hi": "आभासी अवतार", "mr": "व्हर्च्युअल अवतार",
        "es": "Avatar Virtual", "fr": "Avatar Virtuel", "de": "Virtueller Avatar",
        "ar": "الأفاتار الافتراضي", "zh": "虚拟化身", "ja": "バーチャルアバター", "pt": "Avatar Virtual", "ru": "Виртуальный аватар"
    },
    "Type your message...": {
        "en": "Type your message...", "hi": "अपना संदेश टाइप करें...", "mr": "तुमचा संदेश टाइप करा...",
        "es": "Escribe tu mensaje...", "fr": "Tapez votre message...", "de": "Geben Sie Ihre Nachricht ein...",
        "ar": "اكتب رسالتك...", "zh": "输入您的信息...", "ja": "メッセージを入力...", "pt": "Digite sua mensagem...", "ru": "Введите ваше сообщение..."
    },
    "Avatar is speaking...": {
        "en": "Avatar is speaking...", "hi": "अवतार बोल रहा है...", "mr": "अवतार बोलत आहे...",
        "es": "El avatar está hablando...", "fr": "L'avatar parle...", "de": "Avatar spricht...",
        "ar": "الأفاتار يتحدث...", "zh": "化身正在说话...", "ja": "アバターが話しています...", "pt": "O avatar está falando...", "ru": "Аватар говорит..."
    },
    "I want to register as a new patient": {
        "en": "I want to register as a new patient", "hi": "मैं एक नए मरीज के रूप में पंजीकरण करना चाहता हूं", "mr": "मला नवीन रुग्ण म्हणून नोंदणी करायची आहे",
        "es": "Quiero registrarme como nuevo paciente", "fr": "Je souhaite m'inscrire comme nouveau patient", "de": "Ich möchte mich als neuer Patient registrieren",
        "ar": "أريد التسجيل كمريض جديد", "zh": "我想注册成为新患者", "ja": "新患として登録したい", "pt": "Quero me registrar como novo paciente", "ru": "Я хочу зарегистрироваться как новый пациент"
    },
    "I want to book an appointment": {
        "en": "I want to book an appointment", "hi": "मैं अपॉइंटमेंट बुक करना चाहता हूँ", "mr": "मला अपॉइंटमेंट बुक करायची आहे",
        "es": "Quiero reservar una cita", "fr": "Je souhaite prendre rendez-vous", "de": "Ich möchte einen Termin buchen",
        "ar": "أريد حجز موعد", "zh": "我想预约", "ja": "予約をとりたい", "pt": "Quero marcar uma consulta", "ru": "Я хочу записаться на прием"
    },
    "I want to describe my symptoms before my visit": {
        "en": "I want to describe my symptoms before my visit", "hi": "मैं अपनी यात्रा से पहले अपने लक्षणों का वर्णन करना चाहता हूं", "mr": "मी माझ्या भेटीपूर्वी माझी लक्षणे वर्णन करू इच्छितो",
        "es": "Quiero describir mis síntomas antes de mi visita", "fr": "Je veux décrire mes symptômes avant ma visite", "de": "Ich möchte meine Symptome vor meinem Besuch beschreiben",
        "ar": "أرغب في وصف أعراضي قبل زيارتي", "zh": "我想在就诊前描述我的症状", "ja": "訪問前に症状を説明したい", "pt": "Quero descrever meus sintomas antes da minha visita", "ru": "Я хочу описать свои симптомы перед визитом"
    },
    "I want to check my bill": {
        "en": "I want to check my bill", "hi": "मैं अपना बिल जांचना चाहता हूं", "mr": "मला माझे बिल तपासायचे आहे",
        "es": "Quiero revisar mi factura", "fr": "Je veux vérifier ma facture", "de": "Ich möchte meine Rechnung überprüfen",
        "ar": "أريد التحقق من فاتورتي", "zh": "我想查账单", "ja": "請求書を確認したい", "pt": "Quero checar minha conta", "ru": "Я хочу проверить свой счет"
    },
    "I want to schedule a lab test": {
        "en": "I want to schedule a lab test", "hi": "मैं लैब टेस्ट शेड्यूल करना चाहता हूं", "mr": "मला लॅब चाचणी शेड्यूल करायची आहे",
        "es": "Quiero programar una prueba de laboratorio", "fr": "Je veux planifier un test de laboratoire", "de": "Ich möchte einen Labortest planen",
        "ar": "أريد جدولة فحص مختبر", "zh": "我想安排化验", "ja": "臨床検査の予約をしたい", "pt": "Quero agendar um exame de laboratório", "ru": "Я хочу записаться на анализы"
    },
    "I need my discharge instructions": {
        "en": "I need my discharge instructions", "hi": "मुझे अपने डिस्चार्ज निर्देश चाहिए", "mr": "मला माझ्या डिस्चार्ज सूचना हव्या आहेत",
        "es": "Necesito mis instrucciones de alta", "fr": "J'ai besoin de mes instructions de sortie", "de": "Ich brauche meine Entlassungsanweisungen",
        "ar": "أحتاج إلى تعليمات الخروج الخاصة بي", "zh": "我需要出院须知", "ja": "退院時の指示が必要です", "pt": "Preciso das minhas instruções de alta", "ru": "Мне нужны инструкции к выписке"
    },
    "I need directions to a department": {
        "en": "I need directions to a department", "hi": "मुझे किसी विभाग के लिए दिशा-निर्देश चाहिए", "mr": "मला एका विभागासाठी दिशानिर्देश हवे आहेत",
        "es": "Necesito direcciones a un departamento", "fr": "J'ai besoin d'un itinéraire vers un département", "de": "Ich brauche eine Wegbeschreibung zu einer Abteilung",
        "ar": "أحتاج توجيهات إلى قسم", "zh": "需要去某个科室的路线", "ja": "特定の部署への行き方を教えてください", "pt": "Preciso de direções para um departamento", "ru": "Мне нужно пройти в отделение"
    }
}

target_dir = "/home/sujeetnew/Downloads/AXONHIS/frontend/src/i18n/locales"

for file_path in glob.glob(os.path.join(target_dir, "*.json")):
    lang_code = os.path.basename(file_path).split('.')[0]
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    changes = 0
    for eng_key, lang_map in translations.items():
        if eng_key not in data:
            data[eng_key] = lang_map.get(lang_code, eng_key)
            changes += 1
            
    if changes > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Updated {os.path.basename(file_path)} with {changes} strings.")
    else:
        print(f"Skipped {os.path.basename(file_path)} (no changes).")
