"""
ACIP-X1 — Pre-Test Failure Prediction API
Engineering Mode — Feature E3
"""
from fastapi import APIRouter, HTTPException
from agents.requirement_agent.failure_predictor import FailurePredictor

router = APIRouter(
    prefix="/api/engineering/predict",
    tags=["Engineering Mode — Pre-Test Failure Prediction"]
)

predictor = FailurePredictor()


@router.get("/all")
def predict_all_failures():
    """
    Predict which test cases will FAIL before running them.
    Compares requirement limits vs calibration values vs signal ranges.
    """
    return predictor.predict_all()


@router.get("/summary")
def get_prediction_summary():
    """Get high level prediction summary"""
    result = predictor.predict_all()
    return {
        "total_requirements": result["total_requirements"],
        "predicted_pass":     result["predicted_pass"],
        "predicted_fail":     result["predicted_fail"],
        "predicted_warning":  result["predicted_warning"],
        "pass_rate":          result["pass_rate"],
        "summary":            result["summary"],
        "critical_failures":  result["critical_failures"]
    }


@router.get("/requirement/{req_id}")
def predict_single_requirement(req_id: str):
    """
    Predict if test cases for a specific requirement will fail.
    """
    result = predictor.predict_requirement_failure(req_id.upper())
    if result.get("status") == "Not Found":
        raise HTTPException(
            status_code=404,
            detail=f"Requirement {req_id} not found"
        )
    return result


@router.get("/system/{system}")
def predict_by_system(system: str):
    """
    Predict failures for all requirements of a specific system.
    Example: /predict/system/Battery or /predict/system/Powertrain
    """
    return predictor.predict_by_system(system)


@router.get("/failures-only")
def get_failures_only():
    """Get only the requirements predicted to FAIL"""
    result = predictor.predict_all()
    failures = [p for p in result["predictions"] if p["verdict"] == "FAIL"]
    return {
        "total_failures": len(failures),
        "pass_rate":      result["pass_rate"],
        "failures":       failures
    }


@router.get("/warnings-only")
def get_warnings_only():
    """Get only the requirements with warnings"""
    result = predictor.predict_all()
    warnings = [p for p in result["predictions"] if p["verdict"] == "WARNING"]
    return {
        "total_warnings": len(warnings),
        "warnings":       warnings
    }