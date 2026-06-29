"""
ACIP-X1 — Gap & Conflict Detection API
Engineering Mode — Feature E5
"""
from fastapi import APIRouter
from agents.requirement_agent.gap_conflict_engine import GapConflictEngine

router = APIRouter(
    prefix="/api/engineering/analysis",
    tags=["Engineering Mode — Gap & Conflict Detection"]
)

engine = GapConflictEngine()


@router.get("/full-report")
def get_full_report():
    """
    Run complete gap & conflict analysis.
    Returns gaps, conflicts, orphans and overall status.
    """
    return engine.full_report()


@router.get("/gaps")
def get_gaps():
    """Find all requirements with missing chain links"""
    return engine.detect_gaps()


@router.get("/conflicts")
def get_conflicts():
    """Find requirements that contradict each other"""
    return engine.detect_conflicts()


@router.get("/orphans")
def get_orphans():
    """Find signals/DTCs/calibrations not linked to any requirement"""
    return engine.detect_orphans()


@router.get("/summary")
def get_analysis_summary():
    """Get high level summary of all issues found"""
    report = engine.full_report()
    return {
        "overall_status": report["overall_status"],
        "total_issues":   report["total_issues"],
        "summary":        report["summary"]
    }