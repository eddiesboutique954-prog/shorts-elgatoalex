"""
Optimizador de metadatos inteligente para YouTube Shorts (ElGatoAlex).
Genera títulos virales limpios, atractivos y únicos para cada Short,
eliminando códigos de cámara o edición, y ENLAZA AUTOMÁTICAMENTE a los videos largos
más vistos del canal para redirigir tráfico masivo y acelerar la monetización.
"""
import os
import re
import random
from core.multilang_translator import generate_localizations

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
        "keywords": ["ruleta", "sorteo", "premio", "reto", "callejero", "camisetas", "iron", "maiden"]
    },
    {
        "id": "M8gt2lgFYXg",
        "title": "Ese día me cambió la vida (Testimonio Real)",
        "keywords": ["vida", "cambio", "reflexion", "testimonio", "superacion", "tiempo", "ejercito"]
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
        "keywords": ["experiencia", "improvisacion", "trabajo", "oficio", "leccion", "artesano"]
    }
]

# Correcciones ortográficas comunes en títulos
WORD_FIXES = {
    r'\bBogot\b': 'Bogotá',
    r'\bMedellin\b': 'Medellín',
    r'\bDuatlon\b': 'Duatlón',
    r'\bCirugia\b': 'Cirugía',
    r'\bCorazon\b': 'Corazón',
    r'\bIncreible\b': 'Increíble',
    r'\bMusica\b': 'Música',
    r'\bHeroe\b': 'Héroe',
    r'\bHeroes\b': 'Héroes',
    r'\bPapa\b': 'Papá',
    r'\bNino\b': 'Niño',
    r'\bNina\b': 'Niña',
    r'\bAsi\b': 'Así',
    r'\bReaccion\b': 'Reacción',
    r'\bMas\b': 'Más',
    r'\bDia\b': 'Día',
    r'\bAno\b': 'Año',
    r'\bAnos\b': 'Años',
}

# Temas contextuales mapeados para series de cámara o exportaciones técnicas sin descripción en el nombre
SERIES_TOPICS = {
    "V54": [
        "¿Por qué preferimos encajar antes que decir la verdad?",
        "El albergue vacío: Lo que pasa cuando nadie pone límites",
        "La banda de 'Los No Copeo': Cuando el caos se vuelve costumbre",
        "El castigo que no fue al cuerpo sino a la mente",
        "El desorden no se impone, se tolera"
    ],
    "V55": [
        "¿Qué es lo más fuerte que te ha pasado en la calle?",
        "Nadie hacía nada mientras ellos peleaban en la Calle 19",
        "No peleaban por drogas, peleaban por comida vieja",
        "Una lección en el centro de Bogotá que me partió el alma",
        "¿Cuántas veces fuiste invisible para los demás?"
    ],
    "V56": [
        "En qué momento empezamos a creer: Misterio en Usme",
        "Tierra sagrada y caminos ocultos en Bogotá",
        "Lo que no te cuentan de la historia ancestral de Usme",
        "Secretos indígenas que aún se sienten en las montañas",
        "Un viaje al pasado oculto de nuestra ciudad",
        "Mitos reales que la gente de Usme todavía recuerda",
        "El choque entre la ciudad moderna y la tierra sagrada",
        "Caminando por los senderos olvidados de Usme",
        "Una reflexión entre la niebla y la memoria ancestral",
        "Bogotá antes del ruido: El alma de nuestros antepasados"
    ]
}

VIRAL_FALLBACK_HOOKS = [
    "Historias reales que te cambian la perspectiva",
    "Lo que nadie se esperaba que pasara en las calles",
    "Un momento que te dejará sin palabras",
    "La reacción de la gente fue completamente increíble",
    "Nunca juzgues antes de conocer la historia real",
    "Héroes de verdad que caminan por Bogotá",
    "Lo que hizo esta persona es digno de admirar",
    "Tienes que ver esto hasta el final",
    "El mensaje más importante que escucharás hoy",
    "Una historia que te llegará directo al corazón",
    "La verdad detrás de lo que vemos a diario en la ciudad",
    "Un gesto que vale más que mil palabras",
    "La humildad de esta persona te conmoverá el alma",
    "Cuando la vida te pone a prueba y decides avanzar",
    "Una lección de vida real en menos de un minuto",
    "Momentos inolvidables que suceden en Bogotá",
    "El secreto para no rendirse jamás ante la adversidad"
]

