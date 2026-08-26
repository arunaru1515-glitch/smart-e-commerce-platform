from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):
        self.active_connections = {}

    async def connect(
        self,
        user_id: int,
        websocket: WebSocket
    ):
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)

    def disconnect(
        self,
        user_id: int,
        websocket: WebSocket
    ):
        if user_id in self.active_connections:

            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_to_user(
        self,
        user_id: int,
        message: dict
    ):
        connections = self.active_connections.get(
            user_id,
            []
        )

        disconnected = []

        for websocket in connections:

            try:
                await websocket.send_json(message)

            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            self.disconnect(
                user_id,
                websocket
            )


manager = ConnectionManager()