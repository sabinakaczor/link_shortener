from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import RedirectResponse

from app.config import get_settings
from app.database import create_db_and_tables
from app.models import LinkRequest
from app.services import LinkShortener, get_link_info, unfold_link as unfold_helper


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(title=get_settings().app_name, lifespan=lifespan)


@app.get("/")
def home():
    return RedirectResponse("/docs")


@app.post("/add-link")
async def add_link(
    link_request: LinkRequest,
    request: Request,
):
    service = LinkShortener(url=str(link_request.url), request=request)
    await service.add_link()
    return service.get_result_data()


@app.get("/{shortcut}", name="unfold")
async def unfold_link(shortcut: str):
    full_url = await unfold_helper(shortcut)
    if not full_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return RedirectResponse(full_url)


@app.get("/show/{id}")
async def link_info(id: int):
    link_info = await get_link_info(id)
    if not link_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return link_info
