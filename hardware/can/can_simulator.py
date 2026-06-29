"""
ACIP-X1 — CAN Simulator (Day 15 / C1 + Day 15b "Crucial Data" additions)

Simulates a realistic EV driving cycle and posts live telemetry to the
backend every 2 seconds via POST /api/telemetry/.

The backend server MUST already be running:
    python -m uvicorn backend.main:app --reload

Run this in a SEPARATE terminal:
    python hardware/can/can_simulator.py

Driving cycle (repeats every 60 seconds):
    0-10s   Idle        — vehicle stopped, parked (RPM=0, speed=0)
    10-25s  Accelerate  — accelerator ramps up, motor spins up
    25-40s  Cruise      — steady speed, light throttle, gentle turns
    40-50s  Brake       — regen braking, decelerating to a full stop
    50-60s  Idle        — vehicle stopped, parked (RPM=0, speed=0)

Charging is NOT part of the regular driving cycle — like a real EV, this
vehicle only charges when it is actually plugged in. That happens via the
Navigation feature: set a destination, the vehicle drives there, and once
it "arrives" it parks and starts charging (tapering off and stopping at
100% SOC, just like a real charger).

All values are clamped to stay within the safety limits already defined
in the project's calibrations (e.g. Battery_Overvoltage_Limit=420V,
Battery_Overcurrent_Limit=300A, Battery_Overtemperature_Limit=45C)
so the simulator represents NORMAL healthy operation.

── Day 15b additions ("crucial data") ──────────────────────────────
  Location & Motion : gps_lat, gps_lon, heading, accel_x, accel_y, accel_z
  Odometer & Trip    : odometer_km, trip_distance_km, energy_per_100km
  Brake System       : brake_pad_wear_pct, brake_fluid_level_pct
  Charging & Range   : charging_status, charging_current, estimated_range_km
  Environment        : ambient_temp
"""

import time
import math
import random
import requests

BASE_URL = "http://localhost:8000"
VEHICLE_ID = "VEH001"
TICK_SECONDS = 2
CYCLE_SECONDS = 60

# Vehicle assumptions used for derived signals
BATTERY_CAPACITY_KWH = 50.0
NUM_CELLS = 96                 # 96s pack (typical for a ~50kWh EV)
PACK_INTERNAL_RESISTANCE = 0.05  # ohms — pack-equivalent IR for voltage sag/rise under load
START_LAT = 13.0827   # Chennai, Tamil Nadu — starting point for the simulated route
START_LON = 80.2707
LEASH_RADIUS_KM = 1.2          # keep the simulated drive within this radius of START (stays on land)
WEATHER_REFRESH_TICKS = 150    # refresh real outdoor temperature every ~5 minutes
ARRIVAL_RADIUS_KM = 0.03        # "arrived" once within ~30m of the destination
DESTINATION_CHECK_TICKS = 1     # how often (in ticks) to poll for a destination

# Persistent state carried across ticks (slowly-changing values)
state = {
    "soc": 80.0,
    "soh": 96.0,
    "battery_temp": 32.0,
    "rpm": 0.0,
    "speed": 0.0,
    "tyre_pressure_fl": 32.0,
    "tyre_pressure_fr": 32.0,
    "tyre_pressure_rl": 32.0,
    "tyre_pressure_rr": 32.0,

    # Day 15b — Location & Motion
    "gps_lat": START_LAT,
    "gps_lon": START_LON,
    "heading": 45.0,
    "accel_z": 1.0,

    # Day 15b — Odometer & Trip
    "odometer_km": 15000.0,
    "trip_distance_km": 0.0,
    "trip_duration_min": 0.0,
    "energy_per_100km": 16.0,

    # Day 15b — Brake System
    "brake_pad_wear_pct": 35.0,
    "brake_fluid_level_pct": 90.0,

    # Day 15b — Environment
    "ambient_temp": 32.0,

    # Day 15c — Auxiliary Systems & Climate
    "aux_battery_voltage": 13.5,
    "washer_fluid_level_pct": 85.0,
    "cabin_temp": 32.0,
    "ac_setpoint_temp": 22.0,
    "dcdc_converter_temp": 50.0,

    # Real outdoor temperature cache (Day 15 polish)
    "real_ambient_temp": None,

    # Navigation / Destination (Day 15d)
    "destination": None,        # (lat, lon, name) or None
    "arrived_marked": False,    # have we told the backend we arrived?
}


