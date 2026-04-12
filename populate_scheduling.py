import json
import os

locales_dir = "frontend/src/i18n/locales"

scheduling_translations = {
    "en": {
        "title": "Enterprise Appointment Scheduling",
        "subtitle": "Doctor calendars · Slot booking · Overbooking · Cyclic schedules · Modality scheduling · Analytics",
        "doctorCalendar": "Doctor Calendar",
        "bookings": "Bookings",
        "modalityScheduling": "Modality Scheduling",
        "analytics": "Analytics",
        "configuration": "Configuration",
        "selectDoctor": "Select a doctor calendar to view slots",
        "doctorCalendarsTitle": "Doctor Calendars",
        "noCalendars": "No calendars yet. Create one to start."
    },
    "hi": {
        "title": "एंटरप्राइज़ अपॉइंटमेंट शेड्यूलिंग",
        "subtitle": "डॉक्टर कैलेंडर · स्लॉट बुकिंग · ओवरबुकिंग · चक्रीय कार्यक्रम · मोडेलिटी शेड्यूलिंग · एनालिटिक्स",
        "doctorCalendar": "डॉक्टर कैलेंडर",
        "bookings": "बुकिंग",
        "modalityScheduling": "मोडेलिटी शेड्यूलिंग",
        "analytics": "एनालिटिक्स",
        "configuration": "कॉन्फ़िगरेशन",
        "selectDoctor": "स्लॉट देखने के लिए डॉक्टर कैलेंडर चुनें",
        "doctorCalendarsTitle": "डॉक्टर कैलेंडर",
        "noCalendars": "अभी कोई कैलेंडर नहीं है। प्रारंभ करने के लिए एक बनाएं।"
    },
    "mr": {
        "title": "एंटरप्राइज अपॉइंटमेंट शेड्युलिंग",
        "subtitle": "डॉक्टर कॅलेंडर · स्लॉट बुकिंग · ओव्हरबुकिंग · चक्रीय वेळापत्रक · मॉडेलिटी शेड्युलिंग · ॲनालिटिक्स",
        "doctorCalendar": "डॉक्टर कॅलेंडर",
        "bookings": "बुकिंग",
        "modalityScheduling": "मॉडेलिटी शेड्युलिंग",
        "analytics": "ॲनालिटिक्स",
        "configuration": "कॉन्फिगरेशन",
        "selectDoctor": "स्लॉट पाहण्यासाठी डॉक्टर कॅलेंडर निवडा",
        "doctorCalendarsTitle": "डॉक्टर कॅलेंडर",
        "noCalendars": "कोणतेही कॅलेंडर नाही. सुरू करण्यासाठी एक तयार करा."
    },
    "ar": {
        "title": "جدولة المواعيد المؤسسية",
        "subtitle": "تقويم الأطباء · حجز المواعيد · الحجز الزائد · الجداول الدورية · جدول الأقسام · التحليلات",
        "doctorCalendar": "تقويم الطبيب",
        "bookings": "الحجوزات",
        "modalityScheduling": "جدولة الأقسام",
        "analytics": "التحليلات",
        "configuration": "آلإعدادات",
        "selectDoctor": "اختر تقويم طبيب لعرض المواعيد",
        "doctorCalendarsTitle": "تقويمات الأطباء",
        "noCalendars": "لا توجد تقويمات. قم بإنشاء واحد للبدء."
    },
    "es": {
        "title": "Programación de Citas Empresariales",
        "subtitle": "Calendarios médicos · Reserva de turnos · Sobreventa · Horarios cíclicos · Programación de modalidad · Analíticas",
        "doctorCalendar": "Calendario Médico",
        "bookings": "Reservas",
        "modalityScheduling": "Programación de Modalidad",
        "analytics": "Analíticas",
        "configuration": "Configuración",
        "selectDoctor": "Seleccione un calendario médico para ver los turnos",
        "doctorCalendarsTitle": "Calendarios Médicos",
        "noCalendars": "Aún no hay calendarios. Cree uno para empezar."
    },
    "de": {
        "title": "Terminplanung für Unternehmen",
        "subtitle": "Arztkalender · Terminbuchung · Überbuchung · Zyklische Pläne · Modalitätsplanung · Analysen",
        "doctorCalendar": "Arztkalender",
        "bookings": "Buchungen",
        "modalityScheduling": "Modalitätsplanung",
        "analytics": "Analysen",
        "configuration": "Konfiguration",
        "selectDoctor": "Wählen Sie einen Arztkalender aus, um Termine anzuzeigen",
        "doctorCalendarsTitle": "Arztkalender",
        "noCalendars": "Noch keine Kalender. Erstellen Sie einen, um zu beginnen."
    },
    "fr": {
        "title": "Planification des Rendez-vous",
        "subtitle": "Calendriers des médecins · Réservation de créneaux · Surréservation · Horaires cycliques · Planification des modalités · Analytique",
        "doctorCalendar": "Calendrier du Médecin",
        "bookings": "Réservations",
        "modalityScheduling": "Planification des Modalités",
        "analytics": "Analytique",
        "configuration": "Configuration",
        "selectDoctor": "Sélectionnez un calendrier de médecin pour voir les créneaux",
        "doctorCalendarsTitle": "Calendriers des Médecins",
        "noCalendars": "Pas encore de calendrier. Créez-en un pour commencer."
    },
    "pt": {
        "title": "Agendamento Empresarial de Consultas",
        "subtitle": "Calendários médicos · Agendamento · Marcação excedente · Horários cíclicos · Agendamento de modalidade · Analítica",
        "doctorCalendar": "Calendário Médico",
        "bookings": "Marcações",
        "modalityScheduling": "Agendamento de Modalidade",
        "analytics": "Analítica",
        "configuration": "Configuração",
        "selectDoctor": "Selecione um calendário médico para ver as vagas",
        "doctorCalendarsTitle": "Calendários Médicos",
        "noCalendars": "Sem calendários ainda. Crie um para começar."
    },
    "ru": {
        "title": "Корпоративное расписание приемов",
        "subtitle": "Календари врачей · Бронирование слотов · Овербукинг · Циклические графики · Расписание модальностей · Аналитика",
        "doctorCalendar": "Календарь врача",
        "bookings": "Бронирования",
        "modalityScheduling": "Расписание модальностей",
        "analytics": "Аналитика",
        "configuration": "Конфигурация",
        "selectDoctor": "Выберите календарь врача для просмотра слотов",
        "doctorCalendarsTitle": "Календари врачей",
        "noCalendars": "Календарей пока нет. Создайте один, чтобы начать."
    },
    "zh": {
        "title": "企业级预约排班系统",
        "subtitle": "医生排班 · 预约挂号 · 超额预约 · 循环排班 · 设备号源排班 · 统计分析",
        "doctorCalendar": "医生排班",
        "bookings": "预约挂号",
        "modalityScheduling": "设备排班",
        "analytics": "统计分析",
        "configuration": "系统配置",
        "selectDoctor": "选择医生排班以查看号源",
        "doctorCalendarsTitle": "医生排班列表",
        "noCalendars": "暂无排班表。请先创建一个。"
    },
    "ja": {
        "title": "エンタープライズ予約スケジュール",
        "subtitle": "医師カレンダー · 枠予約 · オーバーブッキング · 巡回スケジュール · モダリティ予約 · 分析",
        "doctorCalendar": "医師カレンダー",
        "bookings": "予約状況",
        "modalityScheduling": "モダリティスケジュール",
        "analytics": "分析",
        "configuration": "設定",
        "selectDoctor": "空き枠を表示するには医師のカレンダーを選択してください",
        "doctorCalendarsTitle": "医師カレンダー",
        "noCalendars": "まだカレンダーがありません。開始するには作成してください。"
    }
}

for lang_code, translations in scheduling_translations.items():
    file_path = os.path.join(locales_dir, f"{lang_code}.json")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except:
                data = {}
        
        data["scheduling"] = translations
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Updated {file_path}")
