"""
Orquestador principal autónomo (Worker).
Se ejecuta periódicamente en GitHub Actions (o en local).
Flujo:
1. Candado de Cooldown (anti-duplicados).
2. Obtener siguiente video pendiente en Google Drive.
3. Descargar a entorno efímero.
4. Generar metadatos optimizados (#Shorts + SEO).
5. Subir a YouTube con reintentos y subida reanudable.
6. Mover archivo a carpeta 'Publicados' en Google Drive.
7. Limpieza de archivos temporales.
"""
import os
import sys
import tempfile

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from core.cooldown_lock import check_cooldown_lock
from core.drive_manager import list_pending_videos, download_video_by_id, move_video_to_published
from core.metadata_optimizer import build_metadata
from core.youtube_publisher import upload_video_to_youtube


def write_github_summary(content: str):
    """Escribe en el Step Summary de GitHub Actions si está disponible."""
    summary_file = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_file:
        try:
            with open(summary_file, "a", encoding="utf-8") as f:
                f.write(content + "\n")
        except Exception:
            pass


def run_worker():
    print("=" * 60)
    print("[AUTOPILOT] INICIANDO EJECUCION AUTONOMA DE SUBIDA DE SHORTS")
    print("=" * 60)

    # 1. CANDADO DE COOLDOWN
    can_publish, lock_reason = check_cooldown_lock()
    print(f"[COOLDOWN] {lock_reason}")
    if not can_publish:
        print("[AVISO] Abortando ejecución preventiva para proteger el canal de spam y cuidar la cuota.")
        write_github_summary(f"### ⏸️ Publicación Omitida (Candado Activo)\n\n> {lock_reason}")
        return 0

    # 2. OBTENER LISTA DE VIDEOS EN GOOGLE DRIVE
    pending_videos = list_pending_videos()
    if not pending_videos:
        msg = "⚠️ No hay videos pendientes en la carpeta de Google Drive. La cola está vacía."
        print(f"[DRIVE] {msg}")
        write_github_summary(f"### ⚠️ Cola Vacía\n\nNo se encontraron videos pendientes en Google Drive.")
        return 0

    total_pending = len(pending_videos)
    current_video = pending_videos[0]
    file_id = current_video["id"]
    original_name = current_video["name"]

    print(f"[COLA] Videos pendientes en cola: {total_pending}")
    print(f"[COLA] Siguiente video a procesar: '{original_name}' (ID: {file_id})")

    # 3. METADATOS
    metadata = build_metadata(original_name)
    title = metadata["title"]
    description = metadata["description"]
    tags = metadata["tags"]
    localizations = metadata.get("localizations", {})

    print(f"[METADATOS] Título generado: {title}")
    print(f"[METADATOS] Tags: {', '.join(tags)}")
    print(f"[METADATOS] Localizaciones: {len(localizations)} idiomas")

    # 4. DESCARGA EFÍMERA
    temp_dir = tempfile.gettempdir()
    local_temp_path = os.path.join(temp_dir, f"temp_{file_id}.mp4")

    try:
        download_video_by_id(file_id, local_temp_path)

        # 5. SUBIDA A YOUTUBE
        upload_result = upload_video_to_youtube(
            file_path=local_temp_path,
            title=title,
            description=description,
            tags=tags,
            localizations=localizations
        )

        video_id = upload_result["id"]
        short_url = upload_result["url"]

        # 6. MOVER A CARPETA DE PUBLICADOS EN DRIVE
        move_video_to_published(file_id)

        # 7. REPORTE FINAL
        summary = (
            f"### 🚀 ¡Short Publicado con Éxito!\n\n"
            f"- **Título:** `{title}`\n"
            f"- **Video ID:** `{video_id}`\n"
            f"- **Enlace:** [{short_url}]({short_url})\n"
            f"- **Videos restantes en cola:** `{total_pending - 1}`\n"
        )
        print("\n" + summary)
        write_github_summary(summary)

    finally:
        # Limpieza de archivo temporal
        if os.path.exists(local_temp_path):
            try:
                os.remove(local_temp_path)
                print(f"[SISTEMA] Archivo temporal eliminado: {local_temp_path}")
            except Exception as e:
                print(f"[SISTEMA] No se pudo borrar el temporal: {e}")

    return 0


if __name__ == "__main__":
    exit_code = run_worker()
    sys.exit(exit_code)
