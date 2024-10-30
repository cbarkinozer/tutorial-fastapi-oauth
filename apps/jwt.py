import os
import datetime
import json
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, Boolean, Integer
from sqlalchemy.future import select
import asyncio

from apps.db import is_token_blacklisted

# Load environment variables
load_dotenv()

# Load initial user data from JSON
INITIAL_USER_FILE = 'users.json'
with open(INITIAL_USER_FILE, 'r') as file:
    initial_user_data = json.load(file)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite+aiosqlite:///./user.db"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)
Base = declarative_base()

# User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    is_active = Column(Boolean, default=True)

# Initialize the database with initial user data if not exists
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        async with SessionLocal() as session:
            for email, data in initial_user_data.items():
                result = await session.execute(select(User).where(User.email == email))
                user = result.scalar_one_or_none()
                if not user:
                    user = User(email=email, name=data["name"])
                    session.add(user)
            await session.commit()


asyncio.run(init_db())

# Configuration
def cast_to_number(id):
    temp = os.environ.get(id)
    if temp is not None:
        try:
            return float(temp)
        except ValueError:
            return None
    return None

API_SECRET_KEY = os.getenv('API_SECRET_KEY')
if API_SECRET_KEY is None:
    raise BaseException('Missing API_SECRET_KEY env var.')

API_ALGORITHM = os.getenv('API_ALGORITHM') or 'HS256'
API_ACCESS_TOKEN_EXPIRE_MINUTES = cast_to_number('API_ACCESS_TOKEN_EXPIRE_MINUTES') or 15
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/auth/token')

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Could not validate credentials',
    headers={'WWW-Authenticate': 'Bearer'},
)

# Helper functions
async def create_access_token(*, data: dict, expires_delta: Optional[datetime.timedelta] = None):
    to_encode = data.copy()
    expire = datetime.datetime.now(datetime.timezone.utc) + (expires_delta or datetime.timedelta(minutes=15))
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, API_SECRET_KEY, algorithm=API_ALGORITHM)
    return encoded_jwt

async def create_refresh_token(email):
    expires = datetime.timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES)
    return await create_access_token(data={'sub': email}, expires_delta=expires)

async def decode_token(token):
    return jwt.decode(token, API_SECRET_KEY, algorithms=[API_ALGORITHM])

# Fetch user from the database
async def get_user_by_email(email: str):
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

# Dependency to get the current user email
async def get_current_user_email(token: str = Depends(oauth2_scheme)):
    if await is_token_blacklisted(token):
        raise CREDENTIALS_EXCEPTION
    try:
        payload = await decode_token(token)
        email: str = payload.get('sub')
        if email is None:
            raise CREDENTIALS_EXCEPTION
    except jwt.PyJWTError:
        raise CREDENTIALS_EXCEPTION

    user = await get_user_by_email(email)
    if user:
        return email

    raise CREDENTIALS_EXCEPTION

# Dependency to get the current user token
async def get_current_user_token(token: str = Depends(oauth2_scheme)):
    _ = await get_current_user_email(token)
    return token

# Create token for an email
async def create_token(email):
    access_token_expires = datetime.timedelta(minutes=API_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(data={'sub': email}, expires_delta=access_token_expires)
    return access_token

async def valid_email_from_db(email: str) -> bool:
    # Query the database to check if a user with this email exists
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        return user is not None