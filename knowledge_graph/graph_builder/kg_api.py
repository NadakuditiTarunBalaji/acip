"""
ACIP-X1 Knowledge Graph API
Exposes all KG queries as REST endpoints
"""
from fastapi import APIRouter, HTTPException
from knowledge_graph.graph_builder.kg_engine import get_kg

router = APIRouter(
    prefix="/api/kg",
    tags=["Knowledge Graph"]
)


@router.get("/summary")
def get_kg_summary():
    """Get full KG summary — total nodes, edges, breakdown"""
    kg = get_kg()
    return kg.get_summary()


@router.get("/search")
def search_kg(keyword: str):
    """Keyword search across all node types — used by E9's natural
    language chat assistant for topic questions like 'show me all
    requirements about battery temperature'."""
    kg = get_kg()
    return kg.search_nodes(keyword)


@router.get("/fault/{fault_id}")
def analyze_fault(fault_id: str):
    """
    Get full fault analysis from KG:
    Fault → RootCause → Action → HealthImpact
    """
    kg = get_kg()
    result = kg.get_fault_analysis(fault_id.upper())
    if not result["fault_name"]:
        raise HTTPException(
            status_code=404,
            detail=f"Fault {fault_id} not found in Knowledge Graph"
        )
    return result


@router.get("/dtc/{dtc_id}")
def analyze_dtc(dtc_id: str):
    """
    Get full DTC analysis from KG:
    DTC → Fault → RootCause → Action
    """
    kg = get_kg()
    result = kg.get_dtc_analysis(dtc_id.upper())
    if not result["dtc_name"]:
        raise HTTPException(
            status_code=404,
            detail=f"DTC {dtc_id} not found in Knowledge Graph"
        )
    return result


@router.get("/signal/{signal_id}")
def analyze_signal(signal_id: str):
    """
    Get signal analysis from KG:
    Signal → DTC → Fault → Calibration limits
    """
    kg = get_kg()
    result = kg.get_signal_analysis(signal_id.upper())
    if not result["signal_name"]:
        raise HTTPException(
            status_code=404,
            detail=f"Signal {signal_id} not found in Knowledge Graph"
        )
    return result


@router.get("/requirement/{req_id}/trace")
def get_requirement_traceability(req_id: str):
    """
    Get full requirement traceability from KG:
    Requirement → Signal → TestCase
    """
    kg = get_kg()
    result = kg.get_requirement_trace(req_id.upper())
    if not result["requirement"]:
        raise HTTPException(
            status_code=404,
            detail=f"Requirement {req_id} not found in Knowledge Graph"
        )
    return result


@router.get("/vehicle/{vehicle_id}/chain")
def get_vehicle_chain(vehicle_id: str = "VEH001"):
    """
    Get full vehicle chain from KG:
    Vehicle → ECU → Signal
    """
    kg = get_kg()
    return kg.get_vehicle_chain(vehicle_id.upper())


@router.get("/requirements/gaps")
def get_requirement_gaps():
    """
    Find requirements with missing signal mapping or test cases
    These are potential human mistakes — Engineering Mode feature!
    """
    kg = get_kg()
    gaps = []

    for _, req in kg.requirement_nodes.iterrows():
        req_id = req["node_id"]
        trace = kg.get_requirement_trace(req_id)

        if not trace["traceability_complete"]:
            gaps.append({
                "req_id":           req_id,
                "requirement":      trace["requirement"],
                "has_signal":       len(trace["mapped_signals"]) > 0,
                "has_testcase":     len(trace["test_cases"]) > 0,
                "missing_signal":   len(trace["mapped_signals"]) == 0,
                "missing_testcase": len(trace["test_cases"]) == 0,
                "risk":             "High — test case will fail without signal mapping"
            })

    return {
        "total_requirements": len(kg.requirement_nodes),
        "total_gaps":         len(gaps),
        "gaps":               gaps
    }


@router.get("/faults/all")
def get_all_fault_analyses():
    """Get analysis for all faults in KG"""
    kg = get_kg()
    results = []
    for _, fault in kg.fault_nodes.iterrows():
        analysis = kg.get_fault_analysis(fault["node_id"])
        results.append(analysis)
    return {
        "total": len(results),
        "faults": results
    }