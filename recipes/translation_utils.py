import os
import re
from typing import Dict, List

try:
    from deep_translator import GoogleTranslator
except Exception:  # pragma: no cover - library may be missing
    GoogleTranslator = None
import requests

try:  # pragma: no cover - optional dependency
    import openai
except Exception:  # pragma: no cover
    openai = None

# Supported languages for translations and API responses
SUPPORTED_LANGUAGES = ['uz', 'ru']

LANG_NAMES = {
    'uz': 'Uzbek',
    'ru': 'Russian',
}

def get_requested_lang(request) -> str:
    """Return a supported language code from query params, body or headers."""
    if not request:
        return 'uz'

    lang = request.query_params.get('lang')

    if not lang and hasattr(request, 'data'):
        try:
            lang = request.data.get('lang')
        except Exception:  # pragma: no cover - non-dict data
            lang = None

    if not lang:
        header = request.headers.get('Accept-Language', '')
        if header:
            lang = header.split(',')[0].split('-')[0]

    if lang not in SUPPORTED_LANGUAGES:
        return 'uz'
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

# Comprehensive food-related translations used as a fallback when
# external translation services are unavailable.  The keys are English
# phrases, and each value provides Uzbek (uz) and Russian (ru)
# translations.
FOOD_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    # 🍖 Meat, poultry and fish (Protein)
    "meat, poultry and fish": {
        "uz": "Go‘sht, parranda va baliq",
        "ru": "Мясо, птица и рыба",
    },
    "chicken meat (thigh, breast, whole)": {
        "uz": "tovuq go‘shti (son, ko‘krak, butun)",
        "ru": "куриное мясо (бедро, грудка, целая)",
    },
    "beef (ground, steak, liver, heart)": {
        "uz": "mol go‘shti (qiyma, biftek, jigar, yurak)",
        "ru": "говядина (фарш, стейк, печень, сердце)",
    },
    "lamb": {"uz": "qo‘y go‘shti", "ru": "баранина"},
    "turkey": {"uz": "kurka go‘shti", "ru": "индейка"},
    "fish (salmon, tuna, sardine, mackerel)": {
        "uz": "baliq (losos, orkinos, sardina, skumbriya)",
        "ru": "рыба (лосось, тунец, сардина, скумбрия)",
    },
    "seafood (shrimp, squid, mussels)": {
        "uz": "dengiz mahsulotlari (karides, kalmar, midiya)",
        "ru": "морепродукты (креветки, кальмары, мидии)",
    },
    "egg": {"uz": "tuxum", "ru": "яйцо"},
    "egg white/yolk": {
        "uz": "tuxum oqi/yolig‘i",
        "ru": "яичный белок/желток",
    },
    "sausage, frankfurter, basturma": {
        "uz": "kolbasa, sosiska, basturma",
        "ru": "колбаса, сосиски, бастурма",
    },

    # 🧀 Milk and dairy products
    "milk and dairy products": {
        "uz": "Sut va sut mahsulotlari",
        "ru": "Молоко и молочные продукты",
    },
    "milk (cow, soy, almond)": {
        "uz": "sut (sigir, soya, bodom)",
        "ru": "молоко (коровье, соевое, миндальное)",
    },
    "sour cream": {"uz": "smetana", "ru": "сметана"},
    "cream": {"uz": "qaymoq", "ru": "сливки"},
    "yogurt (plain, Greek)": {
        "uz": "qatiq / yogurt (oddiy, grekcha)",
        "ru": "йогурт (обычный, греческий)",
    },
    "cheese (hard, soft, mozzarella, feta)": {
        "uz": "pishloq (qattiq, yumshoq, mozzarella, feta)",
        "ru": "сыр (твёрдый, мягкий, моцарелла, фета)",
    },
    "cottage cheese / cheese balls": {
        "uz": "tvorog / koptok pishloq",
        "ru": "творог / творожные шарики",
    },
    "butter / margarine": {
        "uz": "sariyog‘ / margarin",
        "ru": "сливочное масло / маргарин",
    },
    "condensed milk": {
        "uz": "kondenslangan sut",
        "ru": "сгущённое молоко",
    },

    # 🌱 Vegetables
    "vegetables": {
        "uz": "Sabzavotlar",
        "ru": "Овощи",
    },
    "potato / sweet potato": {
        "uz": "kartoshka / batat (shirin kartoshka)",
        "ru": "картофель / батат (сладкий картофель)",
    },
    "carrot": {"uz": "sabzi", "ru": "морковь"},
    "onion (white, red, green)": {
        "uz": "piyoz (oq, qizil, yashil)",
        "ru": "лук (белый, красный, зелёный)",
    },
    "garlic": {"uz": "sarimsoq", "ru": "чеснок"},
    "tomato (fresh, canned)": {
        "uz": "pomidor (yangi, konservalangan)",
        "ru": "помидор (свежий, консервированный)",
    },
    "cucumber": {"uz": "bodring", "ru": "огурец"},
    "eggplant": {"uz": "baqlajon", "ru": "баклажан"},
    "broccoli": {"uz": "brokkoli", "ru": "брокколи"},
    "cabbage (white, red, napa)": {
        "uz": "karam (oq, qizil, pekin)",
        "ru": "капуста (белокочанная, краснокочанная, пекинская)",
    },
    "bell pepper (red, green, yellow)": {
        "uz": "bulg‘or qalampiri (qizil, yashil, sariq)",
        "ru": "болгарский перец (красный, зелёный, жёлтый)",
    },
    "pumpkin / zucchini": {
        "uz": "qovoq / zucchini",
        "ru": "тыква / кабачок",
    },
    "spinach": {"uz": "ismaloq", "ru": "шпинат"},
    "parsley, dill, cilantro": {
        "uz": "petrushka, ukrop, kashnich",
        "ru": "петрушка, укроп, кинза",
    },
    "beetroot": {"uz": "lavlagi", "ru": "свёкла"},
    "turnip": {"uz": "sholg‘om", "ru": "репа"},
    "artichoke": {"uz": "artishok", "ru": "артишок"},
    "mushrooms (champignon, portobello, oyster)": {
        "uz": "qo‘ziqorin (champignon, portobello, oyster)",
        "ru": "грибы (шампиньоны, портобелло, вешенки)",
    },

    # 🌾 Grains, cereals and flour products
    "grains, cereals and flour products": {
        "uz": "Don, yorma va un mahsulotlari",
        "ru": "Зерновые, крупы и мучные изделия",
    },
    "wheat flour (regular, refined, whole)": {
        "uz": "bug‘doy uni (oddiy, tozalangan, to‘liq)",
        "ru": "пшеничная мука (обычная, очищенная, цельнозерновая)",
    },
    "rice (white, brown, mixed with lentils)": {
        "uz": "guruch (oq, jigarrang, yasmiq bilan aralash)",
        "ru": "рис (белый, коричневый, смешанный с чечевицей)",
    },
    "buckwheat": {"uz": "grechka", "ru": "гречка"},
    "oatmeal": {"uz": "jo‘xori / oatmeal", "ru": "овсянка"},
    "barley": {"uz": "arpa", "ru": "ячмень"},
    "couscous / bulgur": {
        "uz": "kuskus / bulgur",
        "ru": "кускус / булгур",
    },
    "pasta (regular, whole grain, gluten-free)": {
        "uz": "makaron (oddiy, to‘liq donli, gluten-free)",
        "ru": "макароны (обычные, цельнозерновые, безглютеновые)",
    },
    "bread (white, rye, toast, baguette)": {
        "uz": "non (oq, qora, tost, baget)",
        "ru": "хлеб (белый, чёрный, тостовый, багет)",
    },
    "tortilla / lavash": {
        "uz": "tortilla / lavash",
        "ru": "тортилья / лаваш",
    },
    "yeast, baking powder": {
        "uz": "non pishirish xamirturushlari: droja, razrixlitel",
        "ru": "дрожжи, разрыхлитель",
    },

    # 🪶 Legumes
    "legumes": {"uz": "Dukkaklilar", "ru": "Бобовые"},
    "peas": {"uz": "no‘xat", "ru": "горох"},
    "beans (red, white, black, green)": {
        "uz": "loviya (qizil, oq, qora, yashil)",
        "ru": "фасоль (красная, белая, чёрная, зелёная)",
    },
    "lentils (green, red)": {
        "uz": "yasmiq (yashil, qizil)",
        "ru": "чечевица (зелёная, красная)",
    },
    "soybeans": {"uz": "soya fasoli", "ru": "соевые бобы"},
    "mung beans": {"uz": "mungbo‘", "ru": "мунг"},
    "tofu": {"uz": "tofu (soya pishlog‘i)", "ru": "тофу"},

    # 🍎 Fruits and berries
    "fruits and berries": {
        "uz": "Meva va rezavorlar",
        "ru": "Фрукты и ягоды",
    },
    "apple": {"uz": "olma", "ru": "яблоко"},
    "banana": {"uz": "banan", "ru": "банан"},
    "orange / mandarin": {
        "uz": "apelsin / mandarin",
        "ru": "апельсин / мандарин",
    },
    "lemon / lime": {
        "uz": "limon / laim",
        "ru": "лимон / лайм",
    },
    "pomegranate": {"uz": "anor", "ru": "гранат"},
    "grapes": {"uz": "uzum", "ru": "виноград"},
    "strawberry / raspberry / blackberry": {
        "uz": "qulupnay / malina / maymunjon",
        "ru": "клубника / малина / ежевика",
    },
    "pear": {"uz": "nok", "ru": "груша"},
    "peach": {"uz": "shaftoli", "ru": "персик"},
    "mango": {"uz": "mango", "ru": "манго"},
    "kiwi": {"uz": "kivi", "ru": "киви"},
    "watermelon / melon": {
        "uz": "tarvuz / qovun",
        "ru": "арбуз / дыня",
    },
    "pineapple": {"uz": "ananas", "ru": "ананас"},

    # 🍼 Spices, sauces and condiments
    "spices, sauces and condiments": {
        "uz": "Ziravorlar, souslar va qo‘shimchalar",
        "ru": "Специи, соусы и добавки",
    },
    "salt": {"uz": "tuz", "ru": "соль"},
    "black pepper": {
        "uz": "qora murch",
        "ru": "чёрный перец",
    },
    "paprika": {"uz": "paprika", "ru": "паприка"},
    "cumin": {"uz": "zira / kimyon", "ru": "зира / кмин"},
    "cinnamon": {"uz": "dolchin / koritsa", "ru": "корица"},
    "chili powder / pepper": {
        "uz": "chili kukuni / qalampir",
        "ru": "чили порошок / перец",
    },
    "turmeric": {"uz": "kurkuma / zerdecho", "ru": "куркума"},
    "vinegar (apple, grape, balsamic)": {
        "uz": "sirka (olma, uzum, balsamik)",
        "ru": "уксус (яблочный, винный, бальзамический)",
    },
    "soy sauce": {"uz": "soya sousi", "ru": "соевый соус"},
    "ketchup": {"uz": "ketchup", "ru": "кетчуп"},
    "mayonnaise": {"uz": "mayonez", "ru": "майонез"},
    "mustard": {"uz": "xantal", "ru": "горчица"},
    "olive oil / sunflower oil / coconut oil": {
        "uz": "zaytun yog‘i / kungaboqar yog‘i / kokos yog‘i",
        "ru": "оливковое масло / подсолнечное масло / кокосовое масло",
    },

    # 🍞 Sweets and baked goods
    "sweets and baked goods": {
        "uz": "Shirinliklar va nonvoylik mahsulotlari",
        "ru": "Сладости и выпечка",
    },
    "sugar (white, brown)": {
        "uz": "shakar (oq, jigarrang)",
        "ru": "сахар (белый, коричневый)",
    },
    "honey": {"uz": "asal", "ru": "мёд"},
    "cocoa powder": {"uz": "kakao kukuni", "ru": "какао-порошок"},
    "chocolate (milk, dark, white)": {
        "uz": "shokolad (sutli, qora, oq)",
        "ru": "шоколад (молочный, тёмный, белый)",
    },
    "vanillin": {"uz": "vanilin", "ru": "ванилин"},
    "baking powder, baking soda": {
        "uz": "pishiriq kukuni (razrixlitel, soda)",
        "ru": "разрыхлитель (порошок для выпечки), сода",
    },
    "shredded coconut": {
        "uz": "kokos bo‘lagi",
        "ru": "кокосовая стружка",
    },
    "nuts (almond, peanut, hazelnut, walnut)": {
        "uz": "yong‘oq (bodom, yeryong‘oq, funduk, grek yong‘og‘i)",
        "ru": "орехи (миндаль, арахис, фундук, грецкий орех)",
    },
    "sesame, chia seeds, flax seeds": {
        "uz": "kunjut, chiyam, zig‘ir urug‘i",
        "ru": "кунжут, семена чиа, льняные семена",
    },
    "nut butters (peanut butter, almond butter)": {
        "uz": "yong‘oq yog‘lari (peanut butter, almond butter)",
        "ru": "ореховые пасты (арахисовая, миндальная)",
    },

    # 🍲 Prepared and canned products
    "prepared and canned products": {
        "uz": "Tayyor va konservalangan mahsulotlar",
        "ru": "Готовые и консервированные продукты",
    },
    "canned tomatoes": {
        "uz": "konservalangan pomidor",
        "ru": "консервированные помидоры",
    },
    "canned beans": {
        "uz": "loviya konservalari",
        "ru": "консервированная фасоль",
    },
    "canned fish (tuna, sardine)": {
        "uz": "baliq konservalari (tunets, sardina)",
        "ru": "рыбные консервы (тунец, сардина)",
    },
    "olives / capers": {
        "uz": "zaytun / kapers",
        "ru": "оливки / каперсы",
    },
    "pickled cucumbers": {
        "uz": "tuzlangan bodring",
        "ru": "маринованные огурцы",
    },
    "vegetable mixes (frozen or canned)": {
        "uz": "sabzavotli aralashmalar (muzlatilgan yoki konservalangan)",
        "ru": "овощные смеси (замороженные или консервированные)",
    },

    # ☕️ Drinks
    "drinks (some)": {
        "uz": "Ichimliklar (ba’zilariga)",
        "ru": "Напитки (некоторые)",
    },
    "tea (green, black, herbal)": {
        "uz": "choy (yashil, qora, o‘simlik)",
        "ru": "чай (зелёный, чёрный, травяной)",
    },
    "coffee (ground, beans, instant)": {
        "uz": "qahva (yerilgan, don, instant)",
        "ru": "кофе (молотый, в зёрнах, растворимый)",
    },
    "cocoa drink": {"uz": "kakao ichimligi", "ru": "какао-напиток"},
    "mineral water": {"uz": "mineral suv", "ru": "минеральная вода"},
    "juices (orange, apple)": {
        "uz": "sharbatlar (apelsin, olma)",
        "ru": "соки (апельсиновый, яблочный)",
    },
}

