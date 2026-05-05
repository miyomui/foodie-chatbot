import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import errors

from retrieval import search_menu
from tools import filter_menu, get_dish_detail, format_menu_list, format_dish_detail

# Load environment variables
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ===============================
# Tool Registry
# ===============================
tools = {
    "search_menu": search_menu,
    "filter_menu": filter_menu,
    "get_dish_detail": get_dish_detail
}

# ===============================
# Emoji mapping (BONUS 🔥)
# ===============================
def get_emoji(ingredient, category):
    if ingredient == "กุ้ง": return "🦐"
    elif ingredient == "หมู": return "🐷"
    elif ingredient == "ไก่": return "🐔"
    elif ingredient == "ปลา": return "🐟"
    elif ingredient == "ปู": return "🦀"
    elif category == "ทอด": return "🍗"
    elif category == "ต้ม": return "🍲"
    elif category == "ผัด": return "🥘"
    elif category == "แกง": return "🍛"
    elif category == "ข้าวผัด": return "🍚"
    else: return "🍽️"

def decide_tool(user_input):
    prompt = f"""
คุณคือ AI Agent ผู้ช่วยแนะนำเมนูอาหารไทย
จงวิเคราะห์คำถามของผู้ใช้และเลือกใช้เครื่องมือที่เหมาะสมที่สุดเพียง 1 เครื่องมือ

เครื่องมือที่มี:
1. "search_menu": ค้นหาเมนูอาหารทั่วไปด้วยข้อความ (input: {{"query": "ข้อความค้นหา เช่น อยากกินเผ็ดๆ, เมนูเส้น"}})
2. "filter_menu": กรองเมนูตามเงื่อนไข (input: {{"ingredient": "วัตถุดิบ (เช่น หมู, ไก่, กุ้ง)", "max_price": ราคา (ตัวเลข), "category": "ประเภท (เช่น ผัด, ต้ม, ทอด, แกง, ข้าวผัด)"}}) - ใช้เมื่อระบุเงื่อนไขชัดเจน
3. "get_dish_detail": ดูรายละเอียดเมนูแบบเต็ม (input: {{"dish_name": "ชื่อเมนู"}}) - ใช้เมื่อผู้ใช้ถามรายละเอียดของเมนูใดเมนูหนึ่งโดยเฉพาะ

คำถามผู้ใช้: "{user_input}"

จงตอบกลับเป็น JSON format เท่านั้น โดยมีรูปแบบดังนี้:
```json
{{
  "thought": "เหตุผลในการเลือกเครื่องมือ",
  "action": "ชื่อเครื่องมือที่เลือก (search_menu, filter_menu, get_dish_detail)",
  "action_input": {{
    // พารามิเตอร์ของเครื่องมือที่สอดคล้องกับ input ที่ระบุไว้
  }}
}}
```
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        # Parse JSON
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
    except Exception as e:
        print("⚠️ Gemini LLM Router Error:", e)
        # Fallback to search if LLM fails
        return {
            "thought": "LLM Error, falling back to search_menu",
            "action": "search_menu",
            "action_input": {"query": user_input}
        }

# ===============================
# Agent (ReAct)
# ===============================
def agent(user_input):
    print("\n======================")
    print("User Question:", user_input)
    print("ทวนคำถาม:", f"ผู้ใช้ถามว่า '{user_input}'")

    # Thought & Action (Wow ⭐)
    decision = decide_tool(user_input)
    
    thought = decision.get("thought", "ไม่มีเหตุผล")
    action = decision.get("action", "search_menu")
    action_input = decision.get("action_input", {})

    print("Thought:", thought)
    print("Action:", action)
    print("Action Input:", action_input)

    # ===============================
    # Execute Action
    # ===============================
    result = None
    if action in tools:
        try:
            result = tools[action](**action_input)
        except Exception as e:
            print("⚠️ Tool Execution Error:", e)
    
    # Tool Fallback (Wow ⭐⭐)
    if not result:
        print("Observation: ไม่พบข้อมูล (Empty Result)")
        print("Thought: ไม่พบเมนูตามที่ค้นหา จึงต้องเสนอเมนูทางเลือก (Fallback)")
        
        # Trigger fallback action
        fallback_query = "ยอดนิยม"
        print(f"Action: search_menu (Fallback with '{fallback_query}')")
        
        fallback_result = tools["search_menu"](query=fallback_query)
        
        if fallback_result:
            print("Observation: ได้รับเมนูทางเลือกยอดนิยม")
            answer = "ขออภัยครับ ไม่พบเมนูที่ท่านค้นหา 🥺\nแต่เรามีเมนูทางเลือกที่น่าสนใจมาแนะนำครับ:\n\n"
            for i, item in enumerate(fallback_result, 1):
                m = item["metadata"]
                answer += f"{i}. {m['name']} - {m['price']} บาท\n"
        else:
            print("Observation: ไม่พบข้อมูลแม้ในเมนูทางเลือก")
            answer = "ขออภัยครับ ไม่พบเมนูที่ท่านค้นหา และระบบขัดข้องในการหาเมนูทางเลือก ลองถามเมนูอื่นดูนะครับ"
            
    else:
        # Determine Observation text
        if action == "get_dish_detail":
            print("Observation: พบรายละเอียดเมนู")
        else:
            print(f"Observation: พบเมนูที่ตรงตามเงื่อนไข {len(result)} รายการ")
        
        # Format Answer based on Tool
        if action == "get_dish_detail":
            answer = format_dish_detail(result)
        elif action == "filter_menu":
            ingredient = action_input.get("ingredient")
            max_price = action_input.get("max_price")
            category = action_input.get("category")
            
            emoji = get_emoji(ingredient, category)
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
            answer = "เมนูที่แนะนำ:\n\n"
            for i, item in enumerate(result, 1):
                m = item["metadata"]
                answer += f"{i}. {m['name']} - {m['price']} บาท\n"

    print("Answer:\n" + answer)
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

        agent(q)