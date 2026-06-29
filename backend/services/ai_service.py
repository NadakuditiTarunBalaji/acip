from backend.repositories.fault_repository import get_fault_by_id

def analyze_fault(db, fault_id):
    fault = get_fault_by_id(db, fault_id)

    if not fault:
        return {
            "error": "Fault not found"
        }

    return {
        "fault_id": fault.fault_id,
        "fault_name": fault.fault_name,
        "severity": fault.severity,
        "root_cause": fault.root_cause,
        "recommendation": generate_recommendation(
            fault.severity,
            fault.root_cause
        )
    }

def generate_recommendation(severity, root_cause):

    if severity == "Critical":
        return "Stop vehicle immediately and inspect system."

    if severity == "High":
        return "Schedule immediate maintenance."

    if severity == "Medium":
        return "Inspect during next service."

    return "Monitor vehicle condition."


def analyze_dtc(dtc_code):
    dtc_database = {
        "P0300": {
            "description": "Random/Multiple Cylinder Misfire Detected",
            "possible_causes": [
                "Faulty spark plugs",
                "Ignition coil issue",
                "Fuel injector problem",
                "Vacuum leak"
            ],
            "recommendation": "Inspect ignition system and fuel delivery components."
        },
        "P0171": {
            "description": "System Too Lean (Bank 1)",
            "possible_causes": [
                "Vacuum leak",
                "Dirty MAF sensor",
                "Fuel pump issue"
            ],
            "recommendation": "Check air intake system and fuel pressure."
        }
    }

    return dtc_database.get(
        dtc_code.upper(),
        {
            "description": "Unknown DTC",
            "possible_causes": ["No data available"],
            "recommendation": "Refer to service manual."
        }
    )