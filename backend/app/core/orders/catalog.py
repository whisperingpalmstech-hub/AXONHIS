"""Clinical catalog – searchable list of lab tests, medications, procedures."""

CATALOG: list[dict] = [
    # ── Lab Tests ────────────────────────────────────────────────────────────
    {"code": "CBC",   "name": "Complete Blood Count",        "type": "LAB_ORDER",        "synonyms": ["cbc", "full blood count", "fbc"]},
    {"code": "CRP",   "name": "C-Reactive Protein",         "type": "LAB_ORDER",        "synonyms": ["crp", "c reactive"]},
    {"code": "ESR",   "name": "Erythrocyte Sedimentation Rate", "type": "LAB_ORDER",    "synonyms": ["esr", "sed rate"]},
    {"code": "LFT",   "name": "Liver Function Tests",        "type": "LAB_ORDER",        "synonyms": ["lft", "liver panel", "hepatic panel"]},
    {"code": "KFT",   "name": "Kidney Function Tests",       "type": "LAB_ORDER",        "synonyms": ["kft", "renal panel", "bmp", "bun creatinine"]},
    {"code": "FBS",   "name": "Fasting Blood Sugar",         "type": "LAB_ORDER",        "synonyms": ["fbs", "glucose fasting", "blood sugar"]},
    {"code": "HBA1C", "name": "HbA1c (Glycated Hemoglobin)","type": "LAB_ORDER",        "synonyms": ["hba1c", "a1c", "glycated haemoglobin"]},
    {"code": "TSH",   "name": "Thyroid Stimulating Hormone", "type": "LAB_ORDER",        "synonyms": ["tsh", "thyroid panel"]},
    {"code": "PT_INR","name": "PT / INR (Coagulation)",     "type": "LAB_ORDER",        "synonyms": ["pt", "inr", "prothrombin", "coagulation"]},
    {"code": "TROP",  "name": "Troponin I/T",               "type": "LAB_ORDER",        "synonyms": ["troponin", "trop", "cardiac markers"]},
    {"code": "BNP",   "name": "B-Natriuretic Peptide",      "type": "LAB_ORDER",        "synonyms": ["bnp", "nt-probnp", "heart failure marker"]},
    {"code": "BLDCX", "name": "Blood Culture",              "type": "LAB_ORDER",        "synonyms": ["blood culture", "sepsis panel", "bacteremia"]},
    {"code": "URINE", "name": "Urine Routine & Microscopy", "type": "LAB_ORDER",        "synonyms": ["urine", "urinalysis", "ua"]},
    {"code": "COVID", "name": "COVID-19 Rapid Antigen",     "type": "LAB_ORDER",        "synonyms": ["covid", "covid-19", "corona"]},
    {"code": "LIPID", "name": "Lipid Profile",              "type": "LAB_ORDER",        "synonyms": ["lipid", "cholesterol", "triglycerides"]},
    {"code": "FERR",  "name": "Serum Ferritin",             "type": "LAB_ORDER",        "synonyms": ["ferritin", "iron stores"]},
    {"code": "VIT_D", "name": "Vitamin D (25-OH)",          "type": "LAB_ORDER",        "synonyms": ["vitamin d", "vit d", "25-oh"]},
    {"code": "VIT_B12","name": "Vitamin B12",               "type": "LAB_ORDER",        "synonyms": ["b12", "cobalamin", "vitamin b12"]},
    {"code": "MALARIA","name": "Malaria Parasite (MP Smear)","type": "LAB_ORDER",       "synonyms": ["malaria", "mp smear", "parasite"]},
    {"code": "HIV",   "name": "HIV 1 & 2 Combo ELISA",     "type": "LAB_ORDER",        "synonyms": ["hiv", "aids", "retrovirus"]},
    # ── Imaging ──────────────────────────────────────────────────────────────
    {"code": "CXR",   "name": "Chest X-Ray (PA View)",      "type": "RADIOLOGY_ORDER",  "synonyms": ["chest xray", "cxr", "chest xr"]},
    {"code": "XRAY_AP","name": "X-Ray AP View",             "type": "RADIOLOGY_ORDER",  "synonyms": ["xray ap", "ap view"]},
    {"code": "CT_HEAD","name": "CT Scan – Head/Brain",      "type": "RADIOLOGY_ORDER",  "synonyms": ["ct head", "brain ct", "head scan"]},
    {"code": "CT_CHEST","name": "CT Scan – Chest",          "type": "RADIOLOGY_ORDER",  "synonyms": ["ct chest", "chest ct"]},
    {"code": "CT_ABD","name": "CT Scan – Abdomen & Pelvis", "type": "RADIOLOGY_ORDER",  "synonyms": ["ct abdomen", "ct ap", "abdominal ct"]},
    {"code": "MRI_BRAIN","name": "MRI Brain",               "type": "RADIOLOGY_ORDER",  "synonyms": ["mri brain", "brain mri"]},
    {"code": "MRI_SPINE","name": "MRI Spine",               "type": "RADIOLOGY_ORDER",  "synonyms": ["mri spine", "spinal mri"]},
    {"code": "USG_ABD","name": "Ultrasound – Abdomen",      "type": "RADIOLOGY_ORDER",  "synonyms": ["usg abdomen", "abdominal ultrasound", "sono abdomen"]},
    {"code": "USG_PELV","name": "Ultrasound – Pelvis",      "type": "RADIOLOGY_ORDER",  "synonyms": ["usg pelvis", "pelvic ultrasound"]},
    {"code": "ECHO",  "name": "Echocardiogram",             "type": "RADIOLOGY_ORDER",  "synonyms": ["echo", "echocardiogram", "cardiac echo"]},
    {"code": "ECG",   "name": "ECG / EKG (12-Lead)",        "type": "RADIOLOGY_ORDER",  "synonyms": ["ecg", "ekg", "electrocardiogram"]},
    # ── Medications ──────────────────────────────────────────────────────────
    {"code": "AMOX",  "name": "Amoxicillin 500mg",          "type": "MEDICATION_ORDER", "synonyms": ["amoxicillin", "amox", "amoxil"]},
    {"code": "AUGM",  "name": "Augmentin (Amox+Clav) 625mg","type": "MEDICATION_ORDER", "synonyms": ["augmentin", "co-amoxiclav", "amox-clav"]},
    {"code": "AZITH", "name": "Azithromycin 500mg",         "type": "MEDICATION_ORDER", "synonyms": ["azithromycin", "azithro", "zithromax"]},
    {"code": "CEFTRI","name": "Ceftriaxone 1g IV",          "type": "MEDICATION_ORDER", "synonyms": ["ceftriaxone", "rocephin"]},
    {"code": "METRO", "name": "Metronidazole 500mg",        "type": "MEDICATION_ORDER", "synonyms": ["metronidazole", "flagyl", "metro"]},
    {"code": "CIPRO", "name": "Ciprofloxacin 500mg",        "type": "MEDICATION_ORDER", "synonyms": ["ciprofloxacin", "cipro", "quinolone"]},
    {"code": "PANTO", "name": "Pantoprazole 40mg",          "type": "MEDICATION_ORDER", "synonyms": ["pantoprazole", "pan", "proton pump"]},
    {"code": "ATORV", "name": "Atorvastatin 10mg",          "type": "MEDICATION_ORDER", "synonyms": ["atorvastatin", "atorva", "statin", "lipitor"]},
    {"code": "METF",  "name": "Metformin 500mg",            "type": "MEDICATION_ORDER", "synonyms": ["metformin", "glucophage"]},
    {"code": "AMLO",  "name": "Amlodipine 5mg",             "type": "MEDICATION_ORDER", "synonyms": ["amlodipine", "calcium channel", "norvasc"]},
    {"code": "ASPIRIN","name": "Aspirin 75mg",              "type": "MEDICATION_ORDER", "synonyms": ["aspirin", "asa", "acetylsalicylic"]},
    {"code": "ONDANS","name": "Ondansetron 4mg",            "type": "MEDICATION_ORDER", "synonyms": ["ondansetron", "anti-emetic", "zofran"]},
    {"code": "DICLOF","name": "Diclofenac 50mg",            "type": "MEDICATION_ORDER", "synonyms": ["diclofenac", "nsaid", "voveran"]},
    {"code": "PARACE","name": "Paracetamol 500mg",          "type": "MEDICATION_ORDER", "synonyms": ["paracetamol", "acetaminophen", "tylenol", "pcm"]},
    {"code": "MORPHIN","name": "Morphine 5mg IV",           "type": "MEDICATION_ORDER", "synonyms": ["morphine", "opioid analgesia"]},
    # ── Procedures ───────────────────────────────────────────────────────────
    {"code": "IV_ACC","name": "IV Access / Cannulation",    "type": "PROCEDURE_ORDER",  "synonyms": ["iv access", "cannula", "iv line"]},
    {"code": "CATH",  "name": "Urinary Catheterization",    "type": "PROCEDURE_ORDER",  "synonyms": ["catheter", "foley", "urine catheter"]},
    {"code": "INCIS", "name": "Incision & Drainage",        "type": "PROCEDURE_ORDER",  "synonyms": ["i&d", "incision drainage", "abscess drainage"]},
    {"code": "LP",    "name": "Lumbar Puncture",            "type": "PROCEDURE_ORDER",  "synonyms": ["lumbar puncture", "lp", "spinal tap", "csf"]},
    {"code": "THORA", "name": "Thoracentesis",              "type": "PROCEDURE_ORDER",  "synonyms": ["thoracentesis", "pleural tap", "pleural fluid"]},
    {"code": "NGT",   "name": "Nasogastric Tube Insertion", "type": "PROCEDURE_ORDER",  "synonyms": ["ngt", "nasogastric", "ng tube"]},
    {"code": "WOUND", "name": "Wound Dressing",             "type": "PROCEDURE_ORDER",  "synonyms": ["wound dressing", "dressing change"]},
    {"code": "SUTURE","name": "Suturing / Wound Closure",   "type": "PROCEDURE_ORDER",  "synonyms": ["suture", "stitches", "wound closure"]},
]


def search_catalog(query: str, order_type: str | None = None, limit: int = 15) -> list[dict]:
    """Fuzzy search over the clinical catalog."""
    q = query.lower().strip()
    results = []
    for item in CATALOG:
        if order_type and item["type"] != order_type:
            continue
        if (
            q in item["name"].lower()
            or q in item["code"].lower()
            or any(q in syn for syn in item["synonyms"])
        ):
            results.append({
                "code": item["code"],
                "name": item["name"],
                "type": item["type"],
            })
    return results[:limit]
