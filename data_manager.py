import json
import os

ORDERS_FILE = "orders.json"
RESERVATIONS_FILE = "reservations.json"

# قائمة الطعام الأساسية
MENU = [
    {"id": 1, "name": "شاورما دجاج مع ثومية", "price": 18.0},
    {"id": 2, "name": "برجر لحم مشوي", "price": 28.0},
    {"id": 3, "name": "عصير برتقال طازج", "price": 12.0},
]


def get_menu():
  return MENU


def load_data(file_path):
  if not os.path.exists(file_path):
    return []
  try:
    with open(file_path, "r", encoding="utf-8") as f:
      return json.load(f)
  except Exception:
    return []


def save_data(file_path, new_data):
  data = load_data(file_path)
  data.append(new_data)
  with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


# الدوال التي يستدعيها app.py
def add_order(order_data):
  save_data(ORDERS_FILE, order_data)


def get_orders():
  return load_data(ORDERS_FILE)


def add_reservation(res_data):
  save_data(RESERVATIONS_FILE, res_data)


def get_reservations():
  return load_data(RESERVATIONS_FILE)