def fetch_destination():
    """
    Fetch the destination for VEHICLE_ID from the backend.
    Returns (dest_lat, dest_lon, dest_name, status) or None if no
    destination is set or the backend is unreachable.
    """
    try:
        r = requests.get(f"{BASE_URL}/api/telemetry/destination/{VEHICLE_ID}", timeout=2)
        if r.status_code == 200:
            data = r.json()
            return data["dest_lat"], data["dest_lon"], data["dest_name"], data["status"]
    except Exception:
        pass
    return None


def mark_arrived():
    """Tell the backend that the vehicle has reached its destination."""
    try:
        requests.patch(f"{BASE_URL}/api/telemetry/destination/{VEHICLE_ID}/arrived", timeout=2)
    except Exception:
        pass


def distance_and_bearing(lat1, lon1, lat2, lon2):
    """
    Simple flat-earth distance (km) and bearing (degrees, 0=N/90=E) from
    point 1 to point 2. Accurate enough for short city-scale distances.
    """
    dlat_km = (lat2 - lat1) * 111.0
    dlon_km = (lon2 - lon1) * 111.0 * math.cos(math.radians(lat1))
    distance_km = math.sqrt(dlat_km ** 2 + dlon_km ** 2)
    bearing_deg = math.degrees(math.atan2(dlon_km, dlat_km)) % 360
    return distance_km, bearing_deg


def fetch_real_ambient_temp():
    """
    Fetch the CURRENT real outdoor temperature near START_LAT/START_LON
    using Open-Meteo (free, no API key required).
    Returns a float (°C) on success, or None if unavailable (e.g. no internet).
    Failures are silent and the simulator falls back to its own model.
    """
    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={START_LAT}&longitude={START_LON}&current=temperature_2m"
        )
        r = requests.get(url, timeout=3)
        if r.status_code == 200:
            return float(r.json()["current"]["temperature_2m"])
    except Exception:
        pass
    return None


def get_phase(t):
    """Return the driving phase for the current position in the 60s cycle."""
    pos = t % CYCLE_SECONDS
    if pos < 10:
        return "idle"
    elif pos < 25:
        return "accelerate"
    elif pos < 40:
        return "cruise"
    elif pos < 50:
        return "brake"
    else:
        return "idle"


