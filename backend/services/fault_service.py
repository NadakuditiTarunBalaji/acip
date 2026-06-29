from backend.repositories.fault_repository import (
    get_all_faults,
    create_fault,
    update_fault,
    delete_fault
)

def fetch_faults(db):
    return get_all_faults(db)

def add_fault(
    db,
    fault_id,
    fault_name,
    root_cause,
    severity
):
    return create_fault(
        db,
        fault_id,
        fault_name,
        root_cause,
        severity
    )

def modify_fault(
    db,
    fault_id,
    fault_name,
    root_cause,
    severity
):
    return update_fault(
        db,
        fault_id,
        fault_name,
        root_cause,
        severity
    )

def remove_fault(
    db,
    fault_id
):
    return delete_fault(
        db,
        fault_id
    )