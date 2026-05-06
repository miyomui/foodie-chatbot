try:
    from .database import menu_repository
except ImportError:
    from database import menu_repository

def filter_menu(ingredient=None, max_price=None, category=None, max_calories=None, exclude_allergen=None):
    """
    กรองเมนูตามเงื่อนไขต่างๆ
    """
    return menu_repository.filter_menus(
        ingredient=ingredient,
        max_price=max_price,
        category=category,
        max_calories=max_calories,
        exclude_allergen=exclude_allergen,
    )

def get_dish_detail(dish_name):
    """
    ดึงข้อมูลรายละเอียดของเมนูแบบเจาะจง
    """
    return menu_repository.get_by_name(dish_name)

def get_menu_by_tag(tag):
    """
    ดึงเมนูตามแท็ก (เช่น ยอดนิยม, สุขภาพ, เผ็ด, ไม่เผ็ด)
    """
    return menu_repository.get_by_tag(tag)

