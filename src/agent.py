import os
import json
from dotenv import load_dotenv
from google import genai

# Relative imports
try:
    from .retrieval import search_menu
    from .tools import filter_menu, get_dish_detail, get_menu_by_tag
except ImportError:
    from retrieval import search_menu
    from tools import filter_menu, get_dish_detail, get_menu_by_tag

# Load API Key
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ===============================
# Agent Tool Registry
# ===============================
tools_dict = {
    "search_menu": search_menu,
    "filter_menu": filter_menu,
    "get_dish_detail": get_dish_detail,
    "get_menu_by_tag": get_menu_by_tag
}

def generate_answer(query, context):
    """
    สร้างคำตอบแบบเป็นธรรมชาติจาก Context ที่ได้ (Wow ⭐)
    """
    prompt = (
        f"คุณคือ 'น้องหิวข้าว' AI Agent ผู้เชี่ยวชาญด้านอาหารตามสั่ง\n"
        f"คำถามจากผู้ใช้: {query}\n"
        f"ข้อมูลที่ค้นหามาได้: {context}\n"
        f"คำแนะนำ:\n"
        f"- ให้ตอบอย่างสุภาพและเป็นกันเอง (ใช้ครับ/ค่ะ)\n"
        f"- ถ้าไม่มีข้อมูล ให้บอกอย่างตรงไปตรงมาและแนะนำเมนูอื่นแทน\n"
        f"- ใส่ Emoji ที่เกี่ยวกับอาหารประกอบคำตอบ\n"
        f"- สรุปข้อมูลที่สำคัญ เช่น ราคา หรือแคลอรี่ ให้ชัดเจน"
    )
    
    try:
        resp = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt
        )
        return resp.text.strip()
    except Exception as e:
        return f"ขออภัยค่ะ เกิดข้อผิดพลาดในการสร้างคำตอบ: {e}"

def foodie_agent(user_query):
    """
    Main ReAct Loop (Simplified)
    """
    print(f"\n[User]: {user_query}")
    
    # Step 1: Brain (Reasoning) - LLM Router
    router_prompt = (
        f"คุณคือ Foodie Router หน้าที่ของคุณคือวิเคราะห์คำถามของผู้ใช้ "
        f"และตัดสินใจว่าต้องใช้เครื่องมืออะไรจากรายการต่อไปนี้:\n"
        f"1. search_menu(query): ใช้เมื่อคำถามกว้างๆ หรือต้องการค้นหาเมนูที่ใกล้เคียง\n"
        f"2. filter_menu(ingredient, max_price, category, max_calories, exclude_allergen): ใช้เมื่อมีเงื่อนไขชัดเจน\n"
        f"3. get_dish_detail(dish_name): ใช้เมื่อระบุชื่อเมนูชัดเจน\n"
        f"4. get_menu_by_tag(tag): ใช้เมื่อระบุแท็ก เช่น สุขภาพ, ยอดนิยม\n\n"
        f"คำถาม: '{user_query}'\n"
        f"ตอบในรูปแบบ JSON เท่านั้น: {{\"thought\": \"เหตุผล\", \"tool\": \"ชื่อ tool\", \"params\": {{...}}}}"
    )

    try:
        router_resp = client.models.generate_content(
            model="gemini-flash-latest",
            contents=router_prompt,
            config={'response_mime_type': 'application/json'}
        )
        plan = json.loads(router_resp.text)
        print(f"🤔 [Thought]: {plan['thought']}")
    except Exception as e:
        print(f"⚠️ Router Error: {e}. Falling back to search_menu.")
        plan = {"tool": "search_menu", "params": {"query": user_query}}

    # Step 2: Action
    tool_name = plan.get("tool")
    params = plan.get("params", {})
    
    if tool_name in tools_dict:
        print(f"🛠️ [Action]: Call {tool_name} with {params}")
        observation = tools_dict[tool_name](**params)
    else:
        observation = "ไม่พบเครื่องมือที่เหมาะสม"

    # Step 3: Observation & Final Answer (Generation)
    print(f"👁️ [Observation]: พบข้อมูล {len(observation) if isinstance(observation, list) else '1'} รายการ")
    
    final_answer = generate_answer(user_query, observation)
    return final_answer

if __name__ == "__main__":
    while True:
        query = input("\nหิวหรือยังคะ? ถามมาได้เลย (หรือพิมพ์ 'exit' เพื่อออก): ")
        if query.lower() == 'exit':
            break
        
        answer = foodie_agent(query)
        print(f"\n[Agent]: {answer}")
