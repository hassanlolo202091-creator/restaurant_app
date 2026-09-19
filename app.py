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


# --- إعداد الجلسة واللغة ---
if "cart" not in st.session_state:
  st.session_state.cart = {}

st.sidebar.title("الخيارات / Options 🌐")
selected_lang_name = st.sidebar.selectbox(
    "اللغة / Language", list(LANGUAGES.keys()), index=0
)
lang_code = LANGUAGES[selected_lang_name]

admin_mode = st.sidebar.checkbox("وضع الأدمن / Admin Mode 🔒")

st.title(f"🍔 {get_ui_text('welcome', lang_code)}")

# --- لوحة التحكم للأدمن ---
if admin_mode:
  password = st.sidebar.text_input("كلمة السر / Password", type="password")
  if password == "1234":
    st.sidebar.success("تم الدخول بنجاح")
    st.header("لوحة التحكم / Admin Dashboard")

    tab_admin1, tab_admin2, tab_admin3 = st.tabs(
        ["الطلبات الواردة", "الحجوزات", "إدارة قائمة الطعام (المنيو)"]
    )

    with tab_admin1:
      st.subheader("قائمة الطلبات الواردة")
      orders = load_data(ORDERS_FILE)
      if orders:
        for idx, o in enumerate(reversed(orders), 1):
          with st.expander(
              f"طلب #{idx} - العميل: {o.get('customer')} | الإجمالي:"
              f" {o.get('total')} درهم"
          ):
            st.write(f"**رقم الطاولة:** {o.get('table', 'سفري')}")
            st.write("**الأصناف:**")
            for item_name, qty in o.get("items", {}).items():
              disp = translate_item_from_dict(item_name, lang_code)
              st.write(f"- {disp} × {qty}")
      else:
        st.info("لا توجد طلبات حتى الآن")

    with tab_admin2:
      st.subheader("قائمة الحجوزات")
      reservations = load_data(RESERVATIONS_FILE)
      if reservations:
        for r in reversed(reservations):
          st.write(
              f"📌 **{r.get('name')}** - عدد الأفراد: {r.get('guests')} |"
              f" التاريخ: {r.get('date')} | الوقت: {r.get('time')}"
          )
          st.markdown("---")
      else:
        st.info("لا توجد حجوزات حتى الآن")

    with tab_admin3:
      st.subheader("إضافة وجبة جديدة")
      col_a, col_b = st.columns([2, 1])
      with col_a:
        new_name = st.text_input("اسم الوجبة (بالعربية)")
      with col_b:
        new_price = st.number_input("السعر", min_value=1.0, value=20.0)

      if st.button("إضافة الوجبة للمنيو"):
        if new_name:
          add_menu_item(new_name, new_price)
          st.success(f"تمت إضافة {new_name} بنجاح!")
          st.rerun()
        else:
          st.warning("يرجى كتابة اسم الوجبة")

      st.markdown("---")
      st.subheader("المنيو الحالي (حذف وجبة)")
      current_menu = get_menu()
      for item in current_menu:
        c1, c2 = st.columns([3, 1])
        disp_name = get_item_name(item, lang_code)
        item_id = item.get("id") if isinstance(item, dict) else None
        price = item.get("price", 0) if isinstance(item, dict) else 0
        with c1:
          st.write(f"• **{disp_name}** - {price} درهم")
        with c2:
          if item_id and st.button("حذف", key=f"del_{item_id}"):
            delete_menu_item(item_id)
            st.success("تم الحذف بنجاح")
            st.rerun()
  else:
    st.sidebar.error("كلمة السر خاطئة")

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
            "الكمية",
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
          st.success(f"تمت إضافة {display_name}")
          st.rerun()

  with tab2:
    st.header(get_ui_text("cart", lang_code))
    curr = get_ui_text("curr", lang_code)

    if not st.session_state.cart:
      st.info("السلة فارغة حالياً")
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

      customer_name = st.text_input("اسمك الكريم / Your Name")
      table_num = st.text_input("رقم الطاولة (اختياري) / Table Number")

      if st.button("تأكيد الطلب / Confirm Order"):
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
          st.success("تم إرسال طلبك بنجاح! شكراً لك.")
          st.rerun()
        else:
          st.warning("يرجى كتابة الاسم لتأكيد الطلب")

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
