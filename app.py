import base64
import datetime
import io
import json
import os
import random
import time
import urllib.parse
import pandas as pd
import streamlit as st
from translate import Translator

# استدعاء آمن لمكتبات الباركود
try:
    import qrcode
    from PIL import Image
    QRCODE_AVAILABLE = True
except ImportError:
    QRCODE_AVAILABLE = False

st.set_page_config(page_title="Restaurant App", page_icon="🍔", layout="wide")

# ==========================================
# أسماء ملفات البيانات
# ==========================================
ORDERS_FILE = "orders.json"
RESERVATIONS_FILE = "reservations.json"
MENU_FILE = "menu.json"
SETTINGS_FILE = "settings.json"

LANGUAGES = {
    "English": "en",
    "العربية": "ar",
    "اردو": "ur",
    "हिन्दी": "hi",
}

DEFAULT_MENU = [
    {
        "id": 1,
        "name": "Chicken Shawarma with Garlic",
        "price": 18.0,
        "cost": 8.0,
        "track_stock": False,
        "stock": 0,
        "image": "https://images.unsplash.com/photo-1529006557810-274b9b2fc783?w=300",
    },
    {
        "id": 2,
        "name": "Grilled Beef Burger",
        "price": 28.0,
        "cost": 12.0,
        "track_stock": True,
        "stock": 15,
        "image": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=300",
    },
    {
        "id": 3,
        "name": "Fresh Orange Juice",
        "price": 12.0,
        "cost": 4.0,
        "track_stock": False,
        "stock": 0,
        "image": "https://images.unsplash.com/photo-1613478223719-2ab802602423?w=300",
    },
]

DEFAULT_SETTINGS = {
    "restaurant_name": "Welcome to our restaurant",
    "restaurant_description": "Enjoy the best meals and fresh ingredients everyday!",
    "phone": "+971 50 123 4567",
    "address": "Main Street, City",
    "google_maps_url": "https://maps.google.com",
    "backgrounds": {
        "select_lang": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?q=80&w=1920",
        "main_menu": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?q=80&w=1920",
        "food_menu_page": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?q=80&w=1920",
        "cart_page": "https://images.unsplash.com/photo-1556742049-0a67d5193911?q=80&w=1920",
        "reservation_page": "https://images.unsplash.com/photo-1550966871-3ed3cdb5ed0c?q=80&w=1920",
        "delivery_page": "https://images.unsplash.com/photo-1526367790999-0150786686a2?q=80&w=1920",
        "my_orders_page": "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=1920",
        "contact_page": "https://images.unsplash.com/photo-1423666639041-f56000c27a9a?q=80&w=1920",
        "admin_page": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?q=80&w=1920",
    }
}

ALL_TABLES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

DELIVERY_STAGES = ["Order Received", "Preparing", "Out for Delivery", "Delivered"]
DINEIN_STAGES = ["Order Received", "Table Reserved", "Served"]

PAYMENT_METHODS = ["Cash on Delivery", "Card on Delivery", "Online Payment"]


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


def get_settings():
    settings = load_data(SETTINGS_FILE, DEFAULT_SETTINGS)
    if "backgrounds" not in settings:
        settings["backgrounds"] = DEFAULT_SETTINGS["backgrounds"]
    else:
        for k, v in DEFAULT_SETTINGS["backgrounds"].items():
            if k not in settings["backgrounds"]:
                settings["backgrounds"][k] = v
    return settings


def get_available_tables():
    orders = load_data(ORDERS_FILE)
    reservations = load_data(RESERVATIONS_FILE)
    
    busy_tables = [o.get("table") for o in orders if o.get("order_type") == "Dine-in" and o.get("status") != "Served" and o.get("table")]
    reserved_tables = [r.get("table_number") for r in reservations if "table_number" in r]
    
    occupied = set(busy_tables + reserved_tables)
    return [t for t in ALL_TABLES if t not in occupied]


def add_menu_item(name_en, price, cost, track_stock, stock_qty, image_data=""):
    menu = get_menu()
    new_id = max([item.get("id", 0) for item in menu if isinstance(item, dict)], default=0) + 1
    if not image_data:
        image_data = "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=300"
    menu.append({
        "id": new_id,
        "name": name_en.strip(),
        "price": float(price),
        "cost": float(cost),
        "track_stock": bool(track_stock),
        "stock": int(stock_qty) if track_stock else 0,
        "image": image_data,
    })
    save_data(MENU_FILE, menu)


def delete_menu_item(item_id):
    menu = get_menu()
    menu = [item for item in menu if isinstance(item, dict) and item.get("id") != item_id]
    save_data(MENU_FILE, menu)


