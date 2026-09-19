import json
import os
from deep_translator import GoogleTranslator
from languages import get_ui_text
import streamlit as st

st.set_page_config(page_title="Restaurant App", page_icon="🍔", layout="wide")

ORDERS_FILE = "orders.json"
RESERVATIONS_FILE = "reservations.json"
MENU_FILE = "menu.json"

LANGUAGES = {
    "English": "en",
    "العربية": "ar",
    "اردو": "ur",
    "हिन्दी": "hi",
    "Filipino": "fil",
    "Русский": "ru",
}

DEFAULT_MENU = [
    {
        "id": 1,
        "price": 18.0,
        "names": {
            "ar": "شاورما دجاج مع ثومية",
            "en": "Chicken Shawarma with Garlic",
            "ur": "تومیا کے ساتھ چکن شاورما",
            "hi": "लहसुन के साथ चिकन शावरमा",
            "fil": "Chicken Shawarma na may Bawang",
            "ru": "Куриная шаурма с чесноком",
        },
    },
    {
        "id": 2,
        "price": 28.0,
        "names": {
            "ar": "برجر لحم مشوي",
            "en": "Grilled Beef Burger",
            "ur": "گرل بیف برگر",
            "hi": "ग्रिल्ड बीफ बर्गर",
            "fil": "Inihaw na Beef Burger",
            "ru": "Говяжий бургер на гриле",
        },
    },
    {
        "id": 3,
        "price": 12.0,
        "names": {
            "ar": "عصير برتقال طازج",
            "en": "Fresh Orange Juice",
            "ur": "تازہ مالٹے کا رس",
            "hi": "ताजा संतरे का रस",
            "fil": "Sariwang Juice ng Dalandan",
            "ru": "Свежевыжатый апельсиновый сок",
        },
    },
]


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


def get_menu():
  return load_data(MENU_FILE, DEFAULT_MENU)


def add_menu_item(name, input_lang_code, price):
  names_dict = {}
  # الترجمة التلقائية الفورية لجميع اللغات لحفظ القاموس في menu.json
  for lang_name, code in LANGUAGES.items():
    if code == input_lang_code:
      names_dict[code] = name.strip()
    else:
      try:
        translated = GoogleTranslator(
            source=input_lang_code, target=code
        ).translate(name.strip())
        names_dict[code] = translated if translated else name.strip()
      except Exception:
        names_dict[code] = name.strip()

  menu = get_menu()
  new_id = (
      max(
          [item.get("id", 0) for item in menu if isinstance(item, dict)],
          default=0,
      )
      + 1
  )
  menu.append({"id": new_id, "price": float(price), "names": names_dict})
  save_data(MENU_FILE, menu)


def delete_menu_item(item_id):
  menu = get_menu()
  menu = [
      item
      for item in menu
      if isinstance(item, dict) and item.get("id") != item_id
  ]
  save_data(MENU_FILE, menu)


def get_item_name(item, lang_code):
  if isinstance(item, dict):
    names = item.get("names", {})
    if isinstance(names, dict):
      return names.get(lang_code, names.get("en", item.get("name", "")))
    return item.get("name", "")
  return str(item)


# --- إعداد الجلسة واللغة الافتراضية ---
if "cart" not in st.session_state:
  st.session_state.cart = {}

st.sidebar.title("Options / الخيارات 🌐")
selected_lang_name = st.sidebar.selectbox(
    "Language / اللغة", list(LANGUAGES.keys()), index=0
)
lang_code = LANGUAGES[selected_lang_name]

admin_mode = st.sidebar.checkbox(f"{get_ui_text('admin_mode', lang_code)} 🔒")

st.title(f"🍔 {get_ui_text('welcome', lang_code)}")

# --- لوحة التحكم للأدمن ---
if admin_mode:
  password = st.sidebar.text_input(
      get_ui_text("password", lang_code), type="password"
  )
  if password == "1234":
    st.sidebar.success(get_ui_text("logged_in", lang_code))
    st.header(get_ui_text("admin_dash", lang_code))

    tab_admin1, tab_admin2, tab_admin3 = st.tabs([
        get_ui_text("orders_tab", lang_code),
        get_ui_text("res_tab", lang_code),
        get_ui_text("menu_tab", lang_code),
    ])

    with tab_admin1:
      st.subheader(get_ui_text("orders_tab", lang_code))
      orders = load_data(ORDERS_FILE)
      if orders:
        for idx, o in enumerate(reversed(orders), 1):
          with st.expander(
              f"#{idx} - {get_ui_text('customer', lang_code)}:"
              f" {o.get('customer')} | {get_ui_text('total', lang_code)}:"
              f" {o.get('total')} {get_ui_text('curr', lang_code)}"
          ):
            st.write(
                f"**{get_ui_text('table', lang_code)}:** {o.get('table', '-')}"
            )
            st.write(f"**{get_ui_text('main_menu', lang_code)}:**")
            for item_name, qty in o.get("items", {}).items():
              st.write(f"- {item_name} × {qty}")
      else:
        st.info(get_ui_text("no_orders", lang_code))

    with tab_admin2:
      st.subheader(get_ui_text("res_tab", lang_code))
      reservations = load_data(RESERVATIONS_FILE)
      if reservations:
        for r in reversed(reservations):
          st.write(
              f"📌 **{r.get('name')}** -"
              f" {get_ui_text('guests_count', lang_code)}: {r.get('guests')} |"
              f" {get_ui_text('date', lang_code)}: {r.get('date')} |"
              f" {get_ui_text('time', lang_code)}: {r.get('time')}"
          )
          st.markdown("---")
      else:
        st.info(get_ui_text("no_res", lang_code))

    with tab_admin3:
      st.subheader(get_ui_text("add_new", lang_code))
      col_lang, col_name, col_price = st.columns([1.5, 2, 1])

      with col_lang:
        input_lang_name = st.selectbox(
            get_ui_text("input_lang", lang_code), list(LANGUAGES.keys())
        )
        input_lang_code = LANGUAGES[input_lang_name]

      with col_name:
        new_name = st.text_input(get_ui_text("item_name_input", lang_code))

      with col_price:
        new_price = st.number_input(
            get_ui_text("price_input", lang_code), min_value=1.0, value=20.0
        )

      if st.button(get_ui_text("add_btn", lang_code)):
        if new_name:
          with st.spinner("Translating & Saving..."):
            add_menu_item(new_name, input_lang_code, new_price)
          st.success("OK")
          st.rerun()
        else:
          st.warning(get_ui_text("item_name_input", lang_code))

      st.markdown("---")
      st.subheader(get_ui_text("curr_menu", lang_code))
      current_menu = get_menu()
      for item in current_menu:
        c1, c2 = st.columns([3, 1])
        disp_name = get_item_name(item, lang_code)
        item_id = item.get("id") if isinstance(item, dict) else None
        price = item.get("price", 0) if isinstance(item, dict) else 0
        with c1:
          st.write(
              f"• **{disp_name}** - {price}"
              f" {get_ui_text('curr', lang_code)}"
          )
        with c2:
          if item_id and st.button(
              get_ui_text("delete_btn", lang_code), key=f"del_{item_id}"
          ):
            delete_menu_item(item_id)
            st.rerun()
  else:
    st.sidebar.error(get_ui_text("wrong_pass", lang_code))

