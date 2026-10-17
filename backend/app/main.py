from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast

import httpx
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from app.adapters.base import SourceAdapter, SourceName
from app.adapters.saramin import SaraminAdapter
from app.adapters.work24 import Work24Adapter
from app.api.health import router as health_router
from app.api.runs import router as runs_router
from app.config import Settings
from app.db import create_engine, create_session_factory
from app.services.collection import CollectionController


def create_app() -> FastAPI:
    controller: CollectionController | None = None
    client: httpx.AsyncClient | None = None
    engine: AsyncEngine | None = None

    def get_controller() -> CollectionController:
        nonlocal controller, client, engine
        if controller is None:
            settings = Settings()  # type: ignore[call-arg]
            engine = create_engine(settings)
            client = httpx.AsyncClient(timeout=30)
            adapters: dict[SourceName, SourceAdapter] = {}
            if settings.SARAMIN_ACCESS_KEY:
                adapters["saramin"] = SaraminAdapter(client, settings.SARAMIN_ACCESS_KEY)
            if settings.WORK24_AUTH_KEY:
                # The concrete adapter narrows writable max_page from int | None to int.
                adapters["work24"] = cast(
                    SourceAdapter, Work24Adapter(client, settings.WORK24_AUTH_KEY)
                )
            controller = CollectionController(
                create_session_factory(engine),
                adapters,
                budgets={
                    "saramin": settings.SARAMIN_DAILY_BUDGET,
                    "work24": settings.WORK24_DAILY_BUDGET,
                },
            )
        return controller

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        if controller is not None:
            await controller.wait()
        if client is not None:
            await client.aclose()
        if engine is not None:
            await engine.dispose()

    app = FastAPI(lifespan=lifespan)
    app.state.collection_controller_factory = get_controller
    app.include_router(health_router)
    app.include_router(runs_router)
    return app
