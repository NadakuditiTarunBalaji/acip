import json
from backend.models.can_frame import CANFrame


class CANService:

    # -------------------------
    # STORE FRAME
    # -------------------------
    @staticmethod
    def store(db, data):

        frame = CANFrame(
            vehicle_id=data.vehicle_id,
            can_id=data.can_id,
            dlc=data.dlc,

            # store full decoded data
            payload=json.dumps(data.decoded_data)
        )

        db.add(frame)
        db.commit()
        db.refresh(frame)

        return frame

    # -------------------------
    # GET LATEST FRAME
    # -------------------------
    @staticmethod
    def get_latest(db, vehicle_id):

        return db.query(CANFrame)\
            .filter(CANFrame.vehicle_id == vehicle_id)\
            .order_by(CANFrame.timestamp.desc())\
            .first()

    # -------------------------
    # GET HISTORY
    # -------------------------
    @staticmethod
    def get_history(db, vehicle_id, limit=50):

        return db.query(CANFrame)\
            .filter(CANFrame.vehicle_id == vehicle_id)\
            .order_by(CANFrame.timestamp.desc())\
            .limit(limit)\
            .all()