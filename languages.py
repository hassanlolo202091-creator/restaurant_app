TRANSLATIONS = {
    "ar": {
        "welcome": "مرحباً بكم في المطعم",
        "main_menu": "قائمة الطعام",
        "cart": "سلة الطلبات",
        "reserve": "حجز طاولة",
        "exit": "خروج",
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
        "exit": "Exit",
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
        "exit": "خروج",
        "curr": "درہم",
        "total": "کل",
        "add_item": "کارٹ میں شامل کریں",
        "items": {
            "شاورما دجاج مع ثومية": "تومیا کے ساتھ چکن شاورما",
            "برجر لحم مشوي": "گرل بیف برگر",
            "عصير برتقال طازج": "تازہ مالٹے کا رس",
        },
    },
}


def get_ui_text(key, lang_code="ar"):
  lang_data = TRANSLATIONS.get(lang_code, TRANSLATIONS["en"])
  return lang_data.get(key, TRANSLATIONS["en"].get(key, key))


def get_item_name(item_arabic, lang_code="ar"):
  lang_data = TRANSLATIONS.get(lang_code, TRANSLATIONS["ar"])
  items_dict = lang_data.get("items", {})
  return items_dict.get(item_arabic, item_arabic)
