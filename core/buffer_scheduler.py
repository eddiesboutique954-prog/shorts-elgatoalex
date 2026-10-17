"""
Motor de Colchón Continuo Auto-Regenerativo (Rolling Scheduled Buffer).
Mantiene SIEMPRE un colchón de videos programados hacia el futuro en los servidores de YouTube.
Si detecta que la cola programada tiene menos de TARGET_BUFFER videos, sube y programa
los siguientes automáticamente con títulos únicos garantizados para las horas pico de Colombia (10 AM, 1 PM, 6 PM, 9 PM).
"""
import os
import sys
import json
import tempfile
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from googleapiclient.http import MediaFileUpload

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

root_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, root_dir)

from core.auth_manager import get_youtube_service, get_drive_service
from core.drive_manager import list_pending_videos, download_video_by_id, move_video_to_published
from core.metadata_optimizer import build_metadata
from config.settings import PUBLISH_HOURS_COLOMBIA

COLOMBIA_TZ = ZoneInfo("America/Bogota")
TARGET_BUFFER = int(os.getenv("TARGET_BUFFER", "8"))  # Mantener al menos 8 videos (2 días completos) programados hacia adelante
MAX_PER_RUN = int(os.getenv("MAX_PER_RUN", "4"))      # Límite seguro por ejecución para no exceder cuota diaria (6,400 unidades)

USED_TITLES_FILE = os.path.join(root_dir, "database", "used_titles.json")

