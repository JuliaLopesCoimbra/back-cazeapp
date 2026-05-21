from fastapi import APIRouter, UploadFile, File, Form, Depends, Query
from app.core.security.auth_dependency import get_current_user
from app.domain.auth.models.user_model import User
from app.domain.photo_ai.controllers.user_face_controller import (
    register_face,
    get_face_status,
    get_my_photos,
    delete_my_face,
)

router = APIRouter(prefix="/photo-ai", tags=["Photo AI - Cadastro de Rosto"])


@router.post("/register-face")
async def register_face_endpoint(
    file: UploadFile = File(...),
    event_id: str = Form(...),
    current_user: User = Depends(get_current_user),
):
    return await register_face(file, event_id, current_user.id)


@router.get("/my-face-status")
def get_face_status_endpoint(
    event_id: str = Query(...),
    current_user: User = Depends(get_current_user),
):
    return get_face_status(event_id, current_user.id)


@router.get("/my-photos")
def get_my_photos_endpoint(
    event_id: str = Query(...),
    current_user: User = Depends(get_current_user),
):
    return get_my_photos(event_id, current_user.id)


@router.delete("/my-face")
def delete_my_face_endpoint(
    event_id: str = Query(...),
    current_user: User = Depends(get_current_user),
):
    return delete_my_face(event_id, current_user.id)
