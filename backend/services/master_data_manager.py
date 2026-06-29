import os
import pandas as pd

# Absolute base path — works from any directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data", "raw")


class MasterDataManager:
    def __init__(self):
        self.calibration_data = None
        self.dtc_data = None
        self.fault_data = None
        self.signal_data = None
        self._load_all()

    def _load_file(self, filename):
        path = os.path.join(DATA_DIR, filename)
        if os.path.exists(path):
            try:
                return pd.read_excel(path)
            except Exception as e:
                print(f"Warning: Could not load {filename}: {e}")
                return pd.DataFrame()
        else:
            print(f"Warning: File not found: {path}")
            return pd.DataFrame()

    def _load_all(self):
        self.calibration_data = self._load_file("Calibration_Master.xlsx")
        self.dtc_data = self._load_file("DTC_Master.xlsx")
        self.fault_data = self._load_file("Fault_Master.xlsx")
        self.signal_data = self._load_file("Signal_Master.xlsx")
        print(f"MasterDataManager loaded from: {DATA_DIR}")

    def get_calibration(self):
        return self.calibration_data

    def get_dtc(self):
        return self.dtc_data

    def get_fault(self):
        return self.fault_data

    def get_signal(self):
        return self.signal_data

    def get_calibration_limit(self, parameter_name):
        if self.calibration_data.empty:
            return None
        row = self.calibration_data[
            self.calibration_data.iloc[:, 0].astype(str).str.contains(
                parameter_name, case=False, na=False
            )
        ]
        if not row.empty:
            return row.iloc[0].to_dict()
        return None

    def is_loaded(self):
        return not all([
            self.calibration_data.empty,
            self.dtc_data.empty,
            self.fault_data.empty,
            self.signal_data.empty
        ])