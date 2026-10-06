from deep_translator import GoogleTranslator

def translate_long_text(text: str, target_lang: str) -> str:
    """Translate long text by chunking it if it exceeds 4000 characters."""
    if target_lang.lower() == "english":
        return text
        
    try:
        translator = GoogleTranslator(source='auto', target=target_lang.lower())
        
        # deep-translator limits to 5000 chars, so we chunk safely by 4000
        chunk_size = 4000
        chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
        
        translated_chunks = []
        for chunk in chunks:
            translated_chunks.append(translator.translate(chunk))
            
        return "".join(translated_chunks)
    except Exception as e:
        print(f"Translation error: {e}. Falling back to English.")
        return text
