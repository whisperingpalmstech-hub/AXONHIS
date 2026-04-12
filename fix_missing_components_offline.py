import json
import os

locales_dir = "frontend/src/i18n/locales"

# Massive explicit dictionary for the 5 pages the user is testing
offline_dict = {
  "rpiw": {
    "doctorWorkspace": {"ru": "Рабочее место врача", "ja": "医師ワークスペース", "hi": "डॉक्टर कार्यक्षेत्र", "mr": "डॉक्टर वर्कस्पेस", "de": "Arzt-Arbeitsbereich", "fr": "Espace Médecin", "es": "Espacio del Médico", "ar": "مساحة عمل الطبيب", "pt": "Espaço do Médico", "zh": "医生工作区"},
    "subtitle": {"ru": "Ролевое рабочее пространство для взаимодействия с пациентами (RPIW)", "ja": "役割ベースの患者対話ワークスペース (RPIW)", "hi": "भूमिका-आधारित रोगी इंटरैक्शन कार्यक्षेत्र", "mr": "भूमिका-आधारित रुग्ण संवाद वर्कस्पेस", "de": "Rollenbasierter Patienten-Interaktions-Arbeitsbereich (RPIW)", "fr": "Espace d'interaction patient basé sur les rôles", "es": "Espacio de interacción con el paciente", "ar": "مساحة عمل تفاعل المريض القائمة على الدور", "pt": "Espaço de Interação com Paciente", "zh": "基于角色的患者交互工作区 (RPIW)"},
    "welcomeTo": {"ru": "Добро пожаловать в", "ja": "へようこそ", "hi": "में आपका स्वागत है", "mr": "मध्ये आपले स्वागत आहे", "de": "Willkommen bei", "fr": "Bienvenue à", "es": "Bienvenido a", "ar": "أهلا بك في", "pt": "Bem-vindo ao", "zh": "欢迎来到"},
    "selectWorkflowToStart": {"ru": "Выберите рабочий процесс на левой панели, чтобы начать", "ja": "左側のパネルからワークフローを選択して開始します", "hi": "शुरू करने के लिए बाईं ओर से वर्कफ़्लो चुनें", "mr": "सुरू करण्यासाठी डावीकडील पॅनेलमधून वर्कफ्लो निवडा", "de": "Wählen Sie einen Workflow aus dem linken Bereich", "fr": "Sélectionnez un flux de travail", "es": "Seleccione un flujo de trabajo", "ar": "اختر سير العمل للبدء", "pt": "Selecione um fluxo de trabalho", "zh": "从左侧面板选择工作流程以开始"},
    "recentActivity": {"ru": "Последние действия", "ja": "最近のアクティビティ", "hi": "हाल की गतिविधि", "mr": "अलीकडील क्रियाकलाप", "de": "Letzte Aktivität", "fr": "Activité récente", "es": "Actividad reciente", "ar": "النشاط الأخير", "pt": "Atividade Recente", "zh": "最近活动"},
    "sessionStats": {"ru": "Статистика сеанса", "ja": "セッション統計", "hi": "सत्र आँकड़े", "mr": "सत्र आकडेवारी", "de": "Sitzungsstatistik", "fr": "Statistiques de session", "es": "Estadísticas de la sesión", "ar": "إحصائيات الجلسة", "pt": "Estatísticas da Sessão", "zh": "会话统计"},
    "workflowsAvailable": {"ru": "Доступные рабочие процессы", "ja": "利用可能なワークフロー", "hi": "उपलब्ध वर्कफ़्लो", "mr": "उपलब्ध वर्कफ्लो", "de": "Verfügbare Workflows", "fr": "Flux disponibles", "es": "Flujos disponibles", "ar": "سير العمل المتاح", "pt": "Fluxos Disponíveis", "zh": "可用工作流程"},
    "activePermissions": {"ru": "Активные разрешения", "ja": "アクティブな権限", "hi": "सक्रिय अनुमतियाँ", "mr": "सक्रिय परवानग्या", "de": "Aktive Berechtigungen", "fr": "Autorisations actives", "es": "Permisos activos", "ar": "الأذونات النشطة", "pt": "Permissões Ativas", "zh": "有效权限"},
    "uiComponents": {"ru": "Компоненты UI", "ja": "UIコンポーネント", "hi": "यूआई घटक", "mr": "UI घटक", "de": "UI-Komponenten", "fr": "Composants UI", "es": "Componentes de la interfaz", "ar": "مكونات واجهة المستخدم", "pt": "Componentes de Interface", "zh": "UI 组件"},
    "activityLogs": {"ru": "Журналы активности", "ja": "アクティビティログ", "hi": "गतिविधि लॉग", "mr": "क्रियाकलाप लॉग", "de": "Aktivitätsprotokolle", "fr": "Journaux d'activité", "es": "Registros de actividad", "ar": "سجلات النشاط", "pt": "Registros de Atividade", "zh": "活动日志"},
    "rbacStatus": {"ru": "Статус RBAC", "ja": "RBACステータス", "hi": "RBAC स्थिति", "mr": "RBAC स्थिती", "de": "RBAC-Status", "fr": "Statut RBAC", "es": "Estado RBAC", "ar": "حالة RBAC", "pt": "Status RBAC", "zh": "RBAC 状态"},
    "accessControlActive": {"ru": "Контроль доступа активен", "ja": "アクセス制御がアクティブ", "hi": "पहुंच नियंत्रण सक्रिय", "mr": "प्रवेश नियंत्रण सक्रिय", "de": "Zugriffskontrolle aktiv", "fr": "Contrôle d'accès actif", "es": "Control de acceso activo", "ar": "التحكم في الوصول نشط", "pt": "Controle de Acesso Ativo", "zh": "访问控制处于活动状态"},
    "auditLoggingEnabled": {"ru": "Включено ведение журнала аудита", "ja": "監査ログ有効", "hi": "ऑडिट लॉगिंग सक्षम", "mr": "ऑडिट लॉगिंग सुरू", "de": "Audit-Protokollierung aktiviert", "fr": "Journalisation d'audit activée", "es": "Registro de auditoría habilitado", "ar": "تمكين تسجيل التدقيق", "pt": "Registro de Auditoria Habilitado", "zh": "审核日志已启用"},
    "encryptedSession": {"ru": "Зашифрованный сеанс", "ja": "暗号化されたセッション", "hi": "एन्क्रिप्टेड सत्र", "mr": "एनक्रिप्टेड सत्र", "de": "Verschlüsselte Sitzung", "fr": "Session chiffrée", "es": "Sesión cifrada", "ar": "جلسة مشفرة", "pt": "Sessão Criptografada", "zh": "加密会话"}
  },
  "orders": {
    "orderManagement": {"ru": "Управление заказами", "ja": "オーダー管理", "hi": "आदेश प्रबंधन", "mr": "ऑर्डर व्यवस्थापन", "de": "Auftragsverwaltung", "fr": "Gestion des commandes", "es": "Gestión de pedidos", "ar": "إدارة الطلبات", "pt": "Gerenciamento de Pedidos", "zh": "订单管理"},
    "subtitle": {"ru": "Фаза 4 — Корпоративный механизм заказов", "ja": "フェーズ4 — エンタープライズオーダーエンジン", "hi": "चरण 4 - एंटरप्राइज़ ऑर्डर इंजन", "mr": "टप्पा 4 - एंटरप्राइज ऑर्डर इंजिन", "de": "Phase 4 - Enterprise-Auftrags-Engine", "fr": "Phase 4 - Moteur de commandes", "es": "Fase 4 - Motor de pedidos", "ar": "المرحلة 4 - محرك طلبات المؤسسات", "pt": "Fase 4 - Motor de Pedidos", "zh": "第4阶段 — 企业订单引擎"},
    "selectEncounter": {"ru": "Выберите визит", "ja": "エンカウンターを選択", "hi": "मुठभेड़ का चयन करें", "mr": "मुलाकात निवडा", "de": "Kontakt auswählen", "fr": "Sélectionnez une rencontre", "es": "Seleccionar encuentro", "ar": "حدد اللقاء", "pt": "Selecionar Encontro", "zh": "选择就诊"},
    "selectEncounterDesc": {"ru": "Выберите активный визит для управления заказами", "ja": "オーダーを管理するアクティブなエンカウンターを選択してください", "hi": "ऑर्डर प्रबंधित करने के लिए सक्रिय मुठभेड़ चुनें", "mr": "ऑर्डर व्यवस्थापित करण्यासाठी सक्रिय भेट निवडा", "de": "Wählen Sie einen aktiven Kontakt zur Verwaltung", "fr": "Choisissez une rencontre active", "es": "Elija un encuentro activo", "ar": "اختر لقاء نشط لإدارة الطلبات", "pt": "Escolha um encontro ativo", "zh": "选择处于活动状态的就诊以管理订单"},
    "noEncounterSelected": {"ru": "Визит не выбран", "ja": "エンカウンターが選択されていません", "hi": "कोई मुठभेड़ नहीं चुनी गई", "mr": "कोणतीही भेट निवडलेली नाही", "de": "Kein Kontakt ausgewählt", "fr": "Aucune rencontre sélectionnée", "es": "Ningún encuentro seleccionado", "ar": "لم يتم تحديد أي لقاء", "pt": "Nenhum Encontro Selecionado", "zh": "未选择就诊"}
  },
  "tasks": {
    "taskCareExecution": {"ru": "Выполнение задач и уход", "ja": "タスクとケアの実行", "hi": "कार्य और देखभाल निष्पादन", "mr": "कार्य आणि काळजी अंमलबजावणी", "de": "Aufgaben- & Pflegeausführung", "fr": "Exécution des tâches et soins", "es": "Ejecución de tareas y cuidados", "ar": "تنفيذ المهام والرعاية", "pt": "Execução de Tarefas e Cuidados", "zh": "任务与护理执行"},
    "manageClinicalWorkflowsNursing": {"ru": "Управление клиническими процессами, задачами медсестер и административными обязанностями.", "ja": "臨床ワークフロー、看護業務、管理業務を管理します。", "hi": "नैदानिक कार्यप्रवाह, नर्सिंग कार्यों का प्रबंधन करें।", "mr": "नैदानिक वर्कफ्लो, नर्सिंग कार्य व्यवस्थापित करा.", "de": "Verwalten von klinischen Workflows und Pflegeaufgaben.", "fr": "Gérer les flux de travail cliniques", "es": "Gestión de flujos de trabajo clínicos", "ar": "إدارة سير العمل السريري والمهام التمريضية.", "pt": "Gerenciar fluxos de trabalho clínicos", "zh": "管理临床工作流程、护理任务和行政职责。"},
    "taskQueue": {"ru": "Очередь задач", "ja": "タスクキュー", "hi": "कार्य कतार", "mr": "कार्य रांग", "de": "Aufgabenwarteschlange", "fr": "File d'attente des tâches", "es": "Cola de tareas", "ar": "قائمة المهام", "pt": "Fila de Tarefas", "zh": "任务队列"},
    "myTasks": {"ru": "Мои задачи", "ja": "マイタスク", "hi": "मेरे कार्य", "mr": "माझी कार्ये", "de": "Meine Aufgaben", "fr": "Mes tâches", "es": "Mis tareas", "ar": "مهامي", "pt": "Minhas Tarefas", "zh": "我的任务"},
    "allStatuses": {"ru": "Все статусы", "ja": "すべてのステータス", "hi": "सभी स्थितियाँ", "mr": "सर्व स्थिती", "de": "Alle Status", "fr": "Tous les statuts", "es": "Todos los estados", "ar": "جميع الحالات", "pt": "Todos os Status", "zh": "所有状态"},
    "allRoles": {"ru": "Все роли", "ja": "すべての役割", "hi": "सभी भूमिकाएँ", "mr": "सर्व भूमिका", "de": "Alle Rollen", "fr": "Tous les rôles", "es": "Todos los roles", "ar": "جميع الأدوار", "pt": "Todos os Papéis", "zh": "所有角色"},
    "allCaughtUp": {"ru": "Всё выполнено!", "ja": "すべて完了しました！", "hi": "सब पूरा हो गया!", "mr": "सर्व पूर्ण झाले!", "de": "Alles erledigt!", "fr": "Tout est à jour !", "es": "¡Todo al día!", "ar": "تم إنجاز كل شيء!", "pt": "Tudo em dia!", "zh": "全部完成！"},
    "noTasksFoundQueue": {"ru": "Задачи не найдены.", "ja": "条件に一致するタスクはありません。", "hi": "कतार में कोई कार्य नहीं मिला।", "mr": "रांगेत कोणतेही कार्य आढळले नाही.", "de": "Keine Aufgaben gefunden.", "fr": "Aucune tâche trouvée.", "es": "No se encontraron tareas.", "ar": "لا توجد مهام.", "pt": "Nenhuma tarefa encontrada.", "zh": "队列中未找到匹配的任务。"}
  },
  "wards": {
    "wardAndBedManagement": {"ru": "Управление палатами и койками", "ja": "病棟およびベッド管理", "hi": "वार्ड और बेड प्रबंधन", "mr": "वॉर्ड आणि बेड व्यवस्थापन", "de": "Stations- & Bettenmanagement", "fr": "Gestion des services et des lits", "es": "Gestión de salas y camas", "ar": "إدارة الأجنحة والأسرة", "pt": "Gerenciamento de Alas e Leitos", "zh": "病房和床位管理"},
    "monitorHospitalOccupancy": {"ru": "Мониторинг занятости больницы", "ja": "病院の稼働率を監視します", "hi": "अस्पताल के अधिभोग की निगरानी करें", "mr": "रुग्णालयातील उपस्थितीचे निरीक्षण करा", "de": "Überwachen Sie die Krankenhausbelegung", "fr": "Surveiller l'occupation de l'hôpital", "es": "Monitorear ocupación hospitalaria", "ar": "مراقبة إشغال المستشفى", "pt": "Monitorar a Ocupação", "zh": "监控医院占用情况"},
    "totalCapacity": {"ru": "ОБЩАЯ ВМЕСТИМОСТЬ", "ja": "総容量", "hi": "कुल क्षमता", "mr": "एकूण क्षमता", "de": "GESAMTKAPAZITÄT", "fr": "CAPACITÉ TOTALE", "es": "CAPACIDAD TOTAL", "ar": "السعة الإجمالية", "pt": "CAPACIDADE TOTAL", "zh": "总容量"},
    "occupied": {"ru": "ЗАНЯТО", "ja": "使用中", "hi": "कब्जा", "mr": "व्याप्त", "de": "BELEGT", "fr": "OCCUPÉ", "es": "OCUPADO", "ar": "مشغول", "pt": "OCUPADO", "zh": "已占用"},
    "cleaning": {"ru": "УБОРКА", "ja": "清掃中", "hi": "सफाई", "mr": "स्वच्छता", "de": "REINIGUNG", "fr": "NETTOYAGE", "es": "LIMPIEZA", "ar": "تنظيف", "pt": "LIMPANDO", "zh": "清洁中"},
    "available": {"ru": "СВОБОДНО", "ja": "空室", "hi": "उपलब्ध", "mr": "उपलब्ध", "de": "VERFÜGBAR", "fr": "DISPONIBLE", "es": "DISPONIBLE", "ar": "متاح", "pt": "DISPONÍVEL", "zh": "空闲"},
    "wardDashboard": {"ru": "Панель палат", "ja": "病棟ダッシュボード", "hi": "वार्ड डैशबोर्ड", "mr": "वॉर्ड डॅशबोर्ड", "de": "Stations-Dashboard", "fr": "Tableau de bord du service", "es": "Panel de la sala", "ar": "لوحة الجناح", "pt": "Painel da Ala", "zh": "病房仪表板"},
    "bedInventory": {"ru": "Инвентарь коек", "ja": "ベッドインベントリ", "hi": "बेड इन्वेंटरी", "mr": "बेड इन्व्हेंटरी", "de": "Betteninventar", "fr": "Inventaire des lits", "es": "Inventario de camas", "ar": "جرد الأسرة", "pt": "Inventário de Leitos", "zh": "床位盘点"}
  },
  "nursingIpd": {
    "title": {"ru": "Сестринский лист и прием", "ja": "看護カバーシートと病棟の受け入れ", "hi": "नर्सिंग कवरशीट और वार्ड स्वीकृति", "mr": "नर्सिंग कव्हरशीट आणि वॉर्ड स्वीकृती", "de": "Pflege-Deckblatt & Aufnahme", "fr": "Feuille de soins & Admission", "es": "Hoja de enfermería y admisión", "ar": "ورقة التمريض وقبول الجناح", "pt": "Folha de Rosto e Admissão", "zh": "护理交接表和病房验收"},
    "subtitle": {"ru": "Прием пациентов, листы и документация", "ja": "IPD患者の受け入れと看護の文書化", "hi": "आईपीडी रोगी स्वीकृति और प्रलेखन", "mr": "IPD रुग्ण स्वीकृती आणि दस्तऐवजीकरण", "de": "Stationäre Patientenaufnahme", "fr": "Admission des patients et documentation", "es": "Admisión de pacientes y documentación", "ar": "قبول مرضى العناية وتوثيق التمريض", "pt": "Admissão de Pacientes e Documentação", "zh": "住院患者验收及护理文书"},
    "totalWorklist": {"ru": "Общий список", "ja": "合計ワークリスト", "hi": "कुल कार्यसूची", "mr": "एकूण कार्यसूची", "de": "Gesamte Arbeitsliste", "fr": "Liste de travail totale", "es": "Lista de trabajo total", "ar": "إجمالي قائمة العمل", "pt": "Lista de Trabalho Total", "zh": "总工作单"},
    "accepted": {"ru": "Принятые", "ja": "受け入れ済み", "hi": "स्वीकार किए गए", "mr": "स्वीकारलेले", "de": "Akzeptiert", "fr": "Acceptés", "es": "Aceptados", "ar": "المقبولين", "pt": "Aceitos", "zh": "已接收"},
    "tabWorklist": {"ru": "Список приема", "ja": "入院ワークリスト", "hi": "प्रवेश कार्यसूची", "mr": "प्रवेश कार्यसूची", "de": "Aufnahme-Liste", "fr": "Liste d'admission", "es": "Lista de admisión", "ar": "قائمة القبول", "pt": "Lista de Admissão", "zh": "入院工作单"},
    "tabCoversheets": {"ru": "Принятые пациенты", "ja": "受け入れられた患者", "hi": "स्वीकृत मरीज", "mr": "स्वीकारलेले रुग्ण", "de": "Aufgenommene Patienten", "fr": "Patients acceptés", "es": "Pacientes aceptados", "ar": "المرضى المقبولين", "pt": "Pacientes Aceitos", "zh": "已接收患者"},
    "tabNotes": {"ru": "Сестринские записи", "ja": "看護記録", "hi": "नर्सिंग नोट्स", "mr": "नर्सिंग नोट्स", "de": "Pflegetagebuch", "fr": "Notes infirmières", "es": "Notas de enfermería", "ar": "ملاحظات التمريض", "pt": "Notas de Enfermagem", "zh": "护理记录"},
    "colAdmNo": {"ru": "№ Приема", "ja": "入院番号", "hi": "प्रवेश संख्या", "mr": "प्रवेश क्रमांक", "de": "Aufnahme-Nr", "fr": "Numéro d'admission", "es": "Número de admisión", "ar": "رقم الدخول", "pt": "Nº Admissão", "zh": "入院编号"},
    "colUHID": {"ru": "УИД Пациента", "ja": "患者UHID", "hi": "रोगी UHID", "mr": "रुग्ण UHID", "de": "Patienten-UHID", "fr": "UHID du patient", "es": "UHID del paciente", "ar": "رقم المريض الخاص", "pt": "UHID do Paciente", "zh": "患者UHID"},
    "colBed": {"ru": "Койка / Палата", "ja": "ベッド / 病棟", "hi": "बेड / वार्ड", "mr": "बेड / वॉर्ड", "de": "Bett / Station", "fr": "Lit / Service", "es": "Cama / Sala", "ar": "السرير / الجناح", "pt": "Leito / Ala", "zh": "床位 / 病房"},
    "colAdmittingDoctor": {"ru": "Лечащий врач", "ja": "主治医", "hi": "भर्ती करने वाले डॉक्टर", "mr": "प्रवेश देणारे डॉक्टर", "de": "Aufnehmender Arzt", "fr": "Médecin", "es": "Médico", "ar": "الطبيب المعالج", "pt": "Médico Responsável", "zh": "收治医生"},
    "colTime": {"ru": "Время приема", "ja": "入院時間", "hi": "प्रवेश का समय", "mr": "प्रवेशाची वेळ", "de": "Aufnahmezeit", "fr": "Heure d'admission", "es": "Hora de admisión", "ar": "وقت الدخول", "pt": "Hora de Admissão", "zh": "入院时间"},
    "colStatus": {"ru": "Статус", "ja": "ステータス", "hi": "स्थिति", "mr": "स्थिती", "de": "Status", "fr": "Statut", "es": "Estado", "ar": "الحالة", "pt": "Status", "zh": "状态"},
    "colActions": {"ru": "Действия", "ja": "アクション", "hi": "क्रियाएँ", "mr": "कारवाया", "de": "Aktionen", "fr": "Actions", "es": "Acciones", "ar": "الإجراءات", "pt": "Ações", "zh": "操作"}
  }
}

def apply_massive():
    for f_name in os.listdir(locales_dir):
        if f_name == "en.json" or not f_name.endswith(".json"): continue
        lang = f_name.replace(".json", "")
        path = os.path.join(locales_dir, f_name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except: continue
        
        for module, keys in offline_dict.items():
            if module not in data: data[module] = {}
            for key, val_lang in keys.items():
                if lang in val_lang:
                    data[module][key] = val_lang[lang]
                
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    apply_massive()
    print("Done generating massive offline missing translations!")
