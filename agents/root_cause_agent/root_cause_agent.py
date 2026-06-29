import json

class RootCauseAgent:

    def analyze_fault(self, fault):

        fault_map = {

            "FAULT001": {
                "severity": "High",
                "root_cause": "Battery Overvoltage",
                "recommended_action": "Stop charging and inspect battery pack"
            },

            "FAULT004": {
                "severity": "High",
                "root_cause": "Battery Overtemperature",
                "recommended_action": "Inspect battery cooling system"
            },

            "FAULT016": {
                "severity": "High",
                "root_cause": "Motor Overspeed",
                "recommended_action": "Reduce motor speed and inspect control logic"
            },

        }

        return fault_map.get(
            fault,
            {
                "root_cause": "Unknown",
                "recommended_action": "Manual Investigation Required"
            }
        )


if __name__ == "__main__":

    agent = RootCauseAgent()

    faults = [
        "FAULT001",
        "FAULT004",
        "FAULT016"
    ]

    for fault in faults:

        result = {
            "fault": fault,
            **agent.analyze_fault(fault)
        }

        print(json.dumps(result, indent=4))
        print("-" * 50)