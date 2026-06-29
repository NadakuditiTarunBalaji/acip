"""
ACIP-X1 — Impact Analysis + KG Visualization API
Engineering Mode — Features E7 + E6
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from agents.requirement_agent.impact_analyzer import ImpactAnalyzer
from agents.requirement_agent.kg_visualizer import KGVisualizer

router = APIRouter(
    prefix="/api/engineering",
    tags=["Engineering Mode — Impact Analysis & KG Visualization"]
)

analyzer   = ImpactAnalyzer()
visualizer = KGVisualizer()


class CalibrationChangeRequest(BaseModel):
    cal_id: str
    new_value: Optional[float] = None


# ══════════════════════════════════════════════
# E7 — Impact Analysis
# ══════════════════════════════════════════════

@router.post("/impact/calibration")
def analyze_calibration_change(request: CalibrationChangeRequest):
    """
    Analyze impact of changing a calibration value.
    Shows all affected signals, requirements, DTCs, faults, test cases, ECUs.
    """
    result = analyzer.analyze_calibration_impact(
        request.cal_id.upper(),
        request.new_value
    )
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/impact/signal/{sig_id}")
def analyze_signal_change(sig_id: str):
    """Analyze impact of changing a signal — shows everything connected"""
    result = analyzer.analyze_signal_impact(sig_id.upper())
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/impact/requirement/{req_id}")
def analyze_requirement_change(req_id: str):
    """Analyze impact of changing a requirement — full downstream chain"""
    result = analyzer.analyze_requirement_impact(req_id.upper())
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/impact/calibrations")
def list_calibrations_for_impact():
    """Get all calibrations with current values — for impact analysis dropdown"""
    return analyzer.get_all_calibrations_summary()


# ══════════════════════════════════════════════
# E6 — Knowledge Graph Visualization
# ══════════════════════════════════════════════

@router.get("/kg-viz/full")
def get_full_kg_graph():
    """
    Get complete knowledge graph as nodes + edges.
    Ready for vis.js / D3 / Plotly visualization.
    """
    return visualizer.get_full_graph()


@router.get("/kg-viz/requirement/{req_id}")
def get_requirement_subgraph(req_id: str):
    """
    Get visual subgraph for one requirement's full chain:
    REQ → Signal → ECU/Calibration/DTC → Fault → RootCause → Action
                                       → TestCase
    """
    return visualizer.get_subgraph_for_requirement(req_id.upper())


@router.get("/kg-viz/domain/{domain}")
def get_domain_subgraph(domain: str):
    """Get subgraph filtered by domain — Battery or Powertrain"""
    return visualizer.get_domain_graph(domain.capitalize())


@router.get("/kg-viz/stats")
def get_kg_stats():
    """Get node/edge counts and color legend for visualization"""
    return visualizer.get_stats()