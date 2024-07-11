from fastapi import  WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.message_pipeline=[]

    async def connect(self, websocket: WebSocket, user: int) -> bool:
            await websocket.accept()
            self.active_connections[user] = websocket
            return True
        
    async def disconnect(self, user: int):
        if user in self.active_connections:
            websocket = self.active_connections.pop(user)
            await websocket.close()

    async def send_message_to_user(self, message: str, receiver: int,sender:int):
        if receiver in self.active_connections:
            websocket = self.active_connections[receiver]
            await websocket.send_text(message)
        
             

