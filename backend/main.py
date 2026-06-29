from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.requirement import router as requirements_router
from backend.api.ecu import router as ecus_router
from backend.api.signal import router as signals_router
from backend.api.calibration import router as calibrations_router
from backend.api.fault import router as faults_router
from backend.api.dtc import router as dtcs_router
from backend.api.vehicle_data import router as vehicle_data_router
from backend.api.telemetry import router as telemetry_router
from backend.api.insurance_claim import router as insurance_router
from backend.api.testcase import router as testcase_router
from backend.api.can import router as can_router
from backend.api.ws import router as ws_router
from backend.api.dashboard import router as dashboard_router
from backend.api.ai import router as ai_router
from backend.api.emergency import router as emergency_router
from backend.api.breakdown import router as breakdown_router
from backend.api.personality import router as personality_router
from backend.api.resale import router as resale_router
from backend.api.engineer_chat import router as engineer_chat_router
from knowledge_graph.graph_builder.kg_api import router as kg_router
from agents.requirement_agent.requirement_parser_api import router as req_parser_router
from agents.requirement_agent.traceability_api import router as traceability_router
from agents.requirement_agent.gap_conflict_api import router as gap_conflict_router
from agents.requirement_agent.failure_predictor_api import router as failure_predictor_router
from agents.requirement_agent.mistake_detector_api import router as mistake_detector_router
from agents.requirement_agent.testcase_safety_api import router as testcase_safety_router
from agents.requirement_agent.impact_kg_api import router as impact_kg_router



app = FastAPI(
    title="ACIP-X1 - Automotive Cognitive Intelligence Platform",
    description="World's First Automotive Cognitive Intelligence Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "ACIP-X1 API Running",
        "version": "1.0.0",
        "modes":   ["Engineering Mode", "Customer Mode"],
        "docs":    "/docs"
    }

app.include_router(requirements_router)
app.include_router(ecus_router)
app.include_router(signals_router)
app.include_router(calibrations_router)
app.include_router(faults_router)
app.include_router(dtcs_router)
app.include_router(vehicle_data_router)
app.include_router(telemetry_router)
app.include_router(insurance_router)
app.include_router(testcase_router)
app.include_router(can_router)
app.include_router(ws_router)
app.include_router(dashboard_router)
app.include_router(ai_router)
app.include_router(emergency_router)
app.include_router(breakdown_router)
app.include_router(personality_router)
app.include_router(resale_router)
app.include_router(engineer_chat_router)
app.include_router(kg_router)
app.include_router(req_parser_router)
app.include_router(traceability_router)
app.include_router(gap_conflict_router)
app.include_router(failure_predictor_router)
app.include_router(mistake_detector_router)
app.include_router(testcase_safety_router)
app.include_router(impact_kg_router)