from sqlalchemy import Column, String, Integer
from backend.config.database import Base


class KGNode(Base):
    __tablename__ = "kg_nodes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    node_id = Column(String, unique=True)
    node_type = Column(String)
    name = Column(String)
    domain = Column(String)
    properties = Column(String)