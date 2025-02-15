from typing import Optional
from pydantic import BaseModel, HttpUrl
from sqlalchemy import TEXT, Column
from sqlmodel import Field, SQLModel


class LinkRequest(BaseModel):
    url: HttpUrl


class Link(SQLModel, table=True):
    __tablename__ = "links"

    id: Optional[int] = Field(default=None, primary_key=True)
    full_url: str = Field(sa_column=Column(TEXT, unique=True, index=True))
    shortcut: str = Field(unique=True, index=True)
    visits: int = Field(default=0)
    creator_ip: str
    creator_user_agent: str
