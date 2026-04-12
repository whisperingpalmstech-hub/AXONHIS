const fs = require('fs');
const path = require('path');

const TRANSLATIONS = {
  hi: {
    ipd: {
      title: "आईपीडी प्रबंधन", admissions: "आईपीडी प्रवेश", pendingRequests: "लंबित अनुरोध",
      admittedPatients: "प्रवेशित मरीज़", admissionRequest: "प्रवेश अनुरोध",
      allocateBed: "बेड आवंटित करें", patientName: "मरीज़ का नाम",
      admittingDoctor: "प्रवेश डॉक्टर", treatingDoctor: "उपचार डॉक्टर",
      specialty: "विशेषता", reasonForAdmission: "प्रवेश का कारण",
      admissionCategory: "प्रवेश श्रेणी", admissionSource: "प्रवेश स्रोत",
      clinicalNotes: "नैदानिक नोट्स", bedCategory: "पसंदीदा बेड श्रेणी",
      admissionNumber: "प्रवेश नंबर", ward: "वार्ड", bed: "बेड",
      diagnosis: "निदान", treatmentPlan: "उपचार योजना",
      progressNotes: "प्रगति नोट्स", vitals: "वाइटल्स",
      nursingNotes: "नर्सिंग नोट्स", discharge: "डिस्चार्ज",
      transfer: "स्थानांतरण", smartWardsCentralNursing: "स्मार्ट वार्ड और केंद्रीय नर्सिंग",
      refreshTelemetry: "टेलीमेट्री रीफ्रेश करें", connectingToWardStations: "वार्ड स्टेशनों से कनेक्ट हो रहा है...",
      activeAdmissions: "सक्रिय प्रवेश", currentlyAccommodated: "वर्तमान में समायोजित",
      awaitingErOpdClearance: "ईआर/ओपीडी क्लीयरेंस की प्रतीक्षा", icuOccupancy: "आईसीयू ऑक्यूपेंसी",
      criticalCareBeds: "क्रिटिकल केयर बेड", dischargesToday: "आज के डिस्चार्ज",
      clearedByBilling: "बिलिंग द्वारा मंजूरी", activeWardCensus: "सक्रिय वार्ड जनगणना",
      patient: "मरीज़", wardBed: "वार्ड / बेड",
      attendingDoctor: "उपचार डॉक्टर", status: "स्थिति", action: "कार्रवाई",
      noActiveAdmissionsCurrentlyTra: "वर्तमान में कोई सक्रिय प्रवेश ट्रैकिंग नहीं।",
      stable: "स्थिर", nursingFlowsheet: "नर्सिंग फ्लोशीट",
      requestTime: "अनुरोध का समय", priority: "प्राथमिकता",
      diagnosisNotes: "निदान / नोट्स", noPendingAdmissionRequestsFrom: "ओपीडी/ईआर से कोई लंबित प्रवेश अनुरोध नहीं।",
      allocateWardBed: "वार्ड बेड आवंटित करें", gen101GeneralMaleWard: "GEN-101 (जनरल मेल वार्ड)",
      gen102GeneralMaleWard: "GEN-102 (जनरल मेल वार्ड)", icu01IntensiveCare: "ICU-01 (आईसीयू)",
      pvt205PrivateRoomSuite: "PVT-205 (प्राइवेट रूम सुइट)", cancel: "रद्द करें",
      confirmAllocation: "प्रवेश की पुष्टि करें", inpatientDepartment: "इनपेशेंट विभाग (IPD)",
      ipdSubtitle: "बेड बोर्ड • वाइटल्स मॉनिटरिंग • प्रवेश अनुरोध",
      admissionRequestsTab: "प्रवेश अनुरोध", admHash: "प्रवेश #",
      bedAllocatedStr: "बेड आवंटित", generalWardStr: "जनरल वार्ड",
      assignedDr: "नियुक्त", pendingDoctor: "लंबित डॉक्टर",
      triageStandard: "ट्रायज मानक", priorityLabel: "प्राथमिकता",
      selectAvailableBedStar: "उपलब्ध बेड चुनें *", dropdownSyncedWithBedMatrix: "— बेड मैट्रिक्स के साथ सिंक किया गया —"
    },
    billing: {
      title: "आईपीडी बिलिंग और निपटान",
      subtitle: "मरीज़ शुल्क, जमा, बीमा और अंतिम निपटान प्रबंधित करें।",
      activePatients: "सक्रिय मरीज़", settledDischarged: "निपटाया / डिस्चार्ज",
      manageBill: "बिल प्रबंधित करें", billingDetails: "बिलिंग विवरण",
      serviceCharges: "मदवार सेवाएं और शुल्क", addService: "सेवा जोड़ें",
      serviceCategory: "श्रेणी", serviceName: "सेवा का नाम",
      quantity: "मात्रा", unitPrice: "इकाई मूल्य", totalPrice: "कुल",
      advanceDeposits: "अग्रिम जमा", collectDeposit: "जमा राशि लें",
      insuranceClaims: "बीमा और टीपीए दावे", fileClaim: "दावा दायर करें",
      approveClaim: "मंजूरी दें", provider: "प्रदाता",
      preAuth: "पूर्व-प्राधिकरण", coverageLimit: "कवरेज सीमा",
      claimedAmount: "दावा किया गया", approvedAmount: "अनुमोदित",
      billSummary: "बिल सारांश", grossCharges: "कुल शुल्क",
      discount: "निश्चित छूट", netAmount: "शुद्ध राशि",
      insurancePayable: "बीमा भुगतान योग्य", patientPayable: "मरीज़ देय",
      depositsReceived: "अग्रिम जमा", paymentsReceived: "प्राप्त भुगतान",
      outstandingBalance: "बकाया शेष", refundDue: "रिफंड देय",
      fullySettled: "पूरी तरह से निपटाया गया", processPayment: "भुगतान संसाधित करें",
      paymentAmount: "भुगतान राशि", paymentMode: "मोड",
      referenceId: "संदर्भ आईडी", recalculate: "पुनर्गणना",
      printBill: "विस्तृत बिल प्रिंट करें", printReceipt: "रसीद प्रिंट करें",
      billingFinanceHub: "बिलिंग और वित्त हब", deposits: "जमा",
      estimates: "अनुमान", creditNotes: "क्रेडिट नोट्स",
      crossEvents: "क्रॉस इवेंट्स", loadingFinancialData: "वित्तीय डेटा लोड हो रहा है...",
      patient: "मरीज़", amount: "राशि", utilized: "उपयोग किया गया",
      balance: "शेष राशि", status: "स्थिति", date: "तारीख",
      noDepositsRecordedYet: "अभी तक कोई जमा राशि दर्ज नहीं की गई",
      admissionEstimates: "प्रवेश अनुमान", noEstimatesCreatedYet: "अभी तक कोई अनुमान नहीं बनाया गया",
      insurancePreAuthorizations: "बीमा पूर्व-प्राधिकरण", requested: "अनुरोधित",
      approved: "अनुमोदित", noPreAuthorizations: "कोई पूर्व-प्राधिकरण नहीं",
      crossModuleIntegrationEvents: "क्रॉस-मोड्यूल एकीकरण कार्यक्रम",
      moduleConnectivityMap: "मोड्यूल कनेक्टिविटी मैप"
    }
  },
  mr: {
    ipd: {
      title: "आयपीडी व्यवस्थापन", admissions: "IPD प्रवेश", pendingRequests: "प्रलंबित विनंत्या",
      admittedPatients: "दाखल रुग्ण", admissionRequest: "प्रवेश विनंती",
      allocateBed: "बेड वाटप करा", patientName: "रुग्णाचे नाव",
      admittingDoctor: "प्रवेश डॉक्टर", treatingDoctor: "उपचार डॉक्टर",
      specialty: "विशेषता", reasonForAdmission: "प्रवेशाचे कारण",
      admissionCategory: "प्रवेश प्रवर्ग", admissionSource: "प्रवेश स्रोत",
      clinicalNotes: "क्लिनिकल नोट्स", bedCategory: "पसंतीचा बेड प्रवर्ग",
      admissionNumber: "प्रवेश क्रमांक", ward: "वॉर्ड", bed: "बेड",
      diagnosis: "निदान", treatmentPlan: "उपचार योजना",
      progressNotes: "प्रगती नोट्स", vitals: "वाइटल्स",
      nursingNotes: "नर्सिंग नोट्स", discharge: "डिस्चार्ज",
      transfer: "बदली", smartWardsCentralNursing: "स्मार्ट वॉर्ड आणि केंद्रीय नर्सिंग",
      refreshTelemetry: "टेलीमेट्री रिफ्रेश करा", connectingToWardStations: "वॉर्ड स्टेशन्सशी जोडले जात आहे...",
      activeAdmissions: "सक्रिय प्रवेश", currentlyAccommodated: "सध्याचे रुग्ण",
      awaitingErOpdClearance: "ER/OPD क्लिअरन्सची प्रतीक्षा", icuOccupancy: "ICU व्याप्ती",
      criticalCareBeds: "क्रिटिकल केअर बेड", dischargesToday: "आजचे डिस्चार्ज",
      clearedByBilling: "बिलिंगद्वारे मंजूर", activeWardCensus: "सक्रिय वॉर्ड जनगणना",
      patient: "रुग्ण", wardBed: "वॉर्ड / बेड",
      attendingDoctor: "उपचार डॉक्टर", status: "स्थिती", action: "कृती",
      noActiveAdmissionsCurrentlyTra: "सध्या कोणतेही सक्रिय प्रवेश ट्रॅकिंग नाही.",
      stable: "स्थिर", nursingFlowsheet: "नर्सिंग फ्लोशीट",
      requestTime: "विनंतीची वेळ", priority: "प्राधान्य",
      diagnosisNotes: "निदान / नोट्स", noPendingAdmissionRequestsFrom: "OPD/ER कडून प्रलंबित प्रवेश विनंती नाही.",
      allocateWardBed: "वॉर्ड बेड वाटप करा", gen101GeneralMaleWard: "GEN-101 (जनरल मेल वॉर्ड)",
      gen102GeneralMaleWard: "GEN-102 (जनरल मेल वॉर्ड)", icu01IntensiveCare: "ICU-01 (ICU)",
      pvt205PrivateRoomSuite: "PVT-205 (प्राइवेट रूम सुइट)", cancel: "रद्द करा",
      confirmAllocation: "प्रवेशाची पुष्टी करा", inpatientDepartment: "इनपेशेंट विभाग (IPD)",
      ipdSubtitle: "बेड बोर्ड • वाइटल्स मॉनिटरिंग • प्रवेश विनंती",
      admissionRequestsTab: "प्रवेश विनंती", admHash: "प्रवेश #",
      bedAllocatedStr: "बेड वाटप केले", generalWardStr: "जनरल वॉर्ड",
      assignedDr: "नेमणूक", pendingDoctor: "प्रलंबित डॉक्टर",
      triageStandard: "ट्रायज मानक", priorityLabel: "प्राधान्य",
      selectAvailableBedStar: "उपलब्ध बेड निवडा *", dropdownSyncedWithBedMatrix: "— बेड मॅट्रिक्सशी सिंक केले आहे —"
    },
    billing: {
      title: "आयपीडी बिलिंग आणि सेटलमेंट",
      subtitle: "रुग्ण शुल्क, ठेव, विमा आणि अंतिम सेटलमेंट व्यवस्थापित करा.",
      activePatients: "सक्रिय रुग्ण", settledDischarged: "सेटल / डिस्चार्ज",
      manageBill: "बिल व्यवस्थापित करा", billingDetails: "बिलिंग तपशील",
      serviceCharges: "सेवा आणि शुल्क", addService: "सेवा जोडा",
      serviceCategory: "प्रवर्ग", serviceName: "सेवेचे नाव",
      quantity: "प्रमाण", unitPrice: "दर", totalPrice: "एकूण",
      advanceDeposits: "आगाऊ ठेव", collectDeposit: "ठेव गोळा करा",
      insuranceClaims: "विमा आणि TPA दावे", fileClaim: "दावा दाखल करा",
      approveClaim: "मंजूरी द्या", provider: "प्रदाता",
      preAuth: "पूर्व-मंजुरी", coverageLimit: "कवरेज मर्यादा",
      claimedAmount: "दावा केलेली रक्कम", approvedAmount: "मंजूर रक्कम",
      billSummary: "बिल सारांश", grossCharges: "एकूण शुल्क",
      discount: "सवलत", netAmount: "निव्वळ रक्कम",
      insurancePayable: "विमा देय", patientPayable: "रुग्ण देय",
      depositsReceived: "आगाऊ ठेव", paymentsReceived: "प्राप्त रक्कम",
      outstandingBalance: "थकीत रक्कम", refundDue: "परतावा देय",
      fullySettled: "पूर्ण सेटलमेंट", processPayment: "पेमेंट करा",
      paymentAmount: "पेमेंट रक्कम", paymentMode: "मोड",
      referenceId: "संदर्भ आयडी", recalculate: "पुन्हा गणना करा",
      printBill: "तपशीलवार बिल प्रिंट करा", printReceipt: "पावती प्रिंट करा",
      billingFinanceHub: "बिलिंग आणि फायनान्स हब", deposits: "ठेव",
      estimates: "अंदाज", creditNotes: "क्रेडिट नोट्स",
      crossEvents: "क्रॉस इवेंट्स", loadingFinancialData: "आर्थिक माहिती लोड होत आहे...",
      patient: "रुग्ण", amount: "रक्कम", utilized: "वापरलेले",
      balance: "शिल्लक", status: "स्थिती", date: "तारीख",
      noDepositsRecordedYet: "द्या कोणतीही ठेव नोंदवलेली नाही",
      admissionEstimates: "प्रवेश अंदाज", noEstimatesCreatedYet: "अद्याप कोणतेही अंदाज तयार केलेले नाहीत",
      insurancePreAuthorizations: "विमा पूर्व-मंजुरी", requested: "विनंती केली",
      approved: "मंजूर", noPreAuthorizations: "कोणतीही पूर्व-मंजुरी नाही",
      crossModuleIntegrationEvents: "क्रॉस-मॉड्यूल एकत्रीकरण",
      moduleConnectivityMap: "मॉड्यूल कनेक्टिव्हिटी मॅप"
    }
  }
};

const LANGUAGES = ['hi', 'mr'];

for (const lang of LANGUAGES) {
  const localeFile = path.join(__dirname, `locales/${lang}.json`);
  let data = {};
  if (fs.existsSync(localeFile)) {
    data = JSON.parse(fs.readFileSync(localeFile, 'utf8'));
  }
  
  const tr = TRANSLATIONS[lang];
  if (tr) {
    for (const module in tr) {
      data[module] = { ...(data[module] || {}), ...tr[module] };
    }
    fs.writeFileSync(localeFile, JSON.stringify(data, null, 2) + '\n');
    console.log(`Updated ${lang}.json for ipd, billing`);
  }
}
