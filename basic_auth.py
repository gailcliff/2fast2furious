from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
import secrets


class User(BaseModel):
    username: str
    password: str
    details: str

    def get_username_bytes(self):
        return self.username.encode('utf8')

    def get_password_bytes(self):
        return self.password.encode('utf8')


user = User(username='foo', password='bar', details='siri')

app = FastAPI()
security = HTTPBasic()


@app.get('/user')
def get_user(auth: Annotated[HTTPBasicCredentials, Depends(security)]):
    username_match = secrets.compare_digest(auth.username.encode('utf8'), user.get_username_bytes())
    password_match = secrets.compare_digest(auth.password.encode('utf8'), user.get_password_bytes())

    if not (username_match and password_match):
        raise HTTPException(status_code=401)

    return user