def step(t):
    # ── Navigation: check for an active destination (Day 15d) ────
    dest = fetch_destination()
    dest_distance_km = None
    dest_bearing = None
    dest_name = None
    if dest:
        dest_lat, dest_lon, dest_name, dest_status = dest
        dest_distance_km, dest_bearing = distance_and_bearing(
            state["gps_lat"], state["gps_lon"], dest_lat, dest_lon
        )
        # IMPORTANT: always verify "arrived" against the vehicle's ACTUAL
        # current distance — don't blindly trust a stored "arrived" status.
        # If the simulator restarts, gps resets to the start point, which
        # may now be far from a destination that was "arrived" in a
        # previous run. In that case, re-navigate there instead of
        # incorrectly sitting in "parked & charging" at the wrong spot.
        if dest_distance_km <= ARRIVAL_RADIUS_KM:
            if dest_status == "active":
                mark_arrived()
            phase = "arrived"
        else:
            phase = "navigate"
    else:
        phase = get_phase(t)

    # Remember "before" values so we can derive rate-based signals (G-force etc.)
    prev_speed = state["speed"]
    prev_heading = state["heading"]

    # ── Accelerator / Regen targets per phase ──────────────────
    if phase in ("idle", "arrived", "charging"):
        accel_target, regen_target, target_rpm = 0, 0, 0
    elif phase == "accelerate":
        accel_target, regen_target, target_rpm = 75, 0, 8500
    elif phase == "cruise":
        accel_target, regen_target, target_rpm = 30, 0, 5500
    elif phase == "brake":
        accel_target, regen_target, target_rpm = 0, 55, 0  # decelerate all the way to a stop
    else:  # navigate
        # Drive towards the destination — slow down as we get closer
        if dest_distance_km > 0.5:
            accel_target, regen_target, target_rpm = 35, 0, 5500
        elif dest_distance_km > 0.15:
            accel_target, regen_target, target_rpm = 15, 10, 2500
        else:
            accel_target, regen_target, target_rpm = 0, 30, 600

    accelerator_position = max(0, min(100, accel_target + random.uniform(-3, 3)))
    regen_brake_level = max(0, min(100, regen_target + random.uniform(-3, 3)))

    # ── Motor torque follows accelerator position ──────────────
    motor_torque = round(accelerator_position / 100 * 320, 1)

    # ── Motor RPM smoothly tracks target, speed derived from RPM ─
    if phase in ("idle", "charging", "arrived"):
        # Vehicle is stationary — snap to a true stop (no residual creep)
        state["rpm"] = 0.0
        state["speed"] = 0.0
    else:
        state["rpm"] += (target_rpm - state["rpm"]) * 0.25
        state["rpm"] = max(0, state["rpm"])
        state["speed"] = round(state["rpm"] / 12000 * 200, 1)

    # ── Charging status & current (CC-CV taper, Day 15 polish) ───
    if phase in ("charging", "arrived"):
        charging_status = 1
        if state["soc"] >= 99.95:
            # Battery full — charger holds, no more current flows
            charging_current = 0.0
        elif state["soc"] >= 80:
            # Constant-current up to 80%, then taper down to ~0 by 100%
            taper = max(0.05, (100 - state["soc"]) / 20)
            charging_current = round(max(2, 60 * taper) + random.uniform(-1, 1), 1)
        else:
            charging_current = round(60 + random.uniform(-2, 2), 1)  # ~60A DC fast charge
    else:
        charging_status = 0
        charging_current = 0.0

    # ── Battery current: + = discharge, - = charge (regen/plug-in) ─
    if phase == "brake":
        battery_current = -round(40 + regen_brake_level / 100 * 60, 1)
    elif phase in ("charging", "arrived"):
        battery_current = -charging_current
    elif phase == "idle":
        battery_current = round(2 + random.uniform(-0.5, 0.5), 1)  # accessories / standby draw
    else:
        battery_current = round(motor_torque / 350 * 250, 1)

    # ── Battery voltage: Open-Circuit-Voltage(SOC) curve + IR drop ──
    # In a real pack, voltage IS the state of charge (the OCV curve) —
    # it sags under discharge and rises under charge due to internal
    # resistance, but the baseline tracks SOC, not the other way round.
    cell_ocv = 3.0 + (state["soc"] / 100) * 1.2  # 3.0V (empty) -> 4.2V (full) per cell
    cell_voltage_avg = cell_ocv - (battery_current * PACK_INTERNAL_RESISTANCE) / NUM_CELLS
    battery_voltage = round(cell_voltage_avg * NUM_CELLS, 1)
    battery_voltage = max(260, min(420, battery_voltage))

    # ── SOC slowly drains with average load (rises while charging/regen) ─
    state["soc"] -= battery_current * 0.0005
    state["soc"] = max(5, min(100, state["soc"]))

    # ── Battery temp drifts toward ambient (+ self-heating under load) ──
    # A parked pack settles a few degrees ABOVE ambient — it doesn't keep
    # "cooling" toward an arbitrary fixed number. In Chennai's heat this
    # means the pack runs warmer on hot days, which is realistic.
    battery_target_temp = state["ambient_temp"] + 3 + abs(battery_current) * 0.05
    state["battery_temp"] += (battery_target_temp - state["battery_temp"]) * 0.03
    state["battery_temp"] = max(15, min(55, state["battery_temp"]))

    # ── Inverter / coolant temps: ambient baseline + load-based rise ─
    # A radiator-cooled loop can't run BELOW ambient without active
    # refrigeration, so on a hot Chennai day these track the real
    # outdoor temperature too (same principle as battery_temp above).
    coolant_temp = round(state["ambient_temp"] + 2 + motor_torque / 350 * 25, 1)
    inverter_temp = round(state["ambient_temp"] + 5 + motor_torque / 350 * 35, 1)

    # ── Cell voltage min/max: same OCV model, plus small imbalance ─
    imbalance_mv = random.uniform(5, 25)
    cell_voltage_max = round(cell_voltage_avg + imbalance_mv / 2000, 4)
    cell_voltage_min = round(cell_voltage_avg - imbalance_mv / 2000, 4)

    # ── Tyre pressures: slow random walk 28-36 PSI ───────────────
    for tyre in ("tyre_pressure_fl", "tyre_pressure_fr", "tyre_pressure_rl", "tyre_pressure_rr"):
        state[tyre] += random.uniform(-0.05, 0.05)
        state[tyre] = max(28, min(36, state[tyre]))

    # ══ Day 15b — "Crucial Data" additions ══════════════════════

    # ── Heading: steer toward destination, else gentle drift/leash ─
    # Turn rate is capped so lateral G stays realistic (<=~0.3g) — a real
    # car can't snap its heading around at speed without slowing down
    # first, so the cap effectively makes it "ease into" sharp turns.
    MAX_LATERAL_G = 0.3
    speed_ms = state["speed"] / 3.6
    if speed_ms > 0.5:
        max_turn_deg = math.degrees((MAX_LATERAL_G * 9.81 * TICK_SECONDS) / speed_ms)
    else:
        max_turn_deg = 90.0  # essentially stationary — free to pivot

    if phase == "navigate":
        heading_diff = ((dest_bearing - state["heading"] + 180) % 360) - 180
        desired_turn = heading_diff * 0.4  # steer towards destination
        desired_turn = max(-max_turn_deg, min(max_turn_deg, desired_turn))
        state["heading"] += desired_turn
    else:
        if phase == "cruise":
            state["heading"] += random.uniform(-3, 3)
        else:
            state["heading"] += random.uniform(-0.5, 0.5)

        # ── GPS leash: steer back towards START if drifting too far ──
        # (keeps the simulated route on land near Chennai instead of
        #  wandering out into the Bay of Bengal over a long demo)
        dlat_km = (state["gps_lat"] - START_LAT) * 111.0
        dlon_km = (state["gps_lon"] - START_LON) * 111.0 * math.cos(math.radians(START_LAT))
        dist_from_start_km = math.sqrt(dlat_km ** 2 + dlon_km ** 2)
        if dist_from_start_km > LEASH_RADIUS_KM:
            bearing_to_start = math.degrees(math.atan2(-dlon_km, -dlat_km)) % 360
            heading_diff = ((bearing_to_start - state["heading"] + 180) % 360) - 180
            turn = heading_diff * 0.3
            turn = max(-max_turn_deg, min(max_turn_deg, turn))
            state["heading"] += turn

    state["heading"] %= 360

    # ── Distance traveled this tick (km) ─────────────────────────
    tick_distance_km = state["speed"] * TICK_SECONDS / 3600

    # ── GPS position: move along current heading ────────────────
    heading_rad = math.radians(state["heading"])
    state["gps_lat"] += (tick_distance_km / 111.0) * math.cos(heading_rad)
    state["gps_lon"] += (tick_distance_km / (111.0 * math.cos(math.radians(state["gps_lat"])))) * math.sin(heading_rad)

    # ── Odometer & trip distance ─────────────────────────────────
    state["odometer_km"] += tick_distance_km
    state["trip_distance_km"] += tick_distance_km

    # ── Trip duration & average speed (trip computer) ─────────────
    state["trip_duration_min"] += TICK_SECONDS / 60.0
    if state["trip_duration_min"] > 0:
        avg_speed_kmh = round(state["trip_distance_km"] / (state["trip_duration_min"] / 60.0), 1)
    else:
        avg_speed_kmh = 0.0

    # ── G-force: longitudinal (accel/brake), lateral (turning), vertical (road) ─
    delta_v_ms = (state["speed"] - prev_speed) / 3.6
    accel_x = round((delta_v_ms / TICK_SECONDS) / 9.81, 3)

    heading_delta = ((state["heading"] - prev_heading + 180) % 360) - 180
    omega = math.radians(heading_delta) / TICK_SECONDS
    accel_y = round((state["speed"] / 3.6 * omega) / 9.81, 3)

    state["accel_z"] += random.uniform(-0.02, 0.02)
    state["accel_z"] = max(0.9, min(1.1, state["accel_z"]))

    # ── Energy consumption (kWh/100km), smoothed ─────────────────
    power_kw = (battery_voltage * battery_current) / 1000
    if tick_distance_km > 0.0001:
        instant_consumption = (power_kw * TICK_SECONDS / 3600) / tick_distance_km * 100
        instant_consumption = max(-10, min(35, instant_consumption))
        state["energy_per_100km"] += (instant_consumption - state["energy_per_100km"]) * 0.1
    state["energy_per_100km"] = max(-10, min(35, state["energy_per_100km"]))

    # ── Brake system: mechanical braking slowly wears pads ───────
    if phase == "brake":
        mechanical_braking = max(0, 100 - regen_brake_level) / 100
        state["brake_pad_wear_pct"] += mechanical_braking * 0.002
    state["brake_pad_wear_pct"] = min(100, state["brake_pad_wear_pct"])

    state["brake_fluid_level_pct"] += random.uniform(-0.005, 0.001)
    state["brake_fluid_level_pct"] = max(60, min(100, state["brake_fluid_level_pct"]))

    # ── Charging & range ──────────────────────────────────────────
    # Range is driven by SOC at a STABLE baseline efficiency, so it falls
    # predictably while driving and only rises while charging — not a
    # noisy function of this instant's acceleration/regen (that's what
    # "Energy Use/Recovered per 100km" is for, shown separately).
    BASELINE_CONSUMPTION_KWH_PER_100KM = 16.0
    estimated_range_km = round((state["soc"] / 100 * BATTERY_CAPACITY_KWH) / BASELINE_CONSUMPTION_KWH_PER_100KM * 100, 1)
    estimated_range_km = max(0, min(450, estimated_range_km))

    # ── Time to full charge ───────────────────────────────────────
    # Uses the ACTUAL current charging power (V x I), so this naturally
    # extends during the CC->CV taper near 100% — same as a real EV's
    # "time to full" display getting longer for the last few percent.
    if charging_current > 0:
        charging_power_kw = battery_voltage * charging_current / 1000
        energy_needed_kwh = (100 - state["soc"]) / 100 * BATTERY_CAPACITY_KWH
        time_to_full_min = round(energy_needed_kwh / charging_power_kw * 60, 1) if charging_power_kw > 0 else 0.0
    else:
        time_to_full_min = 0.0

    # ── Ambient temperature: track real outdoor temp if available ─
    if state["real_ambient_temp"] is not None:
        # Converge towards the real reading + tiny sensor noise
        target = state["real_ambient_temp"]
        state["ambient_temp"] += (target - state["ambient_temp"]) * 0.2 + random.uniform(-0.05, 0.05)
    else:
        # No internet / API unavailable — fall back to a slow random walk
        state["ambient_temp"] += random.uniform(-0.05, 0.05)
    state["ambient_temp"] = max(15, min(48, state["ambient_temp"]))

    # ══ Day 15c — Auxiliary Systems & Climate ═══════════════════

    # ── 12V Auxiliary battery: DC-DC keeps it topped up while driving ─
    state["aux_battery_voltage"] += random.uniform(-0.03, 0.03)
    state["aux_battery_voltage"] = max(12.0, min(14.4, state["aux_battery_voltage"]))

    # ── Washer fluid: negligible drain over a normal trip ────────
    state["washer_fluid_level_pct"] -= random.uniform(0, 0.002)
    state["washer_fluid_level_pct"] = max(0, min(100, state["washer_fluid_level_pct"]))

    # ── Cabin temp: AC slowly pulls cabin towards setpoint ───────
    state["cabin_temp"] += (state["ac_setpoint_temp"] - state["cabin_temp"]) * 0.05
    state["cabin_temp"] += random.uniform(-0.1, 0.1)

    # ── Headlamp status: 0=OK, 1=Fault/Bulb failure ──────────────
    # This is a FAULT flag, not an on/off indicator — the dashboard
    # shows "Fault" (red) when this is 1. Healthy simulator => 0.
    headlamp_status = 0

    # ── DC-DC converter temp: rises with electrical load ─────────
    state["dcdc_converter_temp"] = 45 + abs(battery_current) / 300 * 15 + random.uniform(-0.5, 0.5)
    state["dcdc_converter_temp"] = max(35, min(75, state["dcdc_converter_temp"]))

    payload = {
        "vehicle_id": VEHICLE_ID,
        "rpm": round(state["rpm"], 1),
        "speed": state["speed"],
        "motor_torque": motor_torque,
        "accelerator_position": round(accelerator_position, 1),
        "regen_brake_level": round(regen_brake_level, 1),
        "battery_voltage": battery_voltage,
        "battery_current": battery_current,
        "battery_temp": round(state["battery_temp"], 1),
        "soc": round(state["soc"], 2),
        "soh": round(state["soh"], 1),
        "cell_voltage_min": cell_voltage_min,
        "cell_voltage_max": cell_voltage_max,
        "coolant_temp": coolant_temp,
        "inverter_temp": inverter_temp,
        "fuel_level": 100,
        "tyre_pressure_fl": round(state["tyre_pressure_fl"], 1),
        "tyre_pressure_fr": round(state["tyre_pressure_fr"], 1),
        "tyre_pressure_rl": round(state["tyre_pressure_rl"], 1),
        "tyre_pressure_rr": round(state["tyre_pressure_rr"], 1),

        # Day 15b — Location & Motion
        "gps_lat": round(state["gps_lat"], 6),
        "gps_lon": round(state["gps_lon"], 6),
        "heading": round(state["heading"], 1),
        "accel_x": accel_x,
        "accel_y": accel_y,
        "accel_z": round(state["accel_z"], 3),

        # Day 15b — Odometer & Trip
        "odometer_km": round(state["odometer_km"], 2),
        "trip_distance_km": round(state["trip_distance_km"], 2),
        "energy_per_100km": round(state["energy_per_100km"], 2),
        "trip_duration_min": round(state["trip_duration_min"], 2),
        "avg_speed_kmh": avg_speed_kmh,

        # Day 15b — Brake System
        "brake_pad_wear_pct": round(state["brake_pad_wear_pct"], 2),
        "brake_fluid_level_pct": round(state["brake_fluid_level_pct"], 1),

        # Day 15b — Charging & Range
        "charging_status": charging_status,
        "charging_current": charging_current,
        "estimated_range_km": estimated_range_km,
        "time_to_full_min": time_to_full_min,

        # Day 15b — Environment
        "ambient_temp": round(state["ambient_temp"], 1),

        # Day 15c — Auxiliary Systems & Climate
        "aux_battery_voltage": round(state["aux_battery_voltage"], 2),
        "washer_fluid_level_pct": round(state["washer_fluid_level_pct"], 1),
        "cabin_temp": round(state["cabin_temp"], 1),
        "ac_setpoint_temp": round(state["ac_setpoint_temp"], 1),
        "headlamp_status": headlamp_status,
        "dcdc_converter_temp": round(state["dcdc_converter_temp"], 1),
    }

    nav_info = None
    if dest_name is not None:
        nav_info = {"dest_name": dest_name, "dest_distance_km": dest_distance_km}

    return payload, phase, nav_info


