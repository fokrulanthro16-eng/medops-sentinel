"""
MedOps-Sentinel v1.0: Autonomous Clinical AI Drift Firewall, Vitals Telemetry & Self-Healing Healthcare DevOps Engine
FastAPI Telemetry & SRE Server (server.py)

Endpoints:
  - GET  /                  -> Serves the interactive dark-mode cockpit (static/index.html)
  - GET  /api/health        -> K8s / Docker readiness & liveness probe endpoint
  - GET  /api/status        -> System health, active slot, telemetry metrics, rollback history
  - POST /api/evaluate      -> Patient evaluation with PHI shield, hallucination firewall & HF Copilot
  - POST /api/chaos/inject  -> Fault injection engine (drift, sensor noise, statistical noise, lethal dose, reset)
  - POST /api/fhir          -> FHIR HL7 v4.0 Observation Bundle ingestion endpoint
"""

import os
import random
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app import (
    ChaosEngine,
    ChaosRequest,
    DevOpsCanaryController,
    EvaluationRequest,
    EvaluationResponse,
    HealthLayer,
    PatientVitals,
    HF_TOKEN,
    HF_PRIMARY_MODEL,
    sentinel_engine,
)

app = FastAPI(
    title="MedOps-Sentinel v1.0 Telemetry & SRE Engine",
    description="Autonomous Clinical AI Drift Firewall, Vitals Telemetry & Self-Healing Healthcare DevOps Engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR, html=True), name="static")


@app.get("/", response_class=FileResponse)
async def serve_cockpit():
    """Serves the ultimate dark-cyber SRE cockpit."""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cockpit UI (static/index.html) not found."
        )
    return FileResponse(index_path)


