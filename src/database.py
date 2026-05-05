import json
import os

# หา Path ของโฟลเดอร์ Root ของโปรเจกต์
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "menus.json")

def load_menus():
    """
    โหลดข้อมูลเมนูทั้งหมดจาก data/menus.json
    """
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["menus"]