def main():
    print("=" * 64)
    print("  ACIP-X1 CAN Simulator — Customer Mode (C1 + Day 15 polish)")
    print(f"  Posting to {BASE_URL}/api/telemetry/ every {TICK_SECONDS}s")
    print("  Cycle: Idle(10s) -> Accelerate(15s) -> Cruise(15s) -> Brake(10s) -> Idle(10s)")
    print("  Charging only happens when PLUGGED IN — set a destination below,")
    print("  the vehicle drives there, arrives, and starts charging automatically.")
    print("  Includes: GPS/G-force (leashed near start), Odometer/Trip, Brakes,")
    print("            Battery voltage tied to SOC, real outdoor temperature, 12V/AC/etc.")
    print("  Press Ctrl+C to stop")
    print("=" * 64)

    print("Fetching current outdoor temperature...")
    temp = fetch_real_ambient_temp()
    if temp is not None:
        state["real_ambient_temp"] = temp
        state["ambient_temp"] = temp
        print(f"  -> Real outdoor temperature: {temp}°C (will refresh periodically)")
    else:
        print("  -> Could not fetch real temperature (no internet?) — using simulated value")

    t = 0
    while True:
        # Periodically refresh the real outdoor temperature
        if t > 0 and (t // TICK_SECONDS) % WEATHER_REFRESH_TICKS == 0:
            temp = fetch_real_ambient_temp()
            if temp is not None:
                state["real_ambient_temp"] = temp

        payload, phase, nav_info = step(t)
        try:
            r = requests.post(f"{BASE_URL}/api/telemetry/", json=payload, timeout=5)
            if r.status_code == 200:
                charge_flag = "CHG" if payload["charging_status"] == 1 else "---"
                if nav_info:
                    nav_str = f" | -> {nav_info['dest_name']} ({nav_info['dest_distance_km']*1000:.0f}m)"
                else:
                    nav_str = ""
                print(
                    f"[{phase.upper():10}] speed={payload['speed']:5.1f} km/h "
                    f"| rpm={payload['rpm']:6.1f} | torque={payload['motor_torque']:5.1f} Nm "
                    f"| SOC={payload['soc']:5.2f}% | I={payload['battery_current']:6.1f} A "
                    f"| V={payload['battery_voltage']:5.1f} V | T_batt={payload['battery_temp']:4.1f}C "
                    f"| odo={payload['odometer_km']:8.2f}km | range={payload['estimated_range_km']:5.1f}km "
                    f"| pads={payload['brake_pad_wear_pct']:5.2f}% | Gx={payload['accel_x']:+.2f}g "
                    f"| 12V={payload['aux_battery_voltage']:5.2f}V | amb={payload['ambient_temp']:4.1f}C [{charge_flag}]"
                    f"{nav_str}"
                )
            else:
                print(f"⚠️  Server returned {r.status_code}: {r.text}")
        except requests.exceptions.ConnectionError:
            print("❌ Could not connect to backend. Is the server running?")
        except Exception as e:
            print(f"❌ Error: {e}")

        t += TICK_SECONDS
        time.sleep(TICK_SECONDS)


if __name__ == "__main__":
    main()