import json
import os
import streamlit as st
from translate import Translator

st.set_page_config(page_title="Restaurant App", page_icon="🍔", layout="wide")

ORDERS_FILE = "orders.json"
RESERVATIONS_FILE = "reservations.json"

# قائمة اللغات المتاحة مع كود الترجمة
LANGUAGES = {
    "English": "en",
    "العربية": "ar",
    "اردو": "ur",
    "हिन्दी": "hi",
}

# المنيو الأساسي باللغة الإنجليزية
MENU_ITEMS = [
    {"id": 1, "name": "Chicken Shawarma with Garlic", "price": 18.0},
    {"id": 2, "name": "Grilled Beef Burger", "price": 28.0},
    {"id": 3, "name": "Fresh Orange Juice", "price": 12.0},
    {"id": 4, "name": "Lemon Juice", "price": 10.0},
    {"id": 5, "name": "Watermelon", "price": 15.0},
    {"id": 6, "name": "Tea", "price": 5.0},
    {"id": 7, "name": "Coffee", "price": 8.0},
]


# دالة الترجمة باستخدام مكتبة translate
def translate_text(text, target_lang):
  if target_lang == "en" or not text:
    return text
  try:
    translator = Translator(to_lang=target_lang, from_lang="en")
    return translator.translate(text)
  except Exception:
    return text


def load_data(file_path, default_val=None):
  if default_val is None:
    default_val = []
  if not os.path.exists(file_path):
    return default_val
  try:
    with open(file_path, "r", encoding="utf-8") as f:
      return json.load(f)
  except Exception:
    return default_val


def save_data(file_path, data):
  with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


# --- تهيئة الجلسة ---
if "app_language" not in st.session_state:
  st.session_state.app_language = None

if "cart" not in st.session_state:
  st.session_state.cart = {}


# ==========================================
# 1. شاشة اختيار اللغة الابتدائية
# ==========================================
if st.session_state.app_language is None:
  st.markdown("<br><br>", unsafe_allow_html=True)
  st.title("🌐 Select Language / اختر اللغة")
  st.write("---")

  cols = st.columns(len(LANGUAGES))
  for idx, (lang_name, lang_code) in enumerate(LANGUAGES.items()):
    with cols[idx]:
      if st.button(lang_name, use_container_width=True, type="primary"):
        st.session_state.app_language = lang_code
        st.rerun()

# ==========================================
# 2. واجهة الزبون فقط
# ==========================================
else:
  lang = st.session_state.app_language

  # زر تغيير اللغة في الشريط الجانبي
  st.sidebar.title("Options 🌐")
  if st.sidebar.button("Change Language / تغيير اللغة"):
    st.session_state.app_language = None
    st.rerun()

  # ترجمة النصوص الثابتة للواجهة
  title_text = translate_text("Welcome to the Restaurant", lang)
  tab1_text = translate_text("Food Menu", lang)
  tab2_text = translate_text("Shopping Cart", lang)
  tab3_text = translate_text("Table Reservation", lang)
  add_btn_text = translate_text("Add to Cart", lang)
  qty_text = translate_text("Qty", lang)
  currency_text = translate_text("AED", lang)
  total_text = translate_text("Total", lang)
  empty_cart_text = translate_text("Your cart is empty", lang)
  confirm_order_text = translate_text("Confirm Order", lang)
  name_label = translate_text("Your Name", lang)
  table_label = translate_text("Table Number (Optional)", lang)
  res_name_label = translate_text("Reservation Name", lang)
  guests_label = translate_text("Guests Count", lang)
  date_label = translate_text("Date", lang)
  time_label = translate_text("Time", lang)
  reserve_btn_text = translate_text("Reserve Now", lang)

  st.title(f"🍔 {title_text}")

  cart_count = sum(st.session_state.cart.values())
  tab1, tab2, tab3 = st.tabs([
      f"📜 {tab1_text}",
      f"🛒 {tab2_text} ({cart_count})",
      f"📅 {tab3_text}",
  ])

  # --- تبويب قائمة الطعام ---
  with tab1:
    st.header(tab1_text)
    for item in MENU_ITEMS:
      # ترجمة اسم الوجبة من الإنجليزية للغة المختارة
      display_name = translate_text(item["name"], lang)

      c1, c2, c3 = st.columns([3, 2, 2])
      with c1:
        st.subheader(display_name)
        st.write(f"{item['price']} {currency_text}")
      with c2:
        qty = st.number_input(
            qty_text,
            min_value=1,
            value=1,
            key=f"qty_{item['id']}",
            label_visibility="collapsed",
        )
      with c3:
        if st.button(add_btn_text, key=f"btn_{item['id']}"):
          st.session_state.cart[display_name] = (
              st.session_state.cart.get(display_name, 0) + qty
          )
          st.success(
              f"{translate_text('Added', lang)} {display_name} {translate_text('successfully', lang)}"
          )
          st.rerun()

  # --- تبويب سلة الطلبات ---
  with tab2:
    st.header(tab2_text)
    if not st.session_state.cart:
      st.info(empty_cart_text)
    else:
      total_price = 0
      # إيجاد الأسعار حسب الاسم المترجم المعروض
      price_dict = {
          translate_text(item["name"], lang): item["price"]
          for item in MENU_ITEMS
      }

      for item_name, quantity in st.session_state.cart.items():
        price = price_dict.get(item_name, 0)
        item_total = price * quantity
        total_price += item_total
        st.write(
            f"**{item_name}** × {quantity} = {item_total:.1f} {currency_text}"
        )

      st.markdown("---")
      st.subheader(f"{total_text}: {total_price:.1f} {currency_text}")

      customer_name = st.text_input(name_label)
      table_num = st.text_input(table_label)

      if st.button(confirm_order_text):
        if customer_name:
          orders = load_data(ORDERS_FILE)
          orders.append({
              "customer": customer_name,
              "table": table_num,
              "items": st.session_state.cart,
              "total": total_price,
          })
          save_data(ORDERS_FILE, orders)
          st.session_state.cart = {}
          st.success(
              translate_text(
                  "Order submitted successfully! Thank you.", lang
              )
          )
          st.rerun()
        else:
          st.warning(translate_text("Please enter your name", lang))

  # --- تبويب حجز الطاولة ---
  with tab3:
    st.header(tab3_text)
    res_name = st.text_input(res_name_label)
    res_guests = st.number_input(guests_label, min_value=1, value=2)
    res_date = st.date_input(date_label)
    res_time = st.time_input(time_label)

    if st.button(reserve_btn_text):
      if res_name:
        reservations = load_data(RESERVATIONS_FILE)
        reservations.append({
            "name": res_name,
            "guests": res_guests,
            "date": str(res_date),
            "time": str(res_time),
        })
        save_data(RESERVATIONS_FILE, reservations)
        st.success(translate_text("Table reserved successfully!", lang))
      else:
        st.warning(translate_text("Please enter reservation name", lang))
