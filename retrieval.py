import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import errors


# ===============================
# Load Gemini API Key
# ===============================
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# ===============================
# Load Menu Data
# ===============================
def load_menus():
    with open("data/menus.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    return data["menus"]


# ===============================
# Check whether query is food-related
# ===============================
def is_food_related(query):
    food_keywords = [
        "เมนู", "อาหาร", "กิน", "หิว", "อยากกิน", "แนะนำ",
        "หมู", "ไก่", "กุ้ง", "ปู", "ปลา", "ไข่",
        "ข้าว", "เส้น", "ผัด", "ต้ม", "ทอด", "แกง",
        "เผ็ด", "ไม่เผ็ด", "หวาน", "เปรี้ยว", "กรอบ",
        "ราคา", "บาท", "แคลอรี่", "ถูก", "แพง"
    ]

    return any(keyword in query for keyword in food_keywords)


# ===============================
# Local Search Fallback
# ใช้กรณี Gemini ล่ม หรือ API error
# ===============================
def local_search_menu(query: str, n_results: int = 3):
    menus = load_menus()
    results = []

    for menu in menus:
        score = 0

        searchable_text = (
            menu["name"] + " " +
            menu["category"] + " " +
            menu["description"] + " " +
            " ".join(menu["ingredients"]) + " " +
            " ".join(menu["tags"])
        )

        if query in searchable_text:
            score += 5

        for word in query.split():
            if word in searchable_text:
                score += 1

        if score > 0:
            results.append((score, menu))

    results.sort(reverse=True, key=lambda x: x[0])

    return [
        {
            "text": menu["description"],
            "metadata": menu
        }
        for score, menu in results[:n_results]
    ]


# ===============================
# Gemini Search Tool
# ===============================
def search_menu(query: str, n_results: int = 3):
    menus = load_menus()

    # ถ้าคำถามไม่เกี่ยวกับอาหาร ให้หยุดทันที
    if not is_food_related(query):
        return []

    menu_text = ""

    for menu in menus:
        menu_text += (
            f"- {menu['name']} | "
            f"ประเภท: {menu['category']} | "
            f"ราคา: {menu['price']} บาท | "
            f"แคลอรี่: {menu['calories']} kcal | "
            f"ส่วนผสม: {', '.join(menu['ingredients'])} | "
            f"แท็ก: {', '.join(menu['tags'])}\n"
        )

    prompt = f"""
คุณคือผู้ช่วยแนะนำเมนูอาหาร

คำถามผู้ใช้:
{query}

รายการเมนูที่มีให้เลือกเท่านั้น:
{menu_text}

หน้าที่ของคุณ:
เลือกเมนูที่เหมาะสมที่สุดไม่เกิน {n_results} รายการจากรายการที่ให้เท่านั้น

กติกาสำคัญ:
- ถ้าคำถามไม่เกี่ยวกับอาหาร ให้ตอบว่า NOT_FOUND
- ถ้าไม่พบเมนูที่เกี่ยวข้องจริง ๆ ให้ตอบว่า NOT_FOUND
- ห้ามเดาคำผิด เช่น หมา เป็น หมู
- ห้ามแนะนำเมนูที่ไม่เกี่ยวกับคำถาม
- ห้ามแต่งชื่อเมนูใหม่
- ต้องตอบเฉพาะชื่อเมนูที่มีอยู่ในรายการเท่านั้น
- ตอบทีละ 1 เมนูต่อ 1 บรรทัด
- ห้ามใส่เลขลำดับ
- ห้ามอธิบายเพิ่ม
"""

    # เรียก Gemini พร้อม fallback ถ้า Gemini ล่ม
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
    except errors.ServerError:
        print("⚠️ Gemini มีคนใช้เยอะชั่วคราว → ใช้ Local Search แทน")
        return local_search_menu(query, n_results)

    except Exception as e:
        print("⚠️ Gemini error:", e)
        print("ใช้ Local Search แทน")
        return local_search_menu(query, n_results)

    ai_text = response.text.strip()

    if "NOT_FOUND" in ai_text:
        return []

    selected_names = ai_text.splitlines()

    valid_menu_names = [menu["name"] for menu in menus]
    results = []

    for name in selected_names:
        clean_name = name.strip("- ").strip()

        # Validate ว่า Gemini ตอบชื่อเมนูที่มีอยู่จริงเท่านั้น
        if clean_name not in valid_menu_names:
            continue

        for menu in menus:
            if clean_name == menu["name"]:
                results.append({
                    "text": menu["description"],
                    "metadata": menu
                })

    return results[:n_results]


# ===============================
# Test
# ===============================
if __name__ == "__main__":
    print("✅ ใช้ Gemini Search")

    test_queries = [
        "อยากกินเมนูเผ็ด",
        "ขอเมนูที่มีกุ้ง",
        "หมา",
        "รถ"
    ]

    for query in test_queries:
        print("\nคำถาม:", query)

        results = search_menu(query, n_results=3)

        if not results:
            print("ไม่พบเมนูที่ตรงกับคำถาม")
        else:
            for i, item in enumerate(results, start=1):
                menu = item["metadata"]
                print(f"{i}. {menu['name']} - {menu['price']} บาท")
                print(f"   รายละเอียด: {menu['description']}")