from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_collection_controller
from app.services.collection import CollectionController, InvalidCriteria, RunAlreadyActive

router = APIRouter(prefix="/runs", tags=["runs"])
Controller = Annotated[CollectionController, Depends(get_collection_controller)]


class StartRun(BaseModel):
    criteria_id: int = Field(gt=0)


@router.post("", status_code=202)
async def start_run(body: StartRun, controller: Controller) -> dict[str, int]:
    try:
        run_id = await controller.start(body.criteria_id)
    except RunAlreadyActive as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InvalidCriteria as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"run_id": run_id}


@router.get("/{run_id}")
async def read_run(run_id: int, controller: Controller) -> dict[str, Any]:
    run = await controller.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="수집 실행을 찾을 수 없습니다")
    return run
