import json

def load_menus():
    """
    โหลดข้อมูลเมนูทั้งหมดจาก data/menus.json
    """
    with open("data/menus.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["menus"]
