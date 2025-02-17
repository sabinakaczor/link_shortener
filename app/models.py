from typing import Optional
from pydantic import Field, BaseModel, HttpUrl
from sqlalchemy import TEXT, Column
from sqlmodel import Field as DBField, SQLModel


class LinkRequest(BaseModel):
    url: HttpUrl


class Link(SQLModel, table=True):
    __tablename__ = "links"

    id: Optional[int] = DBField(default=None, primary_key=True)
    full_url: str = DBField(sa_column=Column(TEXT, unique=True, index=True))
    shortcut: str = DBField(unique=True, index=True)
    visits: int = DBField(default=0)
    creator_ip: str
    creator_user_agent: str


class CreatedLinkResponse(BaseModel):
    id: int = Field(examples=[1])
    short_link: HttpUrl = Field(examples=["http://localhost:8008/FXg7AErTt0"])


class LinkInfoResponse(BaseModel):
    visits: int = Field(examples=[3])
    creator_ip: str = Field(examples=["192.168.64.1"])
    creator_user_agent: str = Field(
        examples=[
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0"
        ]
    )
