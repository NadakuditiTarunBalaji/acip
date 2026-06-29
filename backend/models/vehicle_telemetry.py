from sqlalchemy import Column, String, Float, Integer, DateTime
from backend.config.database import Base
from datetime import datetime


class VehicleTelemetry(Base):
    __tablename__ = "vehicle_telemetry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_id = Column(String)

    # ── Powertrain / Motor ──────────────────────────────
    rpm = Column(Float)                    # Motor speed (RPM)
    speed = Column(Float)                  # Vehicle speed (km/h)
    motor_torque = Column(Float)           # Motor torque (Nm)
    accelerator_position = Column(Float)   # Accelerator pedal position (%)
    regen_brake_level = Column(Float)      # Regenerative braking level (%)

    # ── Battery ──────────────────────────────────────────
    battery_voltage = Column(Float)        # Battery pack voltage (V)
    battery_current = Column(Float)        # Battery pack current (A)
    battery_temp = Column(Float)           # Battery pack temperature (C)
    soc = Column(Float)                    # State of Charge (%)
    soh = Column(Float)                    # State of Health (%)
    cell_voltage_min = Column(Float)       # Min cell voltage (V)
    cell_voltage_max = Column(Float)       # Max cell voltage (V)

    # ── Thermal ──────────────────────────────────────────
    coolant_temp = Column(Float)           # Coolant temperature (C)
    inverter_temp = Column(Float)          # Inverter temperature (C)

    # ── Misc / Tyres ─────────────────────────────────────
    fuel_level = Column(Float)
    tyre_pressure_fl = Column(Float)
    tyre_pressure_fr = Column(Float)
    tyre_pressure_rl = Column(Float)
    tyre_pressure_rr = Column(Float)

    # ── Location & Motion (Day 15b) ──────────────────────
    gps_lat = Column(Float)                # GPS latitude
    gps_lon = Column(Float)                # GPS longitude
    heading = Column(Float)                # Compass heading (degrees, 0-360)
    accel_x = Column(Float)                # Longitudinal G-force (accel/brake)
    accel_y = Column(Float)                # Lateral G-force (cornering)
    accel_z = Column(Float)                # Vertical G-force (~1.0g at rest)

    # ── Odometer & Trip (Day 15b) ────────────────────────
    odometer_km = Column(Float)            # Total lifetime distance (km)
    trip_distance_km = Column(Float)       # Distance this trip/session (km)
    energy_per_100km = Column(Float)       # Energy consumption (kWh/100km)
    trip_duration_min = Column(Float)      # Elapsed time this trip/session (minutes)
    avg_speed_kmh = Column(Float)          # Average speed this trip (km/h)

    # ── Brake System (Day 15b) ───────────────────────────
    brake_pad_wear_pct = Column(Float)     # Brake pad wear (0=new, 100=worn out)
    brake_fluid_level_pct = Column(Float)  # Brake fluid reservoir level (%)

    # ── Charging & Range (Day 15b) ───────────────────────
    charging_status = Column(Integer)      # 0=not charging, 1=charging
    charging_current = Column(Float)       # Charging current (A), 0 if not charging
    estimated_range_km = Column(Float)     # Estimated remaining range (km)
    time_to_full_min = Column(Float)       # Estimated time to 100% SOC (minutes), 0 if not charging

    # ── Environment (Day 15b) ────────────────────────────
    ambient_temp = Column(Float)           # Outside air temperature (C)

    # ── Auxiliary Systems & Climate (Day 15c) ────────────
    aux_battery_voltage = Column(Float)    # 12V auxiliary battery voltage (V)
    washer_fluid_level_pct = Column(Float) # Windshield washer fluid level (%)
    cabin_temp = Column(Float)             # Cabin air temperature (C)
    ac_setpoint_temp = Column(Float)       # AC target/setpoint temperature (C)
    headlamp_status = Column(Integer)      # 0=off, 1=on (auto-headlamp, based on time of day)
    dcdc_converter_temp = Column(Float)    # DC-DC converter temperature (C)

    timestamp = Column(DateTime, default=datetime.utcnow)