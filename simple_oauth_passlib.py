from fastapi import FastAPI, HTTPException, Depends
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Union, Annotated

app = FastAPI()
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2 = OAuth2PasswordBearer('access-token')


class Journal(BaseModel):
    username: str
    password: str  # hashed password. don't store raw passwords
    secrets: str
    __journals__: list['Journal'] = []

    @classmethod
    def add_to_db(cls, journal: 'Journal'):
        # adds journal to database
        journal.password = pwd_context.hash(journal.password)
        print("Added new journal to db:", journal)
        cls.__journals__.append(journal)

    @classmethod
    def all(cls):
        return cls.__journals__

    @classmethod
    def get_user(cls, username: str) -> Union['Journal', None]:
        for journal in cls.__journals__:
            if journal.username == username:
                return journal
        return None

    def get_hash_salt(self):
        # this method returns content that will be used to generate the access token.
        # the access token will basically be a hash of this
        return self.username + "." + self.password


@app.post('/journal', response_model_include={'username'})
def add_journal(journal: Journal) -> Journal:
    # we don't need an access token for this operation because it is the entry point of the Journal, we're
    # not authorizing anything at this point.
    Journal.add_to_db(journal)
    return journal


@app.post('/access-token')
def get_access_token(creds: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    For a client to access any of the protected path operations, they need an access token, which is generated
    from their username and password.
    First, the code checks whether the username exists in the database. If not, a 404 exception is thrown.
    Next, the client's password is verified against the hashed password stored in the db, if the journal exists.
    If not verified, a 401 unauthorized error is thrown.

    Else, return the access token by hashing the combo of username and password (get_hash_salt())
    :param creds: username and password
    :return: access token
    """
    username = creds.username
    password = creds.password

    journal = Journal.get_user(username)
    if not journal:
        raise HTTPException(status_code=404, detail="You don't exist")
    if not pwd_context.verify(password, journal.password):
        raise HTTPException(status_code=401, detail="Invalid password")

    return {
        "access_token": pwd_context.hash(journal.get_hash_salt()),
        "token_type": "bearer"
    }


@app.get('/journal/{username}', response_model_exclude={'password'})
def get_journal(username: str, token: Annotated[str, Depends(oauth2)]) -> Journal:
    """
    This path op needs an access token.
    To access the journal, the user passes in their username. By this point, they already have the access token,
    which is their hashed-together username and password.
    Code checks if that username exists, if not it throws 404 error.
    Next, code verifies the access token. The raw version is just "username + . + hashed password". This is obtained from
    the Journal object. The raw is checked against the access token and if it's valid, it becomes verified.
    If the token doesn't exist or is unverified, throw 401 Unauthorized error.
    :param username: the user's name for the journal
    :param token: the access token
    :return:
    """
    journal = Journal.get_user(username)

    if not journal:
        raise HTTPException(status_code=404, detail="You don't exist")

    print("tok", token)
    print("salt", journal.get_hash_salt())
    if not token or not pwd_context.verify(journal.get_hash_salt(), token):
        raise HTTPException(status_code=401, headers={'WWW-Authenticate': 'Bearer'})

    return journal
