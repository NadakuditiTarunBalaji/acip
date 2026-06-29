from backend.repositories.insurance_repository import (
    get_all_insurance_claims,
    create_insurance_claim,
    update_insurance_claim,
    delete_insurance_claim
)

def fetch_insurance(db):
    return get_all_insurance_claims(db)

def add_insurance_claim(
    db,
    claim_id,
    status,
    description
):
    return create_insurance_claim(
        db,
        claim_id,
        status,
        description
    )

def modify_insurance_claim(
    db,
    claim_id,
    status,
    description
):
    return update_insurance_claim(
        db,
        claim_id,
        status,
        description
    )

def remove_insurance_claim(
    db,
    claim_id
):
    return delete_insurance_claim(
        db,
        claim_id
    )