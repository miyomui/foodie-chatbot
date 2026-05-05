from retrieval import search_menu
from tools import filter_menu, get_dish_detail, format_menu_list, format_dish_detail


# ===============================
# Tool Registry
# ===============================
tools = {
    "search_menu": search_menu,
    "filter_menu": filter_menu,
    "get_dish_detail": get_dish_detail
}


# ===============================
# Extract functions
# ===============================
def extract_price(user_input):
    words = user_input.replace("บาท", "").split()

    for word in words:
        if word.isdigit():
            return int(word)

    return None


def extract_ingredient(user_input):
    ingredients = ["หมู", "ไก่", "กุ้ง", "ปู", "ปลา", "ไข่"]

    for ing in ingredients:
        if ing in user_input:
            return ing

    return None


def extract_category(user_input):
    categories = ["ข้าวผัด", "ผัด", "ต้ม", "ทอด", "แกง"]

    for cat in categories:
        if cat in user_input:
            return cat

    return None


def extract_dish_name(user_input):
    remove_words = ["ขอรายละเอียด", "รายละเอียด", "อยากรู้", "เมนู"]

    name = user_input
    for w in remove_words:
        name = name.replace(w, "")

    return name.strip()


# ===============================
# Emoji mapping (BONUS 🔥)
# ===============================
def get_emoji(ingredient, category):
    if ingredient == "กุ้ง":
        return "🦐"
    elif ingredient == "หมู":
        return "🐷"
    elif ingredient == "ไก่":
        return "🐔"
    elif ingredient == "ปลา":
        return "🐟"
    elif ingredient == "ปู":
        return "🦀"
    elif category == "ทอด":
        return "🍗"
    elif category == "ต้ม":
        return "🍲"
    elif category == "ผัด":
        return "🥘"
    elif category == "แกง":
        return "🍛"
    elif category == "ข้าวผัด":
        return "🍚"
    else:
        return "🍽️"


# ===============================
# Agent (ReAct)
# ===============================
def agent(user_input):
    print("\n======================")
    print("User Question:", user_input)
    print("ทวนคำถาม:", f"ผู้ใช้ถามว่า '{user_input}'")

    # Thought
    if "รายละเอียด" in user_input:
        thought = "ผู้ใช้ต้องการรายละเอียดเมนู"
        action = "get_dish_detail"

    elif "ไม่เกิน" in user_input or "ราคา" in user_input:
        thought = "ผู้ใช้ต้องการกรองเมนู"
        action = "filter_menu"

    elif extract_ingredient(user_input) or extract_category(user_input):
        thought = "ผู้ใช้พูดถึงวัตถุดิบหรือประเภท"
        action = "filter_menu"

    else:
        thought = "ค้นหาเมนูทั่วไป"
        action = "search_menu"

    print("Thought:", thought)
    print("Action:", action)

    # ===============================
    # Action
    # ===============================
    if action == "get_dish_detail":
        name = extract_dish_name(user_input)
        result = tools[action](name)

        print("Observation:", result)

        if not result:
            answer = "ไม่พบเมนูนี้ ลองพิมพ์ชื่อให้ชัดขึ้น เช่น ข้าวผัดกุ้ง"
        else:
            answer = format_dish_detail(result)

    elif action == "filter_menu":
        ingredient = extract_ingredient(user_input)
        max_price = extract_price(user_input)
        category = extract_category(user_input)

        result = tools[action](
            ingredient=ingredient,
            max_price=max_price,
            category=category
        )

        print("Observation:", result)

        if not result:
            answer = (
                "ไม่พบเมนูที่ตรงเงื่อนไขครับ\n"
                "ลองเช่น:\n"
                "- เมนูกุ้ง\n"
                "- เมนูทอด\n"
                "- เมนูไม่เกิน 60 บาท"
            )
        else:
            emoji = get_emoji(ingredient, category)

            # 🔥 Title
            if ingredient:
                title = f"เมนูที่มี '{ingredient}' {emoji}\n\n"
            elif max_price:
                title = f"เมนูราคาไม่เกิน {max_price} บาท 💸\n\n"
            elif category:
                title = f"เมนูประเภท '{category}' {emoji}\n\n"
            else:
                title = "รายการเมนู:\n\n"

            answer = title + format_menu_list(result)

    else:
        result = tools[action](user_input)

        print("Observation:", result)

        if not result:
            answer = "ไม่พบเมนู ลองถามเช่น เมนูกุ้ง หรือ เมนูเผ็ด"
        else:
            answer = "เมนูที่แนะนำ:\n\n"

            for i, item in enumerate(result, 1):
                m = item["metadata"]
                answer += f"{i}. {m['name']} - {m['price']} บาท\n"

    print("Answer:", answer)
    print("======================\n")

    return answer


# ===============================
# Run
# ===============================
if __name__ == "__main__":
    while True:
        q = input("ถาม (พิมพ์ exit เพื่อออก): ")

        # 🔥 กันพิมพ์ผิด
        if q.lower().strip() == "exit":
            print("จบการทำงาน 👋")
            break

        print(agent(q))