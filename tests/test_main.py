from httpx import AsyncClient
from faker import Faker
import pytest

from app.models import Link
from app.services import LinkShortener


class TestEndpoints:
    async def test_add_link_no_body(self, async_client: AsyncClient):
        response = await async_client.post("/add-link", data={})
        assert response.status_code == 422

    @pytest.mark.parametrize("url", ["", "this is not a URL"])
    async def test_add_link_invalid_url(self, url: str, async_client: AsyncClient):
        response = await async_client.post("/add-link", data={"url": url})
        assert response.status_code == 422

    async def test_add_new_link_happy_path(self, async_client: AsyncClient, faker: Faker, mocker):
        full_url = faker.url()
        shortcut = "foo"
        mock_generate_shortcut = mocker.patch.object(
            LinkShortener, "generate_shortcut", return_value=shortcut
        )
        response = await async_client.post("/add-link", json={"url": full_url})
        assert response.status_code == 201
        response_json = response.json()
        assert "id" in response_json
        assert response_json.get("short_link") == str(async_client.base_url) + "/foo"
        mock_generate_shortcut.assert_called_once()

    async def test_add_existing_link(self, async_client: AsyncClient, fake_link: Link):
        response = await async_client.post(
            "/add-link", json={"url": fake_link.full_url}
        )
        assert response.status_code == 201
        assert response.json() == {
            "id": fake_link.id,
            "short_link": f"{async_client.base_url}/{fake_link.shortcut}",
        }

    async def test_unfold_nonexistent_link(
        self, async_client: AsyncClient, random_shortcut: str
    ):
        response = await async_client.get(f"/{random_shortcut}")
        assert response.status_code == 404

    async def test_unfold_link_happy_path(self, async_client: AsyncClient, fake_link: Link):
        response = await async_client.get(f"/{fake_link.shortcut}")
        assert response.status_code == 301
        assert response.headers.get("Location") == fake_link.full_url

    async def test_show_nonexistent_link_info(self, async_client: AsyncClient):
        response = await async_client.get("/show/99")
        assert response.status_code == 404

    async def test_show_link_info_happy_path(self, async_client: AsyncClient, fake_link: Link):
        response = await async_client.get(f"/show/{fake_link.id}")
        assert response.status_code == 200
        assert response.json() == {
            "creator_ip": fake_link.creator_ip,
            "creator_user_agent": fake_link.creator_user_agent,
            "visits": fake_link.visits,
        }
