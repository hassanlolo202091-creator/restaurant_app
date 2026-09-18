import json
import os
import streamlit as st
from languages import get_ui_text, translate_item_from_dict

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
    {"id": 1, "name": "شاورما دجاج مع ثومية", "price": 18.0},
    {"id": 2, "name": "برجر لحم مشوي", "price": 28.0},
    {"id": 3, "name": "عصير برتقال طازج", "price": 12.0},
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


def add_menu_item(name, price):
  menu = get_menu()
  new_id = (
      max(
          [item.get("id", 0) for item in menu if isinstance(item, dict)],
          default=0,
      )
      + 1
  )
  menu.append({"id": new_id, "name": name.strip(), "price": float(price)})
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
    raw_name = item.get("name", "")
  else:
    raw_name = str(item)
  return translate_item_from_dict(raw_name, lang_code)


# --- إعداد الجلسة واللغة الإنجليزية كافتراضي ---
if "cart" not in st.session_state:
  st.session_state.cart = {}

st.sidebar.title("Options / الخيارات 🌐")
# جعل اللغة الإنجليزية هي الخيار الأول والافتراضي (index=0)
selected_lang_name = st.sidebar.selectbox(
    "Language / اللغة", list(LANGUAGES.keys()), index=0
)
lang_code = LANGUAGES[selected_lang_name]

admin_mode = st.sidebar.checkbox("Admin Mode / وضع الأدمن 🔒")

st.title(f"🍔 {get_ui_text('welcome', lang_code)}")

# --- لوحة التحكم للأدمن ---
if admin_mode:
  password = st.sidebar.text_input("Password / كلمة السر", type="password")
  if password == "1234":
    st.sidebar.success("Logged in successfully / تم الدخول بنجاح")
    st.header("Admin Dashboard / لوحة التحكم")

    tab_admin1, tab_admin2, tab_admin3 = st.tabs([
        "Orders / الطلبات",
        "Reservations / الحجوزات",
        "Manage Menu / إدارة المنيو",
    ])

    with tab_admin1:
      st.subheader("Incoming Orders / قائمة الطلبات الواردة")
      orders = load_data(ORDERS_FILE)
      if orders:
        for idx, o in enumerate(reversed(orders), 1):
          with st.expander(
              f"Order #{idx} - Customer: {o.get('customer')} | Total:"
              f" {o.get('total')} AED"
          ):
            st.write(f"**Table:** {o.get('table', 'Takeaway')}")
            st.write("**Items:**")
            for item_name, qty in o.get("items", {}).items():
              disp = translate_item_from_dict(item_name, lang_code)
              st.write(f"- {disp} × {qty}")
      else:
        st.info("No orders yet / لا توجد طلبات حتى الآن")

    with tab_admin2:
      st.subheader("Reservations List / قائمة الحجوزات")
      reservations = load_data(RESERVATIONS_FILE)
      if reservations:
        for r in reversed(reservations):
          st.write(
              f"📌 **{r.get('name')}** - Guests: {r.get('guests')} | Date:"
              f" {r.get('date')} | Time: {r.get('time')}"
          )
          st.markdown("---")
      else:
        st.info("No reservations yet / لا توجد حجوزات حتى الآن")

    with tab_admin3:
      st.subheader("Add New Item / إضافة وجبة جديدة")
      col_a, col_b = st.columns([2, 1])
      with col_a:
        new_name = st.text_input("Item Name (Arabic) / اسم الوجبة بالعربية")
      with col_b:
        new_price = st.number_input("Price / السعر", min_value=1.0, value=20.0)

      if st.button("Add Item / إضافة الوجبة"):
        if new_name:
          add_menu_item(new_name, new_price)
          st.success(f"Added {new_name} successfully!")
          st.rerun()
        else:
          st.warning("Please enter item name / يرجى كتابة اسم الوجبة")

      st.markdown("---")
      st.subheader("Current Menu / المنيو الحالي")
      current_menu = get_menu()
      for item in current_menu:
        c1, c2 = st.columns([3, 1])
        disp_name = get_item_name(item, lang_code)
        item_id = item.get("id") if isinstance(item, dict) else None
        price = item.get("price", 0) if isinstance(item, dict) else 0
        with c1:
          st.write(f"• **{disp_name}** - {price} AED")
        with c2:
          if item_id and st.button(
              "Delete / حذف", key=f"del_{item_id}"
          ):
            delete_menu_item(item_id)
            st.success("Deleted successfully / تم الحذف")
            st.rerun()
  else:
    st.sidebar.error("Wrong password / كلمة السر خاطئة")

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
            "Quantity",
            min_value=1,
            value=1,
            key=f"qty_{item_id}",
            label_visibility="collapsed",
        )

      with c3:
        if st.button(
            get_ui_text("add_item", lang_code), key=f"btn_{item_id}"
        ):
          raw_ar_name = (
              item.get("name", display_name)
              if isinstance(item, dict)
              else display_name
          )
          if raw_ar_name in st.session_state.cart:
            st.session_state.cart[raw_ar_name] += qty
          else:
            st.session_state.cart[raw_ar_name] = qty
          st.success(f"Added {display_name}")
          st.rerun()

  with tab2:
    st.header(get_ui_text("cart", lang_code))
    curr = get_ui_text("curr", lang_code)

    if not st.session_state.cart:
      st.info("Your cart is currently empty / السلة فارغة")
    else:
      total_price = 0
      menu_items = get_menu()

      price_dict = {
          item.get("name", ""): item.get("price", 0)
          for item in menu_items
          if isinstance(item, dict)
      }

      for item_ar_name, quantity in st.session_state.cart.items():
        disp_name = translate_item_from_dict(item_ar_name, lang_code)
        price = price_dict.get(item_ar_name, 0)
        item_total = price * quantity
        total_price += item_total
        st.write(f"**{disp_name}** × {quantity} = {item_total:.1f} {curr}")

      st.markdown("---")
      st.subheader(f"{get_ui_text('total', lang_code)}: {total_price:.1f} {curr}")

      customer_name = st.text_input("Your Name / اسمك الكريم")
      table_num = st.text_input("Table Number (Optional) / رقم الطاولة")

      if st.button("Confirm Order / تأكيد الطلب"):
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
          st.success("Order submitted successfully! / تم إرسال طلبك بنجاح!")
          st.rerun()
        else:
          st.warning("Please enter your name / يرجى كتابة الاسم")

  with tab3:
    st.header(get_ui_text("reserve", lang_code))

    res_name = st.text_input("Reservation Name / اسم الحجز")
    res_guests = st.number_input(
        "Guests Count / عدد الأفراد", min_value=1, value=2
    )
    res_date = st.date_input("Date / التاريخ")
    res_time = st.time_input("Time / الوقت")

    if st.button("Reserve Now / حجز الآن"):
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

        st.success("Table reserved successfully! / تم تأكيد حجز الطاولة!")
      else:
        st.warning("Please enter reservation name / يرجى إدخال اسم الحجز")
