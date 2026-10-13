"""
Manejador de archivos de Google Drive.
Permite listar la cola de videos pendientes, descargar el siguiente video y moverlo a la carpeta de publicados.
"""
import io
import os
from googleapiclient.http import MediaIoBaseDownload
from core.auth_manager import get_drive_service
from config.settings import GDRIVE_PENDING_FOLDER_ID, GDRIVE_PUBLISHED_FOLDER_ID


def list_pending_videos(folder_id: str = None) -> list:
    """
    Obtiene la lista de videos pendientes en la carpeta de Google Drive,
    ordenados alfabéticamente por nombre para preservar el orden natural de subida.
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
        orderBy="name desc"
    ).execute()

    files = results.get("files", [])
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
