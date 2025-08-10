import os
import re
from typing import Dict, List

try:
    from googletrans import Translator
except Exception:  # pragma: no cover - library may be missing
    Translator = None
import requests
from dotenv import load_dotenv

try:  # pragma: no cover - optional dependency
    import openai
except Exception:  # pragma: no cover
    openai = None

load_dotenv()

# Supported languages for translations and API responses
SUPPORTED_LANGUAGES = ['en', 'uz', 'ru']

LANG_NAMES = {
    'en': 'English',
    'uz': 'Uzbek',
    'ru': 'Russian',
}

def get_requested_lang(request) -> str:
    """Return a supported language code from the request query params."""
    if not request:
        return 'en'
    lang = request.query_params.get('lang', 'en')
    if lang not in SUPPORTED_LANGUAGES:
        return 'en'
    return lang


FALLBACK_DICT: Dict[str, Dict[str, str]] = {
    'uz': {
        'chicken': 'tovuq',
        'onion': 'piyoz',
        'salt': 'tuz',
        'pepper': 'qalampir',
        'water': 'suv',
        'dinner': 'kechki ovqat',
        'breakfast': 'nonushta',
        'lunch': 'tushlik',
        'italian': 'italyancha',
        'condiment': 'ziravor',
        'dip': 'sous',
        'spread': 'surtma',
        'soup': "sho'rva",
        'gluten': 'glyuten',
        'free': 'bepul',
        'ketogenic': 'ketogenik',
        'starter': 'aperitiv',
        'appetizer': 'gazak',
        'dessert': 'shirinlik',
        'desserts': 'shirinliklar',
        'snack': 'tamaddi',
        'american': 'amerika',
        'flour': 'oq un',
        'cinnamon': 'doljin',
        'nutmeg': "muskat yong'og'i",
        'allspice': 'aromatik ziravor',
        'cloves': 'chinnigullar',
        'walnuts': "yong'oq",
        'chopped': "tug'ralgan",
        'whole': "to'liq",
        'wheat': "bug'doy",
        'brown': 'qoramtir',
        'white': 'oq',
        'sugar': 'shakar',
        'raw': 'xom',
        'pumpkin': "qovoq",
        'seeds': "urug'lari",
        'olive': 'zaytun',
        'oil': "yog'i",
        'butter': "sariyog'",
        'vanilla': 'vanil',
        'extract': 'ekstrakti',
        'cocoa': 'kakao',
        'seasonal': 'mavsumiy',
        'sustainable': 'barqaror',
        'companies': 'kompaniyalar',
        'brands': 'brendlar',
        'politics': 'siyosat',
        'safety': 'xavfsizlik',
        'current': 'hozirgi',
        'holidays': 'bayramlar',
        'events': 'voqealar',
        'easter': 'pasxa',
        'passover': 'fisih',
        'halloween': 'xellouin',
        'thanksgiving': 'minnatdorchilik',
        'christmas': "ro'zhdestvo",
        'new': 'yangi',
        'year': 'yil',
        'health': "sog'liqni saqlash",
        'nutrition': 'ovqatlanish',
        'vegetarian': 'vegetarian',
        'vegan': 'vegetarian',
        'diet': 'parhez',
        'weight': 'vazn',
        'loss': "yo'qotish",
        'diabetes': 'diabet',
        'diabetic': 'diabetik',
        'video': 'video',
        'podcasts': 'podkastlar',
        'quick': 'tez',
        'easy': 'oson',
        'funny': 'kulgili',
        'weird': "g'aroyib",
        'news': 'yangiliklari',
        'celebrity': 'mashhurlar',
        'coupons': 'kuponlar',
        'piece': 'dona',
        'pieces': 'dona',
        'cup': 'stakan',
        'teaspoon': 'choy qoshiq',
        'teaspoons': 'choy qoshiq',
        'tablespoon': 'osh qoshiq',
        'tablespoons': 'osh qoshiq',
        'pinch': 'chimdim',
        'main': 'asosiy',
        'course': 'taom',
        'antipasti': 'antipasti',
        'oats': "jo'xori yormasi",
    },
    'ru': {
        'chicken': 'курица',
        'onion': 'лук',
        'salt': 'соль',
        'pepper': 'перец',
        'water': 'вода',
        'dinner': 'ужин',
        'breakfast': 'завтрак',
        'lunch': 'обед',
        'italian': 'итальянский',
        'condiment': 'приправа',
        'dip': 'соус',
        'spread': 'паста',
        'soup': 'суп',
        'gluten': 'глютен',
        'free': 'бесплатный',
        'ketogenic': 'кетогенный',
        'starter': 'закуска',
        'appetizer': 'закуска',
        'dessert': 'десерт',
        'desserts': 'десерты',
        'snack': 'перекус',
        'american': 'американская кухня',
        'oatmeal': 'овсянка',
        'flour': 'мука',
        'cinnamon': 'корица',
        'nutmeg': 'мускатный орех',
        'allspice': 'душистый перец',
        'cloves': 'гвоздика',
        'walnuts': 'грецкие орехи',
        'chopped': 'нарезанный',
        'whole': 'цельнозерновой',
        'wheat': 'пшеница',
        'brown': 'коричневый',
        'white': 'белый',
        'sugar': 'сахар',
        'raw': 'сырые',
        'pumpkin': 'тыква',
        'seeds': 'семена',
        'olive': 'оливковое',
        'oil': 'масло',
        'butter': 'масло',
        'vanilla': 'ваниль',
        'extract': 'экстракт',
        'cocoa': 'какао',
        'seasonal': 'сезонный',
        'sustainable': 'устойчивый',
        'companies': 'компании',
        'brands': 'бренды',
        'politics': 'политика',
        'safety': 'безопасность',
        'current': 'текущие',
        'holidays': 'праздники',
        'events': 'мероприятия',
        'easter': 'пасха',
        'passover': 'пасха',
        'halloween': 'хэллоуин',
        'thanksgiving': 'день благодарения',
        'christmas': 'рождество',
        'new': 'новый',
        'year': 'год',
        'health': 'здоровье',
        'nutrition': 'питание',
        'vegetarian': 'вегетарианский',
        'vegan': 'веганский',
        'diet': 'диета',
        'weight': 'вес',
        'loss': 'потеря',
        'diabetes': 'диабет',
        'diabetic': 'диабетик',
        'video': 'видео',
        'podcasts': 'подкасты',
        'quick': 'быстро',
        'easy': 'легко',
        'funny': 'смешное',
        'weird': 'странное',
        'news': 'новости',
        'celebrity': 'знаменитости',
        'coupons': 'купоны',
        'piece': 'штук',
        'pieces': 'штук',
        'cup': 'стакан',
        'teaspoon': 'чайная ложка',
        'teaspoons': 'чайная ложка',
        'tablespoon': 'столовая ложка',
        'tablespoons': 'столовая ложка',
        'pinch': 'щепотка',
        'main': 'основной',
        'course': 'блюдо',
        'antipasti': 'антипасти',
        'oats': 'овсянка',
    },
}

