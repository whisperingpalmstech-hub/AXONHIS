#!/usr/bin/env node
/**
 * AXONHIS i18n Batch String Replacer
 * Replaces hardcoded UI strings in all pages with t() calls
 */
const fs = require('fs');
const path = require('path');

const DASHBOARD = path.join(__dirname, '..', 'app', 'dashboard');

// Page-specific replacements: [filePath] => [[targetString, replacement]]
const replacements = {
  // ── Settings ─────────────────────────────────
  'settings/page.tsx': [
    ['            System Settings\n', '            {t("settings.title")}\n'],
    ['>Global application configurations, features, and environment variables.</p>', '>{t("settings.subtitle")}</p>'],
    ['<span>Refresh</span>', '<span>{t("common.refresh")}</span>'],
    ['>Loading configurations...</div>', '>{t("settings.loading")}</div>'],
    ['>No settings found.</div>', '>{t("settings.noConfigs")}</div>'],
    ['                    Save\n', '                    {t("common.save")}\n'],
  ],

  // ── System ───────────────────────────────────
  'system/page.tsx': [
    ['System Administration', '{t("system.title")}'],
    ['Core system diagnostics', '{t("system.subtitle")}'],
  ],

  // ── IPD Discharge ────────────────────────────
  'ipd-discharge/page.tsx': [
    ['            Smart Discharge Planning\n', '            {t("ipdDischarge.title")}\n'],
    ['>Manage patient readiness, checklists, and documentation</p>', '>{t("ipdDischarge.subtitle")}</p>'],
    ['>Select Active Admission</label>', '>{t("ipdDischarge.selectAdmission")}</label>'],
    ['>-- Choose Patient Admission --</option>', '>-- {t("ipdDischarge.selectAdmission")} --</option>'],
    ['>Loading Discharge Engine...</div>', '>{t("ipdDischarge.loadingDischarge")}</div>'],
    ['                Discharge Plan\n', '                {t("ipdDischarge.dischargePlan")}\n'],
    ['>Planned Discharge Date</label>', '>{t("ipdDischarge.plannedDate")}</label>'],
    ['                Readiness Checklist\n', '                {t("ipdDischarge.checklist")}\n'],
    ['                Pending Orders\n', '                {t("ipdDischarge.pendingOrders")}\n'],
    ['>All clinical orders are completed.</p>', '>{t("ipdDischarge.noPendingOrders")}</p>'],
    ['                  Discharge Summary\n', '                  {t("ipdDischarge.dischargeSummary")}\n'],
    ['                   Auto-Generate\n', '                   {t("ipdDischarge.generateSummary")}\n'],
    ['                  Ensure all checklist items are ticked and pending orders cleared.\n', '                  {t("ipdDischarge.checklist")}\n'],
    ['                   Finalize Discharge & Release Bed\n', '                   {t("ipdDischarge.completeDischarge")}\n'],
    ['>Select a patient admission to begin discharge planning</p>', '>{t("ipdDischarge.selectAdmission")}</p>'],
  ],

  // ── IPD Doctor Desk ──────────────────────────
  'ipd-doctor-desk/page.tsx': [
    ['IPD Doctor Rounds', '{t("ipdDoctorDesk.title")}'],
    ['Inpatient clinical management', '{t("ipdDoctorDesk.subtitle")}'],
    ['>COVERSHEET</button>', '>{t("ipdDoctorDesk.coversheet")}</button>'],
    ['>DIAGNOSES</button>', '>{t("ipdDoctorDesk.diagnoses")}</button>'],
    ['>TREATMENT</button>', '>{t("ipdDoctorDesk.treatmentPlans")}</button>'],
    ['>PROGRESS</button>', '>{t("ipdDoctorDesk.progressNotes")}</button>'],
    ['>PROCEDURES</button>', '>{t("ipdDoctorDesk.procedures")}</button>'],
  ],

  // ── IPD Orders ───────────────────────────────
  'ipd-orders/page.tsx': [
    ['IPD Clinical Orders', '{t("ipdOrders.title")}'],
    ['>Select a patient to manage orders</p>', '>{t("ipdOrders.selectPatient")}</p>'],
  ],

  // ── IPD Transfers ────────────────────────────
  'ipd-transfers/page.tsx': [
    ['IPD Bed Transfer', '{t("ipdTransfers.title")}'],
    ['Transfer History', '{t("ipdTransfers.transferHistory")}'],
    ['>No transfers recorded</', '>{t("ipdTransfers.noTransfers")}</'],
  ],

  // ── IPD Billing ──────────────────────────────
  'ipd-billing/page.tsx': [
    ['IPD Billing Dashboard', '{t("ipdBilling.title")}'],
    ['Billing & Settlement for Inpatients', '{t("ipdBilling.subtitle")}'],
  ],

  // ── IP Pharmacy Issues ───────────────────────
  'ip-pharmacy-issues/page.tsx': [
    ['IP Medication Issue', '{t("ipPharmacy.title")}'],
    ['Dispense medications', '{t("ipPharmacy.subtitle")}'],
  ],

  // ── IP Pharmacy Returns ──────────────────────
  'ip-pharmacy-returns/page.tsx': [
    ['IP Pharmacy Returns', '{t("ipPharmacy.returnTitle")}'],
    ['Process returns from wards', '{t("ipPharmacy.returnSubtitle")}'],
  ],

  // ── Lab Processing ───────────────────────────
  'lab-processing/page.tsx': [
    ['Lab Processing Workflow', '{t("labProcessing.title")}'],
    ['Track and process lab samples', '{t("labProcessing.subtitle")}'],
  ],

  // ── LIS Orders ───────────────────────────────
  'lis-orders/page.tsx': [
    ['LIS Order Management', '{t("lisOrders.title")}'],
    ['Laboratory Information System', '{t("lisOrders.subtitle")}'],
  ],

  // ── Narcotics Workbench ──────────────────────
  'narcotics-workbench/page.tsx': [
    ['Narcotics Vault', '{t("narcotics.title")}'],
    ['Controlled Substance', '{t("narcotics.subtitle")}'],
    ['>Validation</button>', '>{t("narcotics.validation")}</button>'],
    ['>Dispensing</button>', '>{t("narcotics.dispensing")}</button>'],
    ['>Returns</button>', '>{t("narcotics.returns")}</button>'],
    ['>Audit Trail</button>', '>{t("narcotics.auditTrail")}</button>'],
  ],

  // ── Nursing Vitals ───────────────────────────
  'nursing-vitals/page.tsx': [
    ['Nursing Vitals Dashboard', '{t("nursingVitals.title")}'],
    ['Comprehensive patient vitals', '{t("nursingVitals.subtitle")}'],
  ],

  // ── Phlebotomy ───────────────────────────────
  'phlebotomy/page.tsx': [
    ['Phlebotomy Worklist', '{t("phlebotomy.title")}'],
    ['Sample collection', '{t("phlebotomy.subtitle")}'],
  ],

  // ── Central Receiving ────────────────────────
  'central-receiving/page.tsx': [
    ['Central Sample Receiving', '{t("centralReceiving.title")}'],
    ['Receive, verify', '{t("centralReceiving.subtitle")}'],
  ],

  // ── Result Validation ────────────────────────
  'result-validation/page.tsx': [
    ['Result Validation Desk', '{t("resultValidation.title")}'],
    ['Multi-tier result approval', '{t("resultValidation.subtitle")}'],
  ],

  // ── Reporting Release ────────────────────────
  'reporting-release/page.tsx': [
    ['Lab Report Release', '{t("reportingRelease.title")}'],
    ['Digital Sign', '{t("reportingRelease.subtitle")}'],
  ],

  // ── Radiology ────────────────────────────────
  'radiology/page.tsx': [
    ['Radiology Dashboard', '{t("radiology.title")}'],
    ['Radiology Worklist', '{t("radiology.orders")}'],
  ],

  // ── Blood Bank ───────────────────────────────
  'blood-bank/page.tsx': [
    ['Central Blood Bank', '{t("bloodBank.title")}'],
    ['Crossmatching', '{t("bloodBank.subtitle")}'],
  ],

  // ── Advanced Lab ─────────────────────────────
  'advanced-lab/page.tsx': [
    ['Advanced Diagnostics', '{t("advancedLab.title")}'],
  ],

  // ── Extended Lab ─────────────────────────────
  'extended-lab/page.tsx': [
    ['Extended Lab Services', '{t("extendedLab.title")}'],
  ],

  // ── Analyzer Integration ─────────────────────
  'analyzer-integration/page.tsx': [
    ['Analyzer Integration Hub', '{t("analyzerHub.title")}'],
    ['Bidirectional Interface', '{t("analyzerHub.subtitle")}'],
  ],

  // ── Pharmacy Sales ───────────────────────────
  'pharmacy-sales/page.tsx': [
    ['Walk-In Sales', '{t("pharmacySales.title")}'],
    ['Over-the-counter', '{t("pharmacySales.subtitle")}'],
  ],

  // ── Pharmacy Core ────────────────────────────
  'pharmacy-core/page.tsx': [
    ['Pharmacy Core', '{t("pharmacyCore.title")}'],
    ['Central pharmacy', '{t("pharmacyCore.subtitle")}'],
  ],

  // ── Pharmacy Billing ─────────────────────────
  'pharmacy-billing/page.tsx': [
    ['Pharmacy Billing', '{t("pharmacyBilling.title")}'],
    ['Financial transactions', '{t("pharmacyBilling.subtitle")}'],
  ],

  // ── Inventory Intelligence ───────────────────
  'inventory-intelligence/page.tsx': [
    ['Inventory Intelligence', '{t("inventoryIntelligence.title")}'],
    ['AI-driven demand forecasting', '{t("inventoryIntelligence.subtitle")}'],
  ],

  // ── Rx Worklist ──────────────────────────────
  'rx-worklist/page.tsx': [
    ['Rx Worklist', '{t("rxWorklist.title")}'],
    ['outpatient prescriptions', '{t("rxWorklist.subtitle")}'],
  ],

  // ── Sales Returns ────────────────────────────
  'sales-returns/page.tsx': [
    ['Sales Returns', '{t("salesReturns.title")}'],
    ['Process customer returns', '{t("salesReturns.subtitle")}'],
  ],

  // ── RCM Billing ──────────────────────────────
  'rcm-billing/page.tsx': [
    ['Revenue Cycle Management', '{t("rcmBilling.title")}'],
    ['End-to-end billing', '{t("rcmBilling.subtitle")}'],
  ],

  // ── Billing Masters ──────────────────────────
  'billing-masters/page.tsx': [
    ['Billing Masters', '{t("billingMasters.title")}'],
    ['Configure service groups', '{t("billingMasters.subtitle")}'],
  ],

  // ── Organizations ────────────────────────────
  'administration/organizations/page.tsx': [
    ['Multi-Tenant Organization', '{t("organizations.title")}'],
    ['SaaS tenant', '{t("organizations.subtitle")}'],
  ],

  // ── BI Intelligence ──────────────────────────
  'bi-intelligence/page.tsx': [
    ['Hospital Intelligence', '{t("biIntelligence.title")}'],
    ['Real-time operational', '{t("biIntelligence.subtitle")}'],
  ],

  // ── Analytics ────────────────────────────────
  'analytics/page.tsx': [
    ['Analytics Dashboard', '{t("analytics.title")}'],
  ],

  // ── AI Platform ──────────────────────────────
  'ai/page.tsx': [
    ['AI Platform', '{t("ai.title")}'],
  ],

  // ── Visitor MLC ──────────────────────────────
  'visitor-mlc/page.tsx': [
    ['Visitor & MLC', '{t("visitorMlc.title")}'],
    ['patient visitors', '{t("visitorMlc.subtitle")}'],
  ],

  // ── Ward Nursing ─────────────────────────────
  'wards/nursing/page.tsx': [
    ['Ward Nursing', '{t("wardNursing.title")}'],
    ['Central nursing station', '{t("wardNursing.subtitle")}'],
  ],
};

let totalReplacements = 0;
let filesProcessed = 0;

for (const [relPath, repls] of Object.entries(replacements)) {
  const fullPath = path.join(DASHBOARD, relPath);
  if (!fs.existsSync(fullPath)) {
    console.log(`⚠️  Skipped (not found): ${relPath}`);
    continue;
  }

  let content = fs.readFileSync(fullPath, 'utf-8');
  let count = 0;

  for (const [target, replacement] of repls) {
    if (content.includes(target)) {
      content = content.replace(target, replacement);
      count++;
    }
  }

  if (count > 0) {
    fs.writeFileSync(fullPath, content);
    totalReplacements += count;
    filesProcessed++;
    console.log(`✅ ${relPath}: ${count} replacements`);
  } else {
    console.log(`ℹ️  ${relPath}: no matching strings (may already be translated)`);
  }
}

console.log(`\n🎉 Batch replacement complete!`);
console.log(`📊 Files processed: ${filesProcessed}`);
console.log(`📊 Total string replacements: ${totalReplacements}`);
