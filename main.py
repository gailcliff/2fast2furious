from fastapi import FastAPI, Query
from typing import Annotated
from enum import Enum
from datetime import datetime

from pydantic import BaseModel, Field

app = FastAPI()


class Title(Enum):
    CHIEF = 'ceo'
    OPERATIONS = 'coo'
    TECH = 'cto'


class Recruit(BaseModel):
    name: str
    total_comp: int = 0
    start_date: datetime | None = Field(default_factory=datetime.now)
    __recruits__: list = []

    @classmethod
    def add_recruit(cls, recruit: 'Recruit'):
        cls.__recruits__.append(recruit)

    @classmethod
    def all(cls):
        return cls.__recruits__


@app.get("/team/ceo")
async def get_ceo():
    return {
        Title.CHIEF: "Gail Cliff"
    }


@app.get("/team")
async def get_team_member(title: Annotated[Title, Query()] = None):
    return {
        title or "t": "John Doe"
    }


@app.get("/download/{file:path}")
async def download(file: str):
    return file


@app.post('/team/hire')
def recruit(member: Recruit) -> Recruit:
    Recruit.add_recruit(member)
    return member


@app.get('/team/recruits')
def get_recruits() -> list[Recruit]:
    return Recruit.all()
