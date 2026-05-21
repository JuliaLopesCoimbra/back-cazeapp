import boto3
import uuid
from botocore.exceptions import NoCredentialsError
from fastapi import HTTPException
from app.config.settings import settings

s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY,
    aws_secret_access_key=settings.AWS_SECRET_KEY,
    region_name=settings.AWS_REGION
)

MAX_FILE_SIZE_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


def upload_image_to_s3(image_file, folder: str):
    file_size = _get_file_size(image_file.file)
    if file_size > MAX_FILE_SIZE_BYTES:
        size_mb = file_size / (1024 * 1024)
        raise HTTPException(status_code=413,
                            detail=f"Arquivo '{image_file.filename}' muito grande ({size_mb:.2f} MB). Máximo: {settings.MAX_FILE_SIZE_MB} MB.")
    image_file.file.seek(0)

    file_name = f"{folder}/{uuid.uuid4()}_{image_file.filename}"
    try:
        s3_client.upload_fileobj(image_file.file, settings.AWS_BUCKET, file_name,
                                  ExtraArgs={"ContentType": image_file.content_type})
        return f"https://{settings.AWS_CLOUDFRONT_DOMAIN}/{file_name}"
    except NoCredentialsError:
        raise Exception("Credenciais da AWS não encontradas.")
    except HTTPException:
        raise
    except Exception as e:
        raise Exception(f"Erro ao fazer upload: {str(e)}")


def _get_file_size(file_obj) -> int:
    pos = file_obj.tell()
    file_obj.seek(0, 2)
    size = file_obj.tell()
    file_obj.seek(pos)
    return size
