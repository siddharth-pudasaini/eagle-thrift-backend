# websocket_manager.py
from fastapi import WebSocket, WebSocketDisconnect, HTTPException, Depends
from typing import Dict
from sqlmodel import Session
from db_schema import Listing, Message,Conversation  # Ensure these are imported correctly
from auth import Authhandler  # Ensure your auth handler is imported correctly

auth_handler = Authhandler()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}
        self.message_pipeline = []

    async def connect(self, websocket: WebSocket, user_id: int) -> bool:
        await websocket.accept()
        self.active_connections[user_id] = websocket
        return True

    async def disconnect(self, user_id: int):
        if user_id in self.active_connections:
            self.active_connections.pop(user_id)

    async def send_message_to_user(self, message: str, listing_id: int, sender_id: int, session: Session):
        listing = session.get(Listing, listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        receiver_id = listing.user
        if receiver_id == sender_id:
            raise HTTPException(status_code=400, detail="Sender and receiver cannot be the same")

        # Save message to the database
        new_message = Message.create_message(session=session,content=message, sender_id=sender_id, listing_id=listing_id)
        

        if receiver_id in self.active_connections:
            websocket = self.active_connections[receiver_id]
            await websocket.send_json(new_message)

ws_connection_manager = ConnectionManager()

async def websocket_endpoint(websocket: WebSocket, token: str, session: Session = Depends()):
    try:
        user_id = auth_handler.decode_token(token)
        await ws_connection_manager.connect(websocket, user_id)
        while True:
            data = await websocket.receive_json()
            sender_id = auth_handler.decode_token(data["token"])
            listing_id = data["listing_id"]
            message = data["message"]

            await ws_connection_manager.send_message_to_user(message, listing_id, sender_id, session)
    except WebSocketDisconnect:
        print(f"Client {user_id} disconnected")
        await ws_connection_manager.disconnect(user_id)
    except HTTPException as e:
        await websocket.close(code=1008, reason=e.detail)
        await ws_connection_manager.disconnect(user_id)
    except Exception as e:
        print(f"Unexpected error: {e}")
        await websocket.close(code=1011, reason="Internal server error")
        await ws_connection_manager.disconnect(user_id)
