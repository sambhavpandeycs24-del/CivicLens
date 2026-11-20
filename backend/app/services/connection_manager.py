from collections import defaultdict
from fastapi import WebSocket


class ConnectionManager:
    """In-process WebSocket connection manager for one Uvicorn process."""

    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[user_id].add(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        connections = self._connections.get(user_id)
        if connections is None:
            return
        connections.discard(websocket)
        if not connections:
            self._connections.pop(user_id, None)

    async def broadcast_user(self, user_id: str, payload: dict) -> None:
        stale: list[WebSocket] = []
        for websocket in tuple(self._connections.get(user_id, set())):
            try:
                await websocket.send_json(payload)
            except Exception:
                stale.append(websocket)
        for websocket in stale:
            self.disconnect(user_id, websocket)


connection_manager = ConnectionManager()
