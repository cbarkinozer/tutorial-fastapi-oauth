import os
import datetime

import jwt
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv

from apps.db import is_token_blacklisted

# Create a fake db (UPDATE TO YOUR TEST USER)
FAKE_DB = {'guillermo.paoletti@gmail.com': {'name': 'Guillermo Paoletti'}}

load_dotenv()

# Helper to read numbers using var envs
def cast_to_number(id):
    temp = os.environ.get(id)
    if temp is not None:
        try:
            return float(temp)
        except ValueError:
            return None
    return None


# Configuration
API_SECRET_KEY = os.getenv('API_SECRET_KEY') or None
if API_SECRET_KEY is None:
    raise BaseException('Missing API_SECRET_KEY env var.')
API_ALGORITHM = os.getenv('API_ALGORITHM') or 'HS256'
API_ACCESS_TOKEN_EXPIRE_MINUTES = cast_to_number('API_ACCESS_TOKEN_EXPIRE_MINUTES') or 15
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30

# Token url (We should later create a token url that accepts just a user and a password to use swagger)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')

# Error
CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Could not validate credentials',
    headers={'WWW-Authenticate': 'Bearer'},
)


# Create token internal function
def create_access_token(*, data: dict, expires_delta: datetime.timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=15)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, API_SECRET_KEY, algorithm=API_ALGORITHM)
    return encoded_jwt


def create_refresh_token(email):
    expires = datetime.timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    return create_access_token(data={'sub': email}, expires_delta=expires)


# Create token for an email
def create_token(email):
    access_token_expires = datetime.timedelta(minutes=API_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={'sub': email}, expires_delta=access_token_expires)
    return access_token


def valid_email_from_db(email):
    return email in FAKE_DB


def decode_token(token):
    return jwt.decode(token, API_SECRET_KEY, algorithms=[API_ALGORITHM])


async def get_current_user_email(token: str = Depends(oauth2_scheme)):
    if is_token_blacklisted(token):
        print("jwt.py:get_current_user_email(). is_token_blacklisted(token) return True")
        raise CREDENTIALS_EXCEPTION
    try:
        payload = decode_token(token)
        email: str = payload.get('sub')
        if email is None:
            print("jwt.py:get_current_user_email(). email is None")
            raise CREDENTIALS_EXCEPTION
    except jwt.PyJWTError:
        print("jwt.py:get_current_user_email. jwt.PyJWTError is thrown")
        raise CREDENTIALS_EXCEPTION

    if valid_email_from_db(email):
        return email

    print("jwt.py:get_current_user_email. valid_email_from_db(email) is False")
    raise CREDENTIALS_EXCEPTION


async def get_current_user_token(token: str = Depends(oauth2_scheme)):
    _ = await get_current_user_email(token)
    return token
