#!/usr/bin/env python3
"""
photo_sync.py — Robot: Google Drive → S3 → Rekognition

Fluxo:
  1. Lê a pasta do Drive (fotógrafos jogam fotos lá)
  2. Baixa arquivos que ainda não foram processados
  3. Faz upload para S3 em {event_id}/{nome_arquivo}
  4. Indexa cada novo arquivo no Rekognition (pula os já indexados)
  5. Salva estado local para não reprocessar na próxima rodada

Uso:
  python sync.py --event-id 42 --drive-folder-id 1BxiMVs0XRA5...
  python sync.py --event-id 42 --drive-folder-id 1BxiMVs0XRA5... --once
"""

import os
import json
import time
import logging
import argparse
import urllib.request
import boto3
from io import BytesIO
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("photo-sync")

# ── Config via env ────────────────────────────────────────────────────────────
AWS_ACCESS_KEY      = os.environ["AWS_ACCESS_KEY"]
AWS_SECRET_KEY      = os.environ["AWS_SECRET_KEY"]
AWS_REGION          = os.environ.get("REKOGNITION_REGION", "us-east-2")
S3_BUCKET           = os.environ["REKOGNITION_BUCKET"]
CREDENTIALS_PATH    = os.environ.get("GOOGLE_CREDENTIALS_PATH", "/etc/photo-sync/credentials.json")
STATE_FILE          = os.environ.get("STATE_FILE", "/var/lib/photo-sync/state.json")
CHECK_INTERVAL      = int(os.environ.get("CHECK_INTERVAL_SECONDS", "60"))

HEARTBEAT_URL  = os.environ.get("HEARTBEAT_URL", "")
HEARTBEAT_KEY  = os.environ.get("HEARTBEAT_API_KEY", "")
SERVER_NAME    = os.environ.get("SERVER_NAME", "")

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

# ── Heartbeat ─────────────────────────────────────────────────────────────────
def send_heartbeat(event_id: str, stats: dict, duration: float):
    if not HEARTBEAT_URL or not HEARTBEAT_KEY:
        return
    try:
        payload = json.dumps({
            "event_id": event_id,
            "server_name": SERVER_NAME,
            "new_files": stats.get("new_files", 0),
            "uploaded": stats.get("upload", 0),
            "indexed": stats.get("indexado", 0),
            "no_face": stats.get("sem_rosto", 0),
            "errors": stats.get("erro", 0),
            "duration_seconds": round(duration, 2),
            "total_drive_files": stats.get("total_drive_files", 0),
            "new_s3_keys": stats.get("new_s3_keys", []),
        }).encode()
        req = urllib.request.Request(
            HEARTBEAT_URL,
            data=payload,
            headers={"Content-Type": "application/json", "X-Sync-Api-Key": HEARTBEAT_KEY},
            method="POST",
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        log.warning(f"Heartbeat falhou (não crítico): {e}")

# ── Estado local (quais Drive file IDs já foram processados) ──────────────────
def load_state(event_id: str) -> set:
    try:
        with open(STATE_FILE) as f:
            data = json.load(f)
            return set(data.get(event_id, []))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_state(event_id: str, processed: set):
    Path(STATE_FILE).parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(STATE_FILE) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    data[event_id] = list(processed)
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=2)

# ── Google Drive ───────────────────────────────────────────────────────────────
def get_drive_service():
    creds = service_account.Credentials.from_service_account_file(
        CREDENTIALS_PATH, scopes=DRIVE_SCOPES
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)

def list_drive_images(service, folder_id: str) -> list:
    """Lista todas as imagens na pasta do Drive (inclui subpastas não)."""
    files = []
    page_token = None
    query = (
        f"'{folder_id}' in parents"
        f" and trashed = false"
        f" and (mimeType = 'image/jpeg' or mimeType = 'image/png' or mimeType = 'image/jpg')"
    )
    while True:
        resp = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token,
            pageSize=200,
        ).execute()
        files.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return files

def download_drive_file(service, file_id: str) -> bytes:
    request = service.files().get_media(fileId=file_id)
    buf = BytesIO()
    downloader = MediaIoBaseDownload(buf, request, chunksize=10 * 1024 * 1024)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue()

# ── AWS S3 + Rekognition ───────────────────────────────────────────────────────
def get_aws_clients():
    kwargs = dict(
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
        region_name=AWS_REGION,
    )
    return boto3.client("s3", **kwargs), boto3.client("rekognition", **kwargs)

def upload_to_s3(s3, data: bytes, s3_key: str):
    s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=data)

def get_indexed_face_names(reko, collection_id: str) -> set:
    """Retorna nomes (sem extensão) de todos os rostos já indexados na coleção."""
    indexed = set()
    next_token = None
    while True:
        kwargs = {"CollectionId": collection_id, "MaxResults": 4096}
        if next_token:
            kwargs["NextToken"] = next_token
        try:
            resp = reko.list_faces(**kwargs)
        except reko.exceptions.ResourceNotFoundException:
            # Coleção ainda não existe — cria e retorna vazio
            reko.create_collection(CollectionId=collection_id)
            log.info(f"Coleção '{collection_id}' criada no Rekognition.")
            return set()
        for face in resp.get("Faces", []):
            if "ExternalImageId" in face:
                indexed.add(face["ExternalImageId"])
        next_token = resp.get("NextToken")
        if not next_token:
            break
    return indexed

