"""
Manejador de archivos de Google Drive.
Permite listar la cola de videos pendientes, descargar el siguiente video y moverlo a la carpeta de publicados.
"""
import io
import os
import re
from googleapiclient.http import MediaIoBaseDownload
from core.auth_manager import get_drive_service
from config.settings import GDRIVE_PENDING_FOLDER_ID, GDRIVE_PUBLISHED_FOLDER_ID


def _natural_video_sort_key(f: dict):
    """
    Ordena las series de videos de la más nueva a la más antigua (V56 -> V55 -> V54...),
    pero respetando el orden secuencial de sus partes (S01 -> S02 -> S03...)
    para que la historia se publique en el orden correcto para la audiencia.
    """
    name = f.get("name", "")
    m = re.match(r'^[Vv](\d+)[_-][Ss](\d+)', name)
    if m:
        v_num = int(m.group(1))
        s_num = int(m.group(2))
        return (-v_num, s_num, name)
    m_short = re.match(r'^SHORT_(\d+)', name, re.IGNORECASE)
    if m_short:
        return (0, int(m_short.group(1)), name)
    return (1, 0, name)


def list_pending_videos(folder_id: str = None) -> list:
    """
    Obtiene la lista de videos pendientes en la carpeta de Google Drive,
    ordenados con orden natural (series más recientes primero, pero partes en orden 1 a N).
    """
    target_folder = folder_id or GDRIVE_PENDING_FOLDER_ID
    if not target_folder:
        raise ValueError("GDRIVE_PENDING_FOLDER_ID no está configurado.")

    drive_service = get_drive_service()
    query = (
        f"'{target_folder}' in parents and "
        f"trashed = false and "
        f"(mimeType contains 'video/' or name contains '.mp4' or name contains '.mov')"
    )

    results = drive_service.files().list(
        q=query,
        fields="files(id, name, mimeType, size, createdTime)",
        pageSize=100
    ).execute()

    files = results.get("files", [])
    files.sort(key=_natural_video_sort_key)
    return files


def download_video_by_id(file_id: str, output_path: str) -> str:
    """
    Descarga un archivo de video desde Google Drive hacia el disco local por chunks.
    """
    drive_service = get_drive_service()
    request = drive_service.files().get_media(fileId=file_id)

    print(f"[DRIVE] Descargando video (ID: {file_id}) hacia {output_path}...")
    with io.FileIO(output_path, "wb") as fh:
        downloader = MediaIoBaseDownload(fh, request, chunksize=1024 * 1024 * 8)  # Chunks de 8MB
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                print(f"[DRIVE] Progreso de descarga: {int(status.progress() * 100)}%")

    print(f"[DRIVE] Descarga completada: {output_path} (Tamaño: {os.path.getsize(output_path)} bytes)")
    return output_path


def move_video_to_published(file_id: str, pending_folder_id: str = None, published_folder_id: str = None) -> bool:
    """
    Mueve el archivo de la carpeta de pendientes a la carpeta de publicados
    actualizando sus 'parents' en Google Drive.
    """
    p_folder = pending_folder_id or GDRIVE_PENDING_FOLDER_ID
    pub_folder = published_folder_id or GDRIVE_PUBLISHED_FOLDER_ID

    if not pub_folder:
        print("[DRIVE] AVISO: GDRIVE_PUBLISHED_FOLDER_ID no configurado. El archivo no se moverá.")
        return False

    drive_service = get_drive_service()

    # Obtener los padres actuales del archivo
    file_metadata = drive_service.files().get(
        fileId=file_id,
        fields="parents"
    ).execute()

    previous_parents = ",".join(file_metadata.get("parents", []))

    # Mover el archivo cambiando sus padres
    drive_service.files().update(
        fileId=file_id,
        addParents=pub_folder,
        removeParents=previous_parents,
        fields="id, parents"
    ).execute()

    print(f"[DRIVE] Video {file_id} movido exitosamente a la carpeta de Publicados.")
    return True
