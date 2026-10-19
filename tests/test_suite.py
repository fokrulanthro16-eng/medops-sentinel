"""
MedOps-Sentinel v1.0: Autonomous Clinical AI Drift Firewall & SRE Engine
16-Scenario Comprehensive Verification Suite (tests/test_suite.py)

Covers:
  1. Normal ICU Telemetry & sub-10ms Latency SLA
  2. Critical Sepsis Early-Warning Scoring (MEWS >= 8, MAP < 65)
  3. 100% Deterministic HIPAA PII/PHI Redaction (SSN)
  4. 100% Deterministic HIPAA PII/PHI Redaction (MRN)
  5. 100% Deterministic HIPAA PII/PHI Redaction (Patient & Doctor Names)
  6. 100% Deterministic HIPAA PII/PHI Redaction (Phone & DOB)
  7. Pharmacological Hallucination Firewall: Lethal Epinephrine Overdose
  8. Pharmacological Hallucination Firewall: Prohibited KCl IV Push Route
  9. Pharmacological Hallucination Firewall: Safe Standard Dosage
  10. Statistical Model Drift: Baseline Stability (PSI < 0.10)
  11. Statistical Model Drift Detection (PSI > 0.25) & Auto-Rollback to Safe Fallback
  12. Hardware Sensor Integrity Packet Corruption Circuit-Breaker
  13. Chaos Fault Injection & Self-Healing Lifecycle via REST API
  14. FastAPI Health Probe & Telemetry Status SRE Endpoints
  15. FHIR HL7 v4.0 LOINC Observation Telemetry Ingestion
  16. Hugging Face AI Copilot SBAR & DevOps Drift RCA Report Generation
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ensure parent directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import (
    ChaosEngine,
    DevOpsCanaryController,
    EvaluationRequest,
    HealthLayer,
    HFCopilotEngine,
    MedOpsSentinel,
    PatientVitals,
    HF_TOKEN,
    HF_PRIMARY_MODEL,
    sentinel_engine,
)
from server import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_sentinel_state():
    """Restores baseline telemetry and Canary slot before each test run."""
    sentinel_engine._init_healthy_baseline()
    sentinel_engine.devops_controller.reset_to_canary()
    yield


# ==============================================================================
# SCENARIO 1: Normal ICU Vitals Evaluation & Sub-10ms SLA
# ==============================================================================
def test_01_normal_icu_vitals_evaluation_and_latency():
    vitals = PatientVitals(
        patient_id="PT-NORM-001",
        heart_rate=72.0,
        spo2=98.5,
        systolic_bp=118.0,
        diastolic_bp=78.0,
        resp_rate=15.0,
        temp_c=37.0,
        clinical_notes="Patient resting comfortably in ICU room 4A. Telemetry stable."
    )
    req = EvaluationRequest(vitals=vitals, generate_ai_copilot=False)
    resp = sentinel_engine.evaluate(req)

    assert resp.mews_score == 0, f"Expected MEWS 0, got {resp.mews_score}"
    assert resp.clinical_risk_tier == "LOW_RISK"
    assert resp.active_deployment_slot == DevOpsCanaryController.SLOT_CANARY
    assert resp.circuit_breaker_active is False
    assert resp.telemetry_integrity == "VALID"
    assert resp.latency_ms < 10.0, f"Latency SLA violated: {resp.latency_ms} ms >= 10.0 ms"


# ==============================================================================
# SCENARIO 2: Critical Sepsis Early-Warning Scoring (MEWS)
# ==============================================================================
def test_02_critical_sepsis_mews_alert():
    vitals = PatientVitals(
        patient_id="PT-SEPSIS-CRIT",
        heart_rate=135.0,     # MEWS +3
        spo2=87.0,            # MEWS +2
        systolic_bp=75.0,     # MEWS +2
        diastolic_bp=45.0,    # MAP = 55 mmHg (<65 indicates septic shock)
        resp_rate=32.0,       # MEWS +3
        temp_c=39.6,          # MEWS +2
        clinical_notes="Patient exhibiting hyperdynamic septic shock with acute metabolic acidosis."
    )
    req = EvaluationRequest(vitals=vitals, generate_ai_copilot=False)
    resp = sentinel_engine.evaluate(req)

    assert resp.mews_score >= 8, f"Expected MEWS >= 8 for severe sepsis, got {resp.mews_score}"
    assert resp.map_bp < 65.0, f"Expected MAP < 65 mmHg, got {resp.map_bp}"
    assert resp.clinical_risk_tier == "CRITICAL_SEPSIS_ALERT"
    assert resp.sepsis_risk_index >= 0.60


# ==============================================================================
# SCENARIO 3: HIPAA PII/PHI Redaction - Social Security Numbers (SSN)
# ==============================================================================
def test_03_hipaa_phi_redaction_ssn():
    raw_notes = "Patient SSN is 000-12-3456 and secondary guarantor SSN 987-65-4321 admitted to ICU."
    redacted, count, types = HealthLayer.redact_phi(raw_notes)

    assert "000-12-3456" not in redacted
    assert "987-65-4321" not in redacted
    assert "[REDACTED_SSN]" in redacted
    assert count >= 2
    assert "SSN" in types


# ==============================================================================
# SCENARIO 4: HIPAA PII/PHI Redaction - Medical Record Numbers (MRN)
# ==============================================================================
def test_04_hipaa_phi_redaction_mrn():
    raw_notes = "Clinical assessment for MRN #8492014 and Pt ID: 902194 in critical care."
    redacted, count, types = HealthLayer.redact_phi(raw_notes)

    assert "8492014" not in redacted
    assert "902194" not in redacted
    assert "[REDACTED_MRN]" in redacted
    assert count >= 2
    assert "MRN" in types


# ==============================================================================
# SCENARIO 5: HIPAA PII/PHI Redaction - Patient & Attending Names
# ==============================================================================
def test_05_hipaa_phi_redaction_patient_and_doctor_names():
    raw_notes = "Patient John Doe examined by Attending Dr. Sarah Connor with Jane Doe present."
    redacted, count, types = HealthLayer.redact_phi(raw_notes)

    assert "John Doe" not in redacted
    assert "Sarah Connor" not in redacted
    assert "Jane Doe" not in redacted
    assert "[REDACTED_NAME]" in redacted
    assert count >= 2


# ==============================================================================
# SCENARIO 6: HIPAA PII/PHI Redaction - Phone Numbers & Dates of Birth
# ==============================================================================
def test_06_hipaa_phi_redaction_phone_and_dob():
    raw_notes = "Contact next-of-kin at (415) 555-0199 or 212-555-0143. Patient DOB: 1984-05-12."
    redacted, count, types = HealthLayer.redact_phi(raw_notes)

    assert "415) 555-0199" not in redacted
    assert "212-555-0143" not in redacted
    assert "1984-05-12" not in redacted
    assert "[REDACTED_PHONE]" in redacted
    assert "[REDACTED_DOB]" in redacted
    assert count >= 3


# ==============================================================================
# SCENARIO 7: Pharmacological Hallucination Firewall - Lethal Epinephrine Overdose
# ==============================================================================
def test_07_hallucination_guardrail_lethal_epinephrine_bolus():
    vitals = PatientVitals(
        patient_id="PT-TOX-001",
        heart_rate=140.0,
        spo2=92.0,
        systolic_bp=160.0,
        diastolic_bp=95.0,
        resp_rate=24.0,
        temp_c=37.5,
        clinical_notes="AI recommendation: Epinephrine 5.0 mg IV push immediately for bronchodilation.",
        proposed_medication="epinephrine",
        proposed_dose=5.0,
        dose_unit="mg",
        route="iv_push"
    )
    req = EvaluationRequest(vitals=vitals, generate_ai_copilot=False)
    resp = sentinel_engine.evaluate(req)

    g = resp.hallucination_guardrail
    assert g.hallucination_detected is True
    assert g.guardrail_status == "BLOCKED_LETHAL_DOSAGE"
    assert g.action_taken == "BLOCKED_AND_CLAMPED_TO_PROTOCOL"
    assert g.unsafe_passthrough_rate == "0.0%"
    assert g.safe_clamped_dose == 1.0


# ==============================================================================
# SCENARIO 8: Pharmacological Hallucination Firewall - Prohibited KCl IV Push Route
# ==============================================================================
def test_08_hallucination_guardrail_prohibited_kcl_iv_push():
    vitals = PatientVitals(
        patient_id="PT-TOX-002",
        heart_rate=80.0,
        spo2=98.0,
        systolic_bp=120.0,
        diastolic_bp=80.0,
        resp_rate=16.0,
        temp_c=37.0,
        clinical_notes="Patient hypokalemic. Prescribing Potassium Chloride 20 mEq IV push STAT.",
        proposed_medication="potassium chloride",
        proposed_dose=20.0,
        dose_unit="meq",
        route="iv_push"
    )
    req = EvaluationRequest(vitals=vitals, generate_ai_copilot=False)
    resp = sentinel_engine.evaluate(req)

    g = resp.hallucination_guardrail
    assert g.hallucination_detected is True
    assert g.guardrail_status == "BLOCKED_LETHAL_ROUTE"
    assert g.action_taken == "PROHIBITED"
    assert g.unsafe_passthrough_rate == "0.0%"
    assert "CARDIAC ARREST" in g.clinical_justification.upper()


# ==============================================================================
# SCENARIO 9: Pharmacological Hallucination Firewall - Safe Dosage Allowed
# ==============================================================================
def test_09_hallucination_guardrail_safe_dosage_allowed():
    vitals = PatientVitals(
        patient_id="PT-SAFE-001",
        heart_rate=76.0,
        spo2=98.0,
        systolic_bp=122.0,
        diastolic_bp=78.0,
        resp_rate=16.0,
        temp_c=37.0,
        clinical_notes="Post-op analgesia required.",
        proposed_medication="morphine",
        proposed_dose=4.0,
        dose_unit="mg",
        route="iv"
    )
    req = EvaluationRequest(vitals=vitals, generate_ai_copilot=False)
    resp = sentinel_engine.evaluate(req)

    g = resp.hallucination_guardrail
    assert g.hallucination_detected is False
    assert g.guardrail_status == "PASSED_SAFE"
    assert g.action_taken == "ALLOW"
    assert g.unsafe_passthrough_rate == "0.0%"


# ==============================================================================
# SCENARIO 10: Statistical Model Drift - Baseline Stability (PSI < 0.10)
# ==============================================================================
def test_10_baseline_psi_stability_no_drift():
    psi_score, alert_level = sentinel_engine.ai_layer.calculate_psi()
    assert psi_score < 0.10, f"Expected baseline PSI < 0.10, got {psi_score}"
    assert alert_level == "STABLE"
    assert sentinel_engine.devops_controller.active_slot == DevOpsCanaryController.SLOT_CANARY


# ==============================================================================
# SCENARIO 11: Statistical Model Drift Detection & Auto-Rollback to Safe Fallback
# ==============================================================================
def test_11_model_drift_detection_and_auto_rollback():
    drift_batch = ChaosEngine.generate_drift_telemetry(count=35)
    sentinel_engine.ai_layer.rolling_vitals.extend(drift_batch)

    vitals = PatientVitals(
        patient_id="PT-DRIFT-TEST",
        heart_rate=145.0,
        spo2=82.0,
        systolic_bp=185.0,
        diastolic_bp=100.0,
        resp_rate=34.0,
        temp_c=38.0
    )
    resp = sentinel_engine.evaluate(EvaluationRequest(vitals=vitals, generate_ai_copilot=False))

    assert resp.model_drift_psi > DevOpsCanaryController.DRIFT_PSI_THRESHOLD
    assert resp.active_deployment_slot == DevOpsCanaryController.SLOT_FALLBACK
    assert resp.circuit_breaker_active is True
    assert len(sentinel_engine.devops_controller.rollback_history) > 0


# ==============================================================================
# SCENARIO 12: Hardware Sensor Integrity Packet Corruption Circuit-Breaker
# ==============================================================================
def test_12_sensor_integrity_packet_corruption_circuit_breaker():
    corrupted_vitals = PatientVitals(
        patient_id="PT-CORRUPT-001",
        heart_rate=80.0,
        spo2=-25.0,
        systolic_bp=70.0,
        diastolic_bp=95.0,
        resp_rate=16.0,
        temp_c=37.0
    )
    resp = sentinel_engine.evaluate(EvaluationRequest(vitals=corrupted_vitals, generate_ai_copilot=False))

    assert resp.telemetry_integrity == "CORRUPTED"
    assert resp.circuit_breaker_active is True
    assert resp.active_deployment_slot == DevOpsCanaryController.SLOT_FALLBACK


# ==============================================================================
# SCENARIO 13: Chaos Fault Injection & Self-Healing Lifecycle via REST API
# ==============================================================================
def test_13_chaos_fault_injection_and_self_healing_lifecycle():
    drift_res = client.post("/api/chaos/inject", json={"fault_type": "drift", "intensity": 1.0})
    assert drift_res.status_code == 200
    drift_data = drift_res.json()
    assert drift_data["status"] == "FAULT_INJECTED"
    assert drift_data["circuit_breaker_active"] is True
    assert drift_data["active_slot"] == DevOpsCanaryController.SLOT_FALLBACK

    reset_res = client.post("/api/chaos/inject", json={"fault_type": "reset"})
    assert reset_res.status_code == 200
    reset_data = reset_res.json()
    assert reset_data["status"] == "RESET_SUCCESSFUL"
    assert reset_data["active_slot"] == DevOpsCanaryController.SLOT_CANARY
    assert reset_data["circuit_breaker_active"] is False


# ==============================================================================
# SCENARIO 14: FastAPI Health & Telemetry Status SRE Endpoints
# ==============================================================================
def test_14_fastapi_endpoints_health_and_status():
    health_res = client.get("/api/health")
    assert health_res.status_code == 200
    health_data = health_res.json()
    assert health_data["status"] == "healthy"
    assert health_data["service"] == "medops-sentinel"
    assert health_data["hf_copilot_online"] is True

    status_res = client.get("/api/status")
    assert status_res.status_code == 200
    status_data = status_res.json()
    assert "active_deployment_slot" in status_data
    assert "model_drift_psi" in status_data
    assert "latest_vitals" in status_data
    assert "rollback_history" in status_data
    assert status_data["hf_copilot_configured"] is True


# ==============================================================================
# SCENARIO 15: FHIR HL7 v4.0 LOINC Observation Telemetry Ingestion
# ==============================================================================
def test_15_fhir_hl7_observation_bundle_telemetry_ingestion():
    fhir_bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Observation",
                    "subject": {"reference": "Patient/PT-FHIR-8821"},
                    "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
                    "valueQuantity": {"value": 82.0, "unit": "beats/minute"}
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"system": "http://loinc.org", "code": "2708-6"}]},
                    "valueQuantity": {"value": 97.0, "unit": "%"}
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"system": "http://loinc.org", "code": "8480-6"}]},
                    "valueQuantity": {"value": 125.0, "unit": "mmHg"}
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"system": "http://loinc.org", "code": "8462-4"}]},
                    "valueQuantity": {"value": 82.0, "unit": "mmHg"}
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"system": "http://loinc.org", "code": "9279-1"}]},
                    "valueQuantity": {"value": 17.0, "unit": "breaths/minute"}
                }
            },
            {
                "resource": {
                    "resourceType": "Observation",
                    "code": {"coding": [{"system": "http://loinc.org", "code": "8310-5"}]},
                    "valueQuantity": {"value": 37.1, "unit": "C"}
                }
            }
        ]
    }

    fhir_res = client.post("/api/fhir", json=fhir_bundle)
    assert fhir_res.status_code == 200
    data = fhir_res.json()
    assert data["patient_id"] == "PT-FHIR-8821"
    assert data["vitals"]["heart_rate"] == 82.0
    assert data["vitals"]["spo2"] == 97.0
    assert data["vitals"]["systolic_bp"] == 125.0
    assert data["vitals"]["diastolic_bp"] == 82.0
    assert data["vitals"]["resp_rate"] == 17.0
    assert data["vitals"]["temp_c"] == 37.1
    assert data["telemetry_integrity"] == "VALID"


# ==============================================================================
# SCENARIO 16: Hugging Face AI Copilot SBAR & DevOps Drift RCA Generation
# ==============================================================================
def test_16_hf_ai_copilot_sbar_and_devops_rca_generation():
    assert HF_TOKEN is not None and len(HF_TOKEN) > 20 and HF_TOKEN.startswith("hf_")
    assert "Qwen" in HF_PRIMARY_MODEL

    vitals = PatientVitals(
        patient_id="PT-HF-TEST-001",
        heart_rate=132.0,
        spo2=89.0,
        systolic_bp=82.0,
        diastolic_bp=52.0,
        resp_rate=28.0,
        temp_c=39.1,
        clinical_notes="Patient John Doe, SSN 000-44-5555 diagnosed with severe septicemia.",
        proposed_medication="epinephrine",
        proposed_dose=0.5,
        dose_unit="mg",
        route="iv_push"
    )

    req = EvaluationRequest(vitals=vitals, generate_ai_copilot=True)
    resp = sentinel_engine.evaluate(req)

    # Verify PHI Scrubbing happened before AI Copilot received note
    assert "000-44-5555" not in (resp.redacted_clinical_notes or "")
    assert "[REDACTED_SSN]" in (resp.redacted_clinical_notes or "")

    # Verify HF Copilot Generated Report
    assert resp.hf_copilot is not None
    hf = resp.hf_copilot
    assert hf.token_verified is True
    assert hf.generation_mode == "HUGGING_FACE_QWEN_72B_LIVE"

    # 1. Check Clinical SBAR Summary contains required clinical sections
    assert "SITUATION" in hf.sbar_summary.upper()
    assert "BACKGROUND" in hf.sbar_summary.upper()
    assert "ASSESSMENT" in hf.sbar_summary.upper()
    assert "RECOMMENDATION" in hf.sbar_summary.upper()

    # 2. Check DevOps Drift Root-Cause Analysis (RCA) contains required SRE sections
    assert "INCIDENT CLASSIFICATION" in hf.devops_rca.upper()
    assert "ROOT-CAUSE ATTRIBUTION" in hf.devops_rca.upper()
    assert "CIRCUIT BREAKER STATE" in hf.devops_rca.upper()
    assert "SRE REMEDIATION" in hf.devops_rca.upper()

    # 3. Check ML Outlier Detection Analysis
    assert resp.outlier_analysis is not None
    assert resp.outlier_analysis.anomaly_score >= 0.0

    # 4. Verify /api/copilot/analyze REST endpoint
    api_res = client.post("/api/copilot/analyze", json={
        "clinical_notes": "Patient Jane Doe, MRN #991042 in shock.",
        "vitals": {
            "heart_rate": 110.0,
            "spo2": 94.0,
            "systolic_bp": 95.0,
            "diastolic_bp": 60.0,
            "resp_rate": 22.0,
            "temp_c": 38.2
        }
    })
    assert api_res.status_code == 200
    api_data = api_res.json()
    assert api_data["status"] == "ANALYSIS_COMPLETE"
    assert "991042" not in api_data["redacted_clinical_notes"]
    assert "[REDACTED_MRN]" in api_data["redacted_clinical_notes"]
    assert "hf_copilot" in api_data
    assert api_data["hf_copilot"] is not None
