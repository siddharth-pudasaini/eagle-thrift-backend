
from sqlmodel import SQLModel,create_engine,Session
from db_schema import User,Listing,Category,Message,Conversation
from sqlalchemy import event
from datetime import datetime,timezone


def register_listeners(cls):
    @event.listens_for(cls, "before_insert")
    def set_created_at(mapper, connection, target):
        target.created_at = datetime.now(timezone.utc)
        target.updated_at = datetime.now(timezone.utc)

    @event.listens_for(cls, "before_update")
    def set_updated_at(mapper, connection, target):
        target.updated_at = datetime.now(timezone.utc)


engine=create_engine(f'sqlite:///./api.db')

SQLModel.metadata.create_all(engine)
register_listeners(User)
register_listeners(Listing)
register_listeners(Category)
register_listeners(Message)
register_listeners(Conversation)


def get_session():
    with Session(engine) as session:
        yield session