# Additional phrase-level translations for better accuracy
PHRASE_DICT: Dict[str, Dict[str, str]] = {
    'ru': {
        "gluten free": 'без глютена',
        "main course": 'основное блюдо',
        "hors d'oeuvre": 'закуска',
        "ground cinnamon": 'молотая корица',
        "ground nutmeg": 'молотый мускатный орех',
        "ground allspice": 'молотый душистый перец',
        "ground cloves": 'молотая гвоздика',
        "½ cup pumpkin seeds": '½ стакана тыквенных семечек',
        "½ cup walnuts, chopped": '½ чашки грецких орехов, нарезанных',
        "pumpkin breakfast cake": 'тыквенный завтрак-кекс',
        "1 cup whole wheat flour": '1 чашка цельнозерновой муки',
        "whole wheat flour": 'цельнозерновая мука',
        "lunch / dinner": 'обед или ужин',
        "barbecue and american": 'барбекю и американская кухня',
        "chinese and asian": 'китайская и азиатская кухня',
        "italian and european": 'итальянская и европейская кухня',
        "mexican and latin": 'мексиканская и латиноамериканская кухня',
        "desserts and baking": 'десерты и выпечка',
        "funny & weird": 'смешное и странное',
        "seasonal & sustainable": 'сезонный и устойчивый',
        "companies & brands": 'компании и бренды',
        "politics & safety": 'политика и безопасность',
        "current holidays & events": 'текущие праздники и мероприятия',
        "easter & passover": 'пасха и пасха',
        "halloween & thanksgiving": 'хэллоуин и день благодарения',
        "christmas & new year": 'рождество и новый год',
        "gluten free & food allergies": 'без глютена и пищевая аллергия',
        "vegetarian & vegan": 'вегетарианский и веганский',
        "diet & weight loss": 'диета и потеря веса',
        "diabetes & diabetic": 'диабет и диабетик',
        "video & podcasts": 'видео и подкасты',
        "quick & easy": 'быстро и легко',
        "food newscelebrityfunny & weirdeseasonal & sustaintablecompanies & brandspolitics & safetycoupons": 'Новости еды, знаменитости, смешное и странное, сезонное и устойчивое, компании и бренды, политика и безопасность, купоны',
        "white sugar": 'белый сахар',
        "brown sugar": 'коричневый сахар',
        "raw pumpkin seeds": 'сырые тыквенные семена',
        "olive oil": 'оливковое масло',
        "white flour": 'белая мука',
        "baking powder": 'разрыхлитель',
        "baking soda": 'пищевая сода',
        "pure pumpkin": 'тыквенное пюре',
        "white chocolate mocha cookies": 'печенье с белым шоколадом и мокко',
        "white chocolate chips": 'капли белого шоколада',
        "semi-sweet chocolate chips": 'капли полусладкого шоколада',
        "instant coffee or espresso powder": 'растворимый кофе или порошок эспрессо',
        "bbq & american": 'барбекю и американская кухня',
        "chinese & asian": 'китайская и азиатская кухня',
        "italian & european": 'итальянская и европейская кухня',
        "mexican & latin": 'мексиканская и латиноамериканская кухня',
        "desserts & baking": 'десерты и выпечка',
        "as seen in...": 'Как показано в...',
        "food blog of the day": 'Блог о еде дня',
        "wine blog of the day": 'Винный блог дня',
        "follow on instagram": 'Подписывайтесь в Instagram',
        "like on facebook": 'Поставьте лайк на Facebook',
        "follow on twitter": 'Подписывайтесь в Twitter',
        "follow on pinterest": 'Подписывайтесь в Pinterest',
        "honey strawberry skillet cornbread recipes": 'Рецепты кукурузного хлеба на сковороде с мёдом и клубникой',
    },
    'uz': {
        "gluten free": 'glyutensiz',
        "main course": 'asosiy taom',
        "hors d'oeuvre": 'aperitiv',
        "whole wheat flour": "to'liq bug'doy uni",
        "ground cinnamon": 'doljin',
        "ground nutmeg": "muskat yong'og'i",
        "ground allspice": 'aromatik ziravor',
        "ground cloves": 'chinnigullar',
        "walnuts, chopped": "yong'oq, tug'ralgan",
        "½ teaspoon nutmeg": "½ choy qoshiq muskat yong'og'i",
        "½ teaspoon allspice": "½ choy qoshiq aromatik ziravor",
        "½ teaspoon ground cloves": "½ choy qoshiq chinnigullar",
        "½ cup pumpkin seeds": "½ stakan qovoq urug'lari",
        "lunch / dinner": 'tushlik yoki kechki ovqat',
        "brown sugar": 'qoramtir shakar',
        "white sugar": 'oq shakar',
        "raw pumpkin seeds": "xom qovoq urug'lari",
        "olive oil": "zaytun yog'i",
        "vanilla extract": 'vanil ekstrakti',
        "funny & weird": "kulgili va g'aroyib",
        "seasonal & sustainable": 'mavsumiy va barqaror',
        "companies & brands": 'kompaniyalar va brendlar',
        "politics & safety": 'siyosat va xavfsizlik',
        "current holidays & events": 'hozirgi bayramlar va voqealar',
        "easter & passover": 'pasxa va fisih',
        "halloween & thanksgiving": 'xellouin va minnatdorchilik',
        "christmas & new year": "ro'zhdestvo va yangi yil",
        "health & nutrition": "sog'liqni saqlash va ovqatlanish",
        "vegetarian & vegan": 'vegetarian va vegetarian',
        "diets & weight loss": "parhez va vazn yo'qotish",
        "diabetes & diabetic": 'diabet va diabetik',
        "video & podcasts": 'video va podkastlar',
        "quick & easy": 'tez va oson',
        "food newscelebrityfunny & weirdeseasonal & sustaintablecompanies & brandspolitics & safetycoupons": "Oziq-ovqat yangiliklari, kulgili va g'aroyib, mavsumiy va barqaror, kompaniyalar va brendlar, siyosat va xavfsizlik, kuponlar",
        "pumpkin breakfast cake": 'qovoqli nonushta keki',
        "white flour": 'oq un',
        "baking powder": 'pishirish kukuni',
        "baking soda": 'pishirish sodasi',
        "pure pumpkin": 'qovoq pyuresi',
        "white chocolate mocha cookies": 'oq shokoladli moka kukilar',
        "white chocolate chips": "oq shokoladli bo'lakchalar",
        "semi-sweet chocolate chips": "yarim shirin shokolad bo'lakchalar",
        "instant coffee or espresso powder": "instant qahva yoki espresso kukuni",
        "bbq & american": 'barbekyu va amerika',
        "chinese & asian": 'xitoy va osiyo',
        "italian & european": 'italyan va yevropa',
        "mexican & latin": 'meksika va lotin',
        "desserts & baking": 'shirinliklar va pishiriqlar',
        "as seen in...": 'Ko\'rsatilgan joylar...',
        "food blog of the day": 'Kun taom blogi',
        "wine blog of the day": 'Kun vino blogi',
        "follow on instagram": 'Instagramda kuzatib boring',
        "like on facebook": 'Facebookda yoqtiring',
        "follow on twitter": 'Twitterda kuzatib boring',
        "follow on pinterest": 'Pinterestda kuzatib boring',
        "honey strawberry skillet cornbread recipes": "Asalli qulupnayli skovorodkada makkajo'xori noni retseptlari",
        "gluten free & food allergies": 'glyutensiz va oziq-ovqat allergiyalari',
    },
}


