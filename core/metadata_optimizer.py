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

# Temas contextuales mapeados para series de alto impacto viral
SERIES_TOPICS = {
    "V12": [
        "Empezó a bailar en Transmilenio y todo el bus quedó en shock",
        "El talento callejero que dejó en silencio a Bogotá",
        "Nadie esperaba ver este nivel de baile en Transmilenio",
        "La reacción de los pasajeros en Transmilenio fue épica",
        "Cuando el arte puro le gana a la rutina de la ciudad",
        "Se levantó de su asiento y demostró de qué está hecha",
        "El espectáculo improvisado que se hizo viral en Transmilenio",
        "Así se rompe la tensión en las calles de Bogotá",
        "Deberían verla en los mejores escenarios del mundo",
        "Bogotá tiene un talento oculto que merece ser viral"
    ],
    "V17": [
        "Estuvo clínicamente muerto 60 minutos y vio esto",
        "El hombre que regresó de la muerte en Bogotá",
        "Lo que escuchó mientras los médicos lo daban por muerto",
        "¿Qué hay realmente del otro lado? Testimonio inédito",
        "Los médicos no se explican cómo despertó una hora después",
        "El encuentro en el más allá que le cambió la vida",
        "Sentí cómo me desprendía de mi cuerpo en el hospital",
        "La voz que le dijo: Todavía no es tu momento de morir",
        "Una experiencia cercana a la muerte que te dejará frío",
        "La prueba real de que la conciencia no se apaga al morir"
    ],
    "V28": [
        "Los túneles secretos que ocultan bajo Monserrate",
        "Lo que encontraron oculto en las profundidades de Monserrate",
        "El enigma subterráneo que pocos bogotanos conocen",
        "¿Por qué intentaron taponar las entradas secretas de Monserrate?",
        "El secreto oculto bajo la montaña sagrada de Bogotá"
    ],
    "V31": [
        "Algunos suben a Monserrate y nunca vuelven igual",
        "Lo que pasa de noche en Monserrate que los guías callan",
        "El testimonio de quien subió solo a la montaña y algo cambió",
        "La energía oculta de Monserrate que transforma a la gente",
        "Lo que sucedió en la cima de Monserrate a medianoche"
    ],
    "V43": [
        "Este clarinetista en la Séptima detuvo a cientos de personas",
        "La melodía callejera que le sacó lágrimas a los transeúntes",
        "Un músico brillante que la calle no debería esconder",
        "Tocó una sola canción y la gente empezó a llorar",
        "El talento invisible que camina por el centro de Bogotá"
    ],
    "V45": [
        "El pueblo de Colombia donde los muertos no se pudren",
        "El enigma real de las momias de San Bernardo",
        "¿Por qué la tierra de este pueblo momifica los cuerpos?",
        "Abrieron la tumba y el rostro estaba intacto",
        "Científicos aún no se explican este fenómeno en Colombia",
        "Los secretos del panteón de San Bernardo Cundinamarca",
        "Lo que come la gente aquí: ¿La causa del misterio?",
        "Cuerpos intactos después de 30 años bajo tierra",
        "El misterio natural que desconcierta al mundo entero",
        "Visité el lugar donde nadie puede descomponerse"
    ],
    "V46": [
        "Grabó sus últimos segundos con vida en su celular",
        "Lo que quedó grabado en su teléfono antes de partir",
        "Una niña en medio del fuego cruzado: Momento real",
        "El mensaje en su celular que nadie pudo olvidar",
        "La verdad oculta detrás de este video en su teléfono",
        "El celular que sobrevivió a la mayor tragedia",
        "No tuvo tiempo de escapar: Su última grabación",
        "Las palabras que dejó grabadas antes de morir",
        "La historia que le rompió el corazón a todo el país",
        "¿Por qué nadie pudo salvarla a tiempo?"
    ],
    "V47": [
        "Cuidado con quién sales en internet: El asesino de las citas",
        "Así engañaba a sus víctimas en las citas a ciegas",
        "El detalle oculto que su última cita pasó por alto",
        "La trampa mortal detrás de un perfil falso en redes",
        "Lo que halló la policía en el celular del asesino",
        "Nunca aceptes un trago de un desconocido en una cita",
        "El error fatal que delató al asesino de las citas",
        "Cómo logró escapar con vida una de sus víctimas",
        "El rostro del sujeto que aterrorizó la ciudad",
        "La regla de oro que puede salvarte la vida hoy mismo"
    ],
    "V52": [
        "A los 11 años cayó en el crimen: Su crudo testimonio",
        "Lo que realmente pasa en las ollas más peligrosas de Bogotá",
        "Cómo sobrevivió a décadas de oscuridad en las calles",
        "La regla de la calle que aprendió por las malas",
        "El momento exacto en que decidió salir del infierno",
        "Me dieron por muerto tres veces: Confesión real",
        "El perdón que nadie creía que podía llegar a pedir",
        "La verdadera historia de superación en el bajo mundo",
        "De vivir en el crimen a transformar su vida por completo",
        "Un mensaje urgente para los jóvenes en las calles"
    ],
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

    # 1. Verificar si corresponde a series con temática específica en SERIES_TOPICS
    m_v = re.match(r'^(V\d+)', name, re.IGNORECASE)
    if m_v:
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
        if wl in ["de", "del", "la", "las", "el", "los", "en", "y", "a", "al", "con", "por", "un", "una", "se", "su", "que"]:
            capitalized.append(wl)
        else:
            capitalized.append(w.capitalize())

    title = " ".join(capitalized)
    if title:
        title = title[0].upper() + title[1:]

    # Aplicar correcciones ortográficas
    for pattern, repl in WORD_FIXES.items():
        title = re.sub(pattern, repl, title, flags=re.IGNORECASE)

    # Optimizador Viral: PROHIBIDO agregar "(Clip X)" o "| Parte X"
    # Cada Short se presenta como una historia única de alto impacto.
    VIRAL_SUB_HOOKS = [
        "¿Qué Pasó Realmente?",
        "La Verdad Oculta",
        "Lo que Nadie Vio",
        "El Momento Decisivo",
        "Nadie Esperaba Esto",
        "Una Lección Inolvidable",
        "El Giro Inesperado"
    ]
    if variant_index > 0:
        sub = VIRAL_SUB_HOOKS[(variant_index - 1) % len(VIRAL_SUB_HOOKS)]
        title = f"{title}: {sub}"

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
    
    # Enlace estratégico al video largo para sumar horas de reproducción y detonar comentarios
    funnel_cta = (
        f"🎬 MIRA EL VIDEO LARGO COMPLETO AQUÍ:\n"
        f"👉 https://youtu.be/{linked_video['id']}\n"
        f"📌 Historia: {linked_video['title']}\n\n"
        f"💬 PREGUNTA DEL DÍA: ¿Tú qué opinas de lo que pasó aquí? ¿Habrías actuado igual? Déjame tu comentario abajo 👇\n"
        f"🔥 Dale LIKE si respetas estas historias reales y COMPARTE con un amigo.\n"
        f"🔔 ¡Suscríbete a @ElGatoAlex para más historias y momentos reales todos los días!"
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
