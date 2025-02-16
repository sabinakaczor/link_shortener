from typing import Optional
from fastapi import Request
import mmh3
import base62  # type: ignore
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Link


class LinkNotSet(Exception): ...


class LinkShortener:
    full_url: str
    request: Request
    session: AsyncSession
    link: Optional[Link] = None

    def __init__(self, *, url: str, request: Request, session: AsyncSession) -> None:
        self.full_url = url
        self.request = request
        self.session = session

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
        result = await self.session.execute(
            select(Link).where(Link.full_url == self.full_url)
        )
        self.link = result.scalars().first()

    async def shorten_link(self) -> None:
        link = Link(
            full_url=self.full_url,
            shortcut=self.generate_shortcut(),
            **self.get_creator_data(),
        )
        self.session.add(link)
        await self.session.commit()
        await self.session.refresh(link)
        self.link = link

    def generate_shortcut(self) -> str:
        length = get_settings().shortcut_length
        full_url = self.full_url
        hash_value, _ = mmh3.hash64(full_url, signed=False)
        encoded_url = base62.encode(hash_value)
        return encoded_url[:length].zfill(length)

    def get_creator_data(self) -> dict:
        return {
            "creator_ip": self.request.client.host if self.request.client else None,
            "creator_user_agent": self.request.headers.get("user-agent"),
        }


async def unfold_link(shortcut: str, session: AsyncSession) -> Optional[str]:
    result = await session.execute(select(Link).where(Link.shortcut == shortcut))
    link = result.scalars().first()
    if link is not None:
        link.visits += 1
        session.add(link)
        await session.commit()
        return link.full_url
    return None


async def get_link_info(id: int, session: AsyncSession) -> Optional[dict]:
    link = await session.get(Link, id)
    if link:
        return link.model_dump(include={"visits", "creator_ip", "creator_user_agent"})
    return None
