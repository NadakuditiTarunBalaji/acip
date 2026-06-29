from sqlalchemy import Column, String, Integer
from backend.config.database import Base


class KGRelation(Base):
    __tablename__ = "kg_relations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source = Column(String)
    target = Column(String)
    relationship = Column(String)