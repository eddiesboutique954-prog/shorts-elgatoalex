"""
Optimizador de metadatos inteligente para YouTube Shorts (ElGatoAlex).
Si el archivo tiene un nombre descriptivo, lo transforma en un título limpio.
Si el archivo tiene un nombre técnico de cámara (ej. V56_S10..., VID_..., IMG_...),
genera automáticamente títulos virales de alta retención basados en historias urbanas,
retos y lecciones de vida.
"""
import os
import re
import random
from config.settings import DEFAULT_CTA, DEFAULT_TAGS

# Títulos de alta retención para videos con nombres técnicos
VIRAL_TITLES_POOL = [
    "Lo Que Nadie Se Esperaba Que Pasara",
    "Esto Me Dejó Sin Palabras",
    "La Reacción De La Gente Fue Increíble",
    "Nunca Juzgues Antes De Conocer La Historia",
    "Un Momento Que Te Cambiará La Perspectiva",
    "Héroes Que No Usan Capa En Las Calles",
    "Lo Que Hizo Este Personaje Es De Admirar",
    "Tienes Que Ver Esto Hasta El Final",
    "El Mensaje Más Importante Que Escucharás Hoy",
    "Una Historia Real Que Te Llegará Al Corazón",
    "Reto Urbano: La Respuesta Que Nadie Esperaba",
    "La Verdad Detrás De Lo Que Vemos A Diario",
    "No Creerás Lo Que Pasó En Este Momento",
    "Un Gesto Que Vale Más Que Mil Palabras",
    "La Humildad De Esta Persona Te Conmoverá",
    "Cuando La Vida Te Pone A Prueba",
    "Esto Es Lo Que Pasa Cuando Haces Lo Correcto",
    "Una Lección De Vida En Menos De Un Minuto",
    "Momentos Inolvidables En La Ciudad",
    "El Secreto Para No Rendirse Jamás"
]

def clean_filename_to_title(filename: str) -> str:
    """
    Convierte el nombre del archivo en un título viral atractivo para Shorts.
    """
    name = os.path.splitext(filename)[0]

    # Detectar si es un código técnico de cámara o exportación (ej: V56_S10_lv_0_20260426..., IMG_123, VID_2026...)
    is_technical_name = bool(re.search(r'^(?:v\d+|img|vid|dsc|mov|m4v)[\s_-]*', name, re.IGNORECASE) and re.search(r'\d{6,}', name))
    
    # También si el nombre tiene muy pocas letras reales o parece un hash/código
    clean_words = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ]', ' ', name).split()
    if is_technical_name or len(clean_words) <= 1:
        # Seleccionar un título viral con gancho
        selected_title = random.choice(VIRAL_TITLES_POOL)
        return f"{selected_title} #Shorts"

    # Si es un nombre descriptivo (ej: 'SHORT_1_Abelardo_Por_Que_Se_Disfraza_De_Toro')
    # Eliminar prefijos comunes
    name = re.sub(r'^(?:\d+[\s_-]*|video[\s_-]*|short[\s_-]*|img[\s_-]*)', '', name, flags=re.IGNORECASE)
    # Reemplazar guiones y barras
    name = re.sub(r'[_\-]+', ' ', name).strip()
    title = name.title()

    if len(title) > 85:
        title = title[:82] + "..."

    if "#Shorts" not in title and "#shorts" not in title:
        title = f"{title} #Shorts"

    return title


def build_metadata(filename: str, custom_description: str = None, custom_tags: list = None) -> dict:
    """
    Construye el conjunto completo de metadatos optimizado para ElGatoAlex.
    """
    title = clean_filename_to_title(filename)

    base_desc = custom_description or "Historias reales, momentos inolvidables y lecciones de vida en la ciudad."
    cta = "🔔 ¡Suscríbete a @ElGatoAlex para más historias y momentos reales todos los días!\n💬 Déjanos tu opinión en los comentarios."

    hashtags = "#Shorts #Viral #ElGatoAlex #Historias #Tendencias #ParaTi"

    full_description = f"{base_desc}\n\n{cta}\n\n{hashtags}"

    tags = ["elgatoalex", "historias", "bogota", "colombia", "shorts", "viral", "parati", "fyp", "reflexion"]
    if custom_tags:
        tags.extend(custom_tags)

    return {
        "title": title,
        "description": full_description,
        "tags": tags[:15]
    }
