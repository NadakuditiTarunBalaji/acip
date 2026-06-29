"""
Add missing calibrations CAL016-CAL027 to DB
Run: python seed_new_calibrations.py
"""
import sqlite3
import os

db_path = os.path.join("database", "sqlite", "acip.db")
if not os.path.exists(db_path):
    print(f"ERROR: DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)

new_calibrations = [
    ("CAL016", "Accelerator_Position_Max",      100,   "%"),
    ("CAL017", "Power_Output_Max",              300,   "kW"),
    ("CAL018", "Energy_Consumption_Max",         25,   "kWh"),
    ("CAL019", "Drive_Mode_Valid_Range",          4,   "mode"),
    ("CAL020", "Charging_Status_Timeout",         1,   "s"),
    ("CAL021", "Motor_Current_Max",             300,   "A"),
    ("CAL022", "Motor_Voltage_Max",             450,   "V"),
    ("CAL023", "Range_Estimation_Accuracy",       5,   "%"),
    ("CAL024", "Torque_Request_Max",            350,   "Nm"),
    ("CAL025", "Fault_DTC_Trigger_Delay_Max",  100,   "ms"),
    ("CAL026", "Cell_Voltage_Min",              3.0,   "V"),
    ("CAL027", "Cell_Voltage_Max",              4.2,   "V"),
]

print("=== Adding New Calibrations ===")
added   = 0
skipped = 0

for cal_id, parameter, value, unit in new_calibrations:
    existing = conn.execute(
        "SELECT cal_id FROM calibrations WHERE cal_id=?", (cal_id,)
    ).fetchone()

    if existing:
        # Update to correct value
        conn.execute(
            "UPDATE calibrations SET value=?, parameter=?, unit=? WHERE cal_id=?",
            (value, parameter, unit, cal_id)
        )
        print(f"  Updated {cal_id} = {value} {unit} ({parameter})")
        skipped += 1
    else:
        conn.execute(
            "INSERT INTO calibrations (cal_id, parameter, value, unit) VALUES (?,?,?,?)",
            (cal_id, parameter, value, unit)
        )
        print(f"  Added   {cal_id} = {value} {unit} ({parameter})")
        added += 1

conn.commit()

print(f"\n=== Done! Added: {added} | Updated: {skipped} ===")
print("\n=== All Calibrations in DB ===")
rows = conn.execute(
    "SELECT cal_id, parameter, value, unit FROM calibrations ORDER BY cal_id"
).fetchall()
for r in rows:
    print(f"  {r[0]} | {r[1]} | {r[2]} {r[3]}")

conn.close()
print("\n✅ Restart server and test again!")