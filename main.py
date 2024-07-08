from fastapi import FastAPI, WebSocket, WebSocketDisconnect,Query,Depends,HTTPException
from typing import Dict
from db_schema import  User  # Ensure you have these models defined appropriately
from database import get_session
from mysql.connector.errors import IntegrityError

from sqlmodel import Session,select

from input_models import UserModel,TokenData,Listing


from web_socket import ConnectionManager

app = FastAPI()


manager = ConnectionManager()



#User related routes
@app.post("/api/user/register")
async def user_registration(user:UserModel,session:Session=Depends(get_session)):
    user_data=User.model_validate(user)
    return User.create(user=user_data,session=session)
    

@app.post("/api/user/login")
async def user_login(user:User):
    return "Login"

#Listing related routes 
@app.post("/api/listing")
async def create_listing(token:TokenData,listing:Listing):
    return listing.title

@app.get("/api/listing")
async def get_listing(id:int=Query(None,gt=0),limit:int=Query(None,gt=0),offset:int=Query(None,gt=0)):
    return"Query listing"



#Handling Messaging
@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    print(token)
    if not await manager.connect(websocket, token):
        return
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(data, websocket)
    except WebSocketDisconnect:
        manager.disconnect(token)
