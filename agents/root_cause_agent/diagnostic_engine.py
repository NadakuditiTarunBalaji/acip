import json

from backend.services.master_data_manager import MasterDataManager


class DiagnosticEngine:

    def __init__(self):

        self.master_data = MasterDataManager()

    def evaluate_signal(self, signal, value):

        calibration = self.master_data.get_calibration_by_signal(
            signal
        )

        if calibration is None:

            return {
                "signal": signal,
                "value": value,
                "status": "Unknown Signal"
            }

        limit = float(calibration["value"])

        dtc_code = self.master_data.get_dtc_by_signal(
            signal
        )

        fault = self.master_data.get_fault_by_dtc(
            dtc_code
        )

        if value > limit:

            return {
                "signal": signal,
                "value": value,
                "limit": limit,
                "fault": fault,
                "status": "Fault Detected"
            }

        return {
            "signal": signal,
            "value": value,
            "limit": limit,
            "fault": None,
            "status": "Normal"
        }


if __name__ == "__main__":

    engine = DiagnosticEngine()

    tests = [

        ("Battery_Voltage", 400),
        ("Battery_Voltage", 435),

        ("Battery_Temperature", 45),
        ("Battery_Temperature", 75),

        ("Motor_Speed", 10000),
        ("Motor_Speed", 13000)

    ]

    for signal, value in tests:

        result = engine.evaluate_signal(
            signal,
            value
        )

        print(json.dumps(result, indent=4))
        print("-" * 50)