# Merge food translations into phrase dictionaries for quick lookup
for phrase, translations in FOOD_TRANSLATIONS.items():
    for lang, value in translations.items():
        PHRASE_DICT.setdefault(lang, {})[phrase] = value


def _openai_translate(text: str, dest: str, src: str) -> str:
    """Translate using OpenAI if available and configured."""
    if not openai or not os.getenv("OPENAI_API_KEY"):
        return ""
    try:  # pragma: no cover - network
        openai.api_key = os.getenv("OPENAI_API_KEY")
        src_lang = LANG_NAMES.get(src, src)
        dest_lang = LANG_NAMES.get(dest, dest)
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"Translate the user's text from {src_lang} to {dest_lang}."},
                {"role": "user", "content": text},
            ],
            max_tokens=60,
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

# Instantiate translator class from deep-translator
_translator = GoogleTranslator if GoogleTranslator else None


def translate_text(text: str, dest: str, src: str = 'en') -> str:
    """Translate text to the destination language.

    Tries OpenAI's API first when configured, then Google's translate service
    via deep-translator, and finally a small built-in dictionary as a last
    resort.
    """
    if not text:
        return ''
    lowered = text.lower()
    phrases = PHRASE_DICT.get(dest, {})
    if lowered in phrases:
        return phrases[lowered]
    words = len(text.split())
    if words <= 3:
        manual = _manual_translate(text, dest)
        if manual.lower() != text.lower():
            return manual
    result = _openai_translate(text, dest, src)
    if result:
        return result

    if _translator:
        try:  # pragma: no cover - network
            result = _translator(source=src, target=dest).translate(text)
            if result and result.lower() != text.lower():
                return result
        except Exception:
            pass

    result = _direct_google_translate(text, dest, src)
    if result and result.lower() != text.lower():
        return result

    if words <= 3:
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
