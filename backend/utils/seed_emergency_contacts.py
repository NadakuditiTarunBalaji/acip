"""
Seed demo Emergency Contacts + Nearby Devices for VEH001 (Day 18 / C4).

Run once:
    python -m backend.utils.seed_emergency_contacts
"""
from backend.config.database import SessionLocal
from backend.models.emergency_contact import EmergencyContact
from backend.models.nearby_device import NearbyDevice

# Default starting point used by the CAN simulator (Chennai) — Karthik's
# demo phone starts here too; the demo-trigger endpoint moves it next to
# the vehicle's actual live position each time you click "Simulate Crash."
START_LAT = 13.0827
START_LON = 80.2707


def seed_emergency_contacts():
    db = SessionLocal()
    try:
        if db.query(EmergencyContact).filter(EmergencyContact.vehicle_id == "VEH001").count() == 0:
            contacts = [
                EmergencyContact(
                    vehicle_id="VEH001", name="Naresh Reddy", relationship="Self",
                    phone="9148732715", priority=1
                ),
                EmergencyContact(
                    vehicle_id="VEH001", name="Karthik", relationship="Friend",
                    phone="9123564326", priority=2
                ),
            ]
            db.add_all(contacts)
            db.commit()
            print(f"✅ Emergency contacts seeded: {len(contacts)} records for VEH001")
        else:
            print("⏭️  Emergency contacts already seeded for VEH001")

        if db.query(NearbyDevice).filter(NearbyDevice.owner_name == "Karthik").count() == 0:
            device = NearbyDevice(
                owner_name="Karthik", phone="9123564326",
                gps_lat=START_LAT, gps_lon=START_LON,
            )
            db.add(device)
            db.commit()
            print("✅ Nearby device seeded: Karthik's phone")
        else:
            print("⏭️  Nearby device already seeded for Karthik")

        if db.query(NearbyDevice).filter(NearbyDevice.owner_name == "Naresh Reddy").count() == 0:
            device = NearbyDevice(
                owner_name="Naresh Reddy", phone="9148732715",
                gps_lat=START_LAT, gps_lon=START_LON,
            )
            db.add(device)
            db.commit()
            print("✅ Nearby device seeded: Naresh's phone")
        else:
            print("⏭️  Nearby device already seeded for Naresh Reddy")
    finally:
        db.close()


if __name__ == "__main__":
    seed_emergency_contacts()