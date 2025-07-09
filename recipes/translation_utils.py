from googletrans import Translator

translator = Translator()

def translate_text(text: str, dest: str = 'en') -> str:
    """Translate text to the destination language using googletrans."""
    if not text or dest == 'en':
        return text
    try:
        result = translator.translate(text, dest=dest)
        return result.text
    except Exception:
        # In case of failure, return original text
        return text
