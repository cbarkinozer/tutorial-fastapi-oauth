import os
from datetime import datetime, timezone

from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client import OAuthError
from fastapi import FastAPI
from fastapi import Request
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

from apps.jwt import create_refresh_token
from apps.jwt import create_token
from apps.jwt import CREDENTIALS_EXCEPTION
from apps.jwt import decode_token
from apps.jwt import valid_email_from_db
from dotenv import load_dotenv

load_dotenv()

# Create the auth app
auth_app = FastAPI()

# OAuth settings
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID') or None
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET') or None
if GOOGLE_CLIENT_ID is None or GOOGLE_CLIENT_SECRET is None:
    raise BaseException('Missing env variables')

# Set up OAuth
config_data = {'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID, 'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

# Set up the middleware to read the request session
SECRET_KEY = os.getenv('SECRET_KEY') or None
if SECRET_KEY is None:
    raise 'Missing SECRET_KEY'
auth_app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Frontend URL:
REDIRECT_URI = os.getenv('REDIRECT_URI') or 'http://127.0.0.1:7000/token'


@auth_app.route('/login')
async def login(request: Request):
    redirect_uri = REDIRECT_URI  # This creates the url for our /auth endpoint
    return await oauth.google.authorize_redirect(request, redirect_uri)


@auth_app.route('/token')
async def auth(request: Request):
    try:
        access_token = await oauth.google.authorize_access_token(request)
        user_data = access_token["userinfo"]
    except OAuthError:
        raise CREDENTIALS_EXCEPTION
    if await valid_email_from_db(user_data['email']):
        return JSONResponse({
            'result': True,
            'access_token': await create_token(user_data['email']),
            'refresh_token': await create_refresh_token(user_data['email']),
        })
    raise CREDENTIALS_EXCEPTION


@auth_app.post('/refresh')
async def refresh(request: Request):
    try:
        # Only accept post requests
        if request.method == 'POST':
            form = await request.json()
            if form.get('grant_type') == 'refresh_token':
                token = form.get('refresh_token')
                payload = await decode_token(token)
                # Check if token is not expired
                expire_date = datetime.fromtimestamp(payload.get('exp')).strftime("%Y-%m-%d %H:%M:%S")
                now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                if expire_date > now:
                    email = payload.get('sub')
                    # Validate email
                    if await valid_email_from_db(email):
                        # Create and return token
                        return JSONResponse({'result': True, 'access_token': await create_token(email)})
    except Exception:
        raise CREDENTIALS_EXCEPTION
    raise CREDENTIALS_EXCEPTION
