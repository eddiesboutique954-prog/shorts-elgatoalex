"""
Motor de Programación Automática Anticipada (Zero-Touch AutoPilot).
Calcula automáticamente las próximas franjas horarias libres (8:00 AM, 12:00 PM, 5:00 PM, 9:00 PM UTC-5)
y sube los videos directamente a los servidores de YouTube en estado PROGRAMADO (publishAt).
Garantiza que YouTube siempre tenga videos listos para estrenar aunque la computadora esté apagada.
"""
import os
import sys
import json
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from googleapiclient.http import MediaFileUpload

sys.stdout.reconfigure(encoding="utf-8")
root_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, root_dir)

from core.auth_manager import get_youtube_service
from core.metadata_optimizer import build_metadata
from config.settings import PUBLISH_HOURS_COLOMBIA

STATE_FILE = os.path.join(root_dir, "database", "autopilot_state.json")
LOCAL_SHORTS_DIR = r"C:\Users\Usuario\Desktop\VIDEOS DE MI CANAL\SHORTS"

COLOMBIA_TZ = ZoneInfo("America/Bogota")

def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"uploaded_files": [], "last_scheduled_slot": None}

def save_state(state: dict):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def get_next_available_slots(start_from: datetime, count: int) -> list[datetime]:
    """
    Calcula los siguientes 'count' horarios de publicación válidos (8 AM, 12 PM, 5 PM, 9 PM Colombia).
    """
    slots = []
    current = start_from
    
    # Redondear hacia adelante al siguiente slot libre
    while len(slots) < count:
        current_date = current.date()
        for hour in PUBLISH_HOURS_COLOMBIA:
            slot_time = datetime(current_date.year, current_date.month, current_date.day, hour, 0, 0, tzinfo=COLOMBIA_TZ)
            if slot_time > current and slot_time not in slots:
                slots.append(slot_time)
                if len(slots) >= count:
                    break
        current += timedelta(days=1)
        current = datetime(current.year, current.month, current.day, 0, 0, 0, tzinfo=COLOMBIA_TZ)
        
    return slots

def schedule_batch(max_videos_per_run: int = 4):
    """
    Toma los siguientes videos de la carpeta local (de abajo hacia arriba),
    los sube como PROGRAMADOS a YouTube y guarda el registro.
    """
    state = load_state()
    uploaded_set = set(state.get("uploaded_files", []))
    
    # 1. Obtener videos locales ordenados de abajo hacia arriba
    local_files = [f for f in os.listdir(LOCAL_SHORTS_DIR) if f.lower().endswith((".mp4", ".mov"))]
    local_files.sort(reverse=True)
    
    pending_files = [f for f in local_files if f not in uploaded_set]
    
    if not pending_files:
        print("[AUTOPILOT] Todos los 482 videos ya han sido programados. ¡Catálogo completo!")
        return
        
    batch = pending_files[:max_videos_per_run]
    
    # 2. Determinar fecha de inicio
    now_colombia = datetime.now(COLOMBIA_TZ)
    last_slot_str = state.get("last_scheduled_slot")
    if last_slot_str:
        last_slot = datetime.fromisoformat(last_slot_str).astimezone(COLOMBIA_TZ)
        base_time = max(now_colombia, last_slot)
    else:
        base_time = now_colombia
        
    slots = get_next_available_slots(base_time, len(batch))
    
    youtube = get_youtube_service()
    
    print("=" * 65)
    print(f"🤖 AUTOPILOT: PROGRAMANDO {len(batch)} VIDEOS EN YOUTUBE")
    print(f"   (Restantes en carpeta: {len(pending_files) - len(batch)})")
    print("=" * 65)
    
    for i, (fname, slot) in enumerate(zip(batch, slots), 1):
        fpath = os.path.join(LOCAL_SHORTS_DIR, fname)
        meta = build_metadata(fname)
        
        # Formato ISO 8601 UTC requerido por la API de YouTube: YYYY-MM-DDTHH:MM:SSZ
        slot_utc = slot.astimezone(timezone.utc)
        publish_at_iso = slot_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
        slot_colombia_str = slot.strftime("%Y-%m-%d %I:%M %p")
        
        print(f"\n[{i}/{len(batch)}] Subiendo: '{fname}'")
        print(f"   Título: {meta['title']}")
        print(f"   Estreno programado en YouTube: {slot_colombia_str} (Colombia)")
        
        body = {
            "snippet": {
                "title": meta["title"],
                "description": meta["description"],
                "tags": meta["tags"],
                "categoryId": "22",
                "defaultLanguage": "es",
                "defaultAudioLanguage": "es"
            },
            "status": {
                "privacyStatus": "private",  # Debe ser private para programar fecha de publicación
                "publishAt": publish_at_iso,
                "selfDeclaredMadeForKids": False
            }
        }
        
        # Añadir localizaciones multilingües
        localizations = meta.get("localizations", {})
        if localizations:
            body["localizations"] = localizations
        
        upload_part = "snippet,status"
        if localizations:
            upload_part = "snippet,status,localizations"
        
        media = MediaFileUpload(fpath, chunksize=1024*1024*4, resumable=True)
        request = youtube.videos().insert(
            part=upload_part,
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"   Subiendo: {int(status.progress() * 100)}%", flush=True)
                
        video_id = response.get("id")
        print(f"   ✅ ¡PROGRAMADO CON ÉXITO! ID: {video_id} -> https://youtube.com/shorts/{video_id}")
        
        # Guardar en estado
        state["uploaded_files"].append(fname)
        state["last_scheduled_slot"] = slot.isoformat()
        save_state(state)
        
    print("\n" + "=" * 65)
    print(f"🎉 LOTE COMPLETADO. YouTube publicará estos videos a la hora exacta")
    print(f"   aunque tu computadora esté apagada.")
    print("=" * 65)

if __name__ == "__main__":
    schedule_batch(max_videos_per_run=4)
