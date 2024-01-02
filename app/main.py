from fastapi import (
    FastAPI, Query, Path,
    Body, Cookie, Header,
    Request, Response, Form, HTTPException, Depends
)
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.encoders import jsonable_encoder
from typing import Annotated, Any
from enum import Enum
from datetime import date

from pydantic import BaseModel, Field, HttpUrl, EmailStr


def security_token_verifier(sec_token: Annotated[str, Header(alias='X-Sec-Token')]):
    print("token: ", sec_token)
    if sec_token != 'hash#1234':
        raise SecException('invalid access token')


def secret_key_verifier(sec_key: Annotated[str, Header(alias='X-Sec-Key')]):
    if sec_key != 'key->to_the_city':
        raise SecException('invalid secret key')


SecurityTokenVerifier = Depends(security_token_verifier)
SecretKeyVerifier = Depends(secret_key_verifier)

app = FastAPI()


class Title(Enum):
    CHIEF = 'ceo'
    OPERATIONS = 'coo'
    TECH = 'cto'


class BaseRecruit(BaseModel):
    name: str
    email: EmailStr


class SecureRecruit(BaseRecruit):
    password: str


class Recruit(BaseRecruit):
    linked_in: HttpUrl | None = None
    total_comp: int = Field(gt=50000, default=70000)
    start_date: date | None = Field(default_factory=date.today)
    __recruits__: list['Recruit'] = []

    @classmethod
    def add_recruit(cls, recruit: 'Recruit'):
        cls.__recruits__.append(recruit)

    @classmethod
    def all(cls):
        return cls.__recruits__


@app.get("/team/ceo", tags=['team'], summary='ceo')
async def get_ceo():
    """
    I'm CEO, bitch!
    ~ TGC
    """
    return {
        Title.CHIEF: "Gail Cliff"
    }


@app.get("/team", tags=['team'])
async def get_team_member(title: Annotated[Title, Query()] = None):
    return {
        title or "t": "John Doe"
    }


@app.get("/download/{file:path}")
async def download(file: str):
    return file


@app.post('/team/hire/{app_ac_name}',
          tags=['team'],
          summary="we're hiring",
          description="no bozos allowed"
          )
def recruit(
            member: Annotated[Recruit, Body(embed=True)],
            app_ac_name: Annotated[str, Path(min_length=3, max_length=7)],
            experience_yrs: Annotated[int | None, Query(
                title='how many years of experience do you have?',
                description='we need at least 5 :)',
                ge=5,
                alias='experience-yrs',
                deprecated=True,
                include_in_schema=False
            )] = None,
            experiences: Annotated[set[str] | None, Query()] = None
            ) -> Recruit | dict:
    if experience_yrs is None or experiences is None or len(experiences) == 0:
        return {
            "sorry": f"{app_ac_name}: Inadequate experience"
        }
    Recruit.add_recruit(member)
    return {
        "member": member,
        "experience": f"{experience_yrs} years",
        "experiences": experiences
    }


@app.get('/team/recruits', tags=['team'])
def get_recruits() -> list[BaseRecruit]:
    return Recruit.all()


@app.put("/team/change-tc/{member_id}", tags=['team'])
def change_total_comp(member_id: int, total_comp: Annotated[int, Body(embed=True)]):
    Recruit.__recruits__[member_id].total_comp = total_comp


@app.post("/arbitrary-body")
def body_with_dict(data: dict) -> dict:
    return data


@app.get('/cookies')
def get_cookies(
        content_type: Annotated[str, Header()],
        content_length: Annotated[int, Header()],
        user_name: Annotated[str, Cookie(alias='user-name')],
        pwd: Annotated[str, Cookie()],
        api_token: Annotated[list[str], Header()]
):
    return {
        "type": content_type,
        "len": content_length,
        "usr": user_name,
        "pwd": pwd,
        "tokens": api_token
    }


@app.get('/teleport')
def teleport(url: HttpUrl | None = None):
    return RedirectResponse(url or 'https://google.com')


@app.get('/xml')
def get_xml():
    content = """
    <b>
    TGC
    </b>
    <em>
    $100B
    </em>
    """
    return Response(content, media_type='text/html', headers={'CEO': 'tgc'})


@app.get('/genders', response_model=dict[str, Any])
def get_genders():
    return {
        'm': 'male',
        'f': 'female',
        'other': -1
    }


@app.get('/nf')
def not_found():
    raise HTTPException(status_code=404, headers={'not': 'found'}, detail="NF")


def parse_login_page():
    try:
        with open('page.html', 'r') as page:
            yield page.read()
    except FileNotFoundError as e:
        print("Error occurred holmes: ", e)
        raise NFException("no page found")
    except SecException:
        print("no clearance bud")
    finally:
        print("response sent to client")


@app.get('/team/log-in', tags=['team'])
def get_login_page(content: Annotated[str, Depends(parse_login_page)]):
    return Response(content, media_type='text/html')


@app.post('/login', dependencies=[SecurityTokenVerifier, SecretKeyVerifier])
def log_in(username: Annotated[str, Form()], password: Annotated[str, Form()]):
    print("password: ", password)
    response = f"""
    <html>
    Welcome {username}!
    <br>
    You logged in successfully. <br>
    Here's your secret key: {hash(password)}
    </html>
    """

    return Response(content=response, media_type='text/html')


class NFException(Exception):

    def __init__(self, search_term):
        self.search_term = search_term


class SecException(Exception):

    def __init__(self, detail):
        self.detail = detail


@app.exception_handler(NFException)
def nf_exception_handler(request: Request, e: NFException):
    content = """<html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>404 Not Found</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    color: #333;
                    text-align: center;
                    padding: 50px;
                    margin: 0;
                }
        
                .container {
                    max-width: 600px;
                    margin: 0 auto;
                }
        
                h1 {
                    color: #e44d26;
                }
        
                p {
                    font-size: 18px;
                }
            </style>
        </head>""" + f"""<body>
            <div class="container">
                <h1>404 Not Found</h1>
                <p>Sorry, we couldn't find the page you're requesting</p>
                <p><a href="/team/log-in">Go back to the home page</a></p>
            </div>
        </body>
        </html>"""
    return Response(content, media_type='text/html', status_code=404)


@app.exception_handler(SecException)
def security_exception_handler(request: Request, e: SecException):
    content = """<html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>404 Not Found</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f4f4f4;
                    color: #333;
                    text-align: center;
                    padding: 50px;
                    margin: 0;
                }
        
                .container {
                    max-width: 600px;
                    margin: 0 auto;
                }
        
                h1 {
                    color: #e44d26;
                }
        
                p {
                    font-size: 18px;
                }
            </style>
        </head>""" + f"""<body>
            <div class="container">
                <h1>400 Security Error</h1>
                <p>Invalid authentication: {e.detail}</p>
                <p><a href="/team/log-in">Go back to the home page</a></p>
            </div>
        </body>
        </html>"""

    return Response(content, status_code=400)


@app.get('/search')
def search(query: str):
    raise NFException(query)


@app.post("/json")
def json_enc(p: list[BaseRecruit]):
    foo = jsonable_encoder(p)
    # bar = p.model_dump()
    print(type(foo), foo)
    # print(type(bar), bar)

