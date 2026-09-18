from deep_translator import GoogleTranslator

TRANSLATIONS = {
    "ar": {
        "welcome": "مرحباً بكم في المطعم",
        "main_menu": "قائمة الطعام",
        "cart": "سلة الطلبات",
        "reserve": "حجز طاولة",
        "curr": "درهم",
        "total": "الإجمالي",
        "add_item": "إضافة للسلّة",
        "items": {
            "شاورما دجاج مع ثومية": "شاورما دجاج مع ثومية",
            "برجر لحم مشوي": "برجر لحم مشوي",
            "عصير برتقال طازج": "عصير برتقال طازج",
        },
    },
    "en": {
        "welcome": "Welcome to the Restaurant",
        "main_menu": "Food Menu",
        "cart": "Shopping Cart",
        "reserve": "Table Reservation",
        "curr": "AED",
        "total": "Total",
        "add_item": "Add to Cart",
        "items": {
            "شاورما دجاج مع ثومية": "Chicken Shawarma with Garlic",
            "برجر لحم مشوي": "Grilled Beef Burger",
            "عصير برتقال طازج": "Fresh Orange Juice",
        },
    },
    "ur": {
        "welcome": "ریسٹورانٹ میں خوش آمدید",
        "main_menu": "کھانے کا مینو",
        "cart": "شاپنگ کارٹ",
        "reserve": "ٹیبل کی بکنگ",
        "curr": "درہم",
        "total": "کل",
        "add_item": "کارٹ میں شامل کریں",
        "items": {
            "شاورما دجاج مع ثومية": "تومیا کے ساتھ چکن شاورما",
            "برجر لحم مشوي": "گرل بیف برگر",
            "عصير برتقال طازج": "تازہ مالٹے کا رس",
        },
    },
    "hi": {
        "welcome": "रेस्तरां में आपका स्वागत है",
        "main_menu": "खाद्य मेनू",
        "cart": "शॉपिंग कार्ट",
        "reserve": "टेबल आरक्षण",
        "curr": "AED",
        "total": "कुल",
        "add_item": "कार्‍ट में जोड़ें",
        "items": {
            "شاورما دجاج مع ثومية": "लहसुन के साथ चिकन शावरमा",
            "برجر لحم مشوي": "ग्रिल्ड बीफ बर्गर",
            "عصير برتقال طازج": "ताजा संतरे का रस",
        },
    },
    "fil": {
        "welcome": "Maligayang pagdating sa Restaurant",
        "main_menu": "Menu ng Pagkain",
        "cart": "Shopping Cart",
        "reserve": "Reservasyon ng Lamesa",
        "curr": "AED",
        "total": "Kabuuan",
        "add_item": "Ipadala sa Cart",
        "items": {
            "شاورما دجاج مع ثومية": "Chicken Shawarma na may Bawang",
            "برجر لحم مشوي": "Inihaw na Beef Burger",
            "عصير برتقال طازج": "Sariwang Juice ng Dalandan",
        },
    },
    "ru": {
        "welcome": "Добро пожаловать в ресторан",
        "main_menu": "Меню блюд",
        "cart": "Корзина покупателя",
        "reserve": "Бронирование столика",
        "curr": "Дирхам",
        "total": "Итого",
        "add_item": "Добавить в корзину",
        "items": {
            "شاورما دجاج مع ثومية": "Куриная шаурма с чесноком",
            "برجر لحم مشوي": "Говяжий бургер на гриле",
            "عصير برتقال طازج": "Свежевыжатый апельсиновый сок",
        },
    },
}


def get_ui_text(key, lang_code="ar"):
  lang_data = TRANSLATIONS.get(lang_code, TRANSLATIONS["en"])
  return lang_data.get(key, TRANSLATIONS["en"].get(key, key))


def get_item_name(item_arabic, lang_code="ar"):
  # 1. إذا كانت اللغة هي العربية، اعد الاسم كما هو
  if lang_code == "ar":
    return item_arabic

  # 2. البحث في القاموس الثابت للسرعة والدقة
  lang_data = TRANSLATIONS.get(lang_code, {})
  items_dict = lang_data.get("items", {})
  if item_arabic in items_dict:
    return items_dict[item_arabic]

  # 3. إذا كانت الوجبة جديدة وغير موجودة بالقاموس، ترجمها فوراً تلقائياً
  try:
    translated = GoogleTranslator(
        source="ar", target=lang_code
    ).translate(item_arabic)
    return translated
  except Exception:
    return item_arabic
