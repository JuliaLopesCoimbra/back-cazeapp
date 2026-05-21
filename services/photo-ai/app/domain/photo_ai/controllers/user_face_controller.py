import logging
from fastapi import UploadFile, HTTPException
from app.config.admin_db import AdminSessionLocal
from app.config.interaction_db import SessionLocal as InteractionSessionLocal
from app.domain.photo_ai.services.rekognition_service import RekognitionService
from app.domain.photo_ai.repositories.user_face_repository import UserFaceRepository
from app.domain.users.repositories.user_photo_repository import UserPhotoRepository

logger = logging.getLogger(__name__)

SELFIE_S3_PREFIX = "user-selfies"


def _selfie_s3_key(user_id: int, event_id: str) -> str:
    return f"{SELFIE_S3_PREFIX}/{event_id}/{user_id}.jpg"


def _sync_photos_from_rekognition(service: RekognitionService, user_id: int, event_id: str) -> None:
    """Search user's stored selfie against the event collection and insert any new matches."""
    key = _selfie_s3_key(user_id, event_id)
    try:
        obj = service.s3.get_object(Bucket=service.bucket_name, Key=key)
        selfie_bytes = obj['Body'].read()
    except service.s3.exceptions.NoSuchKey:
        return  # selfie not stored yet (old registration)
    except Exception as e:
        logger.warning(f"Could not load selfie from S3 for user {user_id} event {event_id}: {e}")
        return

    try:
        search_resp = service.rekognition.search_faces_by_image(
            CollectionId=event_id,
            Image={'Bytes': selfie_bytes},
            MaxFaces=100,
            FaceMatchThreshold=60.0,
        )
    except service.rekognition.exceptions.ResourceNotFoundException:
        return  # event collection doesn't exist yet
    except Exception as e:
        logger.warning(f"Rekognition sync failed for user {user_id} event {event_id}: {e}")
        return

    matches = search_resp.get('FaceMatches', [])
    if not matches:
        return

    interaction_db = InteractionSessionLocal()
    try:
        for match in matches:
            drive_file_id = match['Face']['ExternalImageId']
            if not UserPhotoRepository.get(interaction_db, user_id, event_id, drive_file_id):
                nome_completo = service.buscar_nome_completo_s3(drive_file_id, event_id)
                s3_key = f"{event_id}/{nome_completo}"
                UserPhotoRepository.create(interaction_db, {
                    'user_id': user_id,
                    'event_id': event_id,
                    'drive_file_id': drive_file_id,
                    's3_key': s3_key,
                    'similarity': match['Similarity'],
                    'notified': True,
                })
    finally:
        interaction_db.close()


