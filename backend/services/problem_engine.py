"""
ACIP-X1 — Problem -> Solution -> Cost Engine (Day 16 / C2)

Scans the vehicle's LIVE telemetry against the same calibration limits
used by Engineering Mode (backend/models/calibration.py — 27 real limits
defined in Week 1) and turns every check into a customer-friendly card:

    Problem  -> what's actually happening, in plain language
    Solution -> what the customer should do about it
    Cost     -> a realistic India (Rs.) cost estimate if action is needed
    Impact   -> what happens if it's ignored

Every check returns a result even when everything is healthy, so the
dashboard can show "X/Y systems checked, all normal" — not just a
silent list that only appears when something's wrong.
"""
from sqlalchemy.orm import Session
from backend.models.vehicle_telemetry import VehicleTelemetry
from backend.services.dashboard_service import get_calibration_value, get_latest_telemetry


def _check(check_id, category, parameter, value, unit, status, title,
           problem, solution=None, cost=None, impact=None, normal_range=None):
    """Build one uniform check result. solution/cost/impact are only
    needed when status != 'ok' — healthy checks don't need a fix."""
    return {
        "id": check_id,
        "category": category,
        "parameter": parameter,
        "value": value,
        "unit": unit,
        "status": status,            # "ok" | "warning" | "critical"
        "normal_range": normal_range,
        "title": title,
        "problem": problem,
        "solution": solution,
        "cost": cost,
        "impact": impact,
    }


