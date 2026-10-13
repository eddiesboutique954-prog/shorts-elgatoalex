"""
Configuraciones maestras del sistema autónomo de publicación de Shorts.
Permite configuración mediante variables de entorno (GitHub Secrets) o archivo local .env.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURACIÓN DE YOUTUBE ---
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/drive"
]

# Estado de publicación inicial: 'public' para publicación inmediata, o 'unlisted' / 'private' para pruebas
DEFAULT_PRIVACY_STATUS = os.getenv("YOUTUBE_PRIVACY_STATUS", "public")

# Categoría de YouTube: 22 = People & Blogs, 24 = Entertainment, 27 = Education, 28 = Science & Tech
YOUTUBE_CATEGORY_ID = os.getenv("YOUTUBE_CATEGORY_ID", "22")

# Candado Anti-Duplicados: minutos mínimos entre videos
COOLDOWN_MINUTES = int(os.getenv("COOLDOWN_MINUTES", "45"))

# --- CONFIGURACIÓN DE GOOGLE DRIVE ---
# ID de la carpeta en Google Drive donde están los videos pendientes
GDRIVE_PENDING_FOLDER_ID = os.getenv("GDRIVE_PENDING_FOLDER_ID", "")

# ID de la carpeta en Google Drive donde se mueven los videos ya publicados
GDRIVE_PUBLISHED_FOLDER_ID = os.getenv("GDRIVE_PUBLISHED_FOLDER_ID", "")

# --- PLANTILLAS SEO Y LLAMADAS A LA ACCIÓN (CTA) ---
DEFAULT_TAGS = [
    "shorts",
    "youtubeshorts",
    "viral",
    "fyp",
    "parati",
    "tendencias"
]

# Llamada a la acción predeterminada para la descripción
DEFAULT_CTA = os.getenv(
    "DEFAULT_CTA",
    "🔔 ¡Suscríbete para más contenido diario!\n💬 Deja tu comentario y comparte con alguien que lo necesite."
)

# Horarios de publicación objetivo en Colombia (UTC-5):
# 8:00 AM, 12:00 PM, 5:00 PM, 9:00 PM
PUBLISH_HOURS_COLOMBIA = [8, 12, 17, 21]
