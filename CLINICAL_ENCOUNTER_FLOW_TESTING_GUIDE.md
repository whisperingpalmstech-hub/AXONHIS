# Clinical Encounter Flow Testing Guide

This guide walks through testing the complete AI-powered clinical consultation workflow.

## Prerequisites

- Backend running on `http://localhost:9500`
- Database migration completed
- Valid JWT token for authentication (obtain from `/api/v1/auth/login`)

## Test Setup

Set environment variables:
```bash
export API_URL="http://localhost:9500/api/v1"
export TOKEN="your_jwt_token_here"
```

## Complete Workflow Test

### Step 1: Start a Consultation

**Endpoint:** `POST /clinical-encounter-flow/start`

```bash
curl -X POST "$API_URL/clinical-encounter-flow/start" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "encounter_id": "uuid-of-encounter",
    "patient_id": "uuid-of-patient",
    "clinician_id": "uuid-of-clinician",
    "specialty_profile_id": "uuid-of-specialty"
  }'
```

**Expected Response:**
```json
{
  "flow_id": "uuid-of-flow",
  "current_phase": "COMPLAINT_CAPTURE",
  "question_count": 0,
  "started_at": "2026-04-09T..."
}
```

---

### Step 2: Submit Patient Complaint

**Endpoint:** `POST /clinical-encounter-flow/{flow_id}/complaint`

```bash
curl -X POST "$API_URL/clinical-encounter-flow/{flow_id}/complaint" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "complaint_transcript": "Patient has been experiencing chest pain for the past 3 days, especially when climbing stairs. Also feels short of breath.",
    "language": "en"
  }'
```

**Expected Response:**
```json
{
  "flow_id": "uuid-of-flow",
  "current_phase": "INTERACTIVE_QUESTIONING",
  "chief_complaint_transcript": "Patient has been experiencing...",
  "chief_complaint_analyzed": true
}
```

---

### Step 3: Get Next Question (Interactive Questioning)

**Endpoint:** `GET /clinical-encounter-flow/{flow_id}/next-question`

```bash
curl -X GET "$API_URL/clinical-encounter-flow/{flow_id}/next-question?encounter_id={encounter_id}" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "question": "Can you describe the chest pain more specifically? Is it sharp, dull, or pressure-like?",
  "turn_number": 1,
  "suggested_next_action": "CONTINUE_QUESTIONING",
  "should_move_to_examination": false
}
```

---

### Step 4: Submit Patient Answer

**Endpoint:** `POST /clinical-encounter-flow/{flow_id}/answer`

```bash
curl -X POST "$API_URL/clinical-encounter-flow/{flow_id}/answer?turn_id={turn_id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "answer_transcript": "It feels like pressure in the center of my chest, like someone squeezing. It lasts about 5-10 minutes.",
    "language": "en"
  }'
```

**Expected Response:**
```json
{
  "turn_id": "uuid-of-turn",
  "llm_question": "Can you describe the chest pain more specifically?",
  "response_transcript": "It feels like pressure in the center of my chest...",
  "response_analysis": {
    "key_findings": ["pressure-like chest pain", "duration 5-10 minutes"],
    "follow_up_needed": true
  },
  "is_complete": true
}
```

---

### Step 5: Continue Questioning (Repeat Steps 3-4)

Continue getting questions and submitting answers until AI suggests moving to examination.

After several turns, the response will be:
```json
{
  "question": "Based on your symptoms, I recommend we proceed to a physical examination. Are you ready?",
  "suggested_next_action": "MOVE_TO_EXAMINATION",
  "should_move_to_examination": true
}
```

---

### Step 6: Generate Examination Guidance

**Endpoint:** `POST /clinical-encounter-flow/{flow_id}/examination/guidance`

