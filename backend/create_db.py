from backend.config.database import Base, engine

# THIS IS REQUIRED (forces model loading)
import backend.models  # noqa: F401


def init_db():
    print("Creating ACIP-X1 DB...")
    Base.metadata.create_all(bind=engine)
    print("DB Created Successfully")


if __name__ == "__main__":
    init_db()