from datetime import date, time

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.config.admin_db import get_admin_db
from app.core.security.auth_dependency import get_current_user, require_admin
from app.domain.admin.controllers.world_cup_game_controller import WorldCupGameController
from app.domain.admin.schemas.world_cup_game_schema import WorldCupGameResponseSchema
from app.domain.auth.models.user_model import User
from app.infra.s3_upload import upload_image_to_s3

router = APIRouter(prefix="/admin/events", tags=["Admin - World Cup Games"])


def _parse_date(date_str: str) -> date:
    try:
        return date.fromisoformat(date_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use AAAA-MM-DD")


def _parse_time(time_str: str) -> time:
    try:
        parts = time_str.split(":")
        return time(int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        raise HTTPException(status_code=400, detail="Formato de horário inválido. Use HH:mm")


@router.post(
    "/{event_id}/world-cup-games",
    response_model=WorldCupGameResponseSchema,
    status_code=status.HTTP_201_CREATED,
)
def create_world_cup_game(
    event_id: int,
    title: str = Form(...),
    description: str = Form(None),
    game_date: str = Form(None),
    game_time: str = Form(None),
    photo: UploadFile = File(None),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin),
):
    photo_url = upload_image_to_s3(photo, "world_cup_games") if photo else None

    data = {
        "event_id": event_id,
        "title": title,
        "description": description,
        "photo_url": photo_url,
        "game_date": _parse_date(game_date) if game_date else None,
        "game_time": _parse_time(game_time) if game_time else None,
    }

    try:
        return WorldCupGameController.create(db, data, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/{event_id}/world-cup-games",
    response_model=list[WorldCupGameResponseSchema],
)
def list_world_cup_games(
    event_id: int,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    return WorldCupGameController.list_by_event(db, event_id, limit, offset)


@router.get(
    "/{event_id}/world-cup-games/{game_id}",
    response_model=WorldCupGameResponseSchema,
)
def get_world_cup_game(
    event_id: int,
    game_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(get_current_user),
):
    try:
        game = WorldCupGameController.get_by_id(db, game_id)
        if game.event_id != event_id:
            raise HTTPException(status_code=404, detail="Jogo não encontrado neste evento")
        return game
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put(
    "/{event_id}/world-cup-games/{game_id}",
    response_model=WorldCupGameResponseSchema,
)
def update_world_cup_game(
    event_id: int,
    game_id: int,
    title: str = Form(...),
    description: str = Form(None),
    game_date: str = Form(None),
    game_time: str = Form(None),
    photo: UploadFile = File(None),
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin),
):
    try:
        game = WorldCupGameController.get_by_id(db, game_id)
        if game.event_id != event_id:
            raise HTTPException(status_code=404, detail="Jogo não encontrado neste evento")

        photo_url = upload_image_to_s3(photo, "world_cup_games") if photo else game.photo_url

        data = {
            "title": title,
            "description": description,
            "photo_url": photo_url,
            "game_date": _parse_date(game_date) if game_date else None,
            "game_time": _parse_time(game_time) if game_time else None,
        }

        return WorldCupGameController.update(db, game_id, data, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete(
    "/{event_id}/world-cup-games/{game_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_world_cup_game(
    event_id: int,
    game_id: int,
    db: Session = Depends(get_admin_db),
    user: User = Depends(require_admin),
):
    try:
        game = WorldCupGameController.get_by_id(db, game_id)
        if game.event_id != event_id:
            raise HTTPException(status_code=404, detail="Jogo não encontrado neste evento")
        WorldCupGameController.delete(db, game_id, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
