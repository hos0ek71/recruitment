from typing import cast

from fastapi import Request

from app.services.collection import CollectionController


async def get_collection_controller(request: Request) -> CollectionController:
    return cast(CollectionController, request.app.state.collection_controller_factory())
