"""
ACIP-X1 — Auto Test Case Generator + ISO 26262 Safety Check API
Engineering Mode — Features E10 + E8
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agents.requirement_agent.testcase_generator import TestCaseGenerator
from agents.requirement_agent.safety_check import SafetyChecker

router = APIRouter(
    prefix="/api/engineering",
    tags=["Engineering Mode — Test Generator & ISO 26262"]
)

tc_generator   = TestCaseGenerator()
safety_checker = SafetyChecker()


class RequirementTextRequest(BaseModel):
    requirement_text: str
    req_id: str = "REQ_NEW"


# ══════════════════════════════════════════════
# E10 — Auto Test Case Generator
# ══════════════════════════════════════════════

@router.post("/generate-testcase")
def generate_testcase_from_text(request: RequirementTextRequest):
    """
    Generate a complete test case from any requirement text.
    Works for new requirements not yet in the system.
    """
    if not request.requirement_text.strip():
        raise HTTPException(status_code=400, detail="Requirement text cannot be empty")

    return tc_generator.generate_from_text(
        request.requirement_text,
        request.req_id
    )


@router.get("/generate-testcase/{req_id}")
def generate_testcase_for_requirement(req_id: str):
    """Generate a test case for an existing requirement in the KG"""
    result = tc_generator.generate_for_requirement(req_id.upper())
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/generate-testcase-all")
def generate_testcases_for_all():
    """Generate test cases for ALL requirements — bulk generation"""
    return tc_generator.generate_for_all()


# ══════════════════════════════════════════════
# E8 — ISO 26262 Functional Safety Check
# ══════════════════════════════════════════════

@router.get("/safety/check-all")
def check_all_safety():
    """
    Run full ISO 26262 functional safety check on all requirements.
    Classifies ASIL levels and checks compliance.
    """
    return safety_checker.check_all()


@router.get("/safety/check/{req_id}")
def check_safety_for_requirement(req_id: str):
    """ISO 26262 safety check for one requirement"""
    result = safety_checker.check_requirement(req_id.upper())
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/safety/asil-breakdown")
def get_asil_breakdown():
    """Get all requirements grouped by ASIL level (A, B, C, D, QM)"""
    return safety_checker.get_asil_breakdown()


@router.get("/safety/critical-gaps")
def get_critical_safety_gaps():
    """Get only Critical (ASIL C/D) safety gaps — must fix for compliance"""
    result = safety_checker.check_all()
    return {
        "total_critical_gaps": len(result["critical_safety_gaps"]),
        "overall_verdict":     result["overall_verdict"],
        "critical_gaps":       result["critical_safety_gaps"]
    }


@router.get("/safety/summary")
def get_safety_summary():
    """High level ISO 26262 compliance summary"""
    result = safety_checker.check_all()
    return {
        "total_requirements":  result["total_requirements"],
        "average_compliance":  result["average_compliance"],
        "asil_distribution":   result["asil_distribution"],
        "status_summary":      result["status_summary"],
        "overall_verdict":     result["overall_verdict"],
        "total_gaps":          result["total_gaps"]
    }