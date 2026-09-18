import json
import os
import streamlit as st
from deep_translator import GoogleTranslator
from languages import get_ui_text

st.set_page_config(page_title="Restaurant App", page_icon="🍔", layout="wide")

# --- إدارة الملفات والبيانات ---
ORDERS_FILE = "orders.json"
RESERVATIONS_FILE = "reservations.json"
MENU_FILE = "menu.json"

LANGUAGES = {
    "العربية": "ar",
    "English": "en",
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


# دالة ترجمة الوجبة بجميع اللغات فور الإضافة
def create_multilingual_item(item_name, input_lang_code, price):
  names_dict = {}

  # ترجمة الاسم لجميع اللغات المتاحة في التطبيق
  for target_lang_name, target_lang_code in LANGUAGES.items():
    if target_lang_code == input_lang_code:
      names_dict[target_lang_code] = item_name
    else:
      try:
        translated = GoogleTranslator(
            source=input_lang_code, target=target_lang_code
        ).translate(item_name)
        names_dict[target_lang_code] = (
            translated if translated else item_name
        )
      except Exception:
        names_dict[target_lang_code] = item_name

  menu = get_menu()
  new_id = max([item["id"] for item in menu], default=0) + 1
  new_item = {"id": new_id, "price": float(price), "names": names_dict}

  menu.append(new_item)
  save_data(MENU_FILE, menu)


def delete_menu_item(item_id):
  menu = get_menu()
  menu = [item for item in menu if item["id"] != item_id]
  save_data(MENU_FILE, menu)


# دالة إرجاع اسم الوجبة باللغة المختارة
def get_item_name_by_lang(item, lang_code):
  names = item.get("names", {})
  if isinstance(names, dict):
    return names.get(lang_code, names.get("ar", item.get("name", "")))
  return str(names)


# --- إعداد القائمة الجانبية ---
if "cart" not in st.session_state:
  st.session_state.cart = {}

st.sidebar.title("الخيارات / Options 🌐")
selected_lang_name = st.sidebar.selectbox("اللغة / Language", list(LANGUAGES.keys()))
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
      st.subheader("إضافة وجبة جديدة")

      col_a, col_b, col_c = st.columns([2, 2, 1])
      with col_a:
        admin_input_lang = st.selectbox(
            "لغة كتابة اسم الوجبة", list(LANGUAGES.keys()), index=0
        )
        input_lang_code = LANGUAGES[admin_input_lang]
      with col_b:
        new_name = st.text_input("اسم الوجبة")
      with col_c:
        new_price = st.number_input("السعر", min_value=1.0, value=20.0)

      if st.button("إضافة الوجبة وتوليد الترجمات آلياً"):
        if new_name:
          with st.spinner("جاري ترجمة الوجبة وحفظها بجميع اللغات..."):
            create_multilingual_item(new_name, input_lang_code, new_price)
          st.success(f"تمت إضافة {new_name} وترجمتها بنجاح لجميع اللغات!")
          st.rerun()
        else:
          st.warning("يرجى كتابة اسم الوجبة")

      st.markdown("---")
      st.subheader("المنيو الحالي (حذف وجبة)")
      current_menu = get_menu()
      for item in current_menu:
        c1, c2 = st.columns([3, 1])
        disp_name = get_item_name_by_lang(item, lang_code)
        with c1:
          st.write(f"• **{disp_name}** - {item['price']} درهم")
        with c2:
          if st.button("حذف", key=f"del_{item['id']}"):
            delete_menu_item(item["id"])
            st.success("تم الحذف بنجاح")
            st.rerun()
  else:
    st.sidebar.error("كلمة السر خاطئة")

# --- واجهة الزبون العادية ---
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
      display_name = get_item_name_by_lang(item, lang_code)
      c1, c2, c3 = st.columns([3, 2, 2])

      with c1:
        st.subheader(display_name)
        st.write(f"{item['price']} {curr}")

      with c2:
        qty = st.number_input(
            "الكمية",
            min_value=1,
            value=1,
            key=f"qty_{item['id']}",
            label_visibility="collapsed",
        )

      with c3:
        if st.button(
            get_ui_text("add_item", lang_code), key=f"btn_{item['id']}"
        ):
          if display_name in st.session_state.cart:
            st.session_state.cart[display_name] += qty
          else:
            st.session_state.cart[display_name] = qty
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

      # بناء خريطة لأسعار الوجبات
      price_dict = {}
      for item in menu_items:
        disp = get_item_name_by_lang(item, lang_code)
        price_dict[disp] = item["price"]

      for item_disp_name, quantity in st.session_state.cart.items():
        price = price_dict.get(item_disp_name, 0)
        item_total = price * quantity
        total_price += item_total
        st.write(
            f"**{item_disp_name}** × {quantity} = {item_total:.1f} {curr}"
        )

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

    res_name = st.text_input("اسم الحجز / Reservation Name")
    res_guests = st.number_input("عدد الأفراد / Guests", min_value=1, value=2)
    res_date = st.date_input("التاريخ / Date")
    res_time = st.time_input("الوقت / Time")

    if st.button("حجز الآن / Reserve Now"):
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
