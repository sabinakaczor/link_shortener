from typing import cast
from unittest.mock import MagicMock
from fastapi import Request
from faker import Faker
from fastapi.datastructures import URL
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models import Link
from app.services import LinkNotSet, LinkShortener, get_link_info, unfold_link


class TestLinkShortener:
    def test_get_result_data_link_not_set(
        self, async_session: AsyncSession, faker: Faker
    ):
        mock_request = MagicMock(spec=Request)
        service = LinkShortener(
            url=faker.url(), request=mock_request, session=async_session
        )
        with pytest.raises(LinkNotSet):
            service.get_result_data()

    def test_get_result_data_happy_path(
        self, async_session: AsyncSession, fake_link: Link
    ):
        short_url = "http://test/foo"
        mock_request: Request = MagicMock(spec=Request)
        mock_request.url_for.side_effect = lambda name, **args: URL(short_url)
        service = LinkShortener(
            url=fake_link.full_url, request=mock_request, session=async_session
        )
        service.link = fake_link
        result = service.get_result_data()
        assert result == {
            "id": fake_link.id,
            "short_link": short_url,
        }

    async def test_find_existing_link_nonexistent(
        self, async_session: AsyncSession, faker: Faker
    ):
        mock_request = MagicMock(spec=Request)
        service = LinkShortener(
            url=faker.url(), request=mock_request, session=async_session
        )
        await service.find_existing_link()
        assert service.link is None

    async def test_find_existing_link_happy_path(
        self, async_session: AsyncSession, fake_link: Link
    ):
        mock_request = MagicMock(spec=Request)
        service = LinkShortener(
            url=fake_link.full_url, request=mock_request, session=async_session
        )
        await service.find_existing_link()
        assert service.link == fake_link

    async def test_add_link_existent(
        self, async_session: AsyncSession, fake_link: Link, mocker
    ):
        mock_request = MagicMock(spec=Request)
        service = LinkShortener(
            url=fake_link.full_url, request=mock_request, session=async_session
        )
        mock_shorten_link = mocker.patch.object(LinkShortener, "shorten_link")
        await service.add_link()
        mock_shorten_link.assert_not_called()

    async def test_shorten_link(
        self, async_session: AsyncSession, faker: Faker, mocker
    ):
        full_url, shortcut, ip, user_agent = (
            faker.url(),
            "foo",
            faker.ipv4(),
            faker.user_agent(),
        )
        mock_request = MagicMock(spec=Request)
        service = LinkShortener(
            url=full_url, request=mock_request, session=async_session
        )
        mocker.patch.object(service, "generate_shortcut", return_value=shortcut)
        mocker.patch.object(
            service,
            "get_creator_data",
            return_value={
                "creator_ip": ip,
                "creator_user_agent": user_agent,
            },
        )
        await service.shorten_link()
        new_link = service.link
        assert new_link is not None
        assert new_link.full_url == full_url
        assert new_link.shortcut == shortcut
        assert new_link.creator_ip == ip
        assert new_link.creator_user_agent == user_agent

    def test_generate_shortcut(self, async_session: AsyncSession, faker: Faker):
        mock_request = MagicMock(spec=Request)
        service = LinkShortener(
            url=faker.url(), request=mock_request, session=async_session
        )
        shortcut = service.generate_shortcut()
        assert len(shortcut) == get_settings().shortcut_length

    def test_get_creator_data(self, async_session: AsyncSession, faker: Faker):
        ip, user_agent = (faker.ipv4(), faker.user_agent())
        mock_request = MagicMock(spec=Request)
        mock_request.client.host = ip
        mock_request.headers = {"user-agent": user_agent}
        service = LinkShortener(
            url=faker.url(), request=mock_request, session=async_session
        )
        assert service.get_creator_data() == {
            "creator_ip": ip,
            "creator_user_agent": user_agent,
        }


class TestHelperFunctions:
    async def test_unfold_nonexistent_link(
        self, async_session: AsyncSession, random_shortcut: str
    ):
        result = await unfold_link(random_shortcut, async_session)
        assert result is None

    async def test_unfold_link_happy_path(
        self, async_session: AsyncSession, fake_link: Link
    ):
        initial_visits_counter = fake_link.visits
        result = await unfold_link(fake_link.shortcut, async_session)
        assert result == fake_link.full_url
        assert fake_link.visits == initial_visits_counter + 1

    async def test_get_nonexistent_link_info(self, async_session: AsyncSession):
        info = await get_link_info(99, async_session)
        assert info is None

    async def test_get_link_info_happy_path(
        self, async_session: AsyncSession, fake_link: Link
    ):
        info = await get_link_info(cast(int, fake_link.id), async_session)
        assert info == {
            "creator_ip": fake_link.creator_ip,
            "creator_user_agent": fake_link.creator_user_agent,
            "visits": fake_link.visits,
        }
