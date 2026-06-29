"""
ACIP-X1 — Test Scenario Injector (for demo/verification)

Posts a complete telemetry frame representing a chosen scenario, so you
can see exactly how the Live Dashboard and Alerts & Issues tab react.

IMPORTANT: STOP THE CAN SIMULATOR FIRST.
The simulator posts every 2 seconds and will overwrite whatever this
script sends. Stop it (Ctrl+C in its terminal), run this script, then
refresh the dashboard. The injected data will stay until you restart
the simulator.

Usage (from the project root, with the backend server running):
    python -m backend.utils.inject_test_scenario healthy
    python -m backend.utils.inject_test_scenario worst
    python -m backend.utils.inject_test_scenario edge

Scenarios:
    healthy  -> everything comfortably normal (matches simulator defaults)
    worst    -> every one of the 26 checks tripped (critical/warning)
    edge     -> every value sitting exactly AT its threshold boundary,
                to confirm the >/< comparisons are correct (boundary = "ok")
"""
import sys
import requests

BASE_URL = "http://localhost:8000"

# A complete, valid baseline — every field the schema expects.
BASELINE = {
    "vehicle_id": "VEH001",
    "rpm": 2500, "speed": 60, "motor_torque": 90,
    "accelerator_position": 35, "regen_brake_level": 0,
    "battery_voltage": 380, "battery_current": 65, "battery_temp": 35,
    "soc": 80, "soh": 96, "cell_voltage_min": 3.95, "cell_voltage_max": 3.97,
    "coolant_temp": 38, "inverter_temp": 42, "fuel_level": 100,
    "tyre_pressure_fl": 32, "tyre_pressure_fr": 32, "tyre_pressure_rl": 32, "tyre_pressure_rr": 32,
    "gps_lat": 13.0827, "gps_lon": 80.2707, "heading": 45, "accel_x": 0.1, "accel_y": 0.0, "accel_z": 1.0,
    "odometer_km": 15010, "trip_distance_km": 5, "energy_per_100km": 16,
    "trip_duration_min": 8, "avg_speed_kmh": 38,
    "brake_pad_wear_pct": 35, "brake_fluid_level_pct": 90,
    "charging_status": 0, "charging_current": 0, "estimated_range_km": 240, "time_to_full_min": 0,
    "ambient_temp": 32, "aux_battery_voltage": 13.5, "washer_fluid_level_pct": 85,
    "cabin_temp": 28, "ac_setpoint_temp": 22, "headlamp_status": 0, "dcdc_converter_temp": 48,
}

# Every value pushed past its limit -> all 26 checks should fire.
WORST = dict(BASELINE)
WORST.update({
    "coolant_temp": 98,            # > 95 (COOLANT_OVERTEMP)
    "rpm": 12500,                  # > 12000 (MOTOR_OVERSPEED)
    "motor_torque": 360,           # > 350 (MOTOR_OVERTORQUE)
    "speed": 210,                  # > 200 (VEHICLE_OVERSPEED)
    "inverter_temp": 90,           # > 85 (INVERTER_OVERTEMP)
    "regen_brake_level": 75,       # > 70 (REGEN_LEVEL)
    "battery_voltage": 425,        # > 420 (BAT_OVERVOLTAGE, also feeds POWER_OUTPUT)
    "battery_current": 750,        # > 300 (BAT_OVERCURRENT); 425*750/1000=318.75kW > 300 (POWER_OUTPUT)
    "battery_temp": 48,            # > 45 (BAT_OVERTEMP)
    "soc": 5,                      # < 10 (SOC_LEVEL critical)
    "soh": 55,                     # < 60 (SOH_LEVEL critical)
    "cell_voltage_min": 3.5, "cell_voltage_max": 4.25,   # imbalance 750mV > 50 (CELL_IMBALANCE); 4.25 > 4.23 (CELL_VOLTAGE_RANGE)
    "estimated_range_km": 15,      # < 30 (RANGE_LOW critical)
    "energy_per_100km": 32,        # > 25 (ENERGY_CONSUMPTION)
    "charging_status": 1, "charging_current": 0,  # plugged in but no current, soc<99.9 (CHARGING_FAULT)
    "brake_pad_wear_pct": 92,      # >= 80 (BRAKE_PAD_WEAR critical)
    "brake_fluid_level_pct": 45,   # < 70 (BRAKE_FLUID)
    "tyre_pressure_fl": 22, "tyre_pressure_fr": 22, "tyre_pressure_rl": 22, "tyre_pressure_rr": 22,  # < 28 (TYRE x4)
    "aux_battery_voltage": 11.2,   # < 12.0 (AUX_BATTERY critical)
    "dcdc_converter_temp": 78,     # > 70 (DCDC_TEMP)
    "washer_fluid_level_pct": 8,   # < 20 (WASHER_FLUID)
})

