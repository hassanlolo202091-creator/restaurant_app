import base64
import datetime
import json
import os
import random
import time
import pandas as pd
import streamlit as st
from translate import Translator

st.set_page_config(page_title="Restaurant App", page_icon="🍔", layout="wide")

st.markdown(
    """
    <style>
    input, .stNumberInput input, div[data-baseweb="input"] input {
        direction: ltr !important;
        font-family: Arial, Helvetica, sans-serif !important;
        font-variant-numeric: lining-nums tabular-nums !important;
        -webkit-locale: "en-US" !important;
    }
    .print-receipt {
        background-color: #f9f9f9;
        border: 1px dashed #333;
        padding: 15px;
        border-radius: 8px;
        font-family: 'Courier New', Courier, monospace;
        color: #111;
    }
    </style>
""",
    unsafe_allow_html=True,
)

ORDERS_FILE = "orders.json"
RESERVATIONS_FILE = "reservations.json"
MENU_FILE = "menu.json"

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

ALL_TABLES = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

ORDER_STAGES = [
    "Order Received",
    "Preparing",
    "Out for Delivery",
    "Delivered",
]

PAYMENT_METHODS = [
    "Cash on Delivery",
    "Card on Delivery",
    "Online Payment",
]


@st.cache_data(show_spinner=False)
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


def get_menu():
  return load_data(MENU_FILE, DEFAULT_MENU)


def get_available_tables():
  reservations = load_data(RESERVATIONS_FILE)
  reserved_tables = [
      r.get("table_number") for r in reservations if "table_number" in r
  ]
  available = [t for t in ALL_TABLES if t not in reserved_tables]
  return available


def add_menu_item(
    name_en, price, cost, track_stock, stock_qty, image_data=""
):
  menu = get_menu()
  new_id = (
      max(
          [item.get("id", 0) for item in menu if isinstance(item, dict)],
          default=0,
      )
      + 1
  )
  if not image_data:
    image_data = (
        "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=300"
    )
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


def update_menu_item(
    item_id, name_en, price, cost, track_stock, stock_qty, image_data=""
):
  menu = get_menu()
  for item in menu:
    if isinstance(item, dict) and item.get("id") == item_id:
      item["name"] = name_en.strip()
      item["price"] = float(price)
      item["cost"] = float(cost)
      item["track_stock"] = bool(track_stock)
      item["stock"] = int(stock_qty) if track_stock else 0
      if image_data:
        item["image"] = image_data
      break
  save_data(MENU_FILE, menu)


def delete_menu_item(item_id):
  menu = get_menu()
  menu = [
      item
      for item in menu
      if isinstance(item, dict) and item.get("id") != item_id
  ]
  save_data(MENU_FILE, menu)


def deduct_stock_for_order(cart_items):
  menu = get_menu()
  for disp_name, qty in cart_items.items():
    target_item = None
    for item in menu:
      if (
          item["name"] == disp_name
          or translate_text(item["name"], st.session_state.app_language)
          == disp_name
      ):
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

if "admin_language" not in st.session_state:
  st.session_state.admin_language = None

if "cart" not in st.session_state:
  cart_param = query_params.get("cart", "{}")
  try:
    st.session_state.cart = json.loads(cart_param)
  except Exception:
    st.session_state.cart = {}

if "last_order_id" not in st.session_state:
  st.session_state.last_order_id = query_params.get("order_id", None)

if "editing_item_id" not in st.session_state:
  st.session_state.editing_item_id = None


def update_url_params():
  params = {}
  if st.session_state.app_language:
    params["lang"] = st.session_state.app_language
  if st.session_state.current_page:
    params["page"] = st.session_state.current_page
  if st.session_state.cart:
    params["cart"] = json.dumps(st.session_state.cart)
  if st.session_state.last_order_id:
    params["order_id"] = st.session_state.last_order_id

  st.query_params.clear()
  for k, v in params.items():
    st.query_params[k] = v


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
        update_url_params()
        st.rerun()