def run_diagnostics(db: Session, vehicle_id: str = "VEH001") -> dict:
    """Run every Problem->Solution->Cost check against the latest live
    telemetry and return a structured result for the dashboard."""

    t = get_latest_telemetry(db, vehicle_id)
    checks = []

    if not t:
        return {
            "vehicle_id": vehicle_id,
            "timestamp": None,
            "total_checks": 0,
            "checks": [],
            "critical_count": 0,
            "warning_count": 0,
            "ok_count": 0,
        }

    # ── Pull real calibration limits (Week 1 Engineering Mode) ──────
    cal_overvoltage   = get_calibration_value(db, "Battery_Overvoltage_Limit",    420.0)
    cal_undervoltage  = get_calibration_value(db, "Battery_Undervoltage_Limit",   280.0)
    cal_overcurrent   = get_calibration_value(db, "Battery_Overcurrent_Limit",    300.0)
    cal_overtemp      = get_calibration_value(db, "Battery_Overtemperature_Limit", 45.0)
    cal_undertemp     = get_calibration_value(db, "Battery_Undertemp_Limit",      -20.0)
    cal_soc_warning   = get_calibration_value(db, "SOC_Warning_Threshold",         20.0)
    cal_soc_critical  = get_calibration_value(db, "SOC_Critical_Threshold",        10.0)
    cal_soh_warning   = get_calibration_value(db, "SOH_Warning_Threshold",         80.0)
    cal_soh_critical  = get_calibration_value(db, "SOH_Critical_Threshold",        60.0)
    cal_cell_imbalance = get_calibration_value(db, "Cell_Imbalance_Threshold",     50.0)
    cal_motor_speed   = get_calibration_value(db, "Motor_Speed_Max",            12000.0)
    cal_motor_torque  = get_calibration_value(db, "Motor_Torque_Max",             350.0)
    cal_vehicle_speed = get_calibration_value(db, "Vehicle_Speed_Max",            200.0)
    cal_inverter_temp = get_calibration_value(db, "Inverter_Temperature_Max",      85.0)
    cal_regen_max     = get_calibration_value(db, "Regen_Brake_Max",               70.0)
    cal_power_max     = get_calibration_value(db, "Power_Output_Max",             300.0)
    cal_energy_max    = get_calibration_value(db, "Energy_Consumption_Max",        25.0)
    cal_cell_v_min    = get_calibration_value(db, "Cell_Voltage_Min",               3.0)
    cal_cell_v_max    = get_calibration_value(db, "Cell_Voltage_Max",               4.2)
    cal_coolant_temp  = get_calibration_value(db, "Coolant_Temperature_Max",        95.0)

    power_kw = (t.battery_voltage or 0) * (t.battery_current or 0) / 1000
    cell_imbalance_mv = ((t.cell_voltage_max or 0) - (t.cell_voltage_min or 0)) * 1000

    # ══════════════════════════════════════════════════════════════
    # BATTERY & BMS
    # ══════════════════════════════════════════════════════════════

    # -- Battery voltage --
    if (t.battery_voltage or 0) > cal_overvoltage:
        checks.append(_check(
            "BAT_OVERVOLTAGE", "Battery & BMS", "Battery Pack Voltage", t.battery_voltage, "V", "critical",
            "Battery voltage is too high",
            f"Pack voltage of {(t.battery_voltage or 0):.1f}V is above the safe limit of {cal_overvoltage:.0f}V.",
            "Stop charging immediately and have the battery management system (BMS) inspected.",
            "Rs.10,000 - Rs.50,000", "Continued overvoltage can permanently damage battery cells and is a fire risk.",
            normal_range=f"< {cal_overvoltage:.0f} V"))
    elif (t.battery_voltage or 0) < cal_undervoltage:
        checks.append(_check(
            "BAT_UNDERVOLTAGE", "Battery & BMS", "Battery Pack Voltage", t.battery_voltage, "V", "critical",
            "Battery voltage is too low",
            f"Pack voltage of {(t.battery_voltage or 0):.1f}V is below the safe limit of {cal_undervoltage:.0f}V.",
            "Charge the vehicle and have the battery health checked at a service centre.",
            "Rs.5,000 - Rs.30,000", "The vehicle may shut down unexpectedly and the battery could degrade faster.",
            normal_range=f"> {cal_undervoltage:.0f} V"))
    else:
        checks.append(_check(
            "BAT_OVERVOLTAGE", "Battery & BMS", "Battery Pack Voltage", t.battery_voltage, "V", "ok",
            "Battery voltage is normal",
            f"Pack voltage is {(t.battery_voltage or 0):.1f}V, within the {cal_undervoltage:.0f}-{cal_overvoltage:.0f}V safe range.",
            normal_range=f"{cal_undervoltage:.0f} - {cal_overvoltage:.0f} V"))

    # -- Battery current (overcurrent) --
    if abs(t.battery_current or 0) > cal_overcurrent:
        checks.append(_check(
            "BAT_OVERCURRENT", "Battery & BMS", "Battery Current", t.battery_current, "A", "critical",
            "Battery current is too high",
            f"Current draw of {(t.battery_current or 0):.1f}A exceeds the {cal_overcurrent:.0f}A safe limit.",
            "Avoid hard acceleration and have the motor controller checked.",
            "Rs.5,000 - Rs.25,000", "Repeated overcurrent stresses the battery and motor controller, shortening their life.",
            normal_range=f"< {cal_overcurrent:.0f} A"))
    else:
        checks.append(_check(
            "BAT_OVERCURRENT", "Battery & BMS", "Battery Current", t.battery_current, "A", "ok",
            "Battery current is normal",
            f"Current draw of {(t.battery_current or 0):.1f}A is within the {cal_overcurrent:.0f}A limit.",
            normal_range=f"< {cal_overcurrent:.0f} A"))

    # -- Battery temperature --
    if (t.battery_temp or 0) > cal_overtemp:
        checks.append(_check(
            "BAT_OVERTEMP", "Battery & BMS", "Battery Temperature", t.battery_temp, "°C", "critical",
            "Battery is overheating",
            f"Battery temperature of {(t.battery_temp or 0):.1f}°C is above the {cal_overtemp:.0f}°C safe limit.",
            "Park in shade, let the battery cool, and avoid fast charging until it's checked.",
            "Rs.5,000 - Rs.25,000", "Prolonged overheating accelerates battery aging and can trigger a safety shutdown.",
            normal_range=f"< {cal_overtemp:.0f} °C"))
    elif (t.battery_temp or 0) < cal_undertemp:
        checks.append(_check(
            "BAT_UNDERTEMP", "Battery & BMS", "Battery Temperature", t.battery_temp, "°C", "warning",
            "Battery is very cold",
            f"Battery temperature of {(t.battery_temp or 0):.1f}°C is below {cal_undertemp:.0f}°C.",
            "Allow the battery to warm up before fast charging or hard acceleration.",
            "Rs.0 (no repair needed)", "Charging/driving a very cold battery hard can reduce its lifespan over time.",
            normal_range=f"> {cal_undertemp:.0f} °C"))
    else:
        checks.append(_check(
            "BAT_OVERTEMP", "Battery & BMS", "Battery Temperature", t.battery_temp, "°C", "ok",
            "Battery temperature is normal",
            f"Battery temperature is {(t.battery_temp or 0):.1f}°C, within the safe {cal_undertemp:.0f} to {cal_overtemp:.0f}°C range.",
            normal_range=f"{cal_undertemp:.0f} to {cal_overtemp:.0f} °C"))

    # -- State of Charge --
    if (t.soc or 0) < cal_soc_critical:
        checks.append(_check(
            "SOC_LEVEL", "Battery & BMS", "Battery Charge (SOC)", t.soc, "%", "critical",
            "Battery is critically low",
            f"Charge level is {(t.soc or 0):.1f}%, below the critical {cal_soc_critical:.0f}% threshold.",
            "Charge the vehicle immediately — find the nearest charging point.",
            "Rs.0 (charging cost only)", "The vehicle may strand you with no power if you continue driving.",
            normal_range=f"> {cal_soc_warning:.0f} %"))
    elif (t.soc or 0) < cal_soc_warning:
        checks.append(_check(
            "SOC_LEVEL", "Battery & BMS", "Battery Charge (SOC)", t.soc, "%", "warning",
            "Battery is getting low",
            f"Charge level is {(t.soc or 0):.1f}%, below the {cal_soc_warning:.0f}% warning threshold.",
            "Plan to charge within the next 30 minutes.",
            "Rs.0 (charging cost only)", "Range will keep dropping — better to charge soon than risk running out.",
            normal_range=f"> {cal_soc_warning:.0f} %"))
    else:
        checks.append(_check(
            "SOC_LEVEL", "Battery & BMS", "Battery Charge (SOC)", t.soc, "%", "ok",
            "Battery charge is healthy",
            f"Charge level is {(t.soc or 0):.1f}%, comfortably above the {cal_soc_warning:.0f}% warning threshold.",
            normal_range=f"> {cal_soc_warning:.0f} %"))

    # -- State of Health --
    if (t.soh or 0) < cal_soh_critical:
        checks.append(_check(
            "SOH_LEVEL", "Battery & BMS", "Battery Health (SOH)", t.soh, "%", "critical",
            "Battery has degraded significantly",
            f"Battery health is at {(t.soh or 0):.1f}%, below the {cal_soh_critical:.0f}% critical threshold — it holds noticeably less charge than when new.",
            "Book a battery health inspection; pack replacement may be needed.",
            "Rs.1,50,000 - Rs.4,00,000 (pack replacement)", "Range will continue to shrink and the battery is more likely to develop further faults.",
            normal_range=f"> {cal_soh_warning:.0f} %"))
    elif (t.soh or 0) < cal_soh_warning:
        checks.append(_check(
            "SOH_LEVEL", "Battery & BMS", "Battery Health (SOH)", t.soh, "%", "warning",
            "Battery health is gradually declining",
            f"Battery health is at {(t.soh or 0):.1f}%, below the {cal_soh_warning:.0f}% threshold — this is normal wear, but worth monitoring.",
            "No action needed yet — keep an eye on this at your next service.",
            "Rs.0 (monitor only)", "Gradual capacity loss is normal, but a faster-than-usual decline can mean an early pack inspection helps.",
            normal_range=f"> {cal_soh_warning:.0f} %"))
    else:
        checks.append(_check(
            "SOH_LEVEL", "Battery & BMS", "Battery Health (SOH)", t.soh, "%", "ok",
            "Battery health is excellent",
            f"Battery health is at {(t.soh or 0):.1f}% of original capacity — like new.",
            normal_range=f"> {cal_soh_warning:.0f} %"))

    # -- Cell balance --
    if cell_imbalance_mv > cal_cell_imbalance:
        checks.append(_check(
            "CELL_IMBALANCE", "Battery & BMS", "Cell Voltage Imbalance", round(cell_imbalance_mv, 1), "mV", "warning",
            "Battery cells are slightly out of balance",
            f"The gap between the highest and lowest cell voltage is {cell_imbalance_mv:.1f}mV, above the {cal_cell_imbalance:.0f}mV threshold.",
            "Have the BMS run a cell-balancing cycle at your next service.",
            "Rs.8,000 - Rs.20,000 (BMS service)", "Left unaddressed, the weakest cell wears out faster and reduces overall pack life.",
            normal_range=f"< {cal_cell_imbalance:.0f} mV"))
    else:
        checks.append(_check(
            "CELL_IMBALANCE", "Battery & BMS", "Cell Voltage Imbalance", round(cell_imbalance_mv, 1), "mV", "ok",
            "Battery cells are well balanced",
            f"Cell voltage spread is {cell_imbalance_mv:.1f}mV, within the {cal_cell_imbalance:.0f}mV healthy range.",
            normal_range=f"< {cal_cell_imbalance:.0f} mV"))

    # -- Individual cell voltage range --
    cell_v_low_thresh = cal_cell_v_min - 0.1
    cell_v_high_thresh = cal_cell_v_max + 0.03
    if (t.cell_voltage_min or 0) < cell_v_low_thresh or (t.cell_voltage_max or 0) > cell_v_high_thresh:
        checks.append(_check(
            "CELL_VOLTAGE_RANGE", "Battery & BMS", "Individual Cell Voltage",
            round(t.cell_voltage_min or 0, 3) if (t.cell_voltage_min or 0) < cell_v_low_thresh else round(t.cell_voltage_max or 0, 3),
            "V", "warning",
            "A battery cell is outside its safe voltage range",
            f"Cell voltages range {(t.cell_voltage_min or 0):.3f}V - {(t.cell_voltage_max or 0):.3f}V, outside the {cal_cell_v_min:.1f}-{cal_cell_v_max:.1f}V design range.",
            "Have the BMS and affected cell group inspected.",
            "Rs.8,000 - Rs.20,000 (BMS service)", "An out-of-range cell ages faster and can eventually trigger a BMS shutdown.",
            normal_range=f"{cal_cell_v_min:.1f} - {cal_cell_v_max:.1f} V"))
    else:
        checks.append(_check(
            "CELL_VOLTAGE_RANGE", "Battery & BMS", "Individual Cell Voltage",
            f"{(t.cell_voltage_min or 0):.3f}-{(t.cell_voltage_max or 0):.3f}", "V", "ok",
            "Cell voltages are within design range",
            f"All cells are between {(t.cell_voltage_min or 0):.3f}V and {(t.cell_voltage_max or 0):.3f}V, within the {cal_cell_v_min:.1f}-{cal_cell_v_max:.1f}V design range.",
            normal_range=f"{cal_cell_v_min:.1f} - {cal_cell_v_max:.1f} V"))

    # ══════════════════════════════════════════════════════════════
    # MOTOR & POWERTRAIN
    # ══════════════════════════════════════════════════════════════

    # -- Coolant temperature --
    if (t.coolant_temp or 0) > cal_coolant_temp:
        checks.append(_check(
            "COOLANT_OVERTEMP", "Motor & Powertrain", "Coolant Temperature", t.coolant_temp, "°C", "critical",
            "Motor/inverter coolant is overheating",
            f"Coolant temperature of {(t.coolant_temp or 0):.1f}°C exceeds the {cal_coolant_temp:.0f}°C safe limit.",
            "Stop the vehicle, let it cool down, and have the cooling system inspected.",
            "Rs.3,000 - Rs.20,000", "Continued overheating can damage the motor and inverter.",
            normal_range=f"< {cal_coolant_temp:.0f} °C"))
    else:
        checks.append(_check(
            "COOLANT_OVERTEMP", "Motor & Powertrain", "Coolant Temperature", t.coolant_temp, "°C", "ok",
            "Coolant temperature is normal",
            f"Coolant temperature is {(t.coolant_temp or 0):.1f}°C, within the {cal_coolant_temp:.0f}°C limit.",
            normal_range=f"< {cal_coolant_temp:.0f} °C"))

    # -- Motor speed --
    if (t.rpm or 0) > cal_motor_speed:
        checks.append(_check(
            "MOTOR_OVERSPEED", "Motor & Powertrain", "Motor Speed", t.rpm, "RPM", "critical",
            "Motor is over-speeding",
            f"Motor speed of {(t.rpm or 0):.0f} RPM exceeds the {cal_motor_speed:.0f} RPM safe limit.",
            "Ease off the accelerator and have the motor controller checked.",
            "Rs.5,000 - Rs.25,000", "Sustained over-speed can damage motor bearings and the inverter.",
            normal_range=f"< {cal_motor_speed:.0f} RPM"))
    else:
        checks.append(_check(
            "MOTOR_OVERSPEED", "Motor & Powertrain", "Motor Speed", t.rpm, "RPM", "ok",
            "Motor speed is normal",
            f"Motor speed of {(t.rpm or 0):.0f} RPM is within the {cal_motor_speed:.0f} RPM limit.",
            normal_range=f"< {cal_motor_speed:.0f} RPM"))

    # -- Motor torque --
    if (t.motor_torque or 0) > cal_motor_torque:
        checks.append(_check(
            "MOTOR_OVERTORQUE", "Motor & Powertrain", "Motor Torque", t.motor_torque, "Nm", "critical",
            "Motor torque is too high",
            f"Motor torque of {(t.motor_torque or 0):.1f}Nm exceeds the {cal_motor_torque:.0f}Nm safe limit.",
            "Avoid full-throttle acceleration and have the motor controller checked.",
            "Rs.5,000 - Rs.25,000", "Repeated over-torque events stress the drivetrain and gearbox.",
            normal_range=f"< {cal_motor_torque:.0f} Nm"))
    else:
        checks.append(_check(
            "MOTOR_OVERTORQUE", "Motor & Powertrain", "Motor Torque", t.motor_torque, "Nm", "ok",
            "Motor torque is normal",
            f"Motor torque of {(t.motor_torque or 0):.1f}Nm is within the {cal_motor_torque:.0f}Nm limit.",
            normal_range=f"< {cal_motor_torque:.0f} Nm"))

    # -- Vehicle speed --
    if (t.speed or 0) > cal_vehicle_speed:
        checks.append(_check(
            "VEHICLE_OVERSPEED", "Motor & Powertrain", "Vehicle Speed", t.speed, "km/h", "warning",
            "Vehicle is over its rated top speed",
            f"Speed of {(t.speed or 0):.1f} km/h exceeds the rated {cal_vehicle_speed:.0f} km/h top speed.",
            "Reduce speed — this is a driving advisory, not a fault.",
            "Rs.0 (no repair needed)", "Driving above the rated top speed increases tyre, brake, and range strain.",
            normal_range=f"< {cal_vehicle_speed:.0f} km/h"))
    else:
        checks.append(_check(
            "VEHICLE_OVERSPEED", "Motor & Powertrain", "Vehicle Speed", t.speed, "km/h", "ok",
            "Vehicle speed is normal",
            f"Speed of {(t.speed or 0):.1f} km/h is within the {cal_vehicle_speed:.0f} km/h rated top speed.",
            normal_range=f"< {cal_vehicle_speed:.0f} km/h"))

    # -- Inverter temperature --
    if (t.inverter_temp or 0) > cal_inverter_temp:
        checks.append(_check(
            "INVERTER_OVERTEMP", "Motor & Powertrain", "Inverter Temperature", t.inverter_temp, "°C", "critical",
            "Inverter is overheating",
            f"Inverter temperature of {(t.inverter_temp or 0):.1f}°C exceeds the {cal_inverter_temp:.0f}°C safe limit.",
            "Reduce load and have the cooling system inspected.",
            "Rs.10,000 - Rs.40,000", "Sustained overheating can damage power electronics and trigger a drive shutdown.",
            normal_range=f"< {cal_inverter_temp:.0f} °C"))
    else:
        checks.append(_check(
            "INVERTER_OVERTEMP", "Motor & Powertrain", "Inverter Temperature", t.inverter_temp, "°C", "ok",
            "Inverter temperature is normal",
            f"Inverter temperature is {(t.inverter_temp or 0):.1f}°C, within the {cal_inverter_temp:.0f}°C limit.",
            normal_range=f"< {cal_inverter_temp:.0f} °C"))

    # -- Regen braking level --
    if (t.regen_brake_level or 0) > cal_regen_max:
        checks.append(_check(
            "REGEN_LEVEL", "Motor & Powertrain", "Regen Braking Level", t.regen_brake_level, "%", "warning",
            "Regenerative braking is at its limit",
            f"Regen level of {(t.regen_brake_level or 0):.1f}% exceeds the {cal_regen_max:.0f}% design maximum.",
            "No action needed — the system will automatically blend in mechanical braking.",
            "Rs.0 (no repair needed)", "None — this is an informational reading during hard braking.",
            normal_range=f"< {cal_regen_max:.0f} %"))
    else:
        checks.append(_check(
            "REGEN_LEVEL", "Motor & Powertrain", "Regen Braking Level", t.regen_brake_level, "%", "ok",
            "Regenerative braking is normal",
            f"Regen level of {(t.regen_brake_level or 0):.1f}% is within the {cal_regen_max:.0f}% design range.",
            normal_range=f"< {cal_regen_max:.0f} %"))

    # -- Power output --
    if abs(power_kw) > cal_power_max:
        checks.append(_check(
            "POWER_OUTPUT", "Motor & Powertrain", "Power Output", round(power_kw, 1), "kW", "warning",
            "Power output is unusually high",
            f"Instantaneous power of {power_kw:.1f}kW exceeds the {cal_power_max:.0f}kW design maximum.",
            "Have the motor controller checked at your next service.",
            "Rs.5,000 - Rs.25,000", "Repeated extreme power draws can shorten motor and battery life.",
            normal_range=f"< {cal_power_max:.0f} kW"))
    else:
        checks.append(_check(
            "POWER_OUTPUT", "Motor & Powertrain", "Power Output", round(power_kw, 1), "kW", "ok",
            "Power output is normal",
            f"Instantaneous power of {power_kw:+.1f}kW is within the {cal_power_max:.0f}kW design range.",
            normal_range=f"< {cal_power_max:.0f} kW"))

    # ══════════════════════════════════════════════════════════════
    # RANGE & EFFICIENCY
    # ══════════════════════════════════════════════════════════════

    # -- Estimated range --
    if (t.estimated_range_km or 0) < 30:
        checks.append(_check(
            "RANGE_LOW", "Range & Efficiency", "Estimated Range", t.estimated_range_km, "km", "critical",
            "Range is critically low",
            f"Only {(t.estimated_range_km or 0):.0f}km of estimated range remains.",
            "Charge the vehicle as soon as possible — avoid long trips until charged.",
            "Rs.0 (charging cost only)", "You may not reach your destination without charging.",
            normal_range="> 50 km"))
    elif (t.estimated_range_km or 0) < 50:
        checks.append(_check(
            "RANGE_LOW", "Range & Efficiency", "Estimated Range", t.estimated_range_km, "km", "warning",
            "Range is getting low",
            f"Estimated range is {(t.estimated_range_km or 0):.0f}km.",
            "Plan your next charging stop.",
            "Rs.0 (charging cost only)", "Range anxiety on longer trips — better to top up soon.",
            normal_range="> 50 km"))
    else:
        checks.append(_check(
            "RANGE_LOW", "Range & Efficiency", "Estimated Range", t.estimated_range_km, "km", "ok",
            "Range is healthy",
            f"Estimated range is {(t.estimated_range_km or 0):.0f}km — plenty for typical trips.",
            normal_range="> 50 km"))

    # -- Energy consumption --
    if (t.energy_per_100km or 0) > cal_energy_max:
        checks.append(_check(
            "ENERGY_CONSUMPTION", "Range & Efficiency", "Energy Use /100km", t.energy_per_100km, "kWh", "warning",
            "Driving efficiency is currently low",
            f"Current consumption of {(t.energy_per_100km or 0):.1f}kWh/100km is above the {cal_energy_max:.0f}kWh/100km design reference.",
            "Smoother acceleration and braking will improve efficiency — no repair needed.",
            "Rs.0 (driving tip)", "Sustained high consumption will reduce your real-world range below the rated figure.",
            normal_range=f"< {cal_energy_max:.0f} kWh/100km"))
    else:
        checks.append(_check(
            "ENERGY_CONSUMPTION", "Range & Efficiency", "Energy Use /100km", t.energy_per_100km, "kWh", "ok",
            "Driving efficiency is good",
            f"Current consumption of {(t.energy_per_100km or 0):.1f}kWh/100km is within the {cal_energy_max:.0f}kWh/100km design reference.",
            normal_range=f"< {cal_energy_max:.0f} kWh/100km"))

    # -- Charging fault: plugged in but no current flowing while not full --
    if t.charging_status == 1 and (t.charging_current or 0) <= 0.5 and (t.soc or 0) < 99.9:
        checks.append(_check(
            "CHARGING_FAULT", "Charging", "Charging Current", t.charging_current, "A", "warning",
            "Charger isn't delivering power",
            f"The vehicle shows 'plugged in' but charging current is {(t.charging_current or 0):.1f}A while the battery is only {(t.soc or 0):.1f}% charged.",
            "Check the charging cable connection, or try a different charging point.",
            "Rs.1,500 - Rs.8,000 (charging port/onboard charger inspection)", "The battery won't charge until this is resolved.",
            normal_range="> 0 A while plugged in and < 100% SOC"))
    else:
        checks.append(_check(
            "CHARGING_FAULT", "Charging", "Charging System", "Normal", "", "ok",
            "Charging system is working normally",
            "No charging faults detected.",
            normal_range="Normal"))

    # ══════════════════════════════════════════════════════════════
    # BRAKES & TYRES
    # ══════════════════════════════════════════════════════════════

    # -- Brake pad wear --
    wear = t.brake_pad_wear_pct or 0
    if wear >= 80:
        checks.append(_check(
            "BRAKE_PAD_WEAR", "Brakes & Tyres", "Brake Pad Wear", wear, "%", "critical",
            "Brake pads are worn out",
            f"Brake pads are {wear:.1f}% worn (replace at 80%).",
            "Replace brake pads as soon as possible.",
            "Rs.3,000 - Rs.5,000", "Worn pads increase stopping distance and can damage brake discs.",
            normal_range="< 80 %"))
    elif wear >= 60:
        checks.append(_check(
            "BRAKE_PAD_WEAR", "Brakes & Tyres", "Brake Pad Wear", wear, "%", "warning",
            "Brake pads are wearing down",
            f"Brake pads are {wear:.1f}% worn.",
            "Plan a brake pad replacement at your next service.",
            "Rs.3,000 - Rs.5,000", "No immediate risk, but pads will need replacing soon.",
            normal_range="< 80 %"))
    else:
        checks.append(_check(
            "BRAKE_PAD_WEAR", "Brakes & Tyres", "Brake Pad Wear", wear, "%", "ok",
            "Brake pads are in good condition",
            f"Brake pads are {wear:.1f}% worn — plenty of life left.",
            normal_range="< 80 %"))

    # -- Brake fluid level --
    fluid = t.brake_fluid_level_pct or 0
    if fluid < 70:
        checks.append(_check(
            "BRAKE_FLUID", "Brakes & Tyres", "Brake Fluid Level", fluid, "%", "warning",
            "Brake fluid is low",
            f"Brake fluid level is {fluid:.1f}%, below the 70% recommended level.",
            "Top up brake fluid at your next service.",
            "Rs.500 - Rs.1,500", "Low brake fluid can lead to a softer brake pedal and reduced braking performance.",
            normal_range="> 70 %"))
    else:
        checks.append(_check(
            "BRAKE_FLUID", "Brakes & Tyres", "Brake Fluid Level", fluid, "%", "ok",
            "Brake fluid level is normal",
            f"Brake fluid level is {fluid:.1f}%.",
            normal_range="> 70 %"))

    # -- Tyre pressures --
    tyre_labels = {
        "tyre_pressure_fl": "Front Left",
        "tyre_pressure_fr": "Front Right",
        "tyre_pressure_rl": "Rear Left",
        "tyre_pressure_rr": "Rear Right",
    }
    for field, label in tyre_labels.items():
        psi = getattr(t, field, None) or 0
        if not (28 <= psi <= 36):
            checks.append(_check(
                f"TYRE_{field.upper()}", "Brakes & Tyres", f"Tyre Pressure ({label})", round(psi, 1), "PSI", "warning",
                f"{label} tyre pressure is out of range",
                f"{label} tyre is at {psi:.1f} PSI, outside the recommended 28-36 PSI range.",
                "Check and adjust tyre pressure at a fuel station or service centre.",
                "Rs.0 - Rs.200 (air top-up)", "Incorrect tyre pressure affects range, handling, and tyre wear.",
                normal_range="28 - 36 PSI"))
        else:
            checks.append(_check(
                f"TYRE_{field.upper()}", "Brakes & Tyres", f"Tyre Pressure ({label})", round(psi, 1), "PSI", "ok",
                f"{label} tyre pressure is normal",
                f"{label} tyre is at {psi:.1f} PSI, within the 28-36 PSI range.",
                normal_range="28 - 36 PSI"))

    # ══════════════════════════════════════════════════════════════
    # 12V & AUXILIARY SYSTEMS
    # ══════════════════════════════════════════════════════════════

    # -- 12V auxiliary battery --
    aux_v = t.aux_battery_voltage or 0
    if aux_v < 12.0:
        checks.append(_check(
            "AUX_BATTERY", "12V & Auxiliary", "12V Battery Voltage", aux_v, "V", "critical",
            "12V battery is weak",
            f"12V auxiliary battery voltage is {aux_v:.2f}V, below the 12.0V healthy minimum.",
            "Have the 12V battery tested and replaced if needed. A jump-start may be required.",
            "Rs.3,500 - Rs.5,000", "A weak 12V battery can prevent the vehicle from powering on at all.",
            normal_range="> 12.0 V"))
    else:
        checks.append(_check(
            "AUX_BATTERY", "12V & Auxiliary", "12V Battery Voltage", aux_v, "V", "ok",
            "12V battery is healthy",
            f"12V auxiliary battery voltage is {aux_v:.2f}V.",
            normal_range="> 12.0 V"))

    # -- DC-DC converter temperature --
    dcdc = t.dcdc_converter_temp or 0
    if dcdc > 70:
        checks.append(_check(
            "DCDC_TEMP", "12V & Auxiliary", "DC-DC Converter Temperature", dcdc, "°C", "warning",
            "DC-DC converter is running hot",
            f"DC-DC converter temperature is {dcdc:.1f}°C, above the 70°C comfort threshold.",
            "Have the DC-DC converter and its cooling checked at your next service.",
            "Rs.4,000 - Rs.15,000", "Sustained high temperatures can shorten the converter's life and affect 12V supply.",
            normal_range="< 70 °C"))
    else:
        checks.append(_check(
            "DCDC_TEMP", "12V & Auxiliary", "DC-DC Converter Temperature", dcdc, "°C", "ok",
            "DC-DC converter temperature is normal",
            f"DC-DC converter temperature is {dcdc:.1f}°C.",
            normal_range="< 70 °C"))

    # -- Washer fluid --
    washer = t.washer_fluid_level_pct or 0
    if washer < 20:
        checks.append(_check(
            "WASHER_FLUID", "12V & Auxiliary", "Washer Fluid Level", washer, "%", "warning",
            "Washer fluid is low",
            f"Windshield washer fluid is at {washer:.1f}%.",
            "Top up washer fluid — available at any fuel station or service centre.",
            "Rs.100 - Rs.300", "You may run out of washer fluid when you need to clean the windshield.",
            normal_range="> 20 %"))
    else:
        checks.append(_check(
            "WASHER_FLUID", "12V & Auxiliary", "Washer Fluid Level", washer, "%", "ok",
            "Washer fluid level is normal",
            f"Windshield washer fluid is at {washer:.1f}%.",
            normal_range="> 20 %"))

    # ── Summary ──────────────────────────────────────────────────
    critical_count = sum(1 for c in checks if c["status"] == "critical")
    warning_count = sum(1 for c in checks if c["status"] == "warning")
    ok_count = sum(1 for c in checks if c["status"] == "ok")

    return {
        "vehicle_id": vehicle_id,
        "timestamp": str(t.timestamp),
        "total_checks": len(checks),
        "checks": checks,
        "critical_count": critical_count,
        "warning_count": warning_count,
        "ok_count": ok_count,
    }