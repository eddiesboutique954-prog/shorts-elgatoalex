"""
Multilingual translation utilities for YouTube Shorts.
"""

import urllib.request
import urllib.parse
import json
import time

TARGET_LANGS = {
    "en": "English",
    "pt": "Português",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
    "ja": "日本語",
    "ko": "한국어",
    "hi": "हिन्दी",
    "ru": "Русский",
    "ar": "العربية",
}

def translate_text(text: str, target: str, timeout: int = 5) -> str:
    """Translate *text* from Spanish (source) to *target* language.
    Returns an empty string on failure.
    """
    if not text:
        return ""
    try:
        url = (
            "https://translate.googleapis.com/translate_a/single"
            f"?client=gtx&sl=es&tl={target}&dt=t&q="
            + urllib.parse.quote(text)
        )
        req = urllib.request.Request(
            url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return "".join(chunk[0] for chunk in data[0] if chunk and chunk[0])
    except Exception:
        return ""

def generate_localizations(base_title: str, base_description: str) -> dict:
    """Return a dict suitable for YouTube API `localizations` field.
    Keys are language codes; values contain translated title and original description.
    """
    clean_title = base_title.replace("#Shorts", "").replace("#shorts", "").strip()
    clean_desc = base_description.replace("#Shorts", "").replace("#shorts", "").strip()
    localizations = {}
    for lang in TARGET_LANGS:
        title_t = translate_text(clean_title, lang)
        if not title_t:
            continue
        title_t = f"{title_t} #Shorts"
        localizations[lang] = {"title": title_t, "description": clean_desc}
        time.sleep(0.05)
    return localizations
