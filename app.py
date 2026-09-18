import os
import streamlit as st
from data_manager import (
    load_data,
    save_order,
    save_reservation,
    ORDERS_FILE,
    RESERVATIONS_FILE,
)
from deep_translator import GoogleTranslator
from languages import TRANSLATIONS

st.set_page_config(
    page_title="Restaurant App", page_icon="🍔", layout="wide"
)

# --- القائمة الجانبية ---
st.sidebar.title("🌐 Options / الخيارات")
lang_options = {
    "العربية": "ar",
    "English": "en",
    "हिन्दी": "hi",
    "اردو": "ur",
    "Tagalog": "fil",
    "Русский": "ru",
}
selected_lang_name = st.sidebar.selectbox(
    "Language / اللغة", list(lang_options.keys())
)
user_lang = lang_options[selected_lang_name]

st.sidebar.divider()
admin_mode = st.sidebar.checkbox("🔒 Admin Mode / وضع الأدمن")


def get_ui_text(key):
  if user_lang in TRANSLATIONS and key in TRANSLATIONS[user_lang]:
    return TRANSLATIONS[user_lang][key]
  base_text = TRANSLATIONS["en"].get(key, key)
  if user_lang == "en":
    return base_text
  try:
    return GoogleTranslator(source="en", target=user_lang).translate(base_text)
  except Exception:
    return base_text


def translate_item(text):
  if user_lang == "ar":
    return text
  try:
    return GoogleTranslator(source="ar", target=user_lang).translate(text)
  except Exception:
    return text


# --- لوحة الأدمن ---
if admin_mode:
  st.title("👨‍🍳 Admin Dashboard / لوحة التحكم")
  admin_pass = st.sidebar.text_input("Password", type="password")

  if admin_pass == "1234":
    col1, col2 = st.columns(2)

    with col1:
      st.subheader("📦 الطلبات الواردة (Orders)")
      orders = load_data(ORDERS_FILE)
      if orders:
        st.dataframe(orders, use_container_width=True)
        if st.button("🗑️ مسح الطلبات"):
          if os.path.exists(ORDERS_FILE):
            os.remove(ORDERS_FILE)
          st.rerun()
      else:
        st.info("لا توجد طلبات مسجلة.")

    with col2:
      st.subheader("📅 الحجوزات (Reservations)")
      reservations = load_data(RESERVATIONS_FILE)
      if reservations:
        st.dataframe(reservations, use_container_width=True)
        if st.button("🗑️ مسح الحجوزات"):
          if os.path.exists(RESERVATIONS_FILE):
            os.remove(RESERVATIONS_FILE)
          st.rerun()
      else:
        st.info("لا توجد حجوزات مسجلة.")
  else:
    st.warning("أدخل كلمة السر في القائمة الجانبية (1234)")

# --- واجهة الزبون ---
else:
  st.title(f"🍔 {get_ui_text('welcome')}")

  if "cart" not in st.session_state:
    st.session_state.cart = []

  tab1, tab2, tab3 = st.tabs([
      f"📋 {get_ui_text('main_menu')}",
      f"🛒 {get_ui_text('cart')} ({len(st.session_state.cart)})",
      f"📅 {get_ui_text('reserve')}",
  ])

  menu_items = [
      {"id": 1, "name": "شاورما دجاج مع ثومية", "price": 18.0},
      {"id": 2, "name": "برجر لحم مشوي", "price": 28.0},
      {"id": 3, "name": "عصير برتقال طازج", "price": 12.0},
  ]

  with tab1:
    st.header(get_ui_text("main_menu"))
    curr = get_ui_text("curr")

    for item in menu_items:
      display_name = translate_item(item["name"])
      c1, c2, c3 = st.columns([3, 2, 2])

      with c1:
        st.markdown(f"**{display_name}**")
        st.caption(f"{item['price']} {curr}")

      with c2:
        qty = st.number_input(
            "الكمية",
            min_value=1,
            value=1,
            key=f"qty_{item['id']}",
            label_visibility="collapsed",
        )

      with c3:
        if st.button(get_ui_text("add_item"), key=f"btn_{item['id']}"):
          order_item = {
              "name": item["name"],
              "price": item["price"],
              "qty": qty,
          }
          st.session_state.cart.append(order_item)
          save_order(order_item)
          st.success("✅ Added!")

  with tab2:
    st.header(get_ui_text("cart"))
    if not st.session_state.cart:
      st.info("Cart is empty!")
    else:
      total = 0
      curr = get_ui_text("curr")
      for c in st.session_state.cart:
        item_total = c["price"] * c["qty"]
        total += item_total
        display_name = translate_item(c["name"])
        st.write(f"• **{display_name}** x{c['qty']} = {item_total} {curr}")

      st.divider()
      st.subheader(f"💰 {get_ui_text('total')}: {total} {curr}")
      if st.button("Clear Cart / مسح السلة"):
        st.session_state.cart = []
        st.rerun()

  with tab3:
    st.header(get_ui_text("reserve"))
    with st.form("reservation_form"):
      name = st.text_input("Name / الاسم")
      phone = st.text_input("Phone / رقم الهاتف")
      guests = st.number_input("Guests / عدد الأفراد", min_value=1, value=2)
      time_val = st.time_input("Time / الموعد")

      submitted = st.form_submit_button("Submit Reservation / تأكيد الحجز")
      if submitted:
        res_data = {
            "name": name,
            "phone": phone,
            "guests": guests,
            "time": str(time_val),
        }
        save_reservation(res_data)
        st.balloons()
        st.success("🎉 Reservation Saved successfully!")
