"""
ACIP-X1 — Seed All Data
Run this once after init_db to populate all tables with sample data.

Usage:
    python -m backend.utils.seed_all
"""

from backend.config.database import SessionLocal
from backend.models.ecu import ECU
from backend.models.signal import Signal
from backend.models.calibration import Calibration
from backend.models.dtc import DTC
from backend.models.fault import Fault
from backend.models.requirement import Requirement
from backend.models.testcase import TestCase
from backend.models.vehicle_data import VehicleData
from backend.models.insurance_claim import InsuranceClaim
from backend.models.vehicle import Vehicle
from backend.models.vehicle_telemetry import VehicleTelemetry


def seed_all():
    db = SessionLocal()
    try:
        # ── ECUs ──────────────────────────────────────────
        if db.query(ECU).count() == 0:
            ecus = [
                ECU(ecu_id="ECU001", ecu_name="Motor Control ECU",        function="Motor Management"),
                ECU(ecu_id="ECU002", ecu_name="Battery Management System", function="Battery Monitoring"),
                ECU(ecu_id="ECU003", ecu_name="Inverter ECU",              function="Power Conversion"),
                ECU(ecu_id="ECU004", ecu_name="Torque Management ECU",     function="Torque Control"),
                ECU(ecu_id="ECU005", ecu_name="Energy Management ECU",     function="Energy Optimization"),
                ECU(ecu_id="ECU006", ecu_name="Drive Control ECU",         function="Drive Mode Control"),
                ECU(ecu_id="ECU007", ecu_name="Charging Coordination ECU", function="Charging Management"),
                ECU(ecu_id="ECU008", ecu_name="Brake Control ECU",         function="Regenerative Braking"),
                ECU(ecu_id="ECU009", ecu_name="Thermal Management ECU",    function="Thermal Control"),
                ECU(ecu_id="ECU010", ecu_name="Powertrain Gateway ECU",    function="Gateway Communication"),
            ]
            db.add_all(ecus)
            db.commit()
            print(f"✅ ECUs seeded: {len(ecus)} records")
        else:
            print("⏭️  ECUs already seeded")

        # ── Signals ───────────────────────────────────────
        if db.query(Signal).count() == 0:
            signals = [
                Signal(signal_id="SIG001", signal_name="Motor_Speed",          unit="RPM", min_value=0,    max_value=12000, ecu_id="ECU001"),
                Signal(signal_id="SIG002", signal_name="Motor_Torque",          unit="Nm",  min_value=0,    max_value=350,   ecu_id="ECU004"),
                Signal(signal_id="SIG003", signal_name="Vehicle_Speed",         unit="kmh", min_value=0,    max_value=200,   ecu_id="ECU006"),
                Signal(signal_id="SIG004", signal_name="Accelerator_Position",  unit="%",   min_value=0,    max_value=100,   ecu_id="ECU006"),
                Signal(signal_id="SIG005", signal_name="Regen_Brake_Level",     unit="%",   min_value=0,    max_value=100,   ecu_id="ECU008"),
                Signal(signal_id="SIG006", signal_name="Power_Output",          unit="kW",  min_value=0,    max_value=300,   ecu_id="ECU005"),
                Signal(signal_id="SIG007", signal_name="Energy_Consumption",    unit="kWh", min_value=0,    max_value=100,   ecu_id="ECU005"),
                Signal(signal_id="SIG008", signal_name="Drive_Mode",            unit="",    min_value=0,    max_value=4,     ecu_id="ECU006"),
                Signal(signal_id="SIG009", signal_name="Charging_Status",       unit="",    min_value=0,    max_value=1,     ecu_id="ECU007"),
                Signal(signal_id="SIG010", signal_name="Inverter_Temperature",  unit="C",   min_value=-40,  max_value=85,    ecu_id="ECU003"),
                Signal(signal_id="SIG016", signal_name="Battery_Voltage",       unit="V",   min_value=280,  max_value=420,   ecu_id="ECU002"),
                Signal(signal_id="SIG017", signal_name="Battery_Current",       unit="A",   min_value=-300, max_value=300,   ecu_id="ECU002"),
                Signal(signal_id="SIG018", signal_name="Battery_Temperature",   unit="C",   min_value=-20,  max_value=45,    ecu_id="ECU002"),
                Signal(signal_id="SIG019", signal_name="State_of_Charge",       unit="%",   min_value=0,    max_value=100,   ecu_id="ECU002"),
                Signal(signal_id="SIG020", signal_name="State_of_Health",       unit="%",   min_value=0,    max_value=100,   ecu_id="ECU002"),
                Signal(signal_id="SIG023", signal_name="Cell_Voltage_Imbalance",unit="mV",  min_value=0,    max_value=50,    ecu_id="ECU002"),
            ]
            db.add_all(signals)
            db.commit()
            print(f"✅ Signals seeded: {len(signals)} records")
        else:
            print("⏭️  Signals already seeded")

        # ── Calibrations ──────────────────────────────────
        if db.query(Calibration).count() == 0:
            calibrations = [
                Calibration(cal_id="CAL001", parameter="Battery_Overvoltage_Limit",    value=420,   unit="V"),
                Calibration(cal_id="CAL002", parameter="Battery_Undervoltage_Limit",   value=280,   unit="V"),
                Calibration(cal_id="CAL003", parameter="Battery_Overcurrent_Limit",    value=300,   unit="A"),
                Calibration(cal_id="CAL004", parameter="Battery_Overtemperature_Limit",value=45,    unit="C"),
                Calibration(cal_id="CAL005", parameter="Battery_Undertemp_Limit",      value=-20,   unit="C"),
                Calibration(cal_id="CAL006", parameter="SOC_Warning_Threshold",        value=20,    unit="%"),
                Calibration(cal_id="CAL007", parameter="SOC_Critical_Threshold",       value=10,    unit="%"),
                Calibration(cal_id="CAL008", parameter="SOH_Warning_Threshold",        value=80,    unit="%"),
                Calibration(cal_id="CAL009", parameter="SOH_Critical_Threshold",       value=60,    unit="%"),
                Calibration(cal_id="CAL010", parameter="Cell_Imbalance_Threshold",     value=50,    unit="mV"),
                Calibration(cal_id="CAL011", parameter="Motor_Speed_Max",              value=12000, unit="RPM"),
                Calibration(cal_id="CAL012", parameter="Motor_Torque_Max",             value=350,   unit="Nm"),
                Calibration(cal_id="CAL013", parameter="Vehicle_Speed_Max",            value=200,   unit="kmh"),
                Calibration(cal_id="CAL014", parameter="Inverter_Temperature_Max",     value=85,    unit="C"),
                Calibration(cal_id="CAL015", parameter="Regen_Brake_Max",              value=100,   unit="%"),
            ]
            db.add_all(calibrations)
            db.commit()
            print(f"✅ Calibrations seeded: {len(calibrations)} records")
        else:
            print("⏭️  Calibrations already seeded")

        # ── DTCs ──────────────────────────────────────────
        if db.query(DTC).count() == 0:
            dtcs = [
                DTC(dtc_id="DTC001", description="Battery Overvoltage Detected",    severity="High"),
                DTC(dtc_id="DTC002", description="Battery Undervoltage Detected",   severity="High"),
                DTC(dtc_id="DTC003", description="Battery Overcurrent Detected",    severity="High"),
                DTC(dtc_id="DTC004", description="Battery Overtemperature Detected",severity="Critical"),
                DTC(dtc_id="DTC005", description="Battery Undertemperature Detected",severity="Medium"),
                DTC(dtc_id="DTC006", description="SOC Below Warning Threshold",     severity="Medium"),
                DTC(dtc_id="DTC007", description="SOC Critical Level Reached",      severity="High"),
                DTC(dtc_id="DTC008", description="SOH Below Warning Threshold",     severity="Medium"),
                DTC(dtc_id="DTC009", description="SOH Critical Level Reached",      severity="High"),
                DTC(dtc_id="DTC010", description="Cell Voltage Imbalance Detected", severity="High"),
            ]
            db.add_all(dtcs)
            db.commit()
            print(f"✅ DTCs seeded: {len(dtcs)} records")
        else:
            print("⏭️  DTCs already seeded")

        # ── Faults ────────────────────────────────────────
        if db.query(Fault).count() == 0:
            faults = [
                Fault(fault_id="FAULT001", fault_name="Battery Overvoltage Fault",      root_cause="Charging System Failure",      severity="High"),
                Fault(fault_id="FAULT002", fault_name="Battery Undervoltage Fault",     root_cause="Battery Cell Aging",           severity="High"),
                Fault(fault_id="FAULT003", fault_name="Battery Overcurrent Fault",      root_cause="Power Electronics Failure",    severity="High"),
                Fault(fault_id="FAULT004", fault_name="Battery Overtemperature Fault",  root_cause="Thermal Management Failure",   severity="Critical"),
                Fault(fault_id="FAULT005", fault_name="Battery Undertemperature Fault", root_cause="Cooling System Failure",       severity="Medium"),
                Fault(fault_id="FAULT006", fault_name="Low SOC Warning Fault",          root_cause="Excessive Load Demand",        severity="Medium"),
                Fault(fault_id="FAULT007", fault_name="Critical SOC Fault",             root_cause="Battery Pack Degradation",     severity="High"),
                Fault(fault_id="FAULT008", fault_name="Battery SOH Degradation Fault",  root_cause="Battery Cell Aging",           severity="Medium"),
                Fault(fault_id="FAULT009", fault_name="Critical Battery SOH Fault",     root_cause="Battery Pack Degradation",     severity="High"),
                Fault(fault_id="FAULT010", fault_name="Cell Voltage Imbalance Fault",   root_cause="Cell Balancing Failure",       severity="High"),
            ]
            db.add_all(faults)
            db.commit()
            print(f"✅ Faults seeded: {len(faults)} records")
        else:
            print("⏭️  Faults already seeded")

        # ── Requirements ──────────────────────────────────
        if db.query(Requirement).count() == 0:
            requirements = [
                Requirement(req_id="REQ001", description="Battery voltage shall not exceed 420V",               category="Safety",     system="Battery"),
                Requirement(req_id="REQ002", description="Battery voltage shall not drop below 280V",           category="Safety",     system="Battery"),
                Requirement(req_id="REQ003", description="Battery current shall not exceed 300A",               category="Safety",     system="Battery"),
                Requirement(req_id="REQ004", description="Battery temperature shall not exceed 45 degrees C",   category="Safety",     system="Battery"),
                Requirement(req_id="REQ005", description="Battery temperature shall not drop below -20C",       category="Safety",     system="Battery"),
                Requirement(req_id="REQ006", description="SOC warning shall trigger below 20 percent",         category="Functional", system="Battery"),
                Requirement(req_id="REQ007", description="SOC critical shall trigger below 10 percent",        category="Functional", system="Battery"),
                Requirement(req_id="REQ008", description="SOH warning shall trigger below 80 percent",         category="Functional", system="Battery"),
                Requirement(req_id="REQ009", description="SOH critical shall trigger below 60 percent",        category="Functional", system="Battery"),
                Requirement(req_id="REQ010", description="Cell voltage imbalance shall not exceed 50mV",       category="Safety",     system="Battery"),
                Requirement(req_id="REQ011", description="Motor speed shall not exceed 12000 RPM",             category="Safety",     system="Powertrain"),
                Requirement(req_id="REQ012", description="Motor torque shall not exceed 350 Nm",               category="Functional", system="Powertrain"),
                Requirement(req_id="REQ013", description="Vehicle speed shall not exceed 200 kmh",             category="Safety",     system="Powertrain"),
                Requirement(req_id="REQ014", description="Inverter temperature shall not exceed 85 degrees C", category="Safety",     system="Powertrain"),
                Requirement(req_id="REQ015", description="Regen braking shall recover minimum 70 percent energy", category="Functional", system="Powertrain"),
            ]
            db.add_all(requirements)
            db.commit()
            print(f"✅ Requirements seeded: {len(requirements)} records")
        else:
            print("⏭️  Requirements already seeded")

        # ── Test Cases ────────────────────────────────────
        if db.query(TestCase).count() == 0:
            testcases = [
                TestCase(tc_id="TC001", req_id="REQ001", expected_result="DTC001 triggered when voltage exceeds 420V"),
                TestCase(tc_id="TC002", req_id="REQ002", expected_result="DTC002 triggered when voltage drops below 280V"),
                TestCase(tc_id="TC003", req_id="REQ003", expected_result="DTC003 triggered when current exceeds 300A"),
                TestCase(tc_id="TC004", req_id="REQ004", expected_result="DTC004 triggered when temperature exceeds 45C"),
                TestCase(tc_id="TC005", req_id="REQ005", expected_result="DTC005 triggered when temperature drops below -20C"),
                TestCase(tc_id="TC006", req_id="REQ006", expected_result="Warning alert when SOC drops below 20 percent"),
                TestCase(tc_id="TC007", req_id="REQ007", expected_result="Critical alert and limp mode when SOC below 10 percent"),
                TestCase(tc_id="TC008", req_id="REQ008", expected_result="SOH warning displayed when below 80 percent"),
                TestCase(tc_id="TC009", req_id="REQ009", expected_result="Critical SOH alert when below 60 percent"),
                TestCase(tc_id="TC010", req_id="REQ010", expected_result="DTC010 triggered when imbalance exceeds 50mV"),
            ]
            db.add_all(testcases)
            db.commit()
            print(f"✅ Test Cases seeded: {len(testcases)} records")
        else:
            print("⏭️  Test Cases already seeded")

        # ── Vehicle Data ──────────────────────────────────
        if db.query(VehicleData).count() == 0:
            vehicle_data = [
                VehicleData(rpm=800,  battery_temp=30, coolant_temp=75, speed=0),
                VehicleData(rpm=2500, battery_temp=35, coolant_temp=85, speed=60),
                VehicleData(rpm=3200, battery_temp=38, coolant_temp=90, speed=100),
            ]
            db.add_all(vehicle_data)
            db.commit()
            print(f"✅ Vehicle Data seeded: {len(vehicle_data)} records")
        else:
            print("⏭️  Vehicle Data already seeded")

        # ── Insurance Claims ──────────────────────────────
        if db.query(InsuranceClaim).count() == 0:
            claims = [
                InsuranceClaim(claim_id="CLM001", status="Approved", description="Battery overtemperature damage"),
                InsuranceClaim(claim_id="CLM002", status="Pending",  description="Motor replacement claim"),
                InsuranceClaim(claim_id="CLM003", status="Rejected", description="Charging system failure claim"),
            ]
            db.add_all(claims)
            db.commit()
            print(f"✅ Insurance Claims seeded: {len(claims)} records")
        else:
            print("⏭️  Insurance Claims already seeded")

        # ── Vehicle ───────────────────────────────────────
        if db.query(Vehicle).count() == 0:
            vehicles = [
                Vehicle(
                    vin="ACIP2024X1001",
                    model="ACIP-X1",
                    manufacturer="ACIP Motors",
                    year=2024,
                    owner_name="Demo Owner",
                    owner_phone="+91-9999999999"
                ),
            ]
            db.add_all(vehicles)
            db.commit()
            print(f"✅ Vehicles seeded: {len(vehicles)} records")
        else:
            print("⏭️  Vehicles already seeded")

        print("\n🎉 All data seeded successfully!")
        print("=" * 50)

    except Exception as e:
        db.rollback()
        print(f"❌ Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()