# --- واجهة الزبون ---
else:
  cart_count = sum(st.session_state.cart.values())
  tab1, tab2, tab3 = st.tabs([
      f"📜 {get_ui_text('main_menu', lang_code)}",
      f"🛒 {get_ui_text('cart', lang_code)} ({cart_count})",
      f"📅 {get_ui_text('reserve', lang_code)}",
  ])

  with tab1:
    st.header(get_ui_text("main_menu", lang_code))
    curr = get_ui_text("curr", lang_code)
    menu_items = get_menu()

    for item in menu_items:
      display_name = get_item_name(item, lang_code)
      price = item.get("price", 0) if isinstance(item, dict) else 0
      item_id = (
          item.get("id", display_name)
          if isinstance(item, dict)
          else display_name
      )

      c1, c2, c3 = st.columns([3, 2, 2])

      with c1:
        st.subheader(display_name)
        st.write(f"{price} {curr}")

      with c2:
        qty = st.number_input(
            "Qty",
            min_value=1,
            value=1,
            key=f"qty_{item_id}",
            label_visibility="collapsed",
        )

      with c3:
        if st.button(
            get_ui_text("add_item", lang_code), key=f"btn_{item_id}"
        ):
          if display_name in st.session_state.cart:
            st.session_state.cart[display_name] += qty
          else:
            st.session_state.cart[display_name] = qty
          st.success(f"{get_ui_text('add_item', lang_code)}: {display_name}")
          st.rerun()

  with tab2:
    st.header(get_ui_text("cart", lang_code))
    curr = get_ui_text("curr", lang_code)

    if not st.session_state.cart:
      st.info(get_ui_text("empty_cart", lang_code))
    else:
      total_price = 0
      menu_items = get_menu()

      price_dict = {
          get_item_name(item, lang_code): item.get("price", 0)
          for item in menu_items
          if isinstance(item, dict)
      }

      for item_disp_name, quantity in st.session_state.cart.items():
        price = price_dict.get(item_disp_name, 0)
        item_total = price * quantity
        total_price += item_total
        st.write(
            f"**{item_disp_name}** × {quantity} = {item_total:.1f} {curr}"
        )

      st.markdown("---")
      st.subheader(f"{get_ui_text('total', lang_code)}: {total_price:.1f} {curr}")

      customer_name = st.text_input(get_ui_text("your_name", lang_code))
      table_num = st.text_input(get_ui_text("table_num", lang_code))

      if st.button(get_ui_text("confirm_order", lang_code)):
        if customer_name:
          order_data = {
              "customer": customer_name,
              "table": table_num,
              "items": st.session_state.cart,
              "total": total_price,
          }
          orders = load_data(ORDERS_FILE)
          orders.append(order_data)
          save_data(ORDERS_FILE, orders)

          st.session_state.cart = {}
          st.success(get_ui_text("order_success", lang_code))
          st.rerun()
        else:
          st.warning(get_ui_text("enter_name_warn", lang_code))

  with tab3:
    st.header(get_ui_text("reserve", lang_code))

    res_name = st.text_input(get_ui_text("res_name", lang_code))
    res_guests = st.number_input(
        get_ui_text("guests_count", lang_code), min_value=1, value=2
    )
    res_date = st.date_input(get_ui_text("date", lang_code))
    res_time = st.time_input(get_ui_text("time", lang_code))

    if st.button(get_ui_text("reserve_now", lang_code)):
      if res_name:
        res_data = {
            "name": res_name,
            "guests": res_guests,
            "date": str(res_date),
            "time": str(res_time),
        }
        reservations = load_data(RESERVATIONS_FILE)
        reservations.append(res_data)
        save_data(RESERVATIONS_FILE, reservations)

        st.success(get_ui_text("res_success", lang_code))
      else:
        st.warning(get_ui_text("res_warn", lang_code))
