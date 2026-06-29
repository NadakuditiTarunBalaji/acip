from backend.repositories.signal_repository import get_all_signals

def fetch_signals(db):
    return get_all_signals(db)