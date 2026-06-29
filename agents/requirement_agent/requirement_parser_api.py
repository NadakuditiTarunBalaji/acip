"""
ACIP-X1 — AI Requirement Parser API
Engineering Mode — Feature E1
"""
import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from backend.config.database import get_db
from backend.models.requirement import Requirement
from agents.requirement_agent.requirement_parser import RequirementParser

router = APIRouter(
    prefix="/api/engineering/requirements",
    tags=["Engineering Mode — Requirement Parser"]
)

UPLOAD_DIR = "uploads/requirements"
os.makedirs(UPLOAD_DIR, exist_ok=True)

parser = RequirementParser()


class TextParseRequest(BaseModel):
    text: str
    save_to_db: Optional[bool] = False


@router.post("/parse/file")
async def parse_requirements_from_file(
    file: UploadFile = File(...),
    save_to_db: bool = False,
    db: Session = Depends(get_db)
):
    """
    Upload any file (PDF/Excel/Word/CSV/TXT) →
    AI reads and extracts all requirements automatically.

    Engineering Mode — Feature E1
    """
    # Validate file type
    allowed = [".pdf", ".xlsx", ".xls", ".docx", ".doc", ".csv", ".txt"]
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"File type {ext} not supported. Allowed: {', '.join(allowed)}"
        )

    # Save uploaded file temporarily
    temp_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        # Parse requirements
        result = parser.parse_file(temp_path)

        # Save to DB if requested
        saved_count = 0
        skipped_count = 0
        if save_to_db and result["requirements"]:
            for req in result["requirements"]:
                # Check if already exists
                existing = db.query(Requirement).filter(
                    Requirement.req_id == req["req_id"]
                ).first()
                if not existing:
                    new_req = Requirement(
                        req_id=req["req_id"],
                        description=req["description"],
                        category=req["category"],
                        system=req["system"]
                    )
                    db.add(new_req)
                    saved_count += 1
                else:
                    skipped_count += 1
            db.commit()

        return {
            "status":           "success",
            "file_name":        file.filename,
            "file_type":        result["file_type"],
            "total_found":      result["total_found"],
            "raw_lines_total":  result.get("raw_lines_total", 0),
            "filtered_out":     result.get("filtered_out", 0),
            "saved_to_db":      saved_count if save_to_db else 0,
            "skipped":          skipped_count if save_to_db else 0,
            "requirements":     result["requirements"],
            "errors":           result["errors"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/parse/text")
def parse_requirements_from_text(
    request: TextParseRequest,
    db: Session = Depends(get_db)
):
    """
    Paste raw text directly →
    AI extracts all requirements.

    Engineering Mode — Feature E1
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    result = parser.parse_text(request.text)

    saved_count = 0
    if request.save_to_db and result["requirements"]:
        for req in result["requirements"]:
            existing = db.query(Requirement).filter(
                Requirement.req_id == req["req_id"]
            ).first()
            if not existing:
                new_req = Requirement(
                    req_id=req["req_id"],
                    description=req["description"],
                    category=req["category"],
                    system=req["system"]
                )
                db.add(new_req)
                saved_count += 1
        db.commit()

    return {
        "status":       "success",
        "total_found":  result["total_found"],
        "saved_to_db":  saved_count if request.save_to_db else 0,
        "requirements": result["requirements"],
        "errors":       result["errors"]
    }


@router.get("/parse/demo")
def parse_demo_requirements(db: Session = Depends(get_db)):
    """
    Demo mode — parse sample automotive requirements
    to show how the parser works without uploading a file.
    """
    sample_text = """
    REQ001: The battery voltage shall not exceed 420V under any operating condition.
    REQ002: The battery voltage shall not drop below 280V during discharge.
    REQ003: The battery current shall not exceed 300A during peak power demand.
    REQ004: The battery temperature shall not exceed 45 degrees Celsius during charging or discharging.
    REQ005: The battery management system shall trigger a warning alert when SOC drops below 20 percent.
    REQ006: The motor speed shall not exceed 12000 RPM under any operating condition.
    REQ007: The inverter temperature shall not exceed 85 degrees Celsius during operation.
    REQ008: The vehicle speed shall not exceed 200 km/h as governed by the drive control ECU.
    REQ009: The regenerative braking system shall recover a minimum of 70 percent of kinetic energy.
    REQ010: The BMS shall detect cell voltage imbalance greater than 50mV and trigger DTC immediately.
    """

    result = parser.parse_text(sample_text)

    return {
        "status":       "demo",
        "message":      "This is a demo parse — upload your real requirements file to /parse/file",
        "total_found":  result["total_found"],
        "requirements": result["requirements"]
    }


@router.get("/stats")
def get_requirement_stats(db: Session = Depends(get_db)):
    """Get statistics about requirements in DB"""
    from sqlalchemy import func

    total = db.query(Requirement).count()

    # Count by category
    by_category = {}
    reqs = db.query(Requirement).all()
    for r in reqs:
        cat = r.category or "Unknown"
        by_category[cat] = by_category.get(cat, 0) + 1

    # Count by system
    by_system = {}
    for r in reqs:
        sys = r.system or "Unknown"
        by_system[sys] = by_system.get(sys, 0) + 1

    return {
        "total_requirements": total,
        "by_category":        by_category,
        "by_system":          by_system
    }