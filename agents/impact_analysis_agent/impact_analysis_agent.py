import json

class ImpactAnalysisAgent:

    def analyze_fault(self, fault):

        impact_map = {

            "FAULT001": {
                "affected_ecu": "Battery Management ECU",
                "affected_signal": "Battery_Voltage",
                "impact_level": "High"
            },

            "FAULT004": {
                "affected_ecu": "Battery Management ECU",
                "affected_signal": "Battery_Temperature",
                "impact_level": "High"
            },

            "FAULT016": {
                "affected_ecu": "Motor Control ECU",
                "affected_signal": "Motor_Speed",
                "impact_level": "High"
            }

        }

        return impact_map.get(
            fault,
            {
                "affected_ecu": "Unknown",
                "affected_signal": "Unknown",
                "impact_level": "Unknown"
            }
        )


if __name__ == "__main__":

    agent = ImpactAnalysisAgent()

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
        