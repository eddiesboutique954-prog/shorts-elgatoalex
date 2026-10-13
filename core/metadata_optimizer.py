"""
Optimizador de metadatos inteligente para YouTube Shorts (ElGatoAlex).
Genera títulos virales con gancho y ENLAZA AUTOMÁTICAMENTE a los videos largos
más vistos del canal para redirigir tráfico masivo y acelerar la monetización por horas de visualización.
"""
import os
import re
import random

# Videos largos más exitosos de @ElGatoAlex para redirigir tráfico
FEATURED_LONG_VIDEOS = [
    {
        "id": "diZ_v200IBM",
        "title": "Se rompió la aguja en cirugía (Historia Completa)",
        "keywords": ["cirugia", "aguja", "medico", "salud", "hospital"]
    },
    {
        "id": "fUXS2oS60X0",
        "title": "Ruleta de la suerte: Retos y Sorpresas Callejeras",
        "keywords": ["ruleta", "sorteo", "premio", "reto", "callejero", "camisetas"]
    },
    {
        "id": "M8gt2lgFYXg",
        "title": "Ese día me cambió la vida (Testimonio Real)",
        "keywords": ["vida", "cambio", "reflexion", "testimonio", "superacion", "tiempo"]
    },
    {
        "id": "62FDeAy-ax8",
        "title": "Gaitán: Historia y Memoria en las Calles de Bogotá",
        "keywords": ["gaitan", "bogota", "historia", "calle", "heroes", "informal"]
    },
    {
        "id": "i-rk6s2yUTQ",
        "title": "Iceberg del Voto: Lo que nadie te cuenta",
        "keywords": ["voto", "politica", "iceberg", "misterio", "secreto"]
    },
    {
        "id": "ilm6vJuRsfQ",
        "title": "La diferencia entre experiencia e improvisación",
        "keywords": ["experiencia", "improvisacion", "trabajo", "oficio", "leccion"]
    }
]

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
    """Convierte el nombre del archivo en un título viral atractivo para Shorts."""
    name = os.path.splitext(filename)[0]

    # Detectar si es un código técnico de cámara
    is_technical = bool(re.search(r'^(?:v\d+|img|vid|dsc|mov|m4v)[\s_-]*', name, re.IGNORECASE) and re.search(r'\d{6,}', name))
    clean_words = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ]', ' ', name).split()

    if is_technical or len(clean_words) <= 1:
        return f"{random.choice(VIRAL_TITLES_POOL)} #Shorts"

    # Si es descriptivo
    name = re.sub(r'^(?:\d+[\s_-]*|video[\s_-]*|short[\s_-]*|img[\s_-]*)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[_\-]+', ' ', name).strip()
    title = name.title()

    if len(title) > 85:
        title = title[:82] + "..."

    if "#Shorts" not in title and "#shorts" not in title:
        title = f"{title} #Shorts"

    return title


def select_best_long_video(filename: str) -> dict:
    """Selecciona el video largo más afín al tema del short o rota entre los mejores."""
    fname_lower = filename.lower()
    for lv in FEATURED_LONG_VIDEOS:
        if any(k in fname_lower for k in lv["keywords"]):
            return lv
    return random.choice(FEATURED_LONG_VIDEOS)


def build_metadata(filename: str, custom_description: str = None, custom_tags: list = None) -> dict:
    """Construye metadatos que enlazan estratégicamente al video largo para acelerar la monetización."""
    title = clean_filename_to_title(filename)
    linked_video = select_best_long_video(filename)

    base_desc = custom_description or "Historias reales, momentos inolvidables y lecciones de vida en la ciudad."
    
    # Enlace estratégico al video largo
    funnel_cta = (
        f"🎬 MIRA EL VIDEO LARGO COMPLETO AQUÍ:\n"
        f"👉 https://youtu.be/{linked_video['id']}\n"
        f"📌 Historia: {linked_video['title']}\n\n"
        f"🔔 ¡Suscríbete a @ElGatoAlex para más historias y momentos reales todos los días!\n"
        f"💬 Déjanos tu opinión en los comentarios."
    )

    hashtags = "#Shorts #Viral #ElGatoAlex #HistoriasReales #Bogota #Tendencias #ParaTi"

    full_description = f"{base_desc}\n\n{funnel_cta}\n\n{hashtags}"

    tags = ["elgatoalex", "historias", "bogota", "colombia", "shorts", "viral", "parati", "fyp", "reflexion", "testimonio"]
    if custom_tags:
        tags.extend(custom_tags)

    return {
        "title": title,
        "description": full_description,
        "tags": tags[:15]
    }
