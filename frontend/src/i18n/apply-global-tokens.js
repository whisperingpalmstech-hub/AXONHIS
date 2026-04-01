const fs = require('fs');
const path = require('path');

const MAP_HI = {
  "Patient": "मरीज़", "Doctor": "डॉक्टर", "Nurse": "नर्स", "Pharmacist": "फार्मासिस्ट",
  "Laboratory": "प्रयोगशाला", "Pharmacy": "फार्मेसी", "Billing": "बिलिंग",
  "Radiology": "रेडियोलॉजी", "Ward": "वार्ड", "Bed": "बिस्तर", "Room": "कमरा",
  "Register": "पंजीकरण", "Manage": "प्रबंधन", "Clinical": "नैदानिक",
  "Management": "प्रबंधन", "Registry": "रजिस्ट्री", "Operation": "ऑपरेशन",
  "Emergency": "आपातकालीन", "Active": "सक्रिय", "Pending": "लंबित",
  "Cancelled": "रद्द", "Completed": "पूर्ण", "Approved": "स्वीकृत",
  "Rejected": "अस्वीकृत", "Search": "खोजें", "View": "देखें", "Add": "जोड़ें",
  "Edit": "संपादित करें", "Delete": "हटाएं", "Save": "सहेजें", "Submit": "सबमिट करें",
  "Cancel": "रद्द करें", "Total": "कुल", "Average": "औसत", "Count": "गिनती",
  "Status": "स्थिति", "Action": "कार्रवाई", "Date": "तारीख", "Time": "समय",
  "Name": "नाम", "Type": "प्रकार", "Category": "श्रेणी", "Description": "विवरण",
  "Summary": "सारांश", "Result": "परिणाम", "Order": "ऑर्डर", "Test": "परीक्षण",
  "Medicine": "दवा", "Dose": "खुराक", "Amount": "राशि", "Price": "कीमत",
  "Login": "लॉगइन", "Logout": "लॉगआउट", "Profile": "प्रोफ़ाइल", "Settings": "सेटिंग्स",
  "Notifications": "सूचनाएं", "Welcome": "स्वागत है", "Loading": "लोड हो रहा है...",
  "Error": "त्रुटि", "Success": "सफलता", "Warning": "चेतावनी", "Info": "जानकारी",
  "Required": "आवश्यक", "Optional": "वैकल्पिक", "Confirm": "पुष्टि करें",
  "Yes": "हाँ", "No": "नहीं", "Close": "बंद करें", "Back": "वापस", "Next": "अगला",
  "Print": "प्रिंट", "Export": "निर्यात", "Import": "आयात", "Filter": "फ़िल्टर",
  "Sort": "क्रमबद्ध करें", "Select": "चुनें", "All": "सभी"
};

const MAP_MR = {
  "Patient": "रुग्ण", "Doctor": "डॉक्टर", "Nurse": "नर्स", "Pharmacist": "औषधपाल",
  "Laboratory": "प्रयोगशाळा", "Pharmacy": "औषधालय", "Billing": "बिलिंग",
  "Radiology": "रेडिओलॉजी", "Ward": "वॉर्ड", "Bed": "बेड", "Room": "खोली",
  "Register": "नोंदणी", "Manage": "व्यवस्थापन", "Clinical": "क्लिनिकल",
  "Registry": "नोंदणी", "Emergency": "आपत्कालीन", "Active": "सक्रिय",
  "Pending": "प्रलंबित", "Cancelled": "रद्द", "Completed": "पूर्ण",
  "Approved": "मंजूर", "Rejected": "नाकारले", "Search": "शोधा", "View": "पहा",
  "Add": "जोडा", "Edit": "संपादित करा", "Delete": "हटवा", "Save": "जतन करा",
  "Submit": "सादर करा", "Cancel": "रद्द करा", "Total": "एकूण", "Status": "स्थिती",
  "Action": "कृती", "Date": "तारीख", "Time": "वेळ", "Name": "नाव", "Type": "प्रकार",
  "Login": "लॉगिन", "Logout": "लॉगआउट", "Profile": "प्रोफाइल", "Settings": "सेटिंग्ज",
  "Notifications": "सूचना", "Welcome": "स्वागत", "Loading": "लोड होत आहे...",
  "Error": "त्रुटी", "Success": "यश", "Yes": "होय", "No": "नाही", "Close": "बंद करा",
  "Back": "मागे", "Next": "पुढे"
};

const en = JSON.parse(fs.readFileSync(path.join(__dirname, 'locales/en.json'), 'utf8'));

function applyGlobal(lang, map) {
  const file = path.join(__dirname, `locales/${lang}.json`);
  let data = JSON.parse(fs.readFileSync(file, 'utf8'));
  for (const module in en) {
    if (!data[module]) data[module] = {};
    for (const key in en[module]) {
      let val = en[module][key];
      if (typeof val === 'string') {
        // Simple token replacement
        for (const [enToken, trToken] of Object.entries(map)) {
          const regex = new RegExp(`\\b${enToken}\\b`, 'gi');
          if (data[module][key] === val) { // Only if not already translated properly
            data[module][key] = data[module][key].replace(regex, trToken);
          }
        }
      }
    }
  }
  fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
}

applyGlobal('hi', MAP_HI);
applyGlobal('mr', MAP_MR);
console.log("Global token replacement finished for Regional languages.");
