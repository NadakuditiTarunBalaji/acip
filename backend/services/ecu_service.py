from backend.repositories.ecu_repository import get_all_ecus

def fetch_ecus(db):
    return get_all_ecus(db)