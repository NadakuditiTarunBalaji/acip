from backend.repositories.dtc_repository import (
    get_all_dtcs,
    create_dtc,
    update_dtc,
    delete_dtc
)

def fetch_dtcs(db):
    return get_all_dtcs(db)

def add_dtc(
    db,
    dtc_code,
    description,
    severity
):
    return create_dtc(
        db,
        dtc_code,
        description,
        severity
    )

def modify_dtc(
    db,
    dtc_code,
    description,
    severity
):
    return update_dtc(
        db,
        dtc_code,
        description,
        severity
    )

def remove_dtc(
    db,
    dtc_code
):
    return delete_dtc(
        db,
        dtc_code
    )