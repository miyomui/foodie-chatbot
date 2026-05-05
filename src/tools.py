import os
import json
from .database import load_menus

def filter_menu(ingredient=None, max_price=None, category=None, max_calories=None, exclude_allergen=None):
    """
    กรองเมนูตามเงื่อนไขต่างๆ
    """
    menus = load_menus()
    results = []

    for menu in menus:
        # เช็ควัตถุดิบ
        if ingredient and ingredient not in "".join(menu["ingredients"]):
            continue
        
        # เช็คราคา
        if max_price and menu["price"] > max_price:
            continue
            
        # เช็คประเภท
        if category and menu["category"] != category:
            continue

        # เช็คแคลอรี่ (Wow ⭐)
        if max_calories and menu["calories"] > max_calories:
            continue

        # เช็คสารก่อภูมิแพ้ (Wow ⭐⭐)
        if exclude_allergen:
            # ถ้าเมนูมีสารก่อภูมิแพ้ที่ผู้ใช้ระบุ ให้ข้าม
            if any(allergen in menu["allergens"] for allergen in [exclude_allergen] if menu["allergens"]):
                continue

        results.append(menu)

    return results

def get_dish_detail(dish_name):
    """
    ดึงข้อมูลรายละเอียดของเมนูแบบเจาะจง
    """
    menus = load_menus()
    for menu in menus:
        if menu["name"] == dish_name:
            return menu
    return None

def get_menu_by_tag(tag):
    """
    ดึงเมนูตามแท็ก (เช่น ยอดนิยม, สุขภาพ, เผ็ด, ไม่เผ็ด)
    """
    menus = load_menus()
    results = [m for m in menus if tag in m["tags"]]
    return results
