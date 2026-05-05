import json
from database import load_menus

# ===============================
# Tool 1: filter_menu()
# ===============================
def filter_menu(ingredient=None, max_price=None, category=None):
    """
    กรองเมนูตามวัตถุดิบ ราคา และประเภทอาหาร
    """

    menus = load_menus()
    results = []

    for menu in menus:
        match = True

        # กรองตามวัตถุดิบ เช่น กุ้ง หมู ไก่ ไข่
        if ingredient:
            ingredient_found = False

            for item in menu["ingredients"]:
                if ingredient in item:
                    ingredient_found = True
                    break

            if not ingredient_found:
                match = False

        # กรองตามราคาสูงสุด เช่น ไม่เกิน 60 บาท
        if max_price is not None:
            if menu["price"] > max_price:
                match = False

        # กรองตามประเภท เช่น ผัด ต้ม ทอด แกง ข้าวผัด
        if category:
            if category not in menu["category"]:
                match = False

        if match:
            results.append(menu)

    return results


# ===============================
# Tool 2: get_dish_detail()
# ===============================
def get_dish_detail(dish_name):
    """
    ดึงรายละเอียดเมนูแบบเต็มจากชื่อเมนู
    """

    menus = load_menus()

    for menu in menus:
        if dish_name in menu["name"] or menu["name"] in dish_name:
            return menu

    return None


# ===============================
# จัดรูปแบบผลลัพธ์ให้อ่านง่าย
# ===============================


def format_menu_list(menus):
    """
    แปลง list ของเมนูให้เป็นข้อความอ่านง่าย
    """

    if not menus:
        return "ไม่พบเมนูที่ตรงกับเงื่อนไข"

    text = ""

    for i, menu in enumerate(menus, start=1):
        text += f"{i}. {menu['name']} - {menu['price']} บาท ({menu['category']})\n"
        text += f"   แคลอรี่: {menu['calories']} kcal\n"
        text += f"   รายละเอียด: {menu['description']}\n\n"

    return text


def format_dish_detail(menu):
    """
    แปลงรายละเอียดเมนูเดียวให้อ่านง่าย
    """

    if not menu:
        return "ไม่พบรายละเอียดเมนูนี้"

    text = f"ชื่อเมนู: {menu['name']}\n"
    text += f"ประเภท: {menu['category']}\n"
    text += f"ราคา: {menu['price']} บาท\n"
    text += f"แคลอรี่: {menu['calories']} kcal\n"
    text += f"ส่วนผสม: {', '.join(menu['ingredients'])}\n"
    text += f"สารก่อภูมิแพ้: {', '.join(menu['allergens']) if menu['allergens'] else 'ไม่มี'}\n"
    text += f"รายละเอียด: {menu['description']}\n"
    text += f"แท็ก: {', '.join(menu['tags'])}"

    return text