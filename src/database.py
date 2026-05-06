import json
import os
from typing import List, Dict, Any, Optional

# หา Path ของโฟลเดอร์ Root ของโปรเจกต์
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "menus.json")


class MenuRepository:
    """
    Repository สำหรับจัดการข้อมูลเมนูอาหาร
    Abstracts data access from JSON to be easily swappable with DB (SQLite/PostgreSQL) later.
    """

    def __init__(self, data_path: str = DATA_PATH):
        self.data_path = data_path
        self._menus = None

    def _load_data(self) -> List[Dict[str, Any]]:
        if self._menus is None:
            if not os.path.exists(self.data_path):
                raise FileNotFoundError(f"ไม่พบไฟล์ข้อมูลที่: {self.data_path}")
            
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._menus = data.get("menus", [])
        return self._menus

    def get_all(self) -> List[Dict[str, Any]]:
        """ดึงข้อมูลเมนูทั้งหมด"""
        return self._load_data()

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """ดึงเมนูด้วยชื่อเจาะจง"""
        for menu in self._load_data():
            if menu["name"] == name:
                return menu
        return None

    def get_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """ดึงเมนูตามแท็ก"""
        return [menu for menu in self._load_data() if tag in menu.get("tags", [])]

    def filter_menus(
        self,
        ingredient: Optional[str] = None,
        max_price: Optional[int] = None,
        category: Optional[str] = None,
        max_calories: Optional[int] = None,
        exclude_allergen: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        กรองเมนูตามเงื่อนไขที่ซับซ้อน
        """
        results = []
        for menu in self._load_data():
            # เช็ควัตถุดิบ (หา substring ใน ingredients)
            if ingredient and ingredient not in "".join(menu.get("ingredients", [])):
                continue

            # เช็คราคา
            if max_price and menu.get("price", float('inf')) > max_price:
                continue

            # เช็คประเภท
            if category and menu.get("category") != category:
                continue

            # เช็คแคลอรี่
            if max_calories and menu.get("calories", float('inf')) > max_calories:
                continue

            # เช็คสารก่อภูมิแพ้
            if exclude_allergen:
                allergens = menu.get("allergens", [])
                if any(exclude_allergen in allergen for allergen in allergens):
                    continue

            results.append(menu)

        return results

# Singleton instance
menu_repository = MenuRepository()

