from pydantic import EmailStr
from typing import Optional,List
from sqlmodel import Field,SQLModel,Session,select,Relationship
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
import os

from datetime import datetime


from input_models import ConversationModel,UserModel,ListingModel,CategoryModel,MessageModel

class TimeStampedData(SQLModel):
    created_at: Optional[datetime] = Field(default=None, nullable=False)
    updated_at: Optional[datetime] = Field(default=None, nullable=False)


class User(UserModel,TimeStampedData,table=True):
    id:Optional[int]=Field(default=None,primary_key=True)
    email: EmailStr=Field(...,unique=True)
    phone_number:Optional[str]=Field(None,min_length=10)

    @classmethod
    def create(cls, session: Session, user: "User") -> str:
        try:
            session.add(user)
            session.commit()
            session.refresh(user)
            return {f'User with email {user.email} created successfully'}
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e.orig))

    @classmethod
    def get_user(cls,email:EmailStr, session: Session):
        statement=select(cls).where(cls.email==email)
        user=session.exec(statement).first()
        if user:
            return user
        raise HTTPException(status_code=404,detail="User not found")

class Category(CategoryModel,TimeStampedData,table=True):
    id:Optional[int]=Field(default=None,primary_key=True)
    name:str=Field(...,nullable=False,unique=True)
    item_count:Optional[int]=Field(default=0)

    @classmethod
    def create(cls, session: Session, category: "Category") -> str:
        try:
            session.add(category)
            session.commit()
            session.refresh(category)
            return {f'{category.name} created successfully'}
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e.orig))
        
    @classmethod
    def get_all_categories(cls,session:Session):
        statement = select(cls)
        results = session.exec(statement)
        items = results.all()
        return items
      

class Listing(ListingModel,TimeStampedData,table=True):
    id:Optional[int]=Field(default=None,primary_key=True)
    user:int=Field(default=None,foreign_key="user.id",nullable=False)
    category:int=Field(default=0,foreign_key="category.id",nullable=False)
    @classmethod
    def create(cls,user:int,session:Session,listing:"Listing")->str:
        listing.user=user
        try:
            session.add(listing)
            session.commit()
            session.refresh(listing)
            return(listing)
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e.orig))

    @classmethod   
    def get_single_listing(cls,id:int,session:Session):
        listing = session.get(cls, id)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        # Construct image URLs
        image_folder_path = f"uploads/listings/{id}"

        if os.path.exists(image_folder_path) and os.path.isdir(image_folder_path):
            image_files = os.listdir(image_folder_path)
            image_urls = [f"http://localhost:8000/{image_folder_path}/{image_file}" for image_file in image_files]
        else:
            image_urls = []

        listing_dict = listing.dict()
        listing_dict['images'] = image_urls
        return listing_dict
    
    @classmethod
    def get_multiple_listings(
        cls,
        session: Session,
        offset: int = 0,
        limit: int = 100,
        categories: Optional[List[int]] = None,
        sort_order: Optional[str] = None
    ) -> List[dict]:
        query = select(cls)
        
        if categories!=None :
            if 0 not in categories:
                query = query.where(cls.category.in_(categories))
        
        if sort_order:
            if sort_order == "price_low_to_high":
                query = query.order_by(cls.price.asc())
            elif sort_order == "price_high_to_low":
                query = query.order_by(cls.price.desc())
            elif sort_order == "newest":
                query = query.order_by(cls.created_at.desc())
            elif sort_order == "oldest":
                query = query.order_by(cls.created_at.asc())
        
        query = query.offset(offset).limit(limit)
        results = session.exec(query)
        listings = results.all()

        listings_with_images = []
        for listing in listings:
            image_folder_path = f"uploads/listings/{listing.id}"
            if os.path.exists(image_folder_path) and os.path.isdir(image_folder_path):
                image_files = os.listdir(image_folder_path)
                image_urls = [f"http://localhost:8000/{image_folder_path}/{image_file}" for image_file in image_files]
            else:
                image_urls = []
            listing_dict = listing.dict()
            listing_dict['images'] = image_urls
            listings_with_images.append(listing_dict)
        return listings_with_images
    
    @classmethod
    def get_all_user_listings(cls,session=Session,user_id=int):
        query=select(cls).where(cls.user==user_id)
        results=session.exec(query)
        listings=results.all()
        listings_with_images = []
        for listing in listings:
            image_folder_path = f"uploads/listings/{listing.id}"
            if os.path.exists(image_folder_path) and os.path.isdir(image_folder_path):
                image_files = os.listdir(image_folder_path)
                image_urls = [f"http://localhost:8000/{image_folder_path}/{image_file}" for image_file in image_files]
            else:
                image_urls = []
            listing_dict = listing.dict()
            listing_dict['images'] = image_urls
            listings_with_images.append(listing_dict)
        return listings_with_images


class Conversation(ConversationModel, TimeStampedData, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    listing_id: int = Field(foreign_key="listing.id")
    user_1: int = Field(foreign_key="user.id")
    user_2: int = Field(foreign_key="user.id")
    messages: List["Message"] = Relationship(back_populates="conversation")


class Message(MessageModel, TimeStampedData, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(..., max_length=1000)
    sender_id: int = Field(foreign_key="user.id")
    receiver_id: int = Field(foreign_key="user.id")
    listing_id: int = Field(foreign_key="listing.id")
    conversation_id: int = Field(foreign_key="conversation.id")
    conversation: Conversation = Relationship(back_populates="messages")

    @classmethod
    def get_all_messages(cls, user_id: int, session: Session) -> dict:
        statement = select(cls).where(
            (cls.sender_id == user_id) | (cls.receiver_id == user_id)
        )
        messages = session.exec(statement).all()
        grouped_messages = {}
        for message in messages:
            if message.conversation_id not in grouped_messages:
                grouped_messages[message.conversation_id] = []
            grouped_messages[message.conversation_id].append(message)
        return grouped_messages

    @classmethod
    def create_message(cls, session: Session, listing_id: int, sender_id: int, content: str) -> str:
        listing = session.get(Listing, listing_id)
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")

        # Check if a conversation already exists
        conversation = session.exec(
            select(Conversation).where(
                Conversation.listing_id == listing_id,
                (Conversation.user_1 == sender_id) | (Conversation.user_2 == sender_id)
            )
        ).first()
        print(conversation)

        if not conversation:
            # Determine receiver_id based on the listing owner
            receiver_id = listing.user
            if receiver_id == sender_id:
                receiver_id = listing.user if listing.user != sender_id else None

            # Create a new conversation if it doesn't exist
            conversation = Conversation(
                listing_id=listing_id,
                user_1=sender_id,
                user_2=receiver_id,
            )
            session.add(conversation)
            session.commit()
            session.refresh(conversation)
        else:
            # Determine receiver_id based on the conversation
            receiver_id = conversation.user_1 if conversation.user_2 == sender_id else conversation.user_2

        # Save message to the database
        message = cls(
            content=content,
            sender_id=sender_id,
            receiver_id=receiver_id,
            listing_id=listing_id,
            conversation_id=conversation.id
        )

        try:
            session.add(message)
            session.commit()
            session.refresh(message)
            return message
        except IntegrityError as e:
            session.rollback()
            raise HTTPException(status_code=400, detail=str(e.orig))

