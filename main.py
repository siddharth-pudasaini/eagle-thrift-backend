from fastapi import FastAPI, WebSocket, WebSocketDisconnect,Query,Depends,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from db_schema import  User,Listing,Category  # Ensure you have these models defined appropriately
from database import get_session

from sqlmodel import Session,select
from dotenv import dotenv_values


from input_models import UserModel,ListingModel,LoginModel,CategoryModel,AdminIdModel
from auth import Authhandler


from web_socket import ConnectionManager

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from this origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

ws_connection_manager = ConnectionManager()
auth_handler=Authhandler()

config=dotenv_values('.env')


@app.post("/api/category/create")
async def add_category(admin_id:AdminIdModel,category:CategoryModel,session:Session=Depends(get_session)):
    if admin_id==config["ADMIN_CODE"]:
        category_data=Category.model_validate(category)
        return Category.create(category=category_data,session=session)
    raise HTTPException(status_code=401,detail="Unauthorized route")

#=============================================User related routes===========================================================================
@app.post("/api/user/register")
async def user_registration(user:UserModel,session:Session=Depends(get_session)):
    user_data=User.model_validate(user)
    hashed_password=auth_handler.get_password_hash(user_data.password)
    user_data.password=hashed_password
    return User.create(user=user_data,session=session)
    

@app.post("/api/user/login")
async def user_login(user:LoginModel,session:Session=Depends(get_session)):
    print(user)
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

# @app.get("/api/listings/")
# async def get_multiple_listings()


#=============================================Handling Messaging===========================================================
@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket,token:str):
    try:
        user_id = auth_handler.decode_token(token)
        await ws_connection_manager.connect(websocket,user_id)
        while True:
            data = await websocket.receive_json()
            sender_id= auth_handler.decode_token(data["token"])
            await ws_connection_manager.send_message_to_user(data["message"],data["receiver"],sender_id)
    except WebSocketDisconnect:
        print(f"Client {user_id} disconnected")
    except HTTPException as e:
        await websocket.close(code=1008, reason=e.detail)
