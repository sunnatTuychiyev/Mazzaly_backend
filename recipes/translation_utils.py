SUPPORTED_LANGUAGES = ['en', 'uz', 'ru']


def get_requested_lang(request) -> str:
    """Return a supported language code from request query params."""
    if not request:
        return 'en'
    lang = request.query_params.get('lang', 'en')
    return lang if lang in SUPPORTED_LANGUAGES else 'en'