# ==========================================
# 2. الشاشة الرئيسية
# ==========================================
elif st.session_state.current_page == "main_menu":
  lang = st.session_state.app_language

  st.sidebar.title("Options 🌐")
  if st.sidebar.button("Change Language / تغيير اللغة"):
    st.session_state.app_language = None
    st.session_state.current_page = "main_menu"
    update_url_params()
    st.rerun()

  welcome_title = translate_text("Welcome to our restaurant", lang)
  st.title(f"🏠 {welcome_title}")
  st.write("---")

  col1, col2, col3 = st.columns(3)

  with col1:
    btn_menu = translate_text("Food Menu", lang)
    if st.button(f"📜 {btn_menu}", use_container_width=True, type="primary"):
      st.session_state.current_page = "food_menu_page"
      update_url_params()
      st.rerun()

    st.write("<br>", unsafe_allow_html=True)

    btn_reservation = translate_text("Table Reservation", lang)
    if st.button(
        f"📅 {btn_reservation}", use_container_width=True, type="primary"
    ):
      st.session_state.current_page = "reservation_page"
      update_url_params()
      st.rerun()

  with col2:
    btn_delivery = translate_text("Delivery", lang)
    if st.button(
        f"🛵 {btn_delivery}", use_container_width=True, type="primary"
    ):
      st.session_state.current_page = "delivery_page"
      update_url_params()
      st.rerun()

    st.write("<br>", unsafe_allow_html=True)

    btn_cart = translate_text("Shopping Cart", lang)
    if st.button(f"🛒 {btn_cart}", use_container_width=True, type="secondary"):
      st.session_state.current_page = "cart_page"
      update_url_params()
      st.rerun()

  with col3:
    btn_track = translate_text("Track Orders", lang)
    if st.button(
        f"📍 {btn_track}", use_container_width=True, type="secondary"
    ):
      st.session_state.current_page = "track_orders_page"
      update_url_params()
      st.rerun()

    st.write("<br>", unsafe_allow_html=True)

    btn_contact = translate_text("Contact Us", lang)
    if st.button(
        f"📞 {btn_contact}", use_container_width=True, type="secondary"
    ):
      st.session_state.current_page = "contact_page"
      update_url_params()
      st.rerun()

  st.write("---")
  btn_admin = translate_text("Admin Dashboard", lang)
  if st.button(f"🔒 {btn_admin}", use_container_width=True):
    st.session_state.current_page = "admin_page"
    update_url_params()
    st.rerun()


