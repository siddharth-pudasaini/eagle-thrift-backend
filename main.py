from fastapi import FastAPI, WebSocket, WebSocketDisconnect,Query,Depends,HTTPException
from typing import Dict
from db_schema import  User,Listing  # Ensure you have these models defined appropriately
from database import get_session

from sqlmodel import Session,select

from input_models import UserModel,TokenData,ListingModel
from auth import Authhandler


from web_socket import ConnectionManager

app = FastAPI()


manager = ConnectionManager()
auth_handler=Authhandler()


#=============================================User related routes===========================================================================
@app.post("/api/user/register")
async def user_registration(user:UserModel,session:Session=Depends(get_session)):
    user_data=User.model_validate(user)
    hashed_password=auth_handler.get_password_hash(user_data.password)
    user_data.password=hashed_password
    return User.create(user=user_data,session=session)
    

@app.post("/api/user/login")
async def user_login(user:UserModel,session:Session=Depends(get_session)):
    result=User.get_user(user.email,session=session)
    if not auth_handler.verify_password(user.password,result.password):
        raise HTTPException(status_code=401,detail="Invalid email or password")
    token= auth_handler.encode_token(result.id)
    return{"token":token,"id":result.id}

#=============================================Listing related routes===========================================================================
@app.post("/api/listing")
async def create_listing(listing:ListingModel,session:Session=Depends(get_session),user_id:int=Depends(auth_handler.auth_wrapper)):
    listing_data=Listing.model_validate(listing)
    return Listing.create(user_id,listing=listing_data,session=session)

@app.get("/api/listing/{listing_id}")
async def get_listing(id:int,session:Session=Depends(get_session)):
    return Listing.get_single_listing(id,session)



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