def _openai_translate(text: str, dest: str, src: str) -> str:
    """Translate using OpenAI if available and configured."""
    if not openai or not os.getenv("OPENAI_API_KEY"):
        return ""
    try:  # pragma: no cover - network
        openai.api_key = os.getenv("OPENAI_API_KEY")
        src_lang = LANG_NAMES.get(src, src)
        dest_lang = LANG_NAMES.get(dest, dest)
        # Allocate enough tokens to cover longer recipe instructions
        max_tokens = min(1000, max(60, len(text.split()) * 4))
        resp = openai.ChatCompletion.create(
            model="gpt-5-nano",
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a professional culinary translator. Translate from {src_lang} to {dest_lang} "
                        "using correct grammar and preserving meaning. If the text contains multiple lines, "
                        "translate each line separately and maintain line breaks. Respond with only the translated text."
                    ),
                },
                {"role": "user", "content": text},
            ],
            max_tokens=max_tokens,
        )
        return resp.choices[0].message["content"].strip()
    except Exception:
        return ""


def gpt_translate_to_uzbek(text: str) -> str:
    """Translate English text to Uzbek using GPT-5-Nano."""
    if not text or not openai or not os.getenv("OPENAI_API_KEY"):
        return ""
    try:  # pragma: no cover - network
        openai.api_key = os.getenv("OPENAI_API_KEY")
        max_tokens = min(1000, max(60, len(text.split()) * 4))
        resp = openai.ChatCompletion.create(
            model="gpt-5-nano",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a native Uzbek linguist. Translate the user's English text into "
                        "natural, fluent, and grammatically correct Uzbek while preserving the "
                        "original meaning and style. Respond with only the translation."
                    ),
                },
                {"role": "user", "content": text},
            ],
            max_tokens=max_tokens,
        )
        return resp.choices[0].message["content"].strip()
    except Exception:
        return ""


