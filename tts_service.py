import os
import logging
from gtts import gTTS

AUDIO_DIR = "audio_cache"
os.makedirs(AUDIO_DIR, exist_ok=True)


def generate_lesson_audio(lesson_number: int, language: str, words: list) -> str | None:
    """
    Барои дарси додашуда файли mp3-и талаффузи калимаҳоро месозад (агар набошад)
    ва роҳи (path) файлро бармегардонад. Дар сурати хатогӣ None бармегардад.
    """
    path = os.path.join(AUDIO_DIR, f"lesson_{lesson_number}_{language}.mp3")
    if os.path.exists(path):
        return path

    tts_lang = "en" if language == "en" else "ru"
    text = ". ".join(w["word"] for w in words)

    try:
        tts = gTTS(text=text, lang=tts_lang, slow=False)
        tts.save(path)
        return path
    except Exception as e:
        logging.error(f"TTS generation failed for lesson {lesson_number} ({language}): {e}")
        return None