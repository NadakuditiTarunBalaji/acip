from backend.config.database import Base, engine

import backend.models

def init_database():
    Base.metadata.create_all(bind=engine)
    print("ACIP-X1 Database Created Successfully")

if __name__ == "__main__":
    init_database()
    