# ==========================================
# 3. لوحة التحكم (Admin Mode)
# ==========================================
elif st.session_state.current_page == "admin_page":
  lang = st.session_state.app_language

  if st.sidebar.button("Back to Main / العودة للرئيسية"):
    st.session_state.current_page = "main_menu"
    update_url_params()
    st.rerun()

  admin_lang = st.session_state.admin_language if st.session_state.admin_language else lang

  password = st.sidebar.text_input(
      translate_text("Password", admin_lang), type="password"
  )

  if password == "1234":
    st.sidebar.success(translate_text("Logged in successfully", admin_lang))
    st.title(f"🛠️ {translate_text('Admin Dashboard', admin_lang)}")

    tab_a1_text = translate_text("Incoming Orders", admin_lang)
    tab_a2_text = translate_text("Reservations", admin_lang)
    tab_a3_text = translate_text("Manage Menu & Inventory", admin_lang)
    tab_a4_text = translate_text("Reports & Profits", admin_lang)

    tab1, tab2, tab3, tab4 = st.tabs([
        f"📦 {tab_a1_text}",
        f"📅 {tab_a2_text}",
        f"📜 {tab_a3_text}",
        f"📈 {tab_a4_text}",
    ])

    with tab1:
      st.header(tab_a1_text)
      orders = load_data(ORDERS_FILE)
      if orders:
        for idx, o in enumerate(reversed(orders), 1):
          order_id = o.get("order_id", f"#{idx}")
          current_status = o.get("status", "Order Received")

          with st.expander(
              f"Order {order_id} - {o.get('customer')} | Total:"
              f" {o.get('total')} {translate_text('AED', admin_lang)} | Status:"
              f" {translate_text(current_status, admin_lang)}"
          ):
            st.write(
                f"**{translate_text('Order Type', admin_lang)}:**"
                f" {o.get('order_type', '-')}"
            )
            st.write(
                f"**{translate_text('Payment Method', admin_lang)}:**"
                f" {translate_text(o.get('payment_method', '-'), admin_lang)}"
            )
            st.write(
                f"**{translate_text('Phone', admin_lang)}:** {o.get('phone', '-')}"
            )
            if "table" in o:
              st.write(
                  f"**{translate_text('Table Number', admin_lang)}:**"
                  f" {o.get('table')}"
              )
            if "address" in o:
              st.write(
                  f"**{translate_text('Delivery Address', admin_lang)}:**"
                  f" {o.get('address')}"
              )

            st.write(f"**{translate_text('Items', admin_lang)}:**")
            for item_name, qty in o.get("items", {}).items():
              st.write(f"- {item_name} × {qty}")

            st.markdown("---")
            st.write(
                f"**{translate_text('Update Order Status', admin_lang)}:**"
            )
            new_status = st.selectbox(
                translate_text("Select Status", admin_lang),
                options=ORDER_STAGES,
                index=ORDER_STAGES.index(current_status)
                if current_status in ORDER_STAGES
                else 0,
                key=f"status_select_{order_id}",
            )
            if st.button(
                translate_text("Save Status", admin_lang),
                key=f"save_status_{order_id}",
            ):
              for real_order in orders:
                if real_order.get("order_id") == order_id:
                  real_order["status"] = new_status
                  break
              save_data(ORDERS_FILE, orders)
              st.success(
                  translate_text("Status updated successfully!", admin_lang)
              )
              st.rerun()

            if st.button(
                f"🖨️ {translate_text('Print Kitchen Receipt', admin_lang)}",
                key=f"print_{order_id}",
            ):
              items_html = "".join([
                  f"<li>{k} x {v}</li>" for k, v in o.get("items", {}).items()
              ])
              receipt_code = f"""
                            <div class="print-receipt">
                                <h3>🧾 KITCHEN RECEIPT - {order_id}</h3>
                                <p><strong>Customer:</strong> {o.get('customer')}</p>
                                <p><strong>Phone:</strong> {o.get('phone')}</p>
                                <p><strong>Type:</strong> {o.get('order_type')} | <strong>Payment:</strong> {o.get('payment_method')}</p>
                                <hr>
                                <ul>{items_html}</ul>
                                <hr>
                                <h4>TOTAL: {o.get('total')} AED</h4>
                            </div>
                            """
              st.markdown(receipt_code, unsafe_allow_html=True)
      else:
        st.info(translate_text("No orders yet", admin_lang))

    with tab2:
      st.header(tab_a2_text)
      reservations = load_data(RESERVATIONS_FILE)
      if reservations:
        for r in reversed(reservations):
          st.write(
              f"📌 **{r.get('name')}** -"
              f" {translate_text('Table Number', admin_lang)}:"
              f" {r.get('table_number')} |"
              f" {translate_text('Phone', admin_lang)}: {r.get('phone')} |"
              f" {translate_text('Date', admin_lang)}: {r.get('date')} |"
              f" {translate_text('Time', admin_lang)}: {r.get('time')}"
          )
      else:
        st.info(translate_text("No reservations yet", admin_lang))

    with tab3:
      st.header(tab_a3_text)
      st.subheader(
          translate_text("Add New Menu Item (English Source)", admin_lang)
      )

      col_name, col_price, col_cost = st.columns([3, 1, 1])
      with col_name:
        new_name_input = st.text_input(
            translate_text("Item Name (English)", admin_lang)
        )
      with col_price:
        new_price_input = st.number_input(
            f"{translate_text('Price', admin_lang)} ({translate_text('AED', admin_lang)})",
            min_value=1.0,
            value=20.0,
        )
      with col_cost:
        new_cost_input = st.number_input(
            f"{translate_text('Cost Price', admin_lang)} ({translate_text('AED', admin_lang)})",
            min_value=0.0,
            value=8.0,
        )

      st.write(f"**{translate_text('Inventory Settings', admin_lang)}:**")
      track_stock_opt = st.checkbox(
          translate_text(
              "Enable inventory tracking for this item?", admin_lang
          )
      )

      stock_qty_input = 0
      if track_stock_opt:
        stock_qty_input = st.number_input(
            translate_text("Available Stock Quantity", admin_lang),
            min_value=0,
            value=10,
        )

      img_option = st.radio(
          translate_text("Image Source", admin_lang),
          options=[
              translate_text("Image URL (Google/Web)", admin_lang),
              translate_text("Upload from Device", admin_lang),
          ],
          horizontal=True,
      )

      final_image_data = ""
      if "URL" in img_option or "رابط" in img_option or "Google" in img_option:
        final_image_data = st.text_input(
            translate_text("Image URL", admin_lang)
        )
      else:
        uploaded_file = st.file_uploader(
            translate_text("Choose image file", admin_lang),
            type=["png", "jpg", "jpeg", "webp"],
        )
        if uploaded_file is not None:
          bytes_data = uploaded_file.getvalue()
          base64_str = base64.b64encode(bytes_data).decode()
          mime_type = uploaded_file.type
          final_image_data = f"data:{mime_type};base64,{base64_str}"

      if st.button(translate_text("Add Item", admin_lang)):
        if new_name_input:
          add_menu_item(
              new_name_input,
              new_price_input,
              new_cost_input,
              track_stock_opt,
              stock_qty_input,
              final_image_data,
          )
          st.success(translate_text("Item added successfully!", admin_lang))
          st.rerun()
        else:
          st.warning(translate_text("Please enter item name", admin_lang))

      st.markdown("---")
      st.subheader(translate_text("Current Menu & Inventory", admin_lang))
      current_menu = get_menu()

      for item in current_menu:
        c1, c2, c3 = st.columns([3, 1, 1])
        disp_name = translate_text(item["name"], admin_lang)

        if item.get("track_stock", False):
          curr_stk = item.get("stock", 0)
          if curr_stk == 0:
            stock_str = (
                "<span style='color: #d9534f; font-weight: bold;'>🔴 Stock: 0"
                " (Out of Stock)</span>"
            )
          elif curr_stk <= 5:
            stock_str = (
                f"<span style='color: #d9534f; font-weight: bold;'>⚠️ Stock:"
                f" {curr_stk} (Low Stock Warning!)</span>"
            )
          else:
            stock_str = f"📦 Stock: {curr_stk}"
        else:
          stock_str = "♾️ Unlimited Stock"

        cost_status = (
            f"Cost: {item.get('cost', 0.0)} {translate_text('AED', admin_lang)}"
        )

        with c1:
          line_html = f"• <strong>{disp_name}</strong> - Price: {item['price']} {translate_text('AED', admin_lang)} | {cost_status} | {stock_str}"
          st.markdown(line_html, unsafe_allow_html=True)

        with c2:
          if st.button(
              translate_text("Edit", admin_lang), key=f"edit_btn_{item['id']}"
          ):
            st.session_state.editing_item_id = (
                None
                if st.session_state.editing_item_id == item["id"]
                else item["id"]
            )
            st.rerun()

        with c3:
          if st.button(
              translate_text("Delete", admin_lang), key=f"del_{item['id']}"
          ):
            delete_menu_item(item["id"])
            st.success(translate_text("Deleted successfully", admin_lang))
            st.rerun()

        if st.session_state.editing_item_id == item["id"]:
          with st.container():
            st.markdown(
                f"##### ✏️ {translate_text('Edit Item', admin_lang)}:"
                f" {disp_name}"
            )
            ec1, ec2, ec3 = st.columns([3, 1, 1])

            with ec1:
              e_name = st.text_input(
                  translate_text("Item Name", admin_lang),
                  value=item["name"],
                  key=f"e_name_{item['id']}",
              )
            with ec2:
              e_price = st.number_input(
                  translate_text("Price", admin_lang),
                  value=float(item["price"]),
                  key=f"e_price_{item['id']}",
              )
            with ec3:
              e_cost = st.number_input(
                  translate_text("Cost Price", admin_lang),
                  value=float(item.get("cost", 0.0)),
                  key=f"e_cost_{item['id']}",
              )

            e_track = st.checkbox(
                translate_text(
                    "Enable inventory tracking for this item?", admin_lang
                ),
                value=item.get("track_stock", False),
                key=f"e_track_{item['id']}",
            )

            e_stock = item.get("stock", 0)
            if e_track:
              e_stock = st.number_input(
                  translate_text("Available Stock Quantity", admin_lang),
                  min_value=0,
                  value=int(item.get("stock", 0)),
                  key=f"e_stock_{item['id']}",
              )

            e_img = st.text_input(
                translate_text("Image URL", admin_lang),
                value=item.get("image", ""),
                key=f"e_img_{item['id']}",
            )

            col_save, col_cancel = st.columns([1, 1])
            with col_save:
              if st.button(
                  translate_text("Save Changes", admin_lang),
                  key=f"save_edit_{item['id']}",
                  type="primary",
              ):
                update_menu_item(
                    item["id"], e_name, e_price, e_cost, e_track, e_stock, e_img
                )
                st.session_state.editing_item_id = None
                st.success(
                    translate_text("Item updated successfully!", admin_lang)
                )
                st.rerun()

            with col_cancel:
              if st.button(
                  translate_text("Cancel", admin_lang),
                  key=f"cancel_edit_{item['id']}",
              ):
                st.session_state.editing_item_id = None
                st.rerun()
            st.markdown("---")

    # ==========================================
    # 4. التقرير المالي المتقدم
    # ==========================================
    with tab4:
      st.header(tab_a4_text)
      st.subheader(translate_text("Select Date Range", admin_lang))

      col_d1, col_d2 = st.columns(2)
      today = datetime.date.today()
      start_of_month = today.replace(day=1)

      with col_d1:
        start_date = st.date_input(
            translate_text("From Date", admin_lang), value=start_of_month
        )
      with col_d2:
        end_date = st.date_input(
            translate_text("To Date", admin_lang), value=today
        )

      st.markdown("---")

      orders = load_data(ORDERS_FILE)
      menu_items = get_menu()

      price_cost_map = {}
      for item in menu_items:
        orig_name = item["name"]
        trans_name = translate_text(item["name"], admin_lang)
        p = float(item.get("price", 0.0))
        c = float(item.get("cost", 0.0))

        price_cost_map[orig_name] = {"price": p, "cost": c}
        price_cost_map[trans_name] = {"price": p, "cost": c}

      filtered_orders = []
      for o in orders:
        order_date_str = o.get("date", str(today))
        try:
          o_date = datetime.datetime.strptime(
              order_date_str, "%Y-%m-%d"
          ).date()
        except Exception:
          o_date = today

        if start_date <= o_date <= end_date:
          filtered_orders.append(o)

      total_revenue = 0.0
      total_cost = 0.0
      item_stats = {}

      for o in filtered_orders:
        for item_name, qty in o.get("items", {}).items():
          unit_info = price_cost_map.get(
              item_name, {"price": 0.0, "cost": 0.0}
          )
          u_price = unit_info["price"]
          u_cost = unit_info["cost"]

          sales = u_price * qty
          costs = u_cost * qty
          profit = sales - costs

          total_revenue += sales
          total_cost += costs

          if item_name not in item_stats:
            item_stats[item_name] = {
                "qty": 0,
                "sales": 0.0,
                "costs": 0.0,
                "profit": 0.0,
            }

          item_stats[item_name]["qty"] += qty
          item_stats[item_name]["sales"] += sales
          item_stats[item_name]["costs"] += costs
          item_stats[item_name]["profit"] += profit

      net_profit = total_revenue - total_cost

      m1, m2, m3 = st.columns(3)
      with m1:
        st.metric(
            translate_text("Total Revenue (Period)", admin_lang),
            f"{total_revenue:.2f} AED",
        )
      with m2:
        st.metric(
            translate_text("Total Costs (Period)", admin_lang),
            f"{total_cost:.2f} AED",
        )
      with m3:
        st.metric(
            translate_text("Net Profit (Period)", admin_lang),
            f"{net_profit:.2f} AED",
        )

      st.markdown("---")
      st.subheader(translate_text("Item-wise Profitability", admin_lang))

      if item_stats:
        table_data = []
        for name, data in item_stats.items():
          table_data.append({
              translate_text("Item Name", admin_lang): name,
              translate_text("Qty Sold", admin_lang): data["qty"],
              translate_text("Total Sales (AED)", admin_lang): f"{data['sales']:.2f}",
              translate_text("Total Cost (AED)", admin_lang): f"{data['costs']:.2f}",
              translate_text("Net Profit (AED)", admin_lang): f"{data['profit']:.2f}",
          })

        df_items = pd.DataFrame(table_data)
        st.dataframe(df_items, use_container_width=True)
      else:
        st.info(
            translate_text(
                "No sales registered in the selected date range.", admin_lang
            )
        )

  else:
    st.sidebar.error(translate_text("Wrong password", admin_lang))


