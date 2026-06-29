from sqlalchemy import Column, String
from backend.config.database import Base

class TestCase(Base):
    __tablename__ = "test_cases"

    tc_id = Column(String, primary_key=True)
    req_id = Column(String)
    expected_result = Column(String)