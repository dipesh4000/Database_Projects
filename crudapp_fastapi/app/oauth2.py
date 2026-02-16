from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from . import schemas, models
from fastapi import Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer
from .database import get_db
from sqlalchemy.orm import Session


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login") 
#this tokenUrl="login" means that whenever we use the "Depends(oauth2_scheme)" it will go to the login endpoint and take the token from there



SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_access_token(token: str, credentials_exception):
    try:

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        id: int = payload.get("user_id")
        if id is None:
            raise credentials_exception
        token_data = schemas.TokenData(id=id)
    
    except JWTError:
        raise credentials_exception
    return token_data

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)): #it is going to verify that the verify_acess_token's user
    credentials_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail=f"Could not validate credentials, bro", headers={"WWW-Authenticate": "Bearer"})   
    
    token_data = verify_access_token(token, credentials_exception)
    user = db.query(models.User).filter(models.User.id == token_data.id).first()
    if user is None:
        raise credentials_exception
    return user



# token = jwt.encode({'key': 'value'}, 'secret', algorithm='HS256')
# u'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJrZXkiOiJ2YWx1ZSJ9.FG-8UppwHaFp1LgRYQQeS6EDQF7_6-bMFegNucHjmWg'

# jwt.decode(token, 'secret', algorithms=['HS256'])
# {u'key': u'value'}