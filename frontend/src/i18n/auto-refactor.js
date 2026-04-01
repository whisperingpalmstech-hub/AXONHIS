const fs = require('fs');
const path = require('path');

const REPLACEMENTS = {
  "First Name": "t(\"patients.firstName\")",
  "Last Name": "t(\"patients.lastName\")",
  "Date of Birth": "t(\"patients.dateOfBirth\")",
  "Gender": "t(\"patients.gender\")",
  "Phone": "t(\"patients.phone\")",
  "Email": "t(\"patients.email\")",
  "Address Line": "t(\"patients.address\")",
  "Pincode": "t(\"patients.pincode\")",
  "Area": "t(\"patients.area\")",
  "City": "t(\"patients.city\")",
  "State": "t(\"patients.state\")",
  "Country": "t(\"patients.country\")",
  "Blood Group": "t(\"patients.bloodGroup\")",
  "Weight (kg)": "t(\"patients.weight\")",
  "Height (cm)": "t(\"patients.height\")",
  "Allergies": "t(\"patients.allergies\")",
  "Chief Complaint": "t(\"patients.chiefComplaint\")",
  "Reason for Visit": "t(\"patients.reasonForVisit\")",
  "Emergency Contact": "t(\"patients.emergencyContact\")",
  "Emergency Phone": "t(\"patients.emergencyPhone\")",
  "ID Type": "t(\"patients.idType\")",
  "Document Number": "t(\"patients.idNumber\")",
  "Insurance Provider": "t(\"patients.insuranceProvider\")",
  "Policy Number": "t(\"patients.policyNumber\")",
  "Next": "t(\"common.next\")",
  "Back": "t(\"common.back\")",
  "Save": "t(\"common.save\")",
  "Cancel": "t(\"common.cancel\")",
  "Submit": "t(\"common.submit\")"
};

const FILES = [
  'src/app/dashboard/patients/registration/page.tsx',
  'src/app/dashboard/doctor-desk/page.tsx',
  'src/app/dashboard/ipd/page.tsx',
  'src/app/dashboard/billing/page.tsx'
];

for (const file of FILES) {
  const fullPath = path.join(process.cwd(), file);
  if (!fs.existsSync(fullPath)) continue;
  
  let content = fs.readFileSync(fullPath, 'utf8');
  let changed = false;
  
  for (const [text, replace] of Object.entries(REPLACEMENTS)) {
    // Match ">Text<" or "label>Text<" or placeholder="Text"
    const regex1 = new RegExp(`>\\s*${text}\\s*<`, 'g');
    const regex2 = new RegExp(`placeholder="${text}"`, 'g');
    const regex3 = new RegExp(`label="${text}"`, 'g');
    
    if (content.includes(`>${text}<`) || content.includes(`placeholder="${text}"`) || content.includes(`label="${text}"`)) {
        content = content.replace(regex1, `>{${replace}}<`);
        content = content.replace(regex2, `placeholder={${replace}}`);
        content = content.replace(regex3, `label={${replace}}`);
        changed = true;
    }
  }
  
  if (changed) {
    fs.writeFileSync(fullPath, content);
    console.log(`Refactored ${file}`);
  }
}