async def register_face(file: UploadFile, event_id: str, user_id: int) -> dict:
    service = RekognitionService()

    image_bytes = await file.read()
    image_bytes = service.redimensionar_imagem(image_bytes)

    detect_response = service.rekognition.detect_faces(
        Image={'Bytes': image_bytes},
        Attributes=['DEFAULT'],
    )
    face_count = len(detect_response.get('FaceDetails', []))

    if face_count == 0:
        raise HTTPException(
            status_code=400,
            detail="Nenhum rosto detectado. Tire a foto em local bem iluminado, de frente para a câmera.",
        )
    if face_count > 1:
        raise HTTPException(
            status_code=400,
            detail=f"A selfie deve ter apenas 1 rosto. Detectamos {face_count} rostos. Tire a foto sozinho.",
        )

    users_collection = f"users_{event_id}"
    service.inicializar_colecao(users_collection)

    admin_db = AdminSessionLocal()
    try:
        existing = UserFaceRepository.get_by_user_event(admin_db, user_id, event_id)
        if existing and existing.rekognition_face_id:
            try:
                service.rekognition.delete_faces(
                    CollectionId=users_collection,
                    FaceIds=[existing.rekognition_face_id],
                )
            except Exception as e:
                logger.warning(f"Failed to delete old face from Rekognition: {e}")
        if existing:
            UserFaceRepository.delete(admin_db, existing)
    finally:
        admin_db.close()

    index_response = service.rekognition.index_faces(
        CollectionId=users_collection,
        Image={'Bytes': image_bytes},
        ExternalImageId=str(user_id),
        MaxFaces=1,
        QualityFilter="AUTO",
        DetectionAttributes=['DEFAULT'],
    )

    if not index_response.get('FaceRecords'):
        raise HTTPException(
            status_code=422,
            detail="Não foi possível indexar o rosto. Use uma foto com melhor iluminação e enquadramento.",
        )

    face_id = index_response['FaceRecords'][0]['Face']['FaceId']

    admin_db = AdminSessionLocal()
    try:
        UserFaceRepository.create(admin_db, {
            'user_id': user_id,
            'event_id': event_id,
            'rekognition_face_id': face_id,
            'collection_id': users_collection,
        })
    finally:
        admin_db.close()

    # Persist selfie so future syncs can search without re-uploading
    try:
        service.s3.put_object(
            Bucket=service.bucket_name,
            Key=_selfie_s3_key(user_id, event_id),
            Body=image_bytes,
            ContentType='image/jpeg',
        )
    except Exception as e:
        logger.warning(f"Failed to save selfie to S3 for user {user_id}: {e}")

    # Backfill: find existing event photos containing this face
    _sync_photos_from_rekognition(service, user_id, event_id)

    return {
        "success": True,
        "message": "Rosto cadastrado! Você será notificado quando novas fotos suas chegarem.",
    }


def get_face_status(event_id: str, user_id: int) -> dict:
    admin_db = AdminSessionLocal()
    try:
        existing = UserFaceRepository.get_by_user_event(admin_db, user_id, event_id)
        if existing:
            return {
                "registered": True,
                "registered_at": existing.registered_at.isoformat() if existing.registered_at else None,
            }
        return {"registered": False}
    finally:
        admin_db.close()


def get_my_photos(event_id: str, user_id: int) -> list:
    service = RekognitionService()

    # Sync any new matches from Rekognition before returning
    _sync_photos_from_rekognition(service, user_id, event_id)

    interaction_db = InteractionSessionLocal()
    try:
        photos = UserPhotoRepository.list_by_user_event(interaction_db, user_id, event_id)
        result = []
        for p in photos:
            if p.s3_key:
                try:
                    image_url = service._gerar_url_assinada_cloudfront(p.s3_key)
                except Exception:
                    image_url = ""
            else:
                image_url = ""
            result.append({
                "drive_file_id": p.drive_file_id,
                "s3_key": p.s3_key or "",
                "image_url": image_url,
                "similarity": p.similarity,
                "associated_at": p.associated_at.isoformat() if p.associated_at else None,
            })
        return result
    finally:
        interaction_db.close()


def delete_my_face(event_id: str, user_id: int) -> dict:
    service = RekognitionService()
    users_collection = f"users_{event_id}"

    admin_db = AdminSessionLocal()
    try:
        existing = UserFaceRepository.get_by_user_event(admin_db, user_id, event_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Nenhum rosto cadastrado para este evento.")

        if existing.rekognition_face_id:
            try:
                service.rekognition.delete_faces(
                    CollectionId=users_collection,
                    FaceIds=[existing.rekognition_face_id],
                )
            except Exception as e:
                logger.warning(f"Failed to delete face from Rekognition: {e}")

        # Remove stored selfie from S3
        try:
            service.s3.delete_object(
                Bucket=service.bucket_name,
                Key=_selfie_s3_key(user_id, event_id),
            )
        except Exception as e:
            logger.warning(f"Failed to delete selfie from S3 for user {user_id}: {e}")

        UserFaceRepository.delete(admin_db, existing)
        return {"success": True}
    finally:
        admin_db.close()
