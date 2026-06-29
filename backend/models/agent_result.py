from sqlalchemy import Column, String, Integer, DateTime, Text
from backend.config.database import Base
from datetime import datetime


class AgentResult(Base):
    __tablename__ = "agent_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_name = Column(String)
    input_data = Column(Text)
    output_data = Column(Text)
    status = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)