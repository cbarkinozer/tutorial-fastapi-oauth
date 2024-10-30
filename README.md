# FastAPI and Google Login (OAuth)

# My Changes on Hanchon's
- All made async
- Fake DB changed with real async sqlalchemy db
- Packages are updated
- deprecated function calls updated
- ratelimiting example added
- .env added instead of env vars

Note: Do not forget to add users.json to initialize db.  
The content should be like this:
```json
{
    "*@gmail.com": {"name": "*"}
}
```

This is an example following the tutorials:
- [Guide 1 - Google OAuth Login with FastAPI](https://blog.hanchon.live/guides/google-login-with-fastapi/)
- [Guide 2 - Google OAuth and FastAPI JWT](https://blog.hanchon.live/guides/google-login-with-fastapi-and-jwt/)
- [Guide 3 - JWT blacklist and refresh tokens](https://blog.hanchon.live/guides/jwt-tokens-and-fastapi/)

## Requirements:
- Python3.6+

## How to run the example:
- Create a virtualenv `python3 -m venv .venv`
- Activate the virtualenv `. .venv/bin/activate`
- Install the requirements `pip install -r requirements.txt`
- Set up the env vars:
    * GOOGLE_CLIENT_ID=***
    * GOOGLE_CLIENT_SECRET=***
    * SECRET_KEY=**
    * API_SECRET_KEY=**
    * REDIRECT_URI=http://127.0.0.1:7000/token
- Run the app:
    - Guide 1: `python run.py`
    - Guide 2 and 3: `python main.py`
