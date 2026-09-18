import json
import os

ORDERS_FILE = "orders.json"
RESERVATIONS_FILE = "reservations.json"


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


def save_order(order_data):
  save_data(ORDERS_FILE, order_data)


def save_reservation(res_data):
  save_data(RESERVATIONS_FILE, res_data)
