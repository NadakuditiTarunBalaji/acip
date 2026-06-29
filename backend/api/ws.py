from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json

router = APIRouter(tags=["WebSocket"])

# Store active connections per vehicle
active_connections: Dict[str, List[WebSocket]] = {}


@router.websocket("/ws/vehicle/{vehicle_id}")
async def vehicle_websocket(websocket: WebSocket, vehicle_id: str):
    await websocket.accept()

    # Register connection
    if vehicle_id not in active_connections:
        active_connections[vehicle_id] = []
    active_connections[vehicle_id].append(websocket)

    try:
        while True:
            # Wait for data from client
            data = await websocket.receive_text()
            message = json.loads(data)

            # Broadcast to all connections for this vehicle
            await broadcast(vehicle_id, message)

    except WebSocketDisconnect:
        active_connections[vehicle_id].remove(websocket)


async def broadcast(vehicle_id: str, data: dict):
    if vehicle_id in active_connections:
        dead = []
        for connection in active_connections[vehicle_id]:
            try:
                await connection.send_text(json.dumps(data))
            except Exception:
                dead.append(connection)
        for d in dead:
            active_connections[vehicle_id].remove(d)