# ==========================================
# 5. صفحات الأقسام والخدمات
# ==========================================
elif st.session_state.current_page in [
    "food_menu_page",
    "delivery_page",
    "reservation_page",
    "cart_page",
    "track_orders_page",
    "contact_page",
]:
  lang = st.session_state.app_language

  if st.sidebar.button("Back to Main / العودة للرئيسية"):
    st.session_state.current_page = "main_menu"
    update_url_params()
    st.rerun()

  # 1. صفحة قائمة الطعام للزبون مع فحص دقيق يتجاوز المخزون
  if st.session_state.current_page == "food_menu_page":
    st.title(f"📜 {translate_text('Food Menu', lang)}")
    menu_items = get_menu()
    add_btn_text = translate_text("Add to Cart", lang)
    currency_text = translate_text("AED", lang)
    qty_text = translate_text("Qty", lang)

    for item in menu_items:
      display_name = translate_text(item["name"], lang)
      c_img, c1, c2, c3 = st.columns([1.5, 3, 2, 2])

      already_in_cart = st.session_state.cart.get(display_name, 0)
      track_stock = item.get("track_stock", False)
      total_stock = item.get("stock", 0) if track_stock else 999
      available_stock = (
          max(0, total_stock - already_in_cart) if track_stock else 999
      )

      is_out_of_stock = track_stock and available_stock <= 0

      with c_img:
        img_url = item.get(
            "image",
            "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=300",
        )
        st.image(img_url, use_container_width=True)

      with c1:
        st.subheader(display_name)
        st.write(f"{item['price']} {currency_text}")

        if track_stock and total_stock <= 0:
          st.error(f"🔴 {translate_text('Out of Stock', lang)}")

      with c2:
        # إدخال حر بدون max_value صلب لمنع قفز القيمة تلقائياً
        qty = st.number_input(
            qty_text,
            min_value=1,
            value=1,
            step=1,
            key=f"qty_{item['id']}",
            disabled=is_out_of_stock,
            label_visibility="collapsed",
        )

        # فحص مباشر: هل القيمة المطلوبة + الموجودة بالسلة تتجاوز المخزون؟
        exceeds_stock = track_stock and ((already_in_cart + int(qty)) > total_stock)

        if exceeds_stock:
          st.error(
              f"⚠️ {translate_text('Exceeds stock! Max available:', lang)}"
              f" {available_stock}"
          )

      with c3:
        # تعطيل الزر فوراً عند إدخال قيمة تتجاوز المخزون
        btn_disabled = is_out_of_stock or exceeds_stock

        if st.button(
            add_btn_text, key=f"btn_{item['id']}", disabled=btn_disabled
        ):
          st.session_state.cart[display_name] = already_in_cart + int(qty)
          update_url_params()
          st.success(
              f"{translate_text('Added', lang)} {display_name}"
              f" {translate_text('successfully', lang)}"
          )
          st.rerun()
      st.markdown("---")

  # 2. صفحة سلة المشتريات
  elif st.session_state.current_page == "cart_page":
    st.title(f"🛒 {translate_text('Shopping Cart', lang)}")
    currency_text = translate_text("AED", lang)

    if not st.session_state.cart:
      st.info(translate_text("Your cart is empty", lang))
    else:
      total_price = 0.0
      menu_items = get_menu()

      item_info_map = {}
      for item in menu_items:
        disp = translate_text(item["name"], lang)
        item_info_map[disp] = item
        item_info_map[item["name"]] = item

      items_to_remove = []

      if st.button(
          f"🗑️ {translate_text('Clear Cart', lang)}", type="secondary"
      ):
        st.session_state.cart = {}
        update_url_params()
        st.rerun()

      st.markdown("---")

      for item_name, quantity in list(st.session_state.cart.items()):
        item_obj = item_info_map.get(
            item_name, {"price": 0.0, "track_stock": False, "stock": 999}
        )
        price = item_obj.get("price", 0.0)
        track_stock = item_obj.get("track_stock", False)
        total_stock = item_obj.get("stock", 999) if track_stock else 999

        item_total = price * quantity
        total_price += item_total

        c_info, c_qty, c_del = st.columns([3, 2, 1])

        with c_info:
          st.markdown(f"### **{item_name}**")
          st.write(
              f"{translate_text('Price', lang)}: {price:.1f} {currency_text} |"
              f" {translate_text('Total', lang)}: **{item_total:.1f}"
              f" {currency_text}**"
          )

        with c_qty:
          new_qty = st.number_input(
              f"{translate_text('Qty', lang)} ({item_name})",
              min_value=1,
              value=int(quantity),
              step=1,
              key=f"cart_qty_{item_name}",
          )

          exceeds_cart_stock = track_stock and (int(new_qty) > total_stock)
          if exceeds_cart_stock:
            st.error(
                f"⚠️ {translate_text('Max stock available:', lang)}"
                f" {total_stock}"
            )
          elif new_qty != quantity:
            st.session_state.cart[item_name] = int(new_qty)
            update_url_params()
            st.rerun()

        with c_del:
          st.write("<br>", unsafe_allow_html=True)
          if st.button("🗑️", key=f"del_cart_{item_name}"):
            items_to_remove.append(item_name)

        st.markdown("---")

      if items_to_remove:
        for itm in items_to_remove:
          del st.session_state.cart[itm]
        update_url_params()
        st.rerun()

      st.subheader(
          f"{translate_text('Total', lang)}: {total_price:.1f} {currency_text}"
      )
      st.write("---")

      st.subheader(
          translate_text("Would you like to dine-in or delivery?", lang)
      )

      col_dine, col_del = st.columns(2)
      with col_dine:
        if st.button(
            f"🍽️ {translate_text('Dine-in (Eat in Restaurant)', lang)}",
            use_container_width=True,
            type="primary",
        ):
          st.session_state.current_page = "reservation_page"
          update_url_params()
          st.rerun()

      with col_del:
        if st.button(
            f"🛵 {translate_text('Delivery Order', lang)}",
            use_container_width=True,
            type="primary",
        ):
          st.session_state.current_page = "delivery_page"
          update_url_params()
          st.rerun()

  # 3. صفحة حجز الطاولة
  elif st.session_state.current_page == "reservation_page":
    st.title(f"🍽️ {translate_text('Dine-in / Table Reservation', lang)}")

    res_name = st.text_input(translate_text("Your Name", lang))
    res_phone = st.text_input(translate_text("Phone Number", lang))

    available_tables = get_available_tables()
    if available_tables:
      selected_table = st.selectbox(
          translate_text("Available Tables", lang), options=available_tables
      )
    else:
      st.warning(translate_text("No tables available at the moment", lang))
      selected_table = None

    res_date = st.date_input(translate_text("Reservation Date", lang))
    res_time = st.time_input(translate_text("Arrival Time", lang))

    selected_payment = st.radio(
        translate_text("Payment Method", lang),
        options=[translate_text(p, lang) for p in PAYMENT_METHODS],
    )

    if st.button(
        translate_text("Confirm Dine-in Reservation", lang), type="primary"
    ):
      if res_name and res_phone and selected_table:
        reservations = load_data(RESERVATIONS_FILE)
        reservations.append({
            "name": res_name,
            "phone": res_phone,
            "table_number": selected_table,
            "date": str(res_date),
            "time": str(res_time),
        })
        save_data(RESERVATIONS_FILE, reservations)

        if st.session_state.cart:
          orders = load_data(ORDERS_FILE)
          price_dict = {
              translate_text(item["name"], lang): item["price"]
              for item in get_menu()
          }
          total_price = sum(
              price_dict.get(k, 0) * v for k, v in st.session_state.cart.items()
          )
          order_id = f"ORD-{random.randint(1000, 9999)}"

          orders.append({
              "order_id": order_id,
              "customer": res_name,
              "phone": res_phone,
              "table": selected_table,
              "order_type": "Dine-in",
              "payment_method": selected_payment,
              "items": st.session_state.cart,
              "total": total_price,
              "date": str(datetime.date.today()),
              "status": "Order Received",
          })
          save_data(ORDERS_FILE, orders)

          deduct_stock_for_order(st.session_state.cart)

          st.session_state.cart = {}
          st.session_state.last_order_id = order_id

        st.success(
            translate_text("Reservation & Order submitted successfully!", lang)
        )
        st.session_state.current_page = "track_orders_page"
        update_url_params()
        st.rerun()
      else:
        st.warning(
            translate_text("Please fill in your name, phone and table", lang)
        )

  # 4. صفحة الدليفري
  elif st.session_state.current_page == "delivery_page":
    st.title(f"🛵 {translate_text('Delivery Details', lang)}")

    del_name = st.text_input(translate_text("Your Name", lang))
    del_address = st.text_area(
        translate_text("Delivery Location/Address", lang)
    )
    del_phone = st.text_input(translate_text("Phone Number", lang))

    selected_payment = st.radio(
        translate_text("Payment Method", lang),
        options=[translate_text(p, lang) for p in PAYMENT_METHODS],
    )

    if st.button(
        translate_text("Confirm Delivery Order", lang), type="primary"
    ):
      if del_name and del_address and del_phone:
        orders = load_data(ORDERS_FILE)
        price_dict = {
            translate_text(item["name"], lang): item["price"]
            for item in get_menu()
        }
        total_price = sum(
            price_dict.get(k, 0) * v for k, v in st.session_state.cart.items()
        )
        order_id = f"ORD-{random.randint(1000, 9999)}"

        orders.append({
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
        })
        save_data(ORDERS_FILE, orders)

        deduct_stock_for_order(st.session_state.cart)

        st.session_state.cart = {}
        st.session_state.last_order_id = order_id

        st.success(
            translate_text("Delivery order submitted successfully!", lang)
        )
        st.session_state.current_page = "track_orders_page"
        update_url_params()
        st.rerun()
      else:
        st.warning(translate_text("Please fill in all details", lang))

  # 5. صفحة تتبع الطلبيات
  elif st.session_state.current_page == "track_orders_page":
    st.title(f"📍 {translate_text('Track Orders', lang)}")

    orders = load_data(ORDERS_FILE)
    if not orders:
      st.info(translate_text("No active orders to track currently.", lang))
    else:
      last_id = st.session_state.last_order_id
      current_order = None
      if last_id:
        for o in orders:
          if o.get("order_id") == last_id:
            current_order = o
            break

      if not current_order:
        current_order = orders[-1]

      status = current_order.get("status", "Order Received")

      st.subheader(
          f"{translate_text('Order Number', lang)}: {current_order.get('order_id')}"
      )
      st.write(
          f"**{translate_text('Customer', lang)}:**"
          f" {current_order.get('customer')} |"
          f" **{translate_text('Payment Method', lang)}:**"
          f" {current_order.get('payment_method', '-')} |"
          f" **{translate_text('Total', lang)}:** {current_order.get('total')}"
          f" {translate_text('AED', lang)}"
      )

      stage_index = (
          ORDER_STAGES.index(status) if status in ORDER_STAGES else 0
      )
      progress_value = (stage_index + 1) / len(ORDER_STAGES)
      st.progress(progress_value)

      cols = st.columns(4)
      stage_icons = ["📥", "🍳", "🛵", "✅"]

      for idx, stage_name in enumerate(ORDER_STAGES):
        with cols[idx]:
          translated_stage = translate_text(stage_name, lang)
          if idx <= stage_index:
            st.success(f"{stage_icons[idx]} **{translated_stage}**")
          else:
            st.info(f"⚪ {translated_stage}")

      st.markdown("---")
      st.subheader(translate_text("Order Details", lang))
      for item_name, qty in current_order.get("items", {}).items():
        st.write(f"- {item_name} × {qty}")

      time.sleep(5)
      st.rerun()

  # 6. صفحة تواصل معنا
  elif st.session_state.current_page == "contact_page":
    st.title(f"📞 {translate_text('Contact Us', lang)}")
    st.write(f"**{translate_text('Phone', lang)}:** +971 50 123 4567")
    st.write(f"**{translate_text('Address', lang)}:** Main Street, City")
