import json
import os

ORDERS_FILE = "orders.json"
RESERVATIONS_FILE = "reservations.json"
MENU_FILE = "menu.json"

# المنيو الافتراضي في حال عدم وجود ملف menu.json
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


# --- إدارة المنيو ---
def get_menu():
  return load_data(MENU_FILE, DEFAULT_MENU)


def add_menu_item(name, price):
  menu = get_menu()
  new_id = max([item["id"] for item in menu], default=0) + 1
  menu.append({"id": new_id, "name": name, "price": float(price)})
  save_data(MENU_FILE, menu)


def delete_menu_item(item_id):
  menu = get_menu()
  menu = [item for item in menu if item["id"] != item_id]
  save_data(MENU_FILE, menu)


# --- إدارة الطلبات والحجوزات ---
def add_order(order_data):
  orders = load_data(ORDERS_FILE)
  orders.append(order_data)
  save_data(ORDERS_FILE, orders)


def get_orders():
  return load_data(ORDERS_FILE)


def add_reservation(res_data):
  reservations = load_data(RESERVATIONS_FILE)
  reservations.append(res_data)
  save_data(RESERVATIONS_FILE, reservations)


def get_reservations():
  return load_data(RESERVATIONS_FILE)
