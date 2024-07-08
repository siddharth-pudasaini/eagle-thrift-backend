from pydantic import BaseModel,Field as PydanticField ,EmailStr
from typing import Optional
from sqlmodel import Field,SQLModel,Session
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from datetime import datetime


from input_models import UserModel



class User(UserModel,table=True):
    id:Optional[int]=Field(default=None,primary_key=True)
    email: EmailStr=Field(...,unique=True)
    created_at: Optional[datetime] = Field(default=None, nullable=False)
    updated_at: Optional[datetime] = Field(default=None, nullable=False)

    @classmethod
    def register_listeners(cls):
        @event.listens_for(cls, "before_insert")
        def set_created_at(mapper, connection, target):
            target.created_at = datetime.now()
            target.updated_at = datetime.now()

        @event.listens_for(cls, "before_update")
        def set_updated_at(mapper, connection, target):
            target.updated_at = datetime.now()
   

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






    