def clean_filename_to_title(filename: str, variant_index: int = 0) -> str:
    """
    Convierte el nombre del archivo en un título viral atractivo y limpio para Shorts.
    Elimina prefijos técnicos (Vxx_Sxx_, SHORT_x_), números pegados, sufijos y códigos.
    Garantiza títulos descriptivos, únicos y sin duplicados.
    """
    name = os.path.splitext(filename)[0]

    # Extraer número de Short / Parte si existe (ej: S01, S04, SHORT_2)
    part_num = None
    m_s = re.search(r'(?:_S(\d+)|SHORT_(\d+))', name, re.IGNORECASE)
    if m_s:
        part_str = m_s.group(1) or m_s.group(2)
        part_num = int(part_str)

    # 1. Verificar si corresponde a series técnicas conocidas con temática específica (V54, V55, V56)
    m_v = re.match(r'^(V\d+)', name, re.IGNORECASE)
    if m_v and ('lv_' in name.lower() or '2026' in name):
        v_key = m_v.group(1).upper()
        if v_key in SERIES_TOPICS:
            hooks = SERIES_TOPICS[v_key]
            base_idx = (part_num - 1) % len(hooks) if part_num else 0
            hook = hooks[(base_idx + variant_index) % len(hooks)]
            return f"{hook} #Shorts"

    # 2. Limpieza profunda de prefijos técnicos
    clean = name
    # Quitar Vxx_Sxx_ y cualquier número pegado (ej: V50_S06_8 -> Superando...)
    clean = re.sub(r'^V\d+_S\d+_?(?:\d+)?', '', clean, flags=re.IGNORECASE)
    # Quitar SHORT_\d+_
    clean = re.sub(r'^SHORT_\d+_', '', clean, flags=re.IGNORECASE)
    # Quitar números iniciales (ej: "10MAESTRO" -> "MAESTRO", "8Superando" -> "Superando")
    clean = re.sub(r'^\d+[\s_-]*', '', clean)

    # Quitar sufijos técnicos de cámara, resolución o audio
    clean = re.sub(r'(?:2K_60FPS|1080P_HD|VIDEO_OFICIAL|60FPS|mp3|webm|mp4)', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'[_\-]+', ' ', clean).strip()

    # Quitar palabras cortadas o conectores flotantes al final
    clean = re.sub(r'\s+(?:de|la|el|en|y|un|una|del|a|al|con|por)\s+[a-zA-ZáéíóúÁÉÍÓÚñÑ]{1,2}$', '', clean, flags=re.IGNORECASE)
    clean = re.sub(r'\s+(?:de|la|el|en|y|un|una|del|a|al|con|por)$', '', clean, flags=re.IGNORECASE)

    # Si tras la limpieza quedó muy corto o vacío, usar fallback
    clean_words = clean.split()
    if len(clean_words) < 2:
        hook = VIRAL_FALLBACK_HOOKS[variant_index % len(VIRAL_FALLBACK_HOOKS)]
        if part_num:
            return f"{hook} | Parte {part_num} #Shorts"
        return f"{hook} #Shorts"

    # Capitalización natural (preposiciones y artículos en minúscula)
    capitalized = []
    for w in clean_words:
        wl = w.lower()
        if wl in ["de", "del", "la", "las", "el", "los", "en", "y", "a", "al", "con", "por", "un", "una", "se", "su"]:
            capitalized.append(wl)
        else:
            capitalized.append(w.capitalize())

    title = " ".join(capitalized)
    if title:
        title = title[0].upper() + title[1:]

    # Aplicar correcciones ortográficas
    for pattern, repl in WORD_FIXES.items():
        title = re.sub(pattern, repl, title, flags=re.IGNORECASE)

    # Añadir identificador de parte si existe y no está ya en el texto
    if part_num and f"parte {part_num}" not in title.lower():
        title = f"{title} | Parte {part_num}"

    # Si hay una variante solicitada por colisión previa
    if variant_index > 0:
        title = f"{title} (Clip {variant_index + 1})"

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


def build_metadata(filename: str, custom_description: str = None, custom_tags: list = None, variant_index: int = 0) -> dict:
    """Construye metadatos que enlazan estratégicamente al video largo para acelerar la monetización."""
    title = clean_filename_to_title(filename, variant_index=variant_index)
    linked_video = select_best_long_video(filename)

    base_desc = custom_description or "Historias reales, momentos inolvidables y reflexiones de vida en la ciudad."
    
    # Enlace estratégico al video largo para sumar horas de reproducción
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

    # Generar localizaciones (títulos y descripciones en varios idiomas)
    localizations = generate_localizations(title, base_desc)
    
    return {
        "title": title,
        "description": full_description,
        "tags": tags[:15],
        "localizations": localizations
    }
