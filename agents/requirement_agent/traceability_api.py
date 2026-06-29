"""
ACIP-X1 — Auto Traceability Matrix API
Engineering Mode — Feature E2
"""
from fastapi import APIRouter, HTTPException
from agents.requirement_agent.traceability_engine import TraceabilityEngine

router = APIRouter(
    prefix="/api/engineering/traceability",
    tags=["Engineering Mode — Traceability Matrix"]
)

engine = TraceabilityEngine()


@router.get("/matrix")
def get_full_traceability_matrix():
    """
    Build complete traceability matrix for ALL requirements.
    REQ → Signal → ECU → Calibration → DTC → Fault → RootCause → Action → TestCase
    """
    return engine.build_full_matrix()


@router.get("/matrix/flat")
def get_flat_traceability_matrix():
    """Get traceability matrix as flat table — ready for display/export"""
    rows = engine.get_flat_matrix()
    return {
        "total": len(rows),
        "matrix": rows
    }


@router.get("/requirement/{req_id}")
def trace_single_requirement(req_id: str):
    """
    Trace one requirement through complete engineering chain:
    REQ → Signal → ECU → Calibration → DTC → Fault → RootCause → Action → TestCase
    """
    result = engine.trace_requirement(req_id.upper())
    if result["status"] == "Not Found":
        raise HTTPException(
            status_code=404,
            detail=f"Requirement {req_id} not found in Knowledge Graph"
        )
    return result


@router.get("/summary")
def get_traceability_summary():
    """Get high-level traceability summary — counts, scores, gaps"""
    full = engine.build_full_matrix()
    return {
        "total_requirements": full["total"],
        "average_score":      full["average_score"],
        "summary":            full["summary"],
        "status_counts":      full["status_counts"],
        "total_gaps":         full["total_gaps"],
    }


@router.get("/gaps")
def get_traceability_gaps():
    """
    Get all requirements with missing chain links.
    These are potential human mistakes that could cause test failures.
    """
    full = engine.build_full_matrix()
    return {
        "total_requirements": full["total"],
        "total_gaps":         full["total_gaps"],
        "coverage_pct":       full["summary"]["coverage_pct"],
        "gaps":               full["gaps"]
    }


@router.get("/export/csv")
def export_matrix_csv():
    """Export full traceability matrix as CSV-ready data"""
    rows = engine.get_flat_matrix()
    return {
        "message":   "Traceability matrix ready for export",
        "total_rows": len(rows),
        "columns":   list(rows[0].keys()) if rows else [],
        "data":      rows
    }