def deduct_stock_for_order(cart_items):
    menu = get_menu()
    for disp_name, qty in cart_items.items():
        target_item = None
        for item in menu:
            if item["name"] == disp_name or translate_text(item["name"], st.session_state.app_language) == disp_name:
                target_item = item
                break
        if target_item and target_item.get("track_stock", False):
            target_item["stock"] = max(0, target_item.get("stock", 0) - int(qty))
    save_data(MENU_FILE, menu)


query_params = st.query_params

if "app_language" not in st.session_state:
    st.session_state.app_language = query_params.get("lang", None)

if "current_page" not in st.session_state:
    st.session_state.current_page = query_params.get("page", "main_menu")

if "cart" not in st.session_state:
    cart_param = query_params.get("cart", "{}")
    try:
        st.session_state.cart = json.loads(cart_param)
    except Exception:
        st.session_state.cart = {}

if "my_order_ids" not in st.session_state:
    st.session_state.my_order_ids = []


app_settings = get_settings()
page_bgs = app_settings.get("backgrounds", DEFAULT_SETTINGS["backgrounds"])

curr_bg_key = "select_lang" if st.session_state.app_language is None else st.session_state.current_page
bg_url = page_bgs.get(curr_bg_key, page_bgs.get("main_menu", DEFAULT_SETTINGS["backgrounds"]["main_menu"]))