def index_s3_file(reko, s3_key: str, collection_id: str, external_id: str) -> str:
    """
    Indexa um arquivo S3 no Rekognition.
    Retorna: 'ok' | 'no_face' | 'error'
    """
    try:
        resp = reko.index_faces(
            CollectionId=collection_id,
            Image={"S3Object": {"Bucket": S3_BUCKET, "Name": s3_key}},
            ExternalImageId=external_id,
            MaxFaces=15,
            QualityFilter="AUTO",
            DetectionAttributes=["DEFAULT"],
        )
        return "ok" if resp.get("FaceRecords") else "no_face"
    except Exception as e:
        log.warning(f"Erro ao indexar {s3_key}: {e}")
        return "error"

# ── Ciclo de sync ─────────────────────────────────────────────────────────────
def sync_once(drive_service, s3, reko, folder_id: str, event_id: str):
    t0 = time.time()
    collection_id = event_id
    s3_prefix = f"{event_id}/"

    processed = load_state(event_id)
    drive_files = list_drive_images(drive_service, folder_id)
    new_files = [f for f in drive_files if f["id"] not in processed]

    total_drive = len(drive_files)

    if not new_files:
        log.info(f"Sem arquivos novos. Total no Drive: {total_drive}.")
        send_heartbeat(event_id, {"new_files": 0, "upload": 0, "indexado": 0, "sem_rosto": 0, "erro": 0, "total_drive_files": total_drive}, time.time() - t0)
        return

    log.info(f"{len(new_files)} arquivo(s) novo(s). Iniciando sync...")
    send_heartbeat(event_id, {"new_files": len(new_files), "upload": 0, "indexado": 0, "sem_rosto": 0, "erro": 0, "total_drive_files": total_drive}, 0)

    # Pega nomes já indexados para não duplicar no Rekognition
    indexed_names = get_indexed_face_names(reko, collection_id)

    stats = {"new_files": len(new_files), "upload": 0, "indexado": 0, "sem_rosto": 0, "erro": 0, "total_drive_files": total_drive, "new_s3_keys": []}

    for file in new_files:
        name   = file["name"]
        fid    = file["id"]
        ext    = Path(name).suffix.lower() or ".jpg"
        s3_key = f"{s3_prefix}{fid}{ext}"   # Drive ID garante unicidade

        try:
            # 1. Baixa do Drive
            data = download_drive_file(drive_service, fid)

            # 2. Manda pro S3
            upload_to_s3(s3, data, s3_key)
            stats["upload"] += 1
            stats["new_s3_keys"].append(s3_key)
            log.info(f"  ✓ S3: {name} → {fid}{ext}")

            # 3. Indexa no Rekognition (só se ainda não indexado)
            if fid not in indexed_names:
                resultado = index_s3_file(reko, s3_key, collection_id, fid)
                if resultado == "ok":
                    stats["indexado"] += 1
                    indexed_names.add(fid)
                    log.info(f"  ✓ Rekognition: {name}")
                elif resultado == "no_face":
                    stats["sem_rosto"] += 1
                    log.info(f"  ⚠ Sem rosto detectado: {name}")
                else:
                    stats["erro"] += 1
            else:
                log.info(f"  → Já indexado: {name}")

            # 4. Marca como processado (salva a cada arquivo para não perder progresso)
            processed.add(fid)
            save_state(event_id, processed)

        except Exception as e:
            stats["erro"] += 1
            log.error(f"  ✗ Erro em {name}: {e}")

    log.info(
        f"Ciclo concluído — "
        f"upload: {stats['upload']} | "
        f"indexados: {stats['indexado']} | "
        f"sem rosto: {stats['sem_rosto']} | "
        f"erros: {stats['erro']}"
    )
    send_heartbeat(event_id, stats, time.time() - t0)

# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Drive → S3 → Rekognition sync")
    parser.add_argument("--event-id",       required=True, help="ID do evento (= collection_id)")
    parser.add_argument("--drive-folder-id",required=True, help="ID da pasta no Google Drive")
    parser.add_argument("--once", action="store_true",     help="Roda uma vez e sai (sem loop)")
    args = parser.parse_args()

    log.info(f"=== Photo Sync iniciado | evento={args.event_id} | pasta={args.drive_folder_id} ===")
    log.info(f"Bucket S3: {S3_BUCKET} | Região: {AWS_REGION}")
    if not args.once:
        log.info(f"Intervalo: {CHECK_INTERVAL}s")

    drive = get_drive_service()
    s3, reko = get_aws_clients()

    if args.once:
        sync_once(drive, s3, reko, args.drive_folder_id, args.event_id)
        return

    while True:
        try:
            sync_once(drive, s3, reko, args.drive_folder_id, args.event_id)
        except Exception as e:
            log.error(f"Erro inesperado no ciclo: {e}")
        log.info(f"Aguardando {CHECK_INTERVAL}s...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
