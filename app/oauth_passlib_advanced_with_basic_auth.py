"""
This is a slight departure from oauth_passlib_advanced.py
Instead of using OAuth2PasswordRequestForm which reads the username and password from x-www-form-urlencoded entries in the body
of the request (how forms are read), it reads the username and password from the header.

In the previous approach, to get an access token, the client passed in the username and password as a form, which are then
read like so:
    @app.post('/access-token')
    async def get_access_token(credentials: Annotated[OAuth2PasswordRequestForm, Depends()]):
        username = credentials.username
        password = credentials.password

In this new approach, we use HTTPBasicAuth to pass in the username and password encoded as base64 in the request header.
This is a typical request:
    GET http://localhost:8000/user
    Accept: application/json
    Authorization: Basic Zm9vOmJhcg==

    The username and password are concatenated like so:
        username:password -> notice they are separated with only a colon
    The resulting concatenated string is then base64 encoded and used in the request above for the access token.

Running the code below might not work in OpenAPI docs, but it works in real life :)
"""

import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, EmailStr
from fastapi.middleware.cors import CORSMiddleware

from typing import Annotated, Callable, Union

# jwt is imported from jose. make sure python-jose[cryptography] is installed in pip
from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext
import secrets


# load secret key and algo from environment. do this for security - don't store keys in code.
# Run this command in cmd to set env vars
#   export <key_name>=<key_here>
API_KEY = os.environ['X_API_KEY']
API_KEY_ALGO = os.environ['X_API_KEY_ALGO']
API_KEY_TTL = 300

passlib_crypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2 = OAuth2PasswordBearer(tokenUrl='login')
http_basic_security = HTTPBasic()


class Journal(BaseModel):
    username: str
    password: str  # hashed password. don't store raw passwords
    secrets: str
    email: EmailStr | None = None
    __journals__: list['Journal'] = []

    @classmethod
    def add_to_db(cls, journal: 'Journal'):
        # adds journal to database
        journal.password = passlib_crypt_context.hash(journal.password)
        print("Added new journal to db:", journal)
        cls.__journals__.append(journal)

    @classmethod
    def all(cls):
        return cls.__journals__

    @classmethod
    def get(cls, username: str) -> Union['Journal', None]:
        for journal in cls.__journals__:
            # if journal.username == username: # don't use this simple equality approach to compare username
            # using secrets.compare_digest from python's standard 'secret' module is more secure against attacks like
            # timing attacks and a whole range of security attacks.
            if secrets.compare_digest(username.encode('utf8'), journal.username.encode('utf8')):
                return journal
        return None

    def get_hash_salt(self):
        # this method returns content that will be used to generate the access token.
        # the access token will basically be a hash of this
        return self.username + "." + self.password


def get_token_expiry(ttl: int = API_KEY_TTL) -> datetime:
    # use utc time to get current universal time, and then set the expiry date of a token by adding the timedelta.
    # in this case it is 300 seconds (5 minutes)
    return datetime.utcnow() + timedelta(seconds=ttl)


class AccessToken(BaseModel):
    """
    Helper class for generating access token.
    'sub' and 'exp' are fields to be used in the JWT.
        sub - refers to something like a username. The important thing to have in mind is that the sub key should have a
            unique identifier across the entire application, and it should be a string.
        exp - refers to the expiry time of the token
    """

    sub: str
    exp: datetime = Field(default_factory=get_token_expiry)

    def generate(self):
        # first arg to jwt.encode is the payload dict, next is the api key, and next is the algorithm
        token = jwt.encode(self.model_dump(), API_KEY, API_KEY_ALGO)
        return {    # remember to use the keys exactly as defined by oauth standards
            "access_token": token,
            "token_type": "bearer"
        }


app = FastAPI()
# allowed_hosts = [
#     'http://10.203.187.53:8000'
# ]
# app.add_middleware(CORSMiddleware, allow_origins=allowed_hosts)


@app.post('/journal', response_model_include={'username'})
async def insert_journal(journal: Journal) -> Journal:
    Journal.add_to_db(journal)
    return journal


@app.get('/login')
async def get_access_token(credentials: Annotated[HTTPBasicCredentials, Depends(http_basic_security)]):
    username = credentials.username
    password = credentials.password

    print("username:", username)
    print("password:", password)

    journal = Journal.get(username)

    if not journal:
        raise HTTPException(status_code=404, detail='Journal not found')
    if password is None or not passlib_crypt_context.verify(password, journal.password):
        raise HTTPException(status_code=402, detail='Invalid credentials')

    # in simple_oauth_passlib.py, we were generating the access token ourselves by hashing the username and password.
    # in this case, we're generating the access token using JWT. only the username is the personally identifying
    # information stored in the JWT.
    access_token = AccessToken(sub=username)
    return access_token.generate()


@app.get('/journal', response_model_exclude={'password'})
async def get_journal(token: Annotated[str, Depends(oauth2)]) -> Journal:
    CredentialsError = HTTPException(status_code=401, detail='Invalid authorization', headers={'WWW-Authenticate': 'Bearer'})

    try:
        # decoding the token is fairly the same process as encoding it.
        # a little change (at least what i noticed from the tutorials) is that algorithms is passed as a list (even if
        # it's only one algorithm), but still params are as follows: token, key, algo
        token = jwt.decode(token, API_KEY, algorithms=[API_KEY_ALGO])
        username = token.get('sub')     # this info is contained within the claims of the JWT.

        if username is None:
            raise CredentialsError

        journal = Journal.get(username)

        if journal is None:
            raise CredentialsError

        return journal
    except ExpiredSignatureError:
        # error thrown when the JWT expires. in that case, the client will have to request a new token.
        # you can return information in the http exception that will hint the client code that it will have to request
        # a new token.
        raise HTTPException(status_code=401, detail="Expired token")
    except JWTError:
        raise CredentialsError
