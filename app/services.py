from typing import Optional
from fastapi import Request
import mmh3
import base62  # type: ignore
from sqlmodel import select

from app.config import get_settings
from app.database import async_session_maker
from app.models import Link


class LinkNotSet(Exception): ...


class LinkShortener:
    full_url: str
    request: Request
    link: Optional[Link] = None

    def __init__(self, *, url: str, request: Request) -> None:
        self.full_url = url
        self.request = request

    async def add_link(self):
        await self.find_existing_link()
        if self.link is None:
            await self.shorten_link()

    def get_result_data(self) -> dict:
        if self.link is None:
            raise LinkNotSet
        return {
            "id": self.link.id,
            "short_link": str(
                self.request.url_for("unfold", shortcut=self.link.shortcut)
            ),
        }

    async def find_existing_link(self) -> None:
        async with async_session_maker() as session:
            result = await session.execute(
                select(Link).where(Link.full_url == self.full_url)
            )
            self.link = result.scalars().first()

    async def shorten_link(self) -> None:
        length = get_settings().shortcut_length
        full_url = self.full_url
        hash_value, _ = mmh3.hash64(full_url, signed=False)
        encoded_url = base62.encode(hash_value)
        short_url = encoded_url[:length].zfill(length)

        async with async_session_maker() as session:
            link = Link(full_url=full_url, shortcut=short_url, **self.get_creator_data())
            session.add(link)
            await session.commit()
            await session.refresh(link)
            self.link = link

    def get_creator_data(self) -> dict:
        return {
            "creator_ip": self.request.client.host if self.request.client else None,
            "creator_user_agent": self.request.headers.get("user-agent"),
        }


async def unfold_link(shortcut: str) -> Optional[str]:
    async with async_session_maker() as session:
        result = await session.execute(select(Link).where(Link.shortcut == shortcut))
        link = result.scalars().first()
        if link is not None:
            link.visits += 1
            session.add(link)
            await session.commit()
            return link.full_url
        return None


async def get_link_info(id: int) -> Optional[dict]:
    async with async_session_maker() as session:
        link = await session.get(Link, id)
        if link:
            return link.model_dump(
                include={"visits", "creator_ip", "creator_user_agent"}
            )
        return None
