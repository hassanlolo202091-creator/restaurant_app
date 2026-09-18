import streamlit as st
from data_manager import (
    add_order,
    add_reservation,
    get_menu,
    get_orders,
    get_reservations,
)
from languages import get_item_name, get_ui_text

st.set_page_config(page_title="Restaurant App", page_icon="🍔", layout="wide")

# تهيئة الجلسة للسلة والطلبات
if "cart" not in st.session_state:
    st.session_state.cart = {}

# قائمة اللغات المتاحة
LANGUAGES = {
    "العربية": "ar",
    "English": "en",
    "اردو": "ur",
    "हिन्दी": "hi",
    "Filipino": "fil",
    "Русский": "ru",
}

# القائمة الجانبية (Sidebar)
st.sidebar.title("الخيارات / Options 🌐")
selected_lang_name = st.sidebar.selectbox("اللغة / Language", list(LANGUAGES.keys()))
lang_code = LANGUAGES[selected_lang_name]

admin_mode = st.sidebar.checkbox("وضع الأدمن / Admin Mode 🔒")

# الشاشة الرئيسية
st.title(f"🍔 {get_ui_text('welcome', lang_code)}")

if admin_mode:
    password = st.sidebar.text_input("كلمة السر / Password", type="password")
    if password == "1234":
        st.sidebar.success("تم الدخول بنجاح")
        st.header("لوحة التحكم / Admin Dashboard")

        tab_admin1, tab_admin2 = st.tabs(["الطلبات", "الحجوزات"])

        with tab_admin1:
            st.subheader("قائمة الطلبات الواردة")
            orders = get_orders()
            if orders:
                st.json(orders)
            else:
                st.info("لا توجد طلبات حتى الآن")

        with tab_admin2:
            st.subheader("قائمة الحجوزات")
            reservations = get_reservations()
            if reservations:
                st.json(reservations)
            else:
                st.info("لا توجد حجوزات حتى الآن")
    else:
        st.sidebar.error("كلمة السر خاطئة")

else:
    # واجهة المستخدم العادي
    cart_count = sum(st.session_state.cart.values())
    tab1, tab2, tab3 = st.tabs([
        f"📜 {get_ui_text('main_menu', lang_code)}",
        f"🛒 {get_ui_text('cart', lang_code)} ({cart_count})",
        f"📅 {get_ui_text('reserve', lang_code)}",
    ])

    # 1. تبويب قائمة الطعام
    with tab1:
        st.header(get_ui_text("main_menu", lang_code))
        curr = get_ui_text("curr", lang_code)
        menu_items = get_menu()

        for item in menu_items:
            display_name = get_item_name(item["name"], lang_code)
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
                    if item["name"] in st.session_state.cart:
                        st.session_state.cart[item["name"]] += qty
                    else:
                        st.session_state.cart[item["name"]] = qty
                    st.success(f"تمت إضافة {display_name}")
                    st.rerun()

    # 2. تبويب سلة الطلبات
    with tab2:
        st.header(get_ui_text("cart", lang_code))
        curr = get_ui_text("curr", lang_code)

        if not st.session_state.cart:
            st.info("السلة فارغة حالياً")
        else:
            total_price = 0
            menu_dict = {item["name"]: item["price"] for item in get_menu()}

            for item_ar_name, quantity in st.session_state.cart.items():
                item_disp_name = get_item_name(item_ar_name, lang_code)
                price = menu_dict.get(item_ar_name, 0)
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
                    add_order(order_data)
                    st.session_state.cart = {}
                    st.success("تم إرسال طلبك بنجاح! شكراً لك.")
                    st.rerun()
                else:
                    st.warning("يرجى كتابة الاسم لتأكيد الطلب")

    # 3. تبويب حجز طاولة
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
                add_reservation(res_data)
                st.success("تم تأكيد حجز الطاولة بنجاح!")
            else:
                st.warning("يرجى إدخال اسم الحجز")