```bash
curl -X POST "$API_URL/clinical-encounter-flow/{flow_id}/examination/guidance?encounter_id={encounter_id}" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "guidance_id": "uuid-of-guidance",
  "critical_examinations": [
    {
      "body_system": "Cardiovascular",
      "specific_areas": ["heart sounds", "blood pressure", "peripheral pulses"],
      "priority": "HIGH",
      "reasoning": "Chest pain requires cardiovascular assessment"
    },
    {
      "body_system": "Respiratory",
      "specific_areas": ["lung auscultation", "respiratory rate"],
      "priority": "HIGH",
      "reasoning": "Shortness of breath requires respiratory assessment"
    }
  ],
  "red_flags": [
    "Radiating pain to arm/jaw",
    "Diaphoresis",
    "Systolic BP > 180 or < 90"
  ],
  "shown_to_doctor": true
}
```

---

### Step 7: Submit Examination Findings

**Endpoint:** `POST /clinical-encounter-flow/{flow_id}/examination/findings`

```bash
curl -X POST "$API_URL/clinical-encounter-flow/{flow_id}/examination/findings" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "examination_transcript": "Blood pressure 145/90, heart rate 88, regular rhythm. Heart sounds S1 S2 normal, no murmurs. Lung sounds clear bilaterally. No peripheral edema. Patient is alert and oriented.",
    "language": "en"
  }'
```

**Expected Response:**
```json
{
  "guidance_id": "uuid-of-guidance",
  "examination_findings_transcript": "Blood pressure 145/90, heart rate 88...",
  "examination_findings_analyzed": true,
  "structured_findings": {
    "body_systems": {
      "cardiovascular": {
        "blood_pressure": "145/90",
        "heart_rate": "88",
        "heart_sounds": "normal"
      },
      "respiratory": {
        "lung_sounds": "clear"
      }
    }
  }
}
```

---

### Step 8: Generate Management Plan

**Endpoint:** `POST /clinical-encounter-flow/{flow_id}/management-plan`

```bash
curl -X POST "$API_URL/clinical-encounter-flow/{flow_id}/management-plan?encounter_id={encounter_id}" \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "plan_id": "uuid-of-plan",
  "suggested_diagnoses": [
    {
      "diagnosis": "Unstable Angina",
      "confidence": 0.75,
      "reasoning": "Chest pain with exertion, cardiovascular risk factors"
    }
  ],
  "suggested_medications": [
    {
      "medication": "Aspirin",
      "dosage": "81mg",
      "frequency": "once daily",
      "duration": "ongoing",
      "instructions": "Take with food to reduce stomach upset"
    }
  ],
  "suggested_lab_orders": [
    {
      "test": "Troponin I",
      "urgency": "URGENT",
      "reasoning": "Rule out myocardial infarction"
    },
    {
      "test": "Complete Blood Count",
      "urgency": "ROUTINE",
      "reasoning": "Baseline hematology"
    }
  ],
  "suggested_imaging": [
    {
      "modality": "Electrocardiogram (ECG)",
      "indication": "Chest pain evaluation",
      "urgency": "URGENT"
    }
  ],
  "follow_up_recommendations": [
    "Cardiology follow-up within 1 week",
    "Monitor blood pressure at home"
  ],
  "is_accepted": false,
  "is_modified": false
}
```

---

### Step 9: Edit Management Plan

**Endpoint:** `PUT /management-plan/{plan_id}`

```bash
curl -X PUT "$API_URL/clinical-encounter-flow/management-plan/{plan_id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_plan": {
      "diagnoses": ["Unstable Angina"],
      "medications": ["Aspirin 81mg daily", "Metoprolol 25mg twice daily"],
      "lab_orders": ["Troponin I", "CBC", "Lipid Panel"]
    },
    "is_accepted": true,
    "is_modified": true,
    "modification_notes": "Added Metoprolol for BP control and Lipid Panel for cardiovascular risk assessment"
  }'
```

**Expected Response:**
```json
{
  "plan_id": "uuid-of-plan",
  "is_accepted": true,
  "is_modified": true,
  "modification_notes": "Added Metoprolol for BP control...",
  "current_plan": {
    "diagnoses": ["Unstable Angina"],
    "medications": ["Aspirin 81mg daily", "Metoprolol 25mg twice daily"]
  }
}
```

