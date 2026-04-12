import json
import os

locales_dir = "frontend/src/i18n/locales"

base_map = {
  "aiDoctorDesk": {
      "ru": "Стол врача с ИИ", "de": "KI-Arzttisch", "es": "Escritorio Médico IA", "fr": "Bureau Médical IA", 
      "ar": "مكتب طبيب الذكاء الاصطناعي", "pt": "Mesa do Médico com IA", "zh": "AI 医生工作台", "ja": "AIドクターデスク",
      "hi": "एआई डॉक्टर डेस्क", "mr": "एआय डॉक्टर डेस्क"
  },
  "deskSubtitle": {
      "ru": "Интеллектуальная ЭМК и поддержка решений", "de": "Intelligente EMR und Entscheidungsunterstützung", "es": "EMR Inteligente",
      "fr": "DME Intelligent et aide à la décision", "ar": "أنظمة ذكية ودعم قرارات سريرية", "pt": "EMR Inteligente", 
      "zh": "智能EMR和临床决策支持", "ja": "インテリジェントEMRと臨床意思決定サポート",
      "hi": "बुद्धिमान ईएमआर", "mr": "इंटेलिजेंट ईएमआर"
  },
  "waitlist": {"ru": "Список ожидания", "de": "Warteliste", "es": "Lista de espera", "fr": "Liste d'attente", "ar": "قائمة الانتظار", "pt": "Lista de Espera", "zh": "候诊名单", "ja": "順番待ち", "hi": "प्रतीक्षा सूची", "mr": "प्रतीक्षा यादी"},
  "latestPatient": {"ru": "Последний пациент", "de": "Letzter Patient", "es": "Último Paciente", "fr": "Dernier Patient", "ar": "أحدث مريض", "pt": "Último Paciente", "zh": "最新患者", "ja": "最新の患者", "hi": "नवीनतम रोगी", "mr": "नवीनतम रुग्ण"},
  "simulateEntry": {"ru": "Имитировать вход", "de": "Eintrag simulieren", "es": "Simular", "fr": "Simuler l'entrée", "ar": "محاكاة الدخول", "pt": "Simular Entrada", "zh": "模拟输入", "ja": "入力シミュレーション", "hi": "प्रविष्टि का अनुकरण", "mr": "प्रविष्टीचे अनुकरण"},
  "queueEmpty": {"ru": "Очередь пуста.", "de": "Warteschlange leer.", "es": "Cola vacía.", "fr": "File d'attente vide.", "ar": "الطابور فارغ.", "pt": "Fila vazia.", "zh": "队列空。", "ja": "キューが空です。", "hi": "कतार खाली।", "mr": "रांग रिकामी."},
  "token": {"ru": "ТАЛОН", "de": "TICKET", "es": "TURNO", "fr": "JETON", "ar": "رمز", "pt": "FICHA", "zh": "代币", "ja": "トークン", "hi": "टोकन", "mr": "टोकन"},
  "callToChamber": {"ru": "Вызвать в кабинет", "de": "Zum Zimmer rufen", "es": "Llamar al consultorio", "fr": "Appeler au cabinet", "ar": "دعوة للغرفة", "pt": "Chamar para a sala", "zh": "呼叫", "ja": "診察室に呼ぶ", "hi": "कक्ष में बुलाएं", "mr": "चेंबरमध्ये बोलावणे"},
  "consultationInProgress": {"ru": "Идет прием", "de": "Sprechstunde läuft", "es": "Consulta en progreso", "fr": "Consultation en cours", "ar": "استشارة جارية", "pt": "Consulta em andamento", "zh": "就诊中", "ja": "診察中", "hi": "परामर्श जारी", "mr": "सल्लामसलत सुरू"},
  "returnToProfile": {"ru": "Вернуться в профиль", "de": "Zurück zum Profil", "es": "Volver al perfil", "fr": "Retour au profil", "ar": "العودة للملف", "pt": "Retornar ao Perfil", "zh": "返回资料", "ja": "プロファイルに戻る", "hi": "प्रोफ़ाइल पर लौटें", "mr": "प्रोफाईलवर परता"},
  "waitingForNextPatient": {"ru": "Ожидание следующего пациента", "de": "Warten auf nächsten Patienten", "es": "Esperando al próximo paciente", "fr": "En attente du prochain patient", "ar": "في انتظار المريض التالي", "pt": "Aguardando o próximo", "zh": "等待下一位患者", "ja": "次の患者を待っています", "hi": "अगले रोगी की प्रतीक्षा", "mr": "पुढील रुग्णाची प्रतीक्षा"},
  "selectFromWorklist": {"ru": "Выберите пациента из расписания для начала приема.", "de": "Patienten aus Liste wählen.", "es": "Selecciona un paciente.", "fr": "Sélectionnez un patient.", "ar": "اختر مريضا.", "pt": "Selecione um paciente.", "zh": "从工作列表中选择患者。", "ja": "患者を選択してください。", "hi": "रोगी का चयन करें", "mr": "रुग्ण निवडा"}
}

def apply_docdesk():
    for f_name in os.listdir(locales_dir):
        if f_name == "en.json" or not f_name.endswith(".json"): continue
        lang = f_name.replace(".json", "")
        path = os.path.join(locales_dir, f_name)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if "docDesk" not in data: data["docDesk"] = {}
        for key, maps in base_map.items():
            if lang in maps:
                data["docDesk"][key] = maps[lang]
                
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    apply_docdesk()
    print("Done generating offline docDesk translations!")
