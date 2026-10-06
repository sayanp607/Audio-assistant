import os
import requests
from pydub import AudioSegment

# Sarvam's sync STT-translate API rejects audio longer than 30s.
# We slice each chunk into 25s pieces (with a 5s safety margin) before sending.
SARVAM_PIECE_SECONDS = 25

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
SARVAM_STT_TRANSLATE_URL = "https://api.sarvam.ai/speech-to-text-translate"  # translates to English
SARVAM_STT_URL = "https://api.sarvam.ai/speech-to-text"                       # keeps original language
SARVAM_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v2.5")

# Mapping from common language names to Sarvam BCP-47 language codes
LANGUAGE_CODE_MAP = {
    "bengali": "bn-IN",
    "hindi": "hi-IN",
    "tamil": "ta-IN",
    "telugu": "te-IN",
    "kannada": "kn-IN",
    "malayalam": "ml-IN",
    "gujarati": "gu-IN",
    "marathi": "mr-IN",
    "punjabi": "pa-IN",
    "odia": "od-IN",
    "english": "en-IN",
}

def _send_to_sarvam(audio_path: str, translate: bool = True, language_code: str = "bn-IN") -> str:
    url = SARVAM_STT_TRANSLATE_URL if translate else SARVAM_STT_URL
    with open(audio_path, "rb") as f:
        files = {"file": (os.path.basename(audio_path), f, "audio/wav")}
        if translate:
            data = {"model": SARVAM_MODEL, "prompt": ""}
        else:
            data = {"model": SARVAM_MODEL, "language_code": language_code, "prompt": ""}
        headers = {"api-subscription-key": SARVAM_API_KEY}
        response = requests.post(url, headers=headers, files=files, data=data)
        if response.status_code == 200:
            return response.json().get("transcript", "")
        else:
            print(f"Error from Sarvam API ({url}): {response.text}")
            return ""

def transcribe_chunk_sarvam(chunk_path: str, translate: bool = True, language_code: str = "bn-IN") -> str:
    """
    Sarvam sync API only accepts ≤30s audio. We split this chunk into
    25-second pieces, send each separately, and join the transcripts.
    If translate=True  → uses speech-to-text-translate (outputs English).
    If translate=False → uses speech-to-text (outputs original language, needs language_code).
    """
    if not SARVAM_API_KEY:
        raise RuntimeError("SARVAM_API_KEY is not set in environment / .env")

    audio = AudioSegment.from_wav(chunk_path)
    piece_ms = SARVAM_PIECE_SECONDS * 1000

    full_text = ""
    total_pieces = (len(audio) + piece_ms - 1) // piece_ms

    for i, start in enumerate(range(0, len(audio), piece_ms)):
        piece = audio[start: start + piece_ms]
        piece_path = f"{chunk_path}_sv_{i}.wav"
        piece.export(piece_path, format="wav")

        try:
            print(f"  -> Sarvam piece {i + 1}/{total_pieces} ...")
            full_text += _send_to_sarvam(piece_path, translate=translate, language_code=language_code) + " "
        finally:
            if os.path.exists(piece_path):
                os.remove(piece_path)

    return full_text.strip()

def transcribe_chunk(chunk_path: str, language: str = "english") -> str:
    """
    If language is english, always translate to English.
    If language is non-english, use direct STT to keep original script,
    and also get an English translation separately for the RAG engine.
    """
    # Always translate to English for the RAG engine (AI works best in English)
    return transcribe_chunk_sarvam(chunk_path, translate=True)

def transcribe_all(chunks: list, language: str = "english") -> str:
    """Transcribes all chunks and translates to English (for RAG engine)."""
    full_transcript = "" 
    print("Using Sarvam AI for transcription and translation.")

    for i, chunk in enumerate(chunks):  
        print(f"Transcribing chunk {i + 1}/{len(chunks)}...")
        text = transcribe_chunk_sarvam(chunk, translate=True)
        full_transcript += text + " "  

    print("Transcription complete.")
    return full_transcript.strip()


def transcribe_all_native(chunks: list, language: str = "bengali") -> str:
    """Transcribes all chunks in original language WITHOUT translating (for showing raw lyrics)."""
    language_code = LANGUAGE_CODE_MAP.get(language.lower(), "bn-IN")
    print(f"Getting native language transcript [{language_code}] (no translation)...")
    full_transcript = ""

    for i, chunk in enumerate(chunks):
        print(f"Native chunk {i + 1}/{len(chunks)}...")
        text = transcribe_chunk_sarvam(chunk, translate=False, language_code=language_code)
        full_transcript += text + " "

    print("Native transcription complete.")
    return full_transcript.strip()