from fastapi import FastAPI, WebSocket, WebSocketDisconnect,Query,Depends,HTTPException,UploadFile,File,Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List,Optional
from db_schema import  User,Listing,Category,Message # Ensure you have these models defined appropriately
from database import get_session
import shutil

from sqlmodel import Session,select
from dotenv import dotenv_values
import os

from input_models import UserModel,ListingModel,LoginModel,CategoryModel,AdminIdModel,CategoryResponse
from auth import Authhandler


from web_socket import websocket_endpoint

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from this origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)


auth_handler=Authhandler()

config=dotenv_values('.env')

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'uploads', 'listings')

def is_allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

async def validate_and_upload_files(files: List[UploadFile] = File(...)):
    for file in files:
        contents = await file.read()
        if len(contents) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"File {file.filename} exceeds the maximum size of 5MB")
        if not is_allowed_file(file.filename):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not an allowed image type (png, jpg, jpeg)")
        
        file.file.seek(0)  # Reset the file read pointers after reading

    return files


# Mount the static files directory
app.mount("/uploads", StaticFiles(directory=os.path.join(os.path.dirname(__file__), 'uploads')), name="uploads")

#===========================================Category Related Routes========================================
@app.post("/api/category/create")
async def add_category(admin_id:AdminIdModel,category:CategoryModel,session:Session=Depends(get_session)):
    if admin_id.id==config["ADMIN_CODE"]:
        category_data=Category.model_validate(category)
        return Category.create(category=category_data,session=session)
    raise HTTPException(status_code=401,detail="Unauthorized route")

@app.get("/api/categories",response_model=List[CategoryResponse])
async def get_all_categories(session:Session=Depends(get_session)):
    categories=Category.get_all_categories(session=session)
    return categories



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
    return{"token":token,"username":result.username,"email":result.email,"id":result.id}

@app.post("/api/user/profile_image")
async def upload_profile_image(
    user_id: int = Depends(auth_handler.auth_wrapper),
    file: List[UploadFile] = Depends(validate_and_upload_files),
    session: Session = Depends(get_session),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    profile_folder = f"uploads/profiles/{user_id}/"
    os.makedirs(profile_folder, exist_ok=True)
    
    # Delete existing files in the folder
    for filename in os.listdir(profile_folder):
        file_path = os.path.join(profile_folder, filename)
        if os.path.isfile(file_path):
            os.unlink(file_path)
    
    # Save new file
    file_location = os.path.join(profile_folder, file[0].filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file[0].file, buffer)

    return {f'localhost:8000/uploads/profiles/{user_id}/{file[0].filename}'}

@app.get('/api/user/profile_image/{user_id}')
async def get_user_image(user_id:int):
    profile_folder = f"uploads/profiles/{user_id}/"
    file= os.listdir(profile_folder)[0]
    return {f'localhost:8000/uploads/profiles/{user_id}/{file.filename}'}

#=============================================Listing related routes===========================================================================
@app.post("/api/listing")
async def create_listing(
    title: str = Form(...,min_length=1,max_length=100),
    description: str = Form(...,min_length=1,max_length=2000),
    price: float = Form(...,ge=0,le=1000000000),
    category:int=Form(...,ge=0),
    session: Session = Depends(get_session),
    user_id: int = Depends(auth_handler.auth_wrapper),
    files: List[UploadFile] = Depends(validate_and_upload_files)
):
    # Create ListingModel instance manually
    listing_model = ListingModel(title=title, description=description, price=price,category=category)
    
    # Convert ListingModel to Listing
    listing = Listing(**listing_model.model_dump())

    # Create the listing and get the listing_id
    listing_obj = Listing.create(user=user_id, listing=listing, session=session)
    listing_id = listing_obj.id  # Assuming the created listing object has an id attribute
    
    # Directory where images will be saved
    listing_upload_dir = os.path.join(UPLOAD_DIR, str(listing_id))
    os.makedirs(listing_upload_dir, exist_ok=True)
    
    # Save each uploaded file with the specified format
    image_urls = []
    for i, file in enumerate(files):
        file_extension = file.filename.split('.')[-1].lower()
        file_path = os.path.join(listing_upload_dir, f"{i + 1}.{file_extension}")
        
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        image_urls.append(f"/uploads/{listing_id}/{i + 1}.{file_extension}")
    
    return {"message": "Listing created successfully", "listing_id": listing_id, "image_urls": image_urls}


@app.get("/api/listing/{listing_id}")
async def get_listing(listing_id:int,session:Session=Depends(get_session)):
    return Listing.get_single_listing(listing_id,session)


@app.get("/api/listings", response_model=List[dict])
async def get_listings(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    categories: Optional[List[int]] = Query(None),
    sort_order: Optional[str] = Query(None),
    session: Session = Depends(get_session)
):
    listings = Listing.get_multiple_listings(session, offset, limit, categories, sort_order)
    return listings

@app.get('/api/listings/user/{user_id}')
async def get_all_user_listings(user_id:int,session:Session=Depends(get_session)):
    return Listing.get_all_user_listings(session=session,user_id=user_id)


#=============================================Handling Messaging===========================================================
@app.websocket("/ws/{token}")
async def websocket_route(websocket: WebSocket, token: str, session: Session = Depends(get_session)):
    await websocket_endpoint(websocket, token, session)
