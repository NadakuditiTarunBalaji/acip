from backend.repositories.requirement_repository import get_all_requirements

def fetch_requirements(db):
    return get_all_requirements(db)