---

### Step 10: Generate Documents

**Endpoint:** `POST /clinical-encounter-flow/{flow_id}/documents/generate`

```bash
curl -X POST "$API_URL/clinical-encounter-flow/{flow_id}/documents/generate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "flow_id": "uuid-of-flow",
    "encounter_id": "uuid-of-encounter",
    "document_types": ["clinic_letter", "prescription", "lab_orders"]
  }'
```

**Expected Response:**
```json
{
  "flow_id": "uuid-of-flow",
  "current_phase": "COMPLETED",
  "selected_document_types": ["clinic_letter", "prescription", "lab_orders"],
  "documents_generated": [
    {
      "type": "clinic_letter",
      "status": "generated",
      "generated_at": "2026-04-09T..."
    },
    {
      "type": "prescription",
      "status": "generated",
      "generated_at": "2026-04-09T..."
    },
    {
      "type": "lab_orders",
      "status": "generated",
      "generated_at": "2026-04-09T..."
    }
  ],
  "completed_at": "2026-04-09T..."
}
```

---

## Doctor Prompt Override Testing

### Create Doctor Prompt Override

**Endpoint:** `POST /clinical-encounter-flow/doctor-prompts`

```bash
curl -X POST "$API_URL/clinical-encounter-flow/doctor-prompts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "clinician_id": "uuid-of-clinician",
    "specialty_profile_id": "uuid-of-specialty",
    "questioning_prompt": "You are a cardiologist. Ask focused questions about cardiac symptoms...",
    "question_style": "CONCISE",
    "management_style": "DETAILED"
  }'
```

### Get Doctor Prompt Override

**Endpoint:** `GET /clinical-encounter-flow/doctor-prompts/{clinician_id}`

```bash
curl -X GET "$API_URL/clinical-encounter-flow/doctor-prompts/{clinician_id}" \
  -H "Authorization: Bearer $TOKEN"
```

### Update Doctor Prompt Override

**Endpoint:** `PUT /clinical-encounter-flow/doctor-prompts/{override_id}`

```bash
curl -X PUT "$API_URL/clinical-encounter-flow/doctor-prompts/{override_id}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "questioning_prompt": "Updated prompt with more specific cardiac questions...",
    "question_style": "FRIENDLY"
  }'
```

---

## Helper Endpoints

### Get Flow State

```bash
curl -X GET "$API_URL/clinical-encounter-flow/flow/{flow_id}" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Question History

```bash
curl -X GET "$API_URL/clinical-encounter-flow/flow/{flow_id}/questions" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Examination Guidance

```bash
curl -X GET "$API_URL/clinical-encounter-flow/flow/{flow_id}/examination/guidance" \
  -H "Authorization: Bearer $TOKEN"
```

### Get Management Plan

```bash
curl -X GET "$API_URL/clinical-encounter-flow/flow/{flow_id}/management-plan" \
  -H "Authorization: Bearer $TOKEN"
```

---

## Testing Checklist

- [ ] Start consultation successfully
- [ ] Submit patient complaint
- [ ] Get first question from AI
- [ ] Submit patient answer
- [ ] Continue questioning for 3-5 turns
- [ ] AI suggests moving to examination
- [ ] Generate examination guidance
- [ ] Submit examination findings
- [ ] Generate management plan
- [ ] Edit management plan
- [ ] Accept management plan
- [ ] Generate documents
- [ ] Flow completes successfully
- [ ] Create doctor prompt override
- [ ] Verify doctor prompt override is used in questioning

---

## Common Issues

**Issue:** Backend returns 404
- **Solution:** Ensure flow_id is correct and flow exists

**Issue:** AI returns generic questions
- **Solution:** Create doctor prompt override for specialty-specific questioning

**Issue:** Management plan not generating
- **Solution:** Ensure examination findings are submitted and analyzed first

**Issue:** Documents not generating
- **Solution:** Ensure management plan is accepted before generating documents
