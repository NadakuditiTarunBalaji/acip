from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from backend.config.database import get_db
from backend.models.testcase import TestCase

router = APIRouter(
    prefix="/api/testcases",
    tags=["Test Cases"]
)


class TestCaseCreate(BaseModel):
    tc_id: str
    req_id: str
    expected_result: str


@router.get("/")
def get_testcases(db: Session = Depends(get_db)):
    return db.query(TestCase).all()


@router.post("/")
def add_testcase(
    testcase: TestCaseCreate,
    db: Session = Depends(get_db)
):
    tc = TestCase(
        tc_id=testcase.tc_id,
        req_id=testcase.req_id,
        expected_result=testcase.expected_result
    )
    db.add(tc)
    db.commit()
    db.refresh(tc)
    return tc


@router.get("/{tc_id}")
def get_testcase_by_id(
    tc_id: str,
    db: Session = Depends(get_db)
):
    return db.query(TestCase).filter(TestCase.tc_id == tc_id).first()


@router.put("/{tc_id}")
def update_testcase(
    tc_id: str,
    testcase: TestCaseCreate,
    db: Session = Depends(get_db)
):
    tc = db.query(TestCase).filter(TestCase.tc_id == tc_id).first()
    if tc:
        tc.req_id = testcase.req_id
        tc.expected_result = testcase.expected_result
        db.commit()
        db.refresh(tc)
    return tc


@router.delete("/{tc_id}")
def delete_testcase(
    tc_id: str,
    db: Session = Depends(get_db)
):
    tc = db.query(TestCase).filter(TestCase.tc_id == tc_id).first()
    if tc:
        db.delete(tc)
        db.commit()
    return {"message": f"TestCase {tc_id} deleted"}