from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import create_db_and_tables, get_async_session
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
    session: Annotated[AsyncSession, Depends(get_async_session)],
):
    service = LinkShortener(url=str(link_request.url), request=request, session=session)
    await service.add_link()
    return JSONResponse(service.get_result_data(), status.HTTP_201_CREATED)


@app.get("/{shortcut}", name="unfold")
async def unfold_link(
    shortcut: str, session: Annotated[AsyncSession, Depends(get_async_session)]
):
    full_url = await unfold_helper(shortcut, session)
    if not full_url:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return RedirectResponse(full_url, status.HTTP_301_MOVED_PERMANENTLY)


@app.get("/show/{id}")
async def show_link_info(
    id: int, session: Annotated[AsyncSession, Depends(get_async_session)]
):
    link_info = await get_link_info(id, session)
    if not link_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return link_info
