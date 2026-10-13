"""
Asistente local para inventario y subida inicial de tus 482 videos a Google Drive.
Escanea tu carpeta local, valida formatos y puede subirlos por lotes a tu carpeta de Google Drive.
"""
import os
import sys
from googleapiclient.http import MediaFileUpload

# Añadir raíz al sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.auth_manager import get_drive_service
from config.settings import GDRIVE_PENDING_FOLDER_ID

VALID_EXTENSIONS = (".mp4", ".mov", ".m4v", ".webm")


def scan_local_folder(folder_path: str):
    """Escanea la carpeta local y devuelve la lista de videos encontrados."""
    if not os.path.isdir(folder_path):
        print(f"❌ La ruta no existe o no es una carpeta: {folder_path}")
        return []

    video_files = []
    total_bytes = 0

    for root, _, files in os.walk(folder_path):
        for f in files:
            if f.lower().endswith(VALID_EXTENSIONS):
                full_path = os.path.join(root, f)
                size = os.path.getsize(full_path)
                total_bytes += size
                video_files.append((f, full_path, size))

    video_files.sort(key=lambda x: x[0])  # Ordenar por nombre

    print(f"\n📊 RESUMEN DEL CATÁLOGO LOCAL:")
    print(f"   Total de videos encontrados: {len(video_files)}")
    print(f"   Peso total: {total_bytes / (1024 * 1024 * 1024):.2f} GB")
    return video_files


def upload_batch_to_gdrive(video_files: list, folder_id: str, limit: int = None):
    """Sube los videos escaneados a la carpeta de Google Drive."""
    drive_service = get_drive_service()
    to_upload = video_files[:limit] if limit else video_files

    print(f"\n📤 Iniciando subida de {len(to_upload)} videos a Google Drive (Carpeta ID: {folder_id})...\n")

    for i, (fname, fpath, size) in enumerate(to_upload, 1):
        print(f"[{i}/{len(to_upload)}] Subiendo '{fname}' ({size / (1024 * 1024):.1f} MB)...")
        file_metadata = {
            "name": fname,
            "parents": [folder_id]
        }
        media = MediaFileUpload(fpath, resumable=True)
        uploaded_file = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id"
        ).execute()
        print(f"   ✅ Subido con éxito (ID en Drive: {uploaded_file.get('id')})")

    print("\n🎉 ¡Lote subido exitosamente a Google Drive!")


def main():
    print("=" * 65)
    print("🎬 ASISTENTE DE INVENTARIO Y SINCRONIZACIÓN DE VIDEOS")
    print("=" * 65)

    folder = input("Ingresa la ruta de tu carpeta local de videos (ej. D:\\Videos\\Shorts): ").strip().strip('"')
    if not folder:
        print("Operación cancelada.")
        return

    videos = scan_local_folder(folder)
    if not videos:
        return

    upload_opt = input("\n¿Deseas subir estos videos a tu Google Drive ahora? (s/n): ").strip().lower()
    if upload_opt == "s":
        target_folder = GDRIVE_PENDING_FOLDER_ID or input("Ingresa el ID de la carpeta 'Shorts_Pendientes' en Drive: ").strip()
        batch_count = input("¿Cuántos videos deseas subir ahora? (Presiona Enter para TODOS): ").strip()
        limit = int(batch_count) if batch_count.isdigit() else None
        upload_batch_to_gdrive(videos, target_folder, limit)


if __name__ == "__main__":
    main()
