const fs = require('fs');
const path = require('path');

const MAP_HI = {
  "title": "शीर्षक", "subtitle": "उपशीर्षक", "description": "विवरण", "date": "तारीख",
  "time": "समय", "status": "स्थिति", "actions": "कार्रवाई", "name": "नाम",
  "patient": "मरीज़", "doctor": "डॉक्टर", "nurse": "नर्स", "uhid": "UHID",
  "admission": "प्रवेश", "discharge": "डिस्चार्ज", "transfer": "स्थानांतरण",
  "ward": "वार्ड", "bed": "बिस्तर", "room": "कमरा", "unit": "यूनिट",
  "registration": "पंजीकरण", "search": "खोजें", "filter": "फ़िल्टर", "sort": "क्रमबद्ध करें",
  "pending": "लंबित", "completed": "पूर्ण", "cancelled": "रद्द", "active": "सक्रिय",
  "revenue": "राजस्व", "patients": "मरीज़", "total": "कुल", "avg": "औसत",
  "success": "सफलता", "error": "त्रुटि", "warning": "चेतावनी", "info": "जानकारी",
  "yes": "हाँ", "no": "नहीं", "confirm": "पुष्टि करें", "save": "सहेजें",
  "cancel": "रद्द करें", "delete": "हटाएं", "edit": "संपादित करें", "add": "जोड़ें",
  "next": "अगला", "back": "वापस", "close": "बंद करें", "submit": "सबमिट करें"
};

const file = path.join(__dirname, 'locales/hi.json');
let data = JSON.parse(fs.readFileSync(file, 'utf8'));

for (const module in data) {
    for (const key in data[module]) {
        if (MAP_HI[key] && data[module][key] === key) {
            data[module][key] = MAP_HI[key];
        }
    }
}
fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
console.log("Updated Hindi localization with massive token pass.");
