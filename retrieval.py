import json
import os
import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import errors

from database import load_menus

# ===============================
# Load Gemini API Key
# ===============================
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# ===============================
# Initialize ChromaDB
# ===============================
chroma_client = chromadb.PersistentClient(path="./vector_store")
collection = chroma_client.get_or_create_collection("food_menus")

# ===============================
# Embedding Function
# ===============================
def embed_text(text):
    try:
        resp = client.models.embed_content(
            model="models/gemini-embedding-2",
            contents=text
        )
        return resp.embeddings[0].values
    except Exception as e:
        print(f"⚠️ Embedding Error: {e}")
        return None

# ===============================
# Check whether query is food-related (Wow ⭐⭐ - ป้องกันคำถามไม่เกี่ยว)
# ===============================
def is_food_related(query):
    food_keywords = [
        "เมนู", "อาหาร", "กิน", "หิว", "อยากกิน", "แนะนำ",
        "หมู", "ไก่", "กุ้ง", "ปู", "ปลา", "ไข่", "เนื้อ", "ผัก",
        "ข้าว", "เส้น", "ผัด", "ต้ม", "ทอด", "แกง",
        "เผ็ด", "ไม่เผ็ด", "หวาน", "เปรี้ยว", "กรอบ",
        "ราคา", "บาท", "แคลอรี่", "ถูก", "แพง", "แซ่บ", "น้ำ", "อะไรดี"
    ]
    return any(keyword in query for keyword in food_keywords)

# ===============================
# Embed Data into Vector Store
# ===============================
def load_and_embed_menus():
    menus = load_menus()
    print("เริ่มฝังข้อมูลลง ChromaDB...")
    
    # Check if already embedded
    existing_count = collection.count()
    if existing_count >= len(menus):
        print(f"✅ ข้อมูลถูกฝังไว้แล้ว ({existing_count} รายการ) ข้ามการฝังซ้ำ")
        return

    for menu in menus:
        # Create a rich document for embedding
        text = (
            f"ชื่อเมนู: {menu['name']}\n"
            f"ประเภท: {menu['category']}\n"
            f"ราคา: {menu['price']} บาท\n"
            f"แคลอรี่: {menu['calories']} kcal\n"
            f"ส่วนผสม: {', '.join(menu['ingredients'])}\n"
            f"แท็ก: {', '.join(menu['tags'])}\n"
            f"รายละเอียด: {menu['description']}"
        )
        
        embedding = embed_text(text)
        if embedding:
            # Prepare metadata (ChromaDB does not accept empty lists or complex objects in metadata)
            meta = {
                "id": menu["id"],
                "name": menu["name"],
                "category": menu["category"],
                "price": menu["price"],
                "calories": menu["calories"],
                "ingredients": ", ".join(menu["ingredients"]),
                "allergens": ", ".join(menu["allergens"]) if menu["allergens"] else "ไม่มี",
                "description": menu["description"],
                "tags": ", ".join(menu["tags"])
            }
            
            collection.upsert(
                ids=[menu["id"]],
                embeddings=[embedding],
                documents=[text],
                metadatas=[meta]
            )
            print(f"✅ Embedded: {menu['name']}")
    
    print(f"✅ บันทึกข้อมูลสำเร็จทั้งหมด {len(menus)} รายการ")

# ===============================
# Query Rewriting (Wow ⭐ - ช่วยปรับคำค้นหาให้ตรงขึ้น)
# ===============================
def rewrite_query(original_query: str) -> str:
    """
    ปรับปรุงคำถามของผู้ใช้ให้เหมาะกับการค้นหาด้วย Semantic Search มากขึ้น
    """
    try:
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"ปรับปรุงคำถามนี้ให้เป็นคีย์เวิร์ดสั้นๆ สำหรับค้นหาเมนูอาหารตามสั่ง (ไม่ต้องมีคำตอบรับหรือคำสร้อย): '{original_query}'"
        )
        improved_query = resp.text.strip()
        print(f"🔄 [Query Rewriting]: '{original_query}' -> '{improved_query}'")
        return improved_query
    except Exception as e:
        print(f"⚠️ Query Rewriting Error: {e}")
        return original_query

# ===============================
# Semantic Search Tool (ChromaDB)
# ===============================
def search_menu(query: str, n_results: int = 3):
    """
    ค้นหาเมนูที่ตรงกับความต้องการด้วย Semantic Search (Vector Store)
    """
    # กรองคำถามที่ไม่ใช่อาหาร
    if not is_food_related(query):
        return []

    # ถ้าไม่มีข้อมูลใน Vector Store ให้ load ก่อน
    if collection.count() == 0:
        load_and_embed_menus()
        
    # Wow ⭐: Query Rewriting
    improved_query = rewrite_query(query)
        
    query_embedding = embed_text(improved_query)
    
    if not query_embedding:
        print("⚠️ ไม่สามารถสร้าง embedding ได้ (ใช้ fallback ไปที่การส่งคืนข้อมูลว่าง)")
        return []

    # Query ChromaDB
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    formatted_results = []
    
    # Format the results to match previous interface
    if results["documents"] and results["documents"][0]:
        for i in range(len(results["documents"][0])):
            formatted_results.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i]
            })
            
    return formatted_results

# ===============================
# Test
# ===============================
if __name__ == "__main__":
    print("✅ เริ่มทดสอบ Vector Store (ChromaDB)")
    load_and_embed_menus()
    
    test_queries = [
        "อยากกินเมนูเผ็ดๆ",
        "ขอเมนูที่มีกุ้ง",
        "รถยนต์", # should be blocked
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