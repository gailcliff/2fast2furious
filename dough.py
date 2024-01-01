from fastapi import FastAPI, Depends, Request, Response, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from main import SecureRecruit


oauth2 = OAuth2PasswordBearer(tokenUrl='gen-token')

app = FastAPI()


async def get_user_from_token(token: Annotated[str, Depends(oauth2)]) -> SecureRecruit:
    if token != 'adminstrong123':
        raise HTTPException(status_code=401, detail="invalid access token. nice try", headers={"WWW-Authenticate": "Bearer"})
    return SecureRecruit(name='foo', email='ba@r.com', password=token)


@app.post('/gen-token')
def get_access_token(credentials: Annotated[OAuth2PasswordRequestForm, Depends()]):
    username = credentials.username
    pwd = credentials.password

    if username != 'admin':
        raise HTTPException(status_code=401, detail="invalid username: you can't hang here")
    if pwd != 'strong123':
        raise HTTPException(status_code=401, detail="please check your password and try again :/")

    return {
        "access_token": username + pwd,
        "token_type": "bearer"
    }


@app.get('/user/{user_id}')
async def get_user(user_id: int, user: Annotated[SecureRecruit, Depends(get_user_from_token)]):
    return {
        "id": user_id,
        "user": user
    }

