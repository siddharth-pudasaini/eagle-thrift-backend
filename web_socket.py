from fastapi import  WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, token: str) -> bool:
            await websocket.accept()
            self.active_connections[token] = websocket
            return True
        
    async def disconnect(self, token: str):
        if token in self.active_connections:
            websocket = self.active_connections.pop(token)
            await websocket.close()

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_message_to_user(self, message: str, receiver: str):
        if receiver in self.active_connections:
            websocket = self.active_connections[receiver]
            await websocket.send_text(message)
