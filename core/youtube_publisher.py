"""
Módulo de subida de videos a YouTube Data API v3 con subida reanudable (Resumable Upload)
y reintentos automáticos con backoff exponencial.
"""
import os
import time
import http.client
import httplib2
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from core.auth_manager import get_youtube_service
from config.settings import DEFAULT_PRIVACY_STATUS, YOUTUBE_CATEGORY_ID

# Errores recuperables para reintentos
RETRIABLE_EXCEPTIONS = (
    httplib2.HttpLib2Error,
    http.client.NotConnected,
    http.client.IncompleteRead,
    http.client.ImproperConnectionState,
    http.client.CannotSendRequest,
    http.client.CannotSendHeader,
    http.client.ResponseNotReady,
    http.client.BadStatusLine,
    OSError,
)

RETRIABLE_STATUS_CODES = [500, 502, 503, 504]
MAX_RETRIES = 5


def upload_video_to_youtube(
    file_path: str,
    title: str,
    description: str,
    tags: list = None,
    privacy_status: str = DEFAULT_PRIVACY_STATUS,
    category_id: str = YOUTUBE_CATEGORY_ID
) -> dict:
    """
    Sube un video vertical a YouTube como Short usando subida reanudable.
    Retorna el diccionario con la respuesta oficial de YouTube (incluyendo el ID).
    """
    youtube = get_youtube_service()

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or ["shorts"],
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    # Chunk de 4MB para subida estable
    media = MediaFileUpload(
        file_path,
        chunksize=1024 * 1024 * 4,
        resumable=True,
        mimetype="video/*"
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    print(f"[YOUTUBE] Iniciando subida de '{title}' ({os.path.getsize(file_path)} bytes)...")

    response = None
    error = None
    retry = 0

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                print(f"[YOUTUBE] Progreso de subida: {int(status.progress() * 100)}%")
        except HttpError as e:
            if e.resp.status in RETRIABLE_STATUS_CODES:
                error = f"Error HTTP recuperable {e.resp.status}: {e}"
            else:
                raise e
        except RETRIABLE_EXCEPTIONS as e:
            error = f"Error de red recuperable: {e}"

        if error:
            retry += 1
            if retry > MAX_RETRIES:
                raise RuntimeError(f"Se excedió el número máximo de reintentos ({MAX_RETRIES}). Error: {error}")

            sleep_seconds = 2 ** retry
            print(f"[YOUTUBE] {error}. Reintentando en {sleep_seconds} segundos (Intento {retry}/{MAX_RETRIES})...")
            time.sleep(sleep_seconds)
            error = None

    video_id = response.get("id")
    short_url = f"https://youtube.com/shorts/{video_id}"
    print(f"[YOUTUBE] ¡SUBIDA EXITOSA! 🚀")
    print(f"[YOUTUBE] Video ID: {video_id}")
    print(f"[YOUTUBE] Enlace directo: {short_url}")

    return {
        "id": video_id,
        "url": short_url,
        "title": title,
        "privacy": privacy_status
    }
