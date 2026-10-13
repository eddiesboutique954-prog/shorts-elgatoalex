"""
Candado Anti-Duplicados y Protección de Cuota de YouTube.
Consulta el canal para comprobar cuándo se publicó el último video.
Si se publicó hace menos de X minutos, aborta para evitar saturación y duplicados.
"""
from datetime import datetime, timezone

try:
    import dateutil.parser
    def parse_iso(dt_str):
        return dateutil.parser.isoparse(dt_str)
except ImportError:
    def parse_iso(dt_str):
        clean = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(clean)

from core.auth_manager import get_youtube_service
from config.settings import COOLDOWN_MINUTES


def check_cooldown_lock(cooldown_minutes: int = COOLDOWN_MINUTES) -> tuple[bool, str]:
    """
    Verifica si es seguro publicar un nuevo video.
    Retorna:
        (True, "OK para publicar") si pasaron más de cooldown_minutes desde el último video.
        (False, "Razón") si se publicó hace poco tiempo.
    """
    youtube = get_youtube_service()

    # 1. Obtener el ID del canal autenticado y su lista de subidas
    channels_response = youtube.channels().list(
        mine=True,
        part="contentDetails"
    ).execute()

    items = channels_response.get("items", [])
    if not items:
        return True, "No se encontró canal previo; procediendo con la subida."

    uploads_playlist_id = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

    # 2. Consultar el video más reciente en la lista de subidas
    playlist_response = youtube.playlistItems().list(
        playlistId=uploads_playlist_id,
        part="snippet",
        maxResults=1
    ).execute()

    playlist_items = playlist_response.get("items", [])
    if not playlist_items:
        return True, "Canal sin videos previos. Es seguro publicar."

    last_video = playlist_items[0]
    published_at_str = last_video["snippet"]["publishedAt"]
    published_at = parse_iso(published_at_str)

    now_utc = datetime.now(timezone.utc)
    delta_seconds = (now_utc - published_at).total_seconds()
    minutes_elapsed = delta_seconds / 60.0

    if minutes_elapsed < cooldown_minutes:
        remaining = int(cooldown_minutes - minutes_elapsed)
        msg = (
            f"[CANDADO ACTIVO] El último video se publicó hace {int(minutes_elapsed)} minutos "
            f"(menos del límite seguro de {cooldown_minutes} min). "
            f"Faltan {remaining} minutos para poder publicar. ABORTANDO para proteger cuota y evitar spam."
        )
        return False, msg

    return True, f"Último video publicado hace {int(minutes_elapsed)} minutos. Es seguro publicar."
