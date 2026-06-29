from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class VehicleDataBase(BaseModel):
    rpm: float
    battery_temp: float
    coolant_temp: float
    speed: float


class VehicleDataCreate(VehicleDataBase):
    pass


class VehicleDataResponse(VehicleDataBase):
    id: int
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


class VehicleBase(BaseModel):
    vin: str
    model: str
    manufacturer: str
    year: int
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    model: Optional[str] = None
    manufacturer: Optional[str] = None
    year: Optional[int] = None
    owner_name: Optional[str] = None
    owner_phone: Optional[str] = None


class VehicleResponse(VehicleBase):
    id: int

    class Config:
        from_attributes = True


class VehicleTelemetryBase(BaseModel):
    vehicle_id: str

    # Powertrain / Motor
    rpm: Optional[float] = 0
    speed: Optional[float] = 0
    motor_torque: Optional[float] = 0
    accelerator_position: Optional[float] = 0
    regen_brake_level: Optional[float] = 0

    # Battery
    battery_voltage: Optional[float] = 380
    battery_current: Optional[float] = 0
    battery_temp: Optional[float] = 32
    soc: Optional[float] = 80
    soh: Optional[float] = 96
    cell_voltage_min: Optional[float] = 3.6
    cell_voltage_max: Optional[float] = 3.62

    # Thermal
    coolant_temp: Optional[float] = 30
    inverter_temp: Optional[float] = 35

    # Misc / Tyres
    fuel_level: Optional[float] = 100
    tyre_pressure_fl: Optional[float] = 32
    tyre_pressure_fr: Optional[float] = 32
    tyre_pressure_rl: Optional[float] = 32
    tyre_pressure_rr: Optional[float] = 32

    # Location & Motion
    gps_lat: Optional[float] = 13.0827
    gps_lon: Optional[float] = 80.2707
    heading: Optional[float] = 0
    accel_x: Optional[float] = 0
    accel_y: Optional[float] = 0
    accel_z: Optional[float] = 1.0

    # Odometer & Trip
    odometer_km: Optional[float] = 15000
    trip_distance_km: Optional[float] = 0
    energy_per_100km: Optional[float] = 0
    trip_duration_min: Optional[float] = 0
    avg_speed_kmh: Optional[float] = 0

    # Brake System
    brake_pad_wear_pct: Optional[float] = 35
    brake_fluid_level_pct: Optional[float] = 90

    # Charging & Range
    charging_status: Optional[int] = 0
    charging_current: Optional[float] = 0
    estimated_range_km: Optional[float] = 0
    time_to_full_min: Optional[float] = 0

    # Environment
    ambient_temp: Optional[float] = 30

    # Auxiliary Systems & Climate (Day 15c)
    aux_battery_voltage: Optional[float] = 13.5
    washer_fluid_level_pct: Optional[float] = 85
    cabin_temp: Optional[float] = 28
    ac_setpoint_temp: Optional[float] = 22
    headlamp_status: Optional[int] = 0
    dcdc_converter_temp: Optional[float] = 50


class VehicleTelemetryCreate(VehicleTelemetryBase):
    pass


class VehicleTelemetryResponse(VehicleTelemetryBase):
    id: int
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── Destination / Navigation (Day 15d) ───────────────────────
class DestinationCreate(BaseModel):
    vehicle_id: str = "VEH001"
    dest_name: str
    dest_lat: float
    dest_lon: float


class DestinationResponse(BaseModel):
    vehicle_id: str
    dest_name: str
    dest_lat: float
    dest_lon: float
    status: str
    set_at: Optional[datetime] = None

    class Config:
        from_attributes = True