# Every value sitting exactly AT the boundary. The engine uses strict
# >/< comparisons, so a value EQUAL to the limit should still read "ok".
EDGE = dict(BASELINE)
EDGE.update({
    "coolant_temp": 95,
    "rpm": 12000,
    "motor_torque": 350,
    "speed": 200,
    "inverter_temp": 85,
    "regen_brake_level": 70,
    "battery_voltage": 420,
    "battery_current": 300,
    "battery_temp": 45,
    "soc": 20,
    "soh": 80,
    "cell_voltage_min": 3.95, "cell_voltage_max": 4.0,   # imbalance exactly 50mV
    "estimated_range_km": 50,
    "energy_per_100km": 25,
    "brake_pad_wear_pct": 80,
    "brake_fluid_level_pct": 70,
    "tyre_pressure_fl": 28, "tyre_pressure_fr": 36, "tyre_pressure_rl": 28, "tyre_pressure_rr": 36,
    "aux_battery_voltage": 12.0,
    "dcdc_converter_temp": 70,
    "washer_fluid_level_pct": 20,
})

# Stopped, critically low battery, not charging — the exact signature
# breakdown_service.check_for_breakdown() looks for. Distinct from
# WORST (which is a moving vehicle with every check tripped) since
# breakdown detection specifically requires speed=0 AND rpm=0.
STRANDED = dict(BASELINE)
STRANDED.update({
    "speed": 0, "rpm": 0, "motor_torque": 0, "accelerator_position": 0,
    "soc": 4.5,                    # < 10 (SOC_LEVEL critical) — the breakdown trigger
    "charging_status": 0, "charging_current": 0,  # not charging — required for breakdown detection
    "estimated_range_km": 8,
})

SCENARIOS = {"healthy": BASELINE, "worst": WORST, "edge": EDGE, "stranded": STRANDED}


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "worst"
    if name not in SCENARIOS:
        print(f"Unknown scenario '{name}'. Choose from: {list(SCENARIOS.keys())}")
        return

    payload = SCENARIOS[name]
    r = requests.post(f"{BASE_URL}/api/telemetry/", json=payload, timeout=5)
    print(f"POST /api/telemetry/ -> {r.status_code}")

    r2 = requests.get(f"{BASE_URL}/api/dashboard/diagnostics", timeout=5)
    diag = r2.json()
    print(f"\nScenario: {name}")
    print(f"  Total checks : {diag['total_checks']}")
    print(f"  Critical     : {diag['critical_count']}")
    print(f"  Warning      : {diag['warning_count']}")
    print(f"  OK           : {diag['ok_count']}")
    print("\nNon-OK checks:")
    for c in diag["checks"]:
        if c["status"] != "ok":
            print(f"  [{c['status'].upper():8}] {c['title']}  (value={c['value']} {c['unit']}, normal={c['normal_range']})")

    print("\nNow refresh the dashboard — this data will stay until the simulator is restarted.")

    if name == "stranded":
        r3 = requests.post(f"{BASE_URL}/api/breakdown/check/{payload['vehicle_id']}", timeout=5)
        print(f"\nPOST /api/breakdown/check/{payload['vehicle_id']} -> {r3.status_code}")
        print(r3.json())


if __name__ == "__main__":
    main()