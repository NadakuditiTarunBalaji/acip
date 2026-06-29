from backend.repositories.calibration_repository import get_all_calibrations

def fetch_calibrations(db):
    return get_all_calibrations(db)