import json
import os
from deep_translator import GoogleTranslator
import streamlit as st

st.set_page_config(page_title="Restaurant App", page_icon="🍔", layout="wide")

ORDERS_FILE = "orders.json"
RESERVATIONS_FILE = "reservations.json"
MENU_FILE = "menu.json"

DEFAULT_MENU = [
    {
        "id": 1,
        "name_ar": "شاورما دجاج مع ثومية",
        "name_en": "Chicken Shawarma with Garlic",
        "price": 18.0,
    },
    {
        "id": 2,
        "name_ar": "برجر لحم مشوي",
        "name_en": "Grilled Beef Burger",
        "price": 28.0,
    },
    {
        "id": 3,
        "name_ar": "عصير برتقال طازج",
        "name_en": "Fresh Orange Juice",
        "price": 12.0,
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


def get_display_name(item, lang_code):
  if not isinstance(item, dict):
    return str(item)
  if lang_code == "ar":
    return item.get("name_ar") or item.get("name_en") or item.get("name", "")
  else:
    return item.get("name_en") or item.get("name_ar") or item.get("name", "")


def add_menu_item(name_ar, name_en, price):
  menu = get_menu()
  new_id = (
      max(
          [item.get("id", 0) for item in menu if isinstance(item, dict)],
          default=0,
      )
      + 1
  )
  menu.append({
      "id": new_id,
      "name_ar": name_ar.strip(),
      "name_en": name_en.strip() if name_en else name_ar.strip(),
      "price": float(price),
  })
  save_data(MENU_FILE, menu)


def delete_menu_item(item_id):
  menu = get_menu()
  menu = [
      item
      for item in menu
      if isinstance(item, dict) and item.get("id") != item_id
  ]
  save_data(MENU_FILE, menu)


# --- تهيئة الجلسة ---
if "app_language" not in st.session_state:
  st.session_state.app_language = None

if "cart" not in st.session_state:
  st.session_state.cart = {}

if "input_ar" not in st.session_state:
  st.session_state.input_ar = ""

if "input_en" not in st.session_state:
  st.session_state.input_en = ""


# دوال التحديث المتبادل للترجمة الفورية
def on_ar_change():
  txt = st.session_state.input_ar.strip()
  if txt:
    try:
      st.session_state.input_en = GoogleTranslator(
          source="ar", target="en"
      ).translate(txt)
    except Exception:
      pass


def on_en_change():
  txt = st.session_state.input_en.strip()
  if txt:
    try:
      st.session_state.input_ar = GoogleTranslator(
          source="en", target="ar"
      ).translate(txt)
    except Exception:
      pass


# دالة الإضافة الآمنة
def handle_add_item(price):
  if st.session_state.input_ar or st.session_state.input_en:
    add_menu_item(st.session_state.input_ar, st.session_state.input_en, price)
    st.session_state.input_ar = ""
    st.session_state.input_en = ""
    st.session_state.add_success = True


# --- الواجهة العربية ---
def run_arabic_app():
  st.sidebar.title("الخيارات 🌐")
  if st.sidebar.button("تغيير اللغة / Change Language"):
    st.session_state.app_language = None
    st.rerun()

  admin_mode = st.sidebar.checkbox("وضع الأدمن 🔒")
  st.title("🍔 مرحباً بكم في المطعم")

  if admin_mode:
    password = st.sidebar.text_input("كلمة السر", type="password")
    if password == "1234":
      st.sidebar.success("تم الدخول بنجاح")
      st.header("لوحة التحكم (الأدمن)")

      tab_admin1, tab_admin2, tab_admin3 = st.tabs(
          ["الطلبات الواردة", "الحجوزات", "إدارة قائمة الطعام"]
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
                st.write(f"- {item_name} × {qty}")
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
        st.subheader("إضافة وجبة جديدة (ترجمة فورية تلقائية)")

        if st.session_state.get("add_success"):
          st.success("تمت إضافة الوجبة بنجاح!")
          st.session_state.add_success = False

        col_ar, col_en, col_price = st.columns([2, 2, 1])

        with col_ar:
          st.text_input(
              "اسم الوجبة (بالعربية)", key="input_ar", on_change=on_ar_change
          )

        with col_en:
          st.text_input(
              "Item Name (English)", key="input_en", on_change=on_en_change
          )

        with col_price:
          new_price = st.number_input("السعر (درهم)", min_value=1.0, value=20.0)

        st.button(
            "إضافة الوجبة",
            on_click=handle_add_item,
            args=(new_price,),
        )

        st.markdown("---")
        st.subheader("المنيو الحالي (حذف وجبة)")
        current_menu = get_menu()
        for item in current_menu:
          c1, c2 = st.columns([3, 1])
          disp_name = get_display_name(item, "ar")
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

  else:
    cart_count = sum(st.session_state.cart.values())
    tab1, tab2, tab3 = st.tabs([
        f"📜 قائمة الطعام",
        f"🛒 سلة الطلبات ({cart_count})",
        f"📅 حجز طاولة",
    ])

    with tab1:
      st.header("قائمة الطعام")
      menu_items = get_menu()

      for item in menu_items:
        display_name = get_display_name(item, "ar")
        price = item.get("price", 0) if isinstance(item, dict) else 0
        item_id = (
            item.get("id", display_name)
            if isinstance(item, dict)
            else display_name
        )

        c1, c2, c3 = st.columns([3, 2, 2])
        with c1:
          st.subheader(display_name)
          st.write(f"{price} درهم")
        with c2:
          qty = st.number_input(
              "الكمية",
              min_value=1,
              value=1,
              key=f"qty_{item_id}",
              label_visibility="collapsed",
          )
        with c3:
          if st.button("إضافة للسلّة", key=f"btn_{item_id}"):
            if display_name in st.session_state.cart:
              st.session_state.cart[display_name] += qty
            else:
              st.session_state.cart[display_name] = qty
            st.success(f"تمت إضافة {display_name}")
            st.rerun()

    with tab2:
      st.header("سلة الطلبات")
      if not st.session_state.cart:
        st.info("السلة فارغة حالياً")
      else:
        total_price = 0
        menu_items = get_menu()
        price_dict = {
            get_display_name(item, "ar"): item.get("price", 0)
            for item in menu_items
            if isinstance(item, dict)
        }

        for item_name, quantity in st.session_state.cart.items():
          price = price_dict.get(item_name, 0)
          item_total = price * quantity
          total_price += item_total
          st.write(f"**{item_name}** × {quantity} = {item_total:.1f} درهم")

        st.markdown("---")
        st.subheader(f"الإجمالي: {total_price:.1f} درهم")

        customer_name = st.text_input("اسمك الكريم")
        table_num = st.text_input("رقم الطاولة (اختياري)")

        if st.button("تأكيد الطلب"):
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
      st.header("حجز طاولة")
      res_name = st.text_input("اسم الحجز")
      res_guests = st.number_input("عدد الأفراد", min_value=1, value=2)
      res_date = st.date_input("التاريخ")
      res_time = st.time_input("الوقت")

      if st.button("حجز الآن"):
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

          st.success("تم تأكيد حجز الطاولة بنجاح!")
        else:
          st.warning("يرجى إدخال اسم الحجز")


# --- الواجهة الإنجليزية ---
def run_english_app():
  st.sidebar.title("Options 🌐")
  if st.sidebar.button("Change Language / تغيير اللغة"):
    st.session_state.app_language = None
    st.rerun()

  admin_mode = st.sidebar.checkbox("Admin Mode 🔒")
  st.title("🍔 Welcome to the Restaurant")

  if admin_mode:
    password = st.sidebar.text_input("Password", type="password")
    if password == "1234":
      st.sidebar.success("Logged in successfully")
      st.header("Admin Dashboard")

      tab_admin1, tab_admin2, tab_admin3 = st.tabs(
          ["Incoming Orders", "Reservations", "Manage Menu"]
      )

      with tab_admin1:
        st.subheader("Incoming Orders List")
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
                st.write(f"- {item_name} × {qty}")
        else:
          st.info("No orders yet")

      with tab_admin2:
        st.subheader("Reservations List")
        reservations = load_data(RESERVATIONS_FILE)
        if reservations:
          for r in reversed(reservations):
            st.write(
                f"📌 **{r.get('name')}** - Guests: {r.get('guests')} | Date:"
                f" {r.get('date')} | Time: {r.get('time')}"
            )
            st.markdown("---")
        else:
          st.info("No reservations yet")

      with tab_admin3:
        st.subheader("Add New Item (Live Auto-Translation)")

        if st.session_state.get("add_success"):
          st.success("Item added successfully!")
          st.session_state.add_success = False

        col_ar, col_en, col_price = st.columns([2, 2, 1])

        with col_ar:
          st.text_input(
              "اسم الوجبة (بالعربية)", key="input_ar", on_change=on_ar_change
          )

        with col_en:
          st.text_input(
              "Item Name (English)", key="input_en", on_change=on_en_change
          )

        with col_price:
          new_price = st.number_input("Price (AED)", min_value=1.0, value=20.0)

        st.button(
            "Add Item",
            on_click=handle_add_item,
            args=(new_price,),
        )

        st.markdown("---")
        st.subheader("Current Menu (Delete Item)")
        current_menu = get_menu()
        for item in current_menu:
          c1, c2 = st.columns([3, 1])
          disp_name = get_display_name(item, "en")
          item_id = item.get("id") if isinstance(item, dict) else None
          price = item.get("price", 0) if isinstance(item, dict) else 0
          with c1:
            st.write(f"• **{disp_name}** - {price} AED")
          with c2:
            if item_id and st.button("Delete", key=f"del_{item_id}"):
              delete_menu_item(item_id)
              st.success("Deleted successfully")
              st.rerun()
    else:
      st.sidebar.error("Wrong password")

  else:
    cart_count = sum(st.session_state.cart.values())
    tab1, tab2, tab3 = st.tabs([
        f"📜 Food Menu",
        f"🛒 Shopping Cart ({cart_count})",
        f"📅 Table Reservation",
    ])

    with tab1:
      st.header("Food Menu")
      menu_items = get_menu()

      for item in menu_items:
        display_name = get_display_name(item, "en")
        price = item.get("price", 0) if isinstance(item, dict) else 0
        item_id = (
            item.get("id", display_name)
            if isinstance(item, dict)
            else display_name
        )

        c1, c2, c3 = st.columns([3, 2, 2])
        with c1:
          st.subheader(display_name)
          st.write(f"{price} AED")
        with c2:
          qty = st.number_input(
              "Qty",
              min_value=1,
              value=1,
              key=f"qty_{item_id}",
              label_visibility="collapsed",
          )
        with c3:
          if st.button("Add to Cart", key=f"btn_{item_id}"):
            if display_name in st.session_state.cart:
              st.session_state.cart[display_name] += qty
            else:
              st.session_state.cart[display_name] = qty
            st.success(f"Added {display_name}")
            st.rerun()

    with tab2:
      st.header("Shopping Cart")
      if not st.session_state.cart:
        st.info("Your cart is currently empty")
      else:
        total_price = 0
        menu_items = get_menu()
        price_dict = {
            get_display_name(item, "en"): item.get("price", 0)
            for item in menu_items
            if isinstance(item, dict)
        }

        for item_name, quantity in st.session_state.cart.items():
          price = price_dict.get(item_name, 0)
          item_total = price * quantity
          total_price += item_total
          st.write(f"**{item_name}** × {quantity} = {item_total:.1f} AED")

        st.markdown("---")
        st.subheader(f"Total: {total_price:.1f} AED")

        customer_name = st.text_input("Your Name")
        table_num = st.text_input("Table Number (Optional)")

        if st.button("Confirm Order"):
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
            st.success("Order submitted successfully!")
            st.rerun()
          else:
            st.warning("Please enter your name to confirm order")

    with tab3:
      st.header("Table Reservation")
      res_name = st.text_input("Reservation Name")
      res_guests = st.number_input("Guests Count", min_value=1, value=2)
      res_date = st.date_input("Date")
      res_time = st.time_input("Time")

      if st.button("Reserve Now"):
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

          st.success("Table reserved successfully!")
        else:
          st.warning("Please enter reservation name")


# --- التحكم للشاشة الرئيسية ---
if st.session_state.app_language is None:
  st.markdown("<br><br>", unsafe_allow_html=True)
  st.title("🌐 Select Language / اختر اللغة")
  st.write("---")

  col1, col2 = st.columns(2)

  with col1:
    if st.button("🇬🇧 English", use_container_width=True, type="primary"):
      st.session_state.app_language = "en"
      st.rerun()

  with col2:
    if st.button("🇦🇪 العربية", use_container_width=True, type="primary"):
      st.session_state.app_language = "ar"
      st.rerun()

elif st.session_state.app_language == "ar":
  run_arabic_app()

elif st.session_state.app_language == "en":
  run_english_app()
