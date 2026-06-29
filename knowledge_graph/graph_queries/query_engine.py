import json

from backend.services.master_data_manager import MasterDataManager


class QueryEngine:

    def __init__(self):

        self.master_data = MasterDataManager()

    def find_fault_by_signal(self, signal):

        dtc = self.master_data.get_dtc_by_signal(signal)

        if dtc is None:

            return {
                "signal": signal,
                "status": "Not Found"
            }

        fault = self.master_data.get_fault_by_dtc(dtc)

        return {
            "signal": signal,
            "dtc": dtc,
            "fault": fault
        }
    
    def find_ecu_by_signal(self, signal):

        ecu = self.master_data.get_signal_ecu(signal)

        return {
            "signal": signal,
            "ecu": ecu
        }
    



    def full_signal_trace(self, signal):

        ecu = self.master_data.get_signal_ecu(signal)

        dtc = self.master_data.get_dtc_by_signal(signal)

        fault = self.master_data.get_fault_by_dtc(dtc)

        calibration = self.master_data.get_calibration_by_signal(signal)

        return {
            "signal": signal,
            "ecu": ecu,
            "calibration": calibration["parameter_name"] if calibration else None,
            "limit": calibration["value"] if calibration else None,
            "dtc": dtc,
            "fault": fault
        }


if __name__ == "__main__":

    engine = QueryEngine()

    signals = [

        "Battery_Voltage",
        "Battery_Temperature",
        "Motor_Speed"

    ]

    print("\nSIGNAL -> DTC -> FAULT")
    print("=" * 50)

    for signal in signals:

        result = engine.find_fault_by_signal(signal)

        print(json.dumps(result, indent=4))
        print("-" * 50)

    print("\nFULL SIGNAL TRACE")
    print("=" * 50)

    for signal in signals:

        result = engine.full_signal_trace(signal)

        print(json.dumps(result, indent=4))
        print("-" * 50)