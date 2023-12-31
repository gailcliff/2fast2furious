from fastapi import FastAPI, Depends
from pydantic import EmailStr
from typing import Annotated
from datetime import date

from main import SecureRecruit, BaseRecruit
from dataclasses import dataclass


app = FastAPI()


def get_recruit_info(name: str, email: EmailStr, password: str):
    return SecureRecruit(name=name, email=email, password=password)


@dataclass
class AuthorizedRecruit:
    name: str
    email: EmailStr
    password: str
    token: str


@app.get('/user-info/{name}', response_model=BaseRecruit)
def get_user_info(recruit: AuthorizedRecruit):
    return recruit


@app.get('/dining-dollars/{when}')
def get_dining_balance(when: date, recruit: Annotated[AuthorizedRecruit, Depends()]):
    print(recruit)
    return {
        "balance": 548,
        "as_of": when,
        "user_info": BaseRecruit(**recruit.__dict__)
    }
