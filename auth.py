import jwt
from fastapi import HTTPException,Security
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from passlib.context import CryptContext
from datetime import datetime,timedelta,timezone
from dotenv import dotenv_values

config=dotenv_values('.env')


class Authhandler():
    security=HTTPBearer()
    pwd_context=CryptContext(schemes=["bcrypt"],deprecated="auto")
    secret=config["SECRET"]

    def get_password_hash(self,password):
        return self.pwd_context.hash(password)
    
    def verify_password(self,plain_password,hashed_password):
        return self.pwd_context.verify(plain_password,hashed_password)
    
    def encode_token(self,user_id):
        payload={

            'exp':datetime.now(timezone.utc)+timedelta(days=1),
            'iat':datetime.now(timezone.utc),
            "sub":user_id
        }

        return jwt.encode(payload,self.secret,algorithm="HS256")

    def decode_token(self,token):
        try:
            payload=jwt.decode(token,self.secret,algorithms=['HS256'])
            return payload['sub']
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401,detail="Auth token expired")
        except jwt.InvalidTokenError :
            raise HTTPException(status_code=401,detail="Invalid Auth Token")

    
    def auth_wrapper(self,auth:HTTPAuthorizationCredentials=Security(security)):
        return self.decode_token(auth.credentials)