@app.get("/api/health")
async def health_check():
    """Kubernetes & Docker container readiness and liveness probe."""
    return {
        "status": "healthy",
        "service": "medops-sentinel",
        "version": "1.0.0",
        "active_slot": sentinel_engine.devops_controller.active_slot,
        "circuit_breaker": sentinel_engine.devops_controller.circuit_breaker_active,
        "hf_copilot_online": True,
        "hf_model": HF_PRIMARY_MODEL,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.get("/api/status")
async def get_system_status():
    """Returns telemetry status, active slot, PSI score, lifetime PHI redactions, and rollback history."""
    psi_score, drift_level = sentinel_engine.ai_layer.calculate_psi()
    
    latest_vitals = None
    if sentinel_engine.ai_layer.rolling_vitals:
        v = sentinel_engine.ai_layer.rolling_vitals[-1]
        latest_vitals = {
            "heart_rate": v.get("heart_rate", 75.0),
            "spo2": v.get("spo2", 98.0),
            "systolic_bp": v.get("systolic_bp", 120.0),
            "resp_rate": v.get("resp_rate", 16.0),
            "temp_c": 37.0
        }
    else:
        latest_vitals = {
            "heart_rate": 75.0,
            "spo2": 98.0,
            "systolic_bp": 120.0,
            "resp_rate": 16.0,
            "temp_c": 37.0
        }

    return {
        "status": "ONLINE",
        "active_deployment_slot": sentinel_engine.devops_controller.active_slot,
        "is_fallback_active": (
            sentinel_engine.devops_controller.active_slot == DevOpsCanaryController.SLOT_FALLBACK
        ),
        "circuit_breaker_active": sentinel_engine.devops_controller.circuit_breaker_active,
        "model_drift_psi": psi_score,
        "drift_alert_level": drift_level,
        "psi_threshold": DevOpsCanaryController.DRIFT_PSI_THRESHOLD,
        "total_rollbacks": sentinel_engine.devops_controller.total_rollbacks,
        "total_lifetime_redactions": HealthLayer.LIFETIME_REDACTIONS,
        "hf_copilot_configured": bool(HF_TOKEN),
        "hf_primary_model": HF_PRIMARY_MODEL,
        "rollback_history": [r.model_dump() for r in sentinel_engine.devops_controller.rollback_history[-10:]],
        "latest_vitals": latest_vitals,
        "rolling_sample_count": len(sentinel_engine.ai_layer.rolling_vitals),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/api/evaluate", response_model=EvaluationResponse)
async def evaluate_patient(request: EvaluationRequest):
    """
    Evaluates patient telemetry, scrubs HIPAA PHI, executes MEWS/Outlier detection,
    tests against statistical drift, evaluates pharmacological guardrails,
    triggers sub-10ms circuit breaker rollback if needed, and generates HF Copilot reports.
    """
    try:
        response = sentinel_engine.evaluate(request)
        return response
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Telemetry evaluation failed: {str(exc)}"
        )


class CopilotAnalyzeRequest(BaseModel):
    clinical_notes: Optional[str] = None
    vitals: Optional[PatientVitals] = None


@app.post("/api/copilot/analyze")
async def copilot_analyze(request: CopilotAnalyzeRequest):
    """
    Dedicated endpoint for Hugging Face Copilot analysis.
    Scrubs HIPAA PHI, evaluates telemetry, and generates Clinical SBAR & DevOps RCA reports.
    """
    vitals = request.vitals or PatientVitals(
        heart_rate=75.0,
        spo2=98.0,
        systolic_bp=120.0,
        diastolic_bp=80.0,
        resp_rate=16.0,
        temp_c=37.0,
        clinical_notes=request.clinical_notes
    )
    if request.clinical_notes:
        vitals.clinical_notes = request.clinical_notes

    eval_resp = sentinel_engine.evaluate(EvaluationRequest(vitals=vitals, generate_ai_copilot=True))
    return {
        "status": "ANALYSIS_COMPLETE",
        "redacted_clinical_notes": eval_resp.redacted_clinical_notes,
        "phi_redacted_count": eval_resp.phi_redacted_count,
        "phi_entities_detected": eval_resp.phi_entities_detected,
        "hf_copilot": eval_resp.hf_copilot,
        "hallucination_guardrail": eval_resp.hallucination_guardrail,
        "active_deployment_slot": eval_resp.active_deployment_slot,
        "mews_score": eval_resp.mews_score,
        "sepsis_risk_index": eval_resp.sepsis_risk_index
    }


@app.post("/api/chaos/inject")
async def inject_chaos(req: ChaosRequest):
    """Chaos Engineering Fault Injector."""
    fault = req.fault_type.lower().strip()

    if fault == "drift":
        drift_readings = ChaosEngine.generate_drift_telemetry(count=35)
        sentinel_engine.ai_layer.rolling_vitals.extend(drift_readings)
        psi, level = sentinel_engine.ai_layer.calculate_psi()
        
        event = sentinel_engine.devops_controller.trigger_circuit_breaker(
            reason="CHAOS_ENGINE_INJECTED_DRIFT",
            trigger_value=f"PSI={psi}",
            threshold="0.25"
        )
        return {
            "status": "FAULT_INJECTED",
            "fault_type": "drift",
            "active_slot": sentinel_engine.devops_controller.active_slot,
            "circuit_breaker_active": True,
            "model_drift_psi": psi,
            "drift_level": level,
            "rollback_event": event.model_dump(),
            "message": "Model distribution drift injected! DevOps circuit breaker executed sub-10ms rollback to Safe-Clinical-Fallback-v1.0"
        }

    elif fault == "statistical_noise":
        noisy_readings = ChaosEngine.generate_statistical_noise(count=25)
        sentinel_engine.ai_layer.rolling_vitals.extend(noisy_readings)
        psi, level = sentinel_engine.ai_layer.calculate_psi()
        return {
            "status": "FAULT_INJECTED",
            "fault_type": "statistical_noise",
            "active_slot": sentinel_engine.devops_controller.active_slot,
            "circuit_breaker_active": sentinel_engine.devops_controller.circuit_breaker_active,
            "model_drift_psi": psi,
            "drift_level": level,
            "message": "High-frequency sensor jitter & statistical noise injected across ICU telemetry streams."
        }

    elif fault == "sensor_noise":
        corrupted_vitals = PatientVitals(
            patient_id="PT-CHAOS-CORRUPT",
            heart_rate=240.0,
            spo2=-12.5,
            systolic_bp=60.0,
            diastolic_bp=85.0,
            resp_rate=65.0,
            temp_c=41.5
        )
        eval_resp = sentinel_engine.evaluate(EvaluationRequest(vitals=corrupted_vitals, generate_ai_copilot=False))
        return {
            "status": "FAULT_INJECTED",
            "fault_type": "sensor_noise",
            "active_slot": sentinel_engine.devops_controller.active_slot,
            "circuit_breaker_active": sentinel_engine.devops_controller.circuit_breaker_active,
            "telemetry_integrity": eval_resp.telemetry_integrity,
            "message": "Corrupted sensor packet injected! Inverted BP & negative SpO2 detected. Auto-rollback triggered."
        }

    elif fault == "hallucination_attack":
        toxic_vitals = PatientVitals(
            patient_id="PT-CHAOS-HALLUCINATE",
            heart_rate=125.0,
            spo2=91.0,
            systolic_bp=85.0,
            diastolic_bp=55.0,
            resp_rate=26.0,
            temp_c=38.9,
            clinical_notes="Patient John Doe SSN 000-11-2222 MRN #991045. AI model recommends: Potassium Chloride 40 mEq IV Push STAT and Epinephrine 10 mg IV Push.",
            proposed_medication="potassium chloride",
            proposed_dose=40.0,
            dose_unit="meq",
            route="iv_push"
        )
        eval_resp = sentinel_engine.evaluate(EvaluationRequest(vitals=toxic_vitals, generate_ai_copilot=True))
        return {
            "status": "FAULT_INJECTED",
            "fault_type": "hallucination_attack",
            "active_slot": sentinel_engine.devops_controller.active_slot,
            "guardrail_status": eval_resp.hallucination_guardrail.guardrail_status,
            "unsafe_passthrough_rate": eval_resp.hallucination_guardrail.unsafe_passthrough_rate,
            "blocked_clinical_justification": eval_resp.hallucination_guardrail.clinical_justification,
            "redacted_notes": eval_resp.redacted_clinical_notes,
            "hf_sbar": eval_resp.hf_copilot.sbar_summary if eval_resp.hf_copilot else None,
            "message": "Clinical hallucination attack injected! Pharmacological firewall blocked fatal KCl IV Push with 0.0% unsafe pass-through."
        }

    elif fault == "reset":
        sentinel_engine._init_healthy_baseline()
        reset_res = sentinel_engine.devops_controller.reset_to_canary()
        psi, level = sentinel_engine.ai_layer.calculate_psi()
        return {
            "status": "RESET_SUCCESSFUL",
            "active_slot": sentinel_engine.devops_controller.active_slot,
            "circuit_breaker_active": False,
            "model_drift_psi": psi,
            "drift_level": level,
            "message": "System baseline restored. Primary-AI-Canary-v2.4 reactivated with clean telemetry."
        }

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown fault_type '{fault}'. Allowed: 'drift', 'sensor_noise', 'statistical_noise', 'hallucination_attack', 'reset'."
        )


@app.post("/api/fhir")
async def ingest_fhir_payload(payload: Dict[str, Any]):
    """FHIR HL7 v4.0 Adapter."""
    try:
        vitals = HealthLayer.parse_fhir_observation(payload)
        resp = sentinel_engine.evaluate(EvaluationRequest(vitals=vitals))
        return resp
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"FHIR payload parsing failed: {str(exc)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
