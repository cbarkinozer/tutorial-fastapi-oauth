from fastapi import Depends
from fastapi import FastAPI

from apps.jwt import get_current_user_email

api_app = FastAPI()


@api_app.get('/')
async def test():
    return {'message': 'unprotected api_app endpoint'}


@api_app.get('/protected')
async def test2(current_email: str = Depends(get_current_user_email)):
    return {'message': 'protected api_app endpoint'}