def _manual_translate(text: str, dest: str) -> str:
    """Simple phrase and word based translation."""
    mapping = FALLBACK_DICT.get(dest, {})
    phrases = PHRASE_DICT.get(dest, {})
    lowered = text.lower()
    if lowered in phrases:
        return phrases[lowered]
    result = text
    for eng, trans in phrases.items():
        result = re.sub(re.escape(eng), trans, result, flags=re.IGNORECASE)
    words = result.split()
    translated: List[str] = [mapping.get(word.lower(), word) for word in words]
    return ' '.join(translated)


def _direct_google_translate(text: str, dest: str, src: str) -> str:
    """Fallback to Google Translate's unofficial API via HTTP request."""
    try:  # pragma: no cover - network
        resp = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={
                "client": "gtx",
                "sl": src,
                "tl": dest,
                "dt": "t",
                "q": text,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()[0]
        return "".join(part[0] for part in data if part and part[0])
    except Exception:
        return ""

# Instantiate translator with a short timeout so network issues fail fast
try:  # pragma: no cover - network usage not exercised in tests
    _translator = Translator(timeout=5) if Translator else None
except Exception:  # If initialization fails, fall back to manual dictionary
    _translator = None


def translate_text(text: str, dest: str, src: str = 'en') -> str:
    """Translate text to the destination language.

    Tries OpenAI's API first when configured, then googletrans, and finally
    a small built-in dictionary as a last resort.
    """
    if not text:
        return ''
    lowered = text.lower()
    phrases = PHRASE_DICT.get(dest, {})
    if lowered in phrases:
        return phrases[lowered]
    if src == 'en' and dest == 'uz':
        result = gpt_translate_to_uzbek(text)
        if result:
            return result
    result = _openai_translate(text, dest, src)
    if result:
        return result

    if _translator:
        try:  # pragma: no cover - network
            result = _translator.translate(text, src=src, dest=dest).text
            if result and result.lower() != text.lower():
                return result
        except Exception:
            pass

    result = _direct_google_translate(text, dest, src)
    if result and result.lower() != text.lower():
        return result

    if len(text.split()) <= 3:
        return _manual_translate(text, dest)

    return text


def apply_translations(recipe):
    """Populate translation fields for a recipe, its ingredients and instructions."""
    languages = ['uz', 'ru']
    for lang in languages:
        name_trans = translate_text(recipe.name, lang)
        desc_trans = translate_text(recipe.description, lang)
        setattr(recipe, f'name_{lang}', name_trans or recipe.name)
        setattr(recipe, f'description_{lang}', desc_trans or recipe.description)
    recipe.save()

    for category in recipe.categories.all():
        for lang in languages:
            trans = translate_text(category.name, lang)
            setattr(category, f'name_{lang}', trans or category.name)
        category.save()

    for ingredient in recipe.ingredients.all():
        for lang in languages:
            trans = translate_text(ingredient.name, lang)
            setattr(ingredient, f'name_{lang}', trans or ingredient.name)
        ingredient.save()

    steps = list(recipe.instructions.order_by('step_number'))
    for lang in languages:
        joined = "\n".join(step.description for step in steps)
        translated_block = translate_text(joined, lang)
        if translated_block and translated_block.count("\n") == len(steps) - 1:
            lines = translated_block.split("\n")
        else:
            lines = [translate_text(step.description, lang) for step in steps]
        for step, line in zip(steps, lines):
            setattr(step, f'description_{lang}', line or step.description)
    for step in steps:
        step.save()
