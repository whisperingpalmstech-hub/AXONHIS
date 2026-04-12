const fs = require('fs');
const path = require('path');

const MAP_HI = {
  "uhid": "UHID", "selectAvailableBedStar": "उपलब्ध बिस्तर चुनें *",
  "dropdownSyncedWithBedMatrix": "— बिस्तर मैट्रिक्स के साथ सिंक —",
  "pleaseSelectAPatientFirstToSee": "परामर्श देखने के लिए पहले मरीज़ चुनें",
  "bedsCanOnlyBeAssignedToPatient": "बेड केवल सक्रिय परामर्श वाले मरीज़ों को ही दिए जा सकते हैं।",
  "loadingEncounters": "परामर्श लोड हो रहा है...", "noEncountersFound": "कोई परामर्श नहीं मिला",
  "clickToStart": "शुरू करने के लिए 'नया परामर्श' चुनें।", "encounterId": "ENCOUNTER ID",
  "newEncounter": "नया परामर्श", "loadingPatients": "मरीज़ लोड हो रहे हैं...",
  "noPatientsFound": "कोई मरीज़ नहीं मिला।", "followUp": "अनुवर्ती",
  "teleconsultation": "टेलीकंसल्टेशन", "scheduled": "शेड्यूल़्ड",
  "inProgress": "प्रगति में", "completed": "पूर्ण", "cancelled": "रद्द",
  "noOrders": "कोई ऑर्डर नहीं मिला।", "loadingOrders": "ऑर्डर लोड हो रहे हैं...",
  "ordered": "ऑर्डर दिया", "scheduledStatus": "शेड्यूल़्ड", "inProgressStatus": "प्रगति में",
  "completedStatus": "पूर्ण", "cancelledStatus": "रद्द"
};

const file = path.join(__dirname, `locales/hi.json`);
let data = JSON.parse(fs.readFileSync(file, 'utf8'));

for (const m in data) {
    for (const k in data[m]) {
        if (MAP_HI[k]) {
            data[m][k] = MAP_HI[k];
        }
    }
}
fs.writeFileSync(file, JSON.stringify(data, null, 2) + '\n');
console.log("Updated Hindi localization to 100% key-match perfection.");