st.markdown(
    f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(10, 10, 10, 0.78), rgba(10, 10, 10, 0.78)), 
                    url("{bg_url}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    /* إصلاح حقول الإدخال النصية والرقمية */
    input, .stNumberInput input, div[data-baseweb="input"] input {{
        direction: ltr !important;
        font-family: Arial, Helvetica, sans-serif !important;
        color: #000000 !important;
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
    }}

    /* إصلاح نصوص وأرقام اختيار الوقت (st.time_input) بالتفصيل لتجاوز اللون الأبيض */
    div[data-testid="stTimeInput"] * {{
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }}
    div[data-testid="stTimeInput"] input {{
        background-color: #FFFFFF !important;
        font-weight: bold !important;
        opacity: 1 !important;
        direction: ltr !important;
    }}

    /* إصلاح نصوص وأرقام اختيار التاريخ (st.date_input) */
    div[data-testid="stDateInput"] * {{
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }}
    div[data-testid="stDateInput"] input {{
        background-color: #FFFFFF !important;
        font-weight: bold !important;
        opacity: 1 !important;
    }}

    div[data-baseweb="popover"] * {{
        color: #000000 !important;
    }}

    /* إصلاح زر ونصوص رفع الصور (st.file_uploader) */
    div[data-testid="stFileUploader"] * {{
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }}
    div[data-testid="stFileUploader"] section {{
        background-color: #FFFFFF !important;
        border-radius: 8px !important;
    }}
    div[data-testid="stFileUploader"] button {{
        background-color: #f0f2f6 !important;
        border: 1px solid #ccc !important;
    }}
    div[data-testid="stFileUploader"] button * {{
        color: #000000 !important;
    }}

    [data-testid="stSidebar"] {{
        background-color: rgba(20, 20, 20, 0.92) !important;
        backdrop-filter: blur(12px);
    }}

    h1, h2, h3, h4, h5, h6, p, label, span, .stMarkdown {{
        color: #FFFFFF !important;
    }}

    div.stButton > button {{
        background-color: #FF4B4B !important;
        border-radius: 10px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.3s ease !important;
    }}

    div.stButton > button * {{
        color: #FFFFFF !important;
        font-weight: bold !important;
    }}

    div.stButton > button:hover {{
        background-color: #FF2B2B !important;
        transform: translateY(-2px) scale(1.02) !important;
    }}

    .receipt-box {{
        background-color: #FFFFFF !important;
        color: #000000 !important;
        padding: 20px;
        border-radius: 8px;
        width: 100%;
        max-width: 380px;
        margin: 15px auto;
        font-family: 'Courier New', Courier, monospace;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        border: 1px solid #ddd;
    }}
    .receipt-box * {{ color: #000000 !important; }}
    .receipt-header {{
        text-align: center;
        border-bottom: 2px dashed #000;
        padding-bottom: 10px;
        margin-bottom: 10px;
    }}
    .receipt-row {{ 
        display: flex; 
        justify-content: space-between; 
        margin: 5px 0; 
    }}
    .receipt-footer {{
        border-top: 2px dashed #000;
        margin-top: 10px;
        padding-top: 10px;
        text-align: center;
    }}
    </style>
""",
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def translate_text(text, target_lang):
    if target_lang == "en" or not text:
        return text
    try:
        translator = Translator(to_lang=target_lang, from_lang="en")
        return translator.translate(text)
    except Exception:
        return text


def generate_receipt_html(order):
    settings = get_settings()
    
    items_lines = []
    items_dict = order.get("items", {})
    if isinstance(items_dict, dict):
        for name, qty in items_dict.items():
            items_lines.append(f'<div class="receipt-row"><span>{name}</span><span>x{qty}</span></div>')
    
    items_html = "".join(items_lines)

    table_str = f'<p style="margin:2px 0;"><strong>Table:</strong> #{order.get("table")}</p>' if order.get("table") else ""
    time_str = f'<p style="margin:2px 0;"><strong>Time:</strong> {order.get("time")}</p>' if order.get("time") else ""
    email_str = f'<p style="margin:2px 0;"><strong>Email:</strong> {order.get("email")}</p>' if order.get("email") else ""
    address_str = f'<p style="margin:2px 0;"><strong>Address:</strong> {order.get("address")}</p>' if order.get("address") else ""

    res_name = settings.get("restaurant_name", "RESTAURANT RECEIPT")
    phone = settings.get("phone", "")
    date_val = order.get("date", "")
    order_id = order.get("order_id", "")
    customer = order.get("customer", "")
    cust_phone = order.get("phone", "")
    order_type = order.get("order_type", "")
    pay_method = order.get("payment_method", "")
    tot_val = float(order.get("total", 0))

    receipt = (
        '<div class="receipt-box">'
        '<div class="receipt-header">'
        f'<h3 style="margin:0 0 5px 0;">🧾 {res_name}</h3>'
        f'<p style="margin:2px 0;">Tel: {phone}</p>'
        f'<p style="margin:2px 0;">Date: {date_val}</p>'
        f'<p style="margin:4px 0;"><strong>Order ID: {order_id}</strong></p>'
        '</div>'
        f'<p style="margin:2px 0;"><strong>Customer:</strong> {customer}</p>'
        f'<p style="margin:2px 0;"><strong>Phone:</strong> {cust_phone}</p>'
        f'{email_str}'
        f'<p style="margin:2px 0;"><strong>Type:</strong> {order_type} | <strong>Pay:</strong> {pay_method}</p>'
        f'{table_str}'
        f'{time_str}'
        f'{address_str}'
        '<hr style="border-top: 1px dashed #000; margin: 10px 0;">'
        '<h4 style="margin: 5px 0 10px 0;">ITEMS:</h4>'
        f'{items_html}'
        '<div class="receipt-footer">'
        f'<h3 style="margin: 5px 0;">TOTAL: {tot_val:.2f} AED</h3>'
        '<p style="margin: 5px 0 0 0;">Thank you for your visit!</p>'
        '</div>'
        '</div>'
    )
    return receipt


def update_url_params():
    params = {}
    if st.session_state.app_language:
        params["lang"] = st.session_state.app_language
    if st.session_state.current_page:
        params["page"] = st.session_state.current_page
    if st.session_state.cart:
        params["cart"] = json.dumps(st.session_state.cart)

    st.query_params.clear()
    for k, v in params.items():
        st.query_params[k] = v


# ==========================================
# 1. شاشة اختيار اللغة
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
                update_url_params()
                st.rerun()

# ==========================================
# 2. الشاشة الرئيسية
# ==========================================
elif st.session_state.current_page == "main_menu":
    lang = st.session_state.app_language

    col_top1, col_top2 = st.columns([3, 1])
    with col_top2:
        if st.button("🌐 Language / اللغة", use_container_width=True):
            st.session_state.app_language = None
            st.session_state.current_page = "main_menu"
            update_url_params()
            st.rerun()

    welcome_title = translate_text(app_settings.get("restaurant_name", "Welcome to our restaurant"), lang)
    st.title(f"🏠 {welcome_title}")
    st.write(translate_text(app_settings.get("restaurant_description", ""), lang))
    st.write("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(f"📜 {translate_text('Food Menu', lang)}", use_container_width=True, type="primary"):
            st.session_state.current_page = "food_menu_page"
            update_url_params()
            st.rerun()
        st.write("<br>", unsafe_allow_html=True)
        if st.button(f"📅 {translate_text('Table Reservation', lang)}", use_container_width=True, type="primary"):
            st.session_state.current_page = "reservation_page"
            update_url_params()
            st.rerun()

    with col2:
        if st.button(f"🛵 {translate_text('Delivery', lang)}", use_container_width=True, type="primary"):
            st.session_state.current_page = "delivery_page"
            update_url_params()
            st.rerun()
        st.write("<br>", unsafe_allow_html=True)
        if st.button(f"🛒 {translate_text('Shopping Cart', lang)}", use_container_width=True, type="secondary"):
            st.session_state.current_page = "cart_page"
            update_url_params()
            st.rerun()

    with col3:
        if st.button(f"🛍️ {translate_text('My Orders / طلباتي', lang)}", use_container_width=True, type="secondary"):
            st.session_state.current_page = "my_orders_page"
            update_url_params()
            st.rerun()
        st.write("<br>", unsafe_allow_html=True)
        if st.button(f"📞 {translate_text('Contact Us', lang)}", use_container_width=True, type="secondary"):
            st.session_state.current_page = "contact_page"
            update_url_params()
            st.rerun()

    st.write("---")
    if st.button(f"🔒 {translate_text('Admin Dashboard', lang)}", use_container_width=True):
        st.session_state.current_page = "admin_page"
        update_url_params()
        st.rerun()


# ==========================================
# 3. لوحة التحكم (Admin Dashboard)
# ==========================================
elif st.session_state.current_page == "admin_page":
    lang = st.session_state.app_language

    if st.button("⬅️ Back to Main / العودة للرئيسية"):
        st.session_state.current_page = "main_menu"
        update_url_params()
        st.rerun()

    st.write("---")
    
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:
        st.subheader("🔒 Enter Admin Password / أدخل كلمة المرور")
        password = st.text_input("Password", type="password", key="admin_pwd_main")
        if st.button("Login / دخول", type="primary"):
            if password == "1234":
                st.session_state.admin_logged_in = True
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error("Wrong password!")
    else:
        st.title(f"🛠️ Admin Dashboard")

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📦 Orders",
            "📅 Reservations",
            "📜 Menu",
            "📈 Reports",
            "⚙️ Settings",
            "📲 Table QR Code",
        ])

        with tab1:
            st.header("Incoming Orders")
            orders = load_data(ORDERS_FILE)
            if orders:
                for idx, o in enumerate(reversed(orders), 1):
                    order_id = o.get("order_id", f"#{idx}")
                    order_type = o.get("order_type", "Delivery")
                    stages = DINEIN_STAGES if order_type == "Dine-in" else DELIVERY_STAGES
                    current_status = o.get("status", "Order Received")

                    with st.expander(f"Order {order_id} ({order_type}) - {o.get('customer')} | Total: {o.get('total')} AED | Status: {current_status}"):
                        st.markdown(generate_receipt_html(o), unsafe_allow_html=True)
                        new_status = st.selectbox(
                            "Select Status",
                            options=stages,
                            index=stages.index(current_status) if current_status in stages else 0,
                            key=f"status_select_{order_id}",
                        )
                        if st.button("Save Status", key=f"save_status_{order_id}"):
                            for real_order in orders:
                                if real_order.get("order_id") == order_id:
                                    real_order["status"] = new_status
                                    break
                            save_data(ORDERS_FILE, orders)
                            st.success("Status updated!")
                            st.rerun()
            else:
                st.info("No orders yet")

        with tab2:
            st.header("Reservations")
            reservations = load_data(RESERVATIONS_FILE)
            if reservations:
                for r in reversed(reservations):
                    st.write(f"📌 **{r.get('name')}** - Table: #{r.get('table_number')} | Phone: {r.get('phone')} | Date: {r.get('date')} | Time: {r.get('time')}")
            else:
                st.info("No reservations yet")

        with tab3:
            st.header("Manage Menu & Inventory")
            col_name, col_price, col_cost = st.columns([3, 1, 1])
            with col_name:
                new_name_input = st.text_input("Item Name (English)")
            with col_price:
                new_price_input = st.number_input("Price (AED)", min_value=1.0, value=20.0)
            with col_cost:
                new_cost_input = st.number_input("Cost Price (AED)", min_value=0.0, value=8.0)

            track_stock_opt = st.checkbox("Enable inventory tracking?")
            stock_qty_input = st.number_input("Stock Quantity", min_value=0, value=10) if track_stock_opt else 0
            
            uploaded_file = st.file_uploader("Upload Item Image / تحميل صورة للمنتج من الجهاز", type=["png", "jpg", "jpeg", "webp"])
            final_image_data = st.text_input("Or Image URL / أو ضع رابط الصورة مباشر")
            
            if st.button("Add Item"):
                if new_name_input:
                    if uploaded_file is not None:
                        bytes_data = uploaded_file.getvalue()
                        base64_str = base64.b64encode(bytes_data).decode()
                        mime_type = uploaded_file.type
                        final_image_data = f"data:{mime_type};base64,{base64_str}"

                    add_menu_item(new_name_input, new_price_input, new_cost_input, track_stock_opt, stock_qty_input, final_image_data)
                    st.success("Item added!")
                    st.rerun()

            st.markdown("---")
            for item in get_menu():
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.write(f"• **{item['name']}** - Price: {item['price']} AED | Stock: {item.get('stock', 'Unlimited')}")
                with c2:
                    if st.button("Delete", key=f"del_{item['id']}"):
                        delete_menu_item(item["id"])
                        st.rerun()

        with tab4:
            st.header("📈 Reports & Sales Analytics / تقارير المبيعات والأرباح")
            
            orders = load_data(ORDERS_FILE)
            menu_items = get_menu()
            
            cost_map = {}
            price_map = {}
            for item in menu_items:
                cost_map[item["name"]] = float(item.get("cost", 0.0))
                cost_map[translate_text(item["name"], lang)] = float(item.get("cost", 0.0))
                price_map[item["name"]] = float(item.get("price", 0.0))
                price_map[translate_text(item["name"], lang)] = float(item.get("price", 0.0))

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                start_date = st.date_input("From Date / من تاريخ", value=datetime.date.today() - datetime.timedelta(days=7))
            with col_d2:
                end_date = st.date_input("To Date / إلى تاريخ", value=datetime.date.today())

            if orders:
                sales_summary = {}
                filtered_total_revenue = 0.0

                for o in orders:
                    o_date_str = o.get("date", "")
                    try:
                        o_date = datetime.datetime.strptime(o_date_str, "%Y-%m-%d").date()
                    except Exception:
                        o_date = datetime.date.today()

                    if start_date <= o_date <= end_date:
                        items_dict = o.get("items", {})
                        if isinstance(items_dict, dict):
                            for item_name, qty in items_dict.items():
                                qty = int(qty)
                                if item_name not in sales_summary:
                                    sales_summary[item_name] = 0
                                sales_summary[item_name] += qty
                        filtered_total_revenue += float(o.get("total", 0.0))

                if sales_summary:
                    table_rows = []
                    total_period_profit = 0.0

                    for item_name, qty_sold in sales_summary.items():
                        unit_cost = cost_map.get(item_name, 0.0)
                        unit_price = price_map.get(item_name, 0.0)
                        
                        total_item_revenue = unit_price * qty_sold
                        total_item_cost = unit_cost * qty_sold
                        item_profit = total_item_revenue - total_item_cost
                        total_period_profit += item_profit

                        table_rows.append({
                            "Item Name / اسم الصنف": item_name,
                            "Quantity Sold / الكمية المباعة": qty_sold,
                            "Purchase Cost / تكلفة الشراء": f"{unit_cost:.2f} AED",
                            "Selling Price / سعر البيع": f"{unit_price:.2f} AED",
                            "Item Profit / ربح الصنف": f"{item_profit:.2f} AED",
                        })

                    df_sales = pd.DataFrame(table_rows)
                    df_sales.index = range(1, len(df_sales) + 1)
                    
                    st.write("<br>", unsafe_allow_html=True)
                    st.subheader("📊 Sales Breakdown / تفاصيل المبيعات للفترة المحدد")
                    st.dataframe(df_sales, use_container_width=True)

                    st.markdown("---")
                    col_m1, col_m2 = st.columns(2)
                    with col_m1:
                        st.metric("Total Revenue / إجمالي المبيعات", f"{filtered_total_revenue:.2f} AED")
                    with col_m2:
                        st.metric("Total Profit / إجمالي ربح الفترة", f"{total_period_profit:.2f} AED")
                else:
                    st.info("No sales found for the selected date range.")
            else:
                st.info("No sales data recorded yet.")

        with tab5:
            st.header("⚙️ General Settings / الإعدادات العامة")
            
            set_tab1, set_tab2, set_tab3, set_tab4 = st.tabs([
                "🏪 Profile",
                "🖼️ Backgrounds",
                "📞 Contact Info",
                "📍 Google Maps",
            ])

            settings_data = get_settings()

            with set_tab1:
                st.subheader("Restaurant Profile / بروفايل المطعم")
                res_name = st.text_input("Restaurant Name", value=settings_data.get("restaurant_name", ""))
                res_desc = st.text_area("Restaurant Description", value=settings_data.get("restaurant_description", ""))
                if st.button("Save Profile", type="primary"):
                    settings_data["restaurant_name"] = res_name
                    settings_data["restaurant_description"] = res_desc
                    save_data(SETTINGS_FILE, settings_data)
                    st.success("Profile saved successfully!")
                    st.rerun()

            with set_tab2:
                st.subheader("Customize Page Backgrounds / خلفيات الصفحات")
                st.info("Paste image URLs (Unsplash / Google / Direct Image Link) to change page backgrounds.")
                
                bgs = settings_data.get("backgrounds", DEFAULT_SETTINGS["backgrounds"])
                
                bg_main = st.text_input("Main Page Background URL", value=bgs.get("main_menu", ""))
                bg_food = st.text_input("Food Menu Background URL", value=bgs.get("food_menu_page", ""))
                bg_cart = st.text_input("Shopping Cart Background URL", value=bgs.get("cart_page", ""))
                bg_res = st.text_input("Reservation Background URL", value=bgs.get("reservation_page", ""))
                bg_del = st.text_input("Delivery Background URL", value=bgs.get("delivery_page", ""))
                bg_contact = st.text_input("Contact Us Background URL", value=bgs.get("contact_page", ""))

                if st.button("Save Backgrounds", type="primary"):
                    settings_data["backgrounds"]["main_menu"] = bg_main
                    settings_data["backgrounds"]["food_menu_page"] = bg_food
                    settings_data["backgrounds"]["cart_page"] = bg_cart
                    settings_data["backgrounds"]["reservation_page"] = bg_res
                    settings_data["backgrounds"]["delivery_page"] = bg_del
                    settings_data["backgrounds"]["contact_page"] = bg_contact
                    save_data(SETTINGS_FILE, settings_data)
                    st.success("Backgrounds updated successfully!")
                    st.rerun()

            with set_tab3:
                st.subheader("Contact Information / بيانات التواصل")
                edit_phone = st.text_input("Phone Number", value=settings_data.get("phone", ""))
                edit_address = st.text_input("Address", value=settings_data.get("address", ""))
                if st.button("Save Contact Info", type="primary"):
                    settings_data["phone"] = edit_phone
                    settings_data["address"] = edit_address
                    save_data(SETTINGS_FILE, settings_data)
                    st.success("Contact info saved successfully!")
                    st.rerun()

            with set_tab4:
                st.subheader("Google Maps Location / موقع الجوجل مابس")
                edit_maps = st.text_input("Google Maps URL", value=settings_data.get("google_maps_url", ""))
                if st.button("Save Location URL", type="primary"):
                    settings_data["google_maps_url"] = edit_maps
                    save_data(SETTINGS_FILE, settings_data)
                    st.success("Google Maps URL saved successfully!")
                    st.rerun()

        with tab6:
            st.header("📲 Table QR Code Generator")
            base_app_url = "https://restaurantapp-q9mvwzvmevytzln2zbzryx.streamlit.app"
            selected_qr_table = st.selectbox("Select Table Number", ALL_TABLES)
            qr_url = f"{base_app_url}/?table={selected_qr_table}"
            
            if QRCODE_AVAILABLE:
                qr = qrcode.QRCode(version=1, box_size=10, border=4)
                qr.add_data(qr_url)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                byte_im = buf.getvalue()
                
                st.image(byte_im, caption=f"QR Code for Table #{selected_qr_table}", width=250)
                st.download_button(
                    label=f"📥 Download QR Code for Table #{selected_qr_table}",
                    data=byte_im,
                    file_name=f"table_{selected_qr_table}_qr.png",
                    mime="image/png",
                )
            else:
                st.warning("Please add 'qrcode' and 'Pillow' to requirements.txt on GitHub to generate QR images.")
                st.info(f"Direct Table Link: {qr_url}")


# ==========================================
# 5. صفحات الخدمة للعميل
# ==========================================
elif st.session_state.current_page in [
    "food_menu_page",
    "delivery_page",
    "reservation_page",
    "cart_page",
    "my_orders_page",
    "contact_page",
]:
    lang = st.session_state.app_language

    if st.button("⬅️ Back to Main / العودة للرئيسية"):
        st.session_state.current_page = "main_menu"
        update_url_params()
        st.rerun()

    st.write("---")

    if st.session_state.current_page == "food_menu_page":
        st.title(f"📜 {translate_text('Food Menu', lang)}")
        
        if "just_added_id" not in st.session_state:
            st.session_state.just_added_id = None

        for item in get_menu():
            display_name = translate_text(item["name"], lang)
            c_img, c1, c2 = st.columns([1.5, 4, 2])
            with c_img:
                st.image(item.get("image"), use_container_width=True)
            with c1:
                st.subheader(display_name)
                st.write(f"{item['price']} AED")
            with c2:
                qty = st.number_input("Qty", min_value=1, value=1, key=f"qty_{item['id']}")
                
                is_just_added = (st.session_state.just_added_id == item["id"])
                btn_label = "✅ Added! / تمت الإضافة" if is_just_added else translate_text("Add to Cart", lang)
                btn_type = "secondary" if is_just_added else "primary"
                
                if st.button(btn_label, key=f"btn_{item['id']}", type=btn_type):
                    st.session_state.cart[display_name] = st.session_state.cart.get(display_name, 0) + int(qty)
                    st.session_state.just_added_id = item["id"]
                    update_url_params()
                    st.rerun()
            st.markdown("---")

        if st.session_state.just_added_id is not None:
            time.sleep(1.5)
            st.session_state.just_added_id = None
            st.rerun()

    elif st.session_state.current_page == "cart_page":
        st.title(f"🛒 {translate_text('Shopping Cart', lang)}")
        if not st.session_state.cart:
            st.info(translate_text("Your cart is empty", lang))
        else:
            total_price = 0.0
            menu_items = get_menu()
            price_map = {translate_text(i["name"], lang): i["price"] for i in menu_items}
            price_map.update({i["name"]: i["price"] for i in menu_items})

            for item_name, quantity in list(st.session_state.cart.items()):
                p = price_map.get(item_name, 0.0)
                tot = p * quantity
                total_price += tot
                st.write(f"• **{item_name}** x{quantity} = {tot:.2f} AED")

            st.subheader(f"Total: {total_price:.2f} AED")
            st.write("---")
            c_dine, c_del = st.columns(2)
            with c_dine:
                if st.button("🍽️ Dine-in (Eat in Restaurant)", use_container_width=True, type="primary"):
                    st.session_state.current_page = "reservation_page"
                    update_url_params()
                    st.rerun()
            with c_del:
                if st.button("🛵 Delivery Order", use_container_width=True, type="primary"):
                    st.session_state.current_page = "delivery_page"
                    update_url_params()
                    st.rerun()

    elif st.session_state.current_page == "reservation_page":
        st.title(f"🍽️ Dine-in & Table Reservation / حجز داخل المطعم")
        res_name = st.text_input("Your Name / الاسم")
        res_phone = st.text_input("Phone Number / رقم الهاتف")
        res_email = st.text_input("Email / البريد الإلكتروني (لإرسال التنبيه قبل الحضور بساعة)")
        
        available_tables = get_available_tables()
        if available_tables:
            selected_table = st.selectbox("Available Tables Only / التربيزات الفاضية المتاحة فقط", options=available_tables)
        else:
            selected_table = None
            st.error("جميع الطاولات محجوزة حالياً / All tables are currently reserved!")

        col_time1, col_time2 = st.columns(2)
        with col_time1:
            res_date = st.date_input("Reservation Date / تاريخ الحضور")
        with col_time2:
            res_time = st.time_input("Expected Arrival Time / وقت الحضور المتوقع", value=datetime.time(19, 0))

        selected_payment = st.radio("Payment Method / طريقة الدفع", options=PAYMENT_METHODS)

        if st.button("Confirm Table Reservation & Order / تأكيد الحجز والطلب", type="primary"):
            if res_name and res_phone and selected_table:
                orders = load_data(ORDERS_FILE)
                price_dict = {translate_text(item["name"], lang): item["price"] for item in get_menu()}
                total_price = sum(price_dict.get(k, 0) * v for k, v in st.session_state.cart.items())
                order_id = f"ORD-{random.randint(1000, 9999)}"

                time_formatted = res_time.strftime("%I:%M %p")

                new_order = {
                    "order_id": order_id,
                    "customer": res_name,
                    "phone": res_phone,
                    "email": res_email,
                    "table": selected_table,
                    "time": time_formatted,
                    "order_type": "Dine-in",
                    "payment_method": selected_payment,
                    "items": st.session_state.cart,
                    "total": total_price,
                    "date": str(res_date),
                    "status": "Order Received",
                }
                orders.append(new_order)
                save_data(ORDERS_FILE, orders)
                deduct_stock_for_order(st.session_state.cart)

                rest_phone = app_settings.get("phone", "").replace(" ", "").replace("+", "")
                msg = f"مرحباً! تم تأكيد حجز طاولة #{selected_table} باسم {res_name} بتاريخ {res_date} الساعة {time_formatted}. سيتم تذكيركم بالموعد قبل الحضور بساعة."
                whatsapp_url = f"https://wa.me/{rest_phone}?text={urllib.parse.quote(msg)}"

                st.success(f"تم حجز الطاولة #{selected_table} بنجاح!")
                st.info(f"📧 سيتم إرسال إشعار تذكير إلى إيميلك: {res_email} قبل موعد الحضور بساعة ({time_formatted}).")
                st.markdown(f"📲 [**إرسال تفاصيل الفاتورة والحجز إلى إدارة المطعم عبر واتساب**]({whatsapp_url})", unsafe_allow_html=True)

                st.session_state.cart = {}
                st.session_state.my_order_ids.append(order_id)
                time.sleep(2)
                st.session_state.current_page = "my_orders_page"
                update_url_params()
                st.rerun()
            else:
                st.warning("رجاء إدخال جميع البيانات واختيار طاولة متاحة!")

    elif st.session_state.current_page == "delivery_page":
        st.title(f"🛵 Delivery Details / تفاصيل الدليفري")
        del_name = st.text_input("Your Name")
        del_address = st.text_area("Delivery Address")
        del_phone = st.text_input("Phone Number")
        selected_payment = st.radio("Payment Method", options=PAYMENT_METHODS)

        if st.button("Confirm Delivery Order", type="primary"):
            if del_name and del_address and del_phone:
                orders = load_data(ORDERS_FILE)
                price_dict = {translate_text(item["name"], lang): item["price"] for item in get_menu()}
                total_price = sum(price_dict.get(k, 0) * v for k, v in st.session_state.cart.items())
                order_id = f"ORD-{random.randint(1000, 9999)}"

                new_order = {
                    "order_id": order_id,
                    "customer": del_name,
                    "address": del_address,
                    "phone": del_phone,
                    "order_type": "Delivery",
                    "payment_method": selected_payment,
                    "items": st.session_state.cart,
                    "total": total_price,
                    "date": str(datetime.date.today()),
                    "status": "Order Received",
                }
                orders.append(new_order)
                save_data(ORDERS_FILE, orders)
                deduct_stock_for_order(st.session_state.cart)

                st.session_state.cart = {}
                st.session_state.my_order_ids.append(order_id)
                st.session_state.current_page = "my_orders_page"
                update_url_params()
                st.rerun()
            else:
                st.warning("Please fill in all details (Name, Address, Phone)!")

    # ==========================================
    # 🛍️ صفحة طلباتي (My Orders)
    # ==========================================
    elif st.session_state.current_page == "my_orders_page":
        st.title(f"🛍️ {translate_text('My Orders / طلباتي', lang)}")
        all_orders = load_data(ORDERS_FILE)
        
        user_order_ids = st.session_state.my_order_ids
        if user_order_ids:
            my_orders = [o for o in all_orders if o.get("order_id") in user_order_ids]
        else:
            my_orders = all_orders[-3:] if all_orders else []

        if not my_orders:
            st.info("لا توجد لديك أي طلبات حالياً / No orders found.")
        else:
            active_orders = [o for o in my_orders if (o.get("order_type") == "Dine-in" and o.get("status") != "Served") or (o.get("order_type") != "Dine-in" and o.get("status") != "Delivered")]
            completed_orders = [o for o in my_orders if (o.get("order_type") == "Dine-in" and o.get("status") == "Served") or (o.get("order_type") != "Dine-in" and o.get("status") == "Delivered")]

            tab_active, tab_completed = st.tabs([
                "⏳ الطلبات قيد التنفيذ (Active Orders)",
                "✅ الطلبات المنفذة (Completed Orders)"
            ])

            with tab_active:
                if active_orders:
                    for o in reversed(active_orders):
                        order_type = o.get("order_type", "Delivery")
                        st.subheader(f"Order #{o.get('order_id')} ({order_type})")
                        
                        stages = DINEIN_STAGES if order_type == "Dine-in" else DELIVERY_STAGES
                        current_status = o.get("status", "Order Received")
                        
                        stage_idx = stages.index(current_status) if current_status in stages else 0
                        progress_val = (stage_idx + 1) / len(stages)
                        st.progress(progress_val)
                        
                        cols_stages = st.columns(len(stages))
                        for i, stage in enumerate(stages):
                            with cols_stages[i]:
                                if i <= stage_idx:
                                    st.markdown(f"✅ **{stage}**")
                                else:
                                    st.markdown(f"⚪ {stage}")
                        
                        st.markdown(generate_receipt_html(o), unsafe_allow_html=True)
                        st.markdown("---")
                else:
                    st.info("لا توجد طلبات قيد التنفيذ حالياً.")

            with tab_completed:
                if completed_orders:
                    for o in reversed(completed_orders):
                        st.markdown(generate_receipt_html(o), unsafe_allow_html=True)
                        st.markdown("---")
                else:
                    st.info("لا توجد طلبات مكتملة بعد.")

    elif st.session_state.current_page == "contact_page":
        st.title(f"📞 Contact Us")
        st.write(f"**Phone:** {app_settings.get('phone', '')}")
        st.write(f"**Address:** {app_settings.get('address', '')}")
        
        maps_url = app_settings.get("google_maps_url", "")
        if maps_url:
            st.markdown(f"📍 [**Open Location in Google Maps**]({maps_url})", unsafe_allow_html=True)
