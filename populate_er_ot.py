import json
import os

locales_dir = "frontend/src/i18n/locales"

translations = {
    "er": {
        # missing er strings
        "digitalCommandCenter": "Digital Command Center • Triage • Bed Map • MLC",
        "erPatientFlow": "ER Patient Flow",
        "reg": "Registration",
        "triageEsi": "Triage (ESI)",
        "bedAssign": "Bed Assignment",
        "tx": "Treatment",
        "disposition": "Disposition",
        "dischargeAdmit": "Discharge/Admit",
        "commandCenter": "Command Center",
        "patientList": "Patient List",
        "triageQueue": "Triage Queue",
        "bedMap": "Bed Map",
        "mlcCasesTab": "MLC Cases",
        "erHash": "ER #",
        "noErBeds": "No ER beds configured. Click 'Seed Beds' to set up default zones.",
        "regFailed": "Registration failed",
        "triageFailed": "Triage failed",
        "mlcFailed": "MLC creation failed",
        "updateStatusFailed": "Failed to update status",
        "urgentType": "🔴 Urgent (Minimal Info)",
        "normalType": "🟢 Normal (Full UHID)",
        "patientNameStar": "Patient Name *",
        "chiefComplaintStar": "Chief Complaint *",
        "triageCategoryStar": "Triage Category (ESI) *",
        "esi1": "🔴 ESI-1 Resuscitation (Immediate)",
        "esi2": "🟠 ESI-2 Emergent (< 10 min)",
        "esi3": "🟡 ESI-3 Urgent (< 30 min)",
        "esi4": "🟢 ESI-4 Less Urgent (< 60 min)",
        "esi5": "🔵 ESI-5 Non-Urgent (< 120 min)",
        # some existing items may need fallback just in case
        "resuscitation": "Resuscitation"
    },
    "ot": {
        "operatingTheatre": "Operating Theatre (OT)",
        "surgeonCommandCenter": "Surgeon Command Center",
        "otSubtitle": "Surgery Schedules • OT Status • PAC Forms",
        "constructOtRooms": "Construct OT Rooms",
        "scheduleSurgery": "Schedule Surgery",
        "checkingOt": "Checking OT Sterilization & Availability...",
        "totalRooms": "Total Rooms",
        "available": "Available",
        "todaysSurgeries": "Today's Surgeries",
        "inProgress": "In Progress (Cutting)",
        "completed": "Completed",
        "dailySurgicalSchedule": "Daily Surgical Schedule",
        "otAvailabilityMatrix": "OT Availability Matrix",
        "time": "Time",
        "patient": "Patient",
        "surgery": "Surgery",
        "surgeon": "Surgeon",
        "room": "Room",
        "status": "Status",
        "noSurgeries": "No surgeries scheduled for today.",
        "noOtRooms": "No OT Rooms configured. Click 'Construct OT Rooms' at the top to bootstrap default suites.",
        "laminarFlow": "LAMINAR FLOW",
        "cArmEq": "C-ARM EQ.",
        "laserSuite": "LASER SUITE",
        "blockOt": "Block Operating Theatre",
        "selectLivePatient": "Select Live Patient *",
        "corePatientRegistry": "— Core Patient Registry —",
        "selectOtRoom": "Select OT Room *",
        "availableSuites": "— Available Suites —",
        "primarySurgeon": "Primary Surgeon *",
        "egDrHouse": "e.g. Dr. House",
        "surgeryProcedure": "Surgery Procedure *",
        "egAppendectomy": "e.g. Appendectomy",
        "cancel": "Cancel",
        "commitToBoard": "Commit to Board",
        "surgeryScheduledSuccessfully": "Surgery Scheduled Successfully",
        "scheduleError": "Failed to schedule surgery.",
        "seedRoomsError": "Failed to seed rooms."
    }
}

prefixes = {
    "en": "",
    "hi": "[HI] ",
    "mr": "[MR] ",
    "ar": "[AR] ",
    "es": "[ES] ",
    "fr": "[FR] ",
    "pt": "[PT] ",
    "de": "[DE] ",
    "ru": "[RU] ",
    "zh": "[ZH] ",
    "ja": "[JA] "
}

for f in os.listdir(locales_dir):
    if f.endswith(".json"):
        path = os.path.join(locales_dir, f)
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
            
        lang = f.split(".")[0]
        prefix = prefixes.get(lang, f"[{lang.upper()}] ")
        
        for module in ["er", "ot"]:
            if module not in data or not isinstance(data[module], dict):
                data[module] = {}
            
            for key, val in translations[module].items():
                if lang == "en":
                    data[module][key] = val
                else:
                    data[module][key] = prefix + val
                
        with open(path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
            
print("Successfully populated ER & OT translations!")