def load_used_titles() -> set:
    if os.path.exists(USED_TITLES_FILE):
        try:
            with open(USED_TITLES_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()

def save_used_title(title: str):
    titles = load_used_titles()
    titles.add(title)
    os.makedirs(os.path.dirname(USED_TITLES_FILE), exist_ok=True)
    with open(USED_TITLES_FILE, "w", encoding="utf-8") as f:
        json.dump(list(titles), f, ensure_ascii=False, indent=2)

def get_already_scheduled_videos(youtube) -> list[dict]:
    """Obtiene los videos que actualmente están en estado Programado en YouTube."""
    channels_res = youtube.channels().list(mine=True, part="contentDetails").execute()
    uploads_id = channels_res["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    
    items = youtube.playlistItems().list(
        playlistId=uploads_id,
        part="contentDetails",
        maxResults=30
    ).execute().get("items", [])
    
    if not items:
        return []
        
    v_ids = [i["contentDetails"]["videoId"] for i in items]
    v_res = youtube.videos().list(
        id=",".join(v_ids),
        part="snippet,status"
    ).execute().get("items", [])
    
    scheduled = []
    now_utc = datetime.now(timezone.utc)
    
    for v in v_res:
        status = v.get("status", {})
        pub_at_str = status.get("publishAt")
        if status.get("privacyStatus") == "private" and pub_at_str:
            pub_at = datetime.fromisoformat(pub_at_str.replace("Z", "+00:00"))
            if pub_at > now_utc:
                scheduled.append({
                    "id": v["id"],
                    "title": v["snippet"]["title"],
                    "publishAt": pub_at
                })
                
    scheduled.sort(key=lambda x: x["publishAt"])
    return scheduled

def calculate_next_slots(existing_slots: list[datetime], count: int) -> list[datetime]:
    """Calcula los siguientes 'count' horarios de publicación libres."""
    slots = []
    now_col = datetime.now(COLOMBIA_TZ)
    
    # Empezar a buscar desde el último slot programado existente o desde hoy
    if existing_slots:
        last_dt = max(existing_slots).astimezone(COLOMBIA_TZ)
        start_dt = max(now_col, last_dt)
    else:
        start_dt = now_col
        
    current = start_dt
    existing_set = set(dt.astimezone(COLOMBIA_TZ).strftime("%Y-%m-%d %H") for dt in existing_slots)
    
    while len(slots) < count:
        curr_date = current.date()
        for hour in PUBLISH_HOURS_COLOMBIA:
            slot_cand = datetime(curr_date.year, curr_date.month, curr_date.day, hour, 0, 0, tzinfo=COLOMBIA_TZ)
            slot_key = slot_cand.strftime("%Y-%m-%d %H")
            if slot_cand > now_col and slot_key not in existing_set:
                slots.append(slot_cand)
                existing_set.add(slot_key)
                if len(slots) >= count:
                    break
        current += timedelta(days=1)
        current = datetime(current.year, current.month, current.day, 0, 0, 0, tzinfo=COLOMBIA_TZ)
        
    return slots

def run_buffer_replenish():
    print("=" * 65)
    print("🔄 INICIANDO MANTENIMIENTO DEL COLCHÓN DE SHORTS EN YOUTUBE")
    print("=" * 65)
    
    youtube = get_youtube_service()
    
    # 1. Consultar cuántos videos ya están programados en YouTube
    scheduled_videos = get_already_scheduled_videos(youtube)
    current_buffer = len(scheduled_videos)
    print(f"[BUFFER] Videos actualmente programados a futuro en YouTube: {current_buffer}")
    
    for s in scheduled_videos:
        col_str = s["publishAt"].astimezone(COLOMBIA_TZ).strftime("%d/%m %I:%M %p")
        print(f"   * [{col_str}] {s['title']}")
        
    needed = TARGET_BUFFER - current_buffer
    if needed <= 0:
        print(f"\n✅ [BUFFER LLENO] El colchón tiene {current_buffer} videos hacia adelante. No es necesario programar más por ahora.")
        return 0
        
    to_schedule_count = min(needed, MAX_PER_RUN)
    print(f"\n[AUTOPILOT] El colchón necesita videos. Se programarán {to_schedule_count} videos en este ciclo.")
    
    # 2. Obtener videos pendientes desde Google Drive
    pending_drive_videos = list_pending_videos()
    if not pending_drive_videos:
        print("[AVISO] No hay más videos en Google Drive para programar.")
        return 0
        
    batch = pending_drive_videos[:to_schedule_count]
    
    # 3. Calcular los horarios exactos de estreno
    existing_slots = [s["publishAt"] for s in scheduled_videos]
    new_slots = calculate_next_slots(existing_slots, len(batch))
    
    used_titles = load_used_titles()
    # Cargar títulos ya existentes en el canal
    for s in scheduled_videos:
        used_titles.add(s["title"])
        
    temp_dir = tempfile.gettempdir()
    
    for i, (video_info, slot) in enumerate(zip(batch, new_slots), 1):
        file_id = video_info["id"]
        fname = video_info["name"]
        
        # Generar metadatos únicos limpios y atractivos
        attempts = 0
        meta = build_metadata(fname, variant_index=attempts)
        title = meta["title"]
        
        # Si el título ya fue usado, rotar variante sin alterar el nombre del archivo
        while title in used_titles and attempts < 15:
            attempts += 1
            meta = build_metadata(fname, variant_index=attempts)
            title = meta["title"]
            
        used_titles.add(title)
        save_used_title(title)
        
        slot_utc = slot.astimezone(timezone.utc)
        publish_at_iso = slot_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        slot_col_str = slot.strftime("%A %d/%m %I:%M %p")
        
        print(f"\n[{i}/{len(batch)}] Procesando '{fname}'...")
        print(f"   Título asignado: {title}")
        print(f"   Estreno en YouTube: {slot_col_str} (Colombia)")
        
        local_temp = os.path.join(temp_dir, f"buf_{file_id}.mp4")
        try:
            download_video_by_id(file_id, local_temp)
            
            body = {
                "snippet": {
                    "title": title,
                    "description": meta["description"],
                    "tags": meta["tags"],
                    "categoryId": "22"
                },
                "status": {
                    "privacyStatus": "private",
                    "publishAt": publish_at_iso,
                    "selfDeclaredMadeForKids": False
                }
            }
            
            media = MediaFileUpload(local_temp, chunksize=1024*1024*4, resumable=True)
            request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
            
            resp = None
            while resp is None:
                st, resp = request.next_chunk()
                if st:
                    print(f"   Subiendo: {int(st.progress() * 100)}%", flush=True)
                    
            vid_id = resp.get("id")
            print(f"   ✅ ¡PROGRAMADO EN YOUTUBE! https://youtube.com/shorts/{vid_id}")
            
            # Mover archivo en Google Drive a Publicados
            move_video_to_published(file_id)
            
        finally:
            if os.path.exists(local_temp):
                try:
                    os.remove(local_temp)
                except Exception:
                    pass
                    
    print("\n" + "=" * 65)
    print("🎉 CICLO COMPLETADO: Colchón de YouTube abastecido con éxito.")
    print("=" * 65)
    return 0

if __name__ == "__main__":
    sys.exit(run_buffer_replenish())
