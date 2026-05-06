import hashlib
import math
import os
import re
import chromadb

# Relative imports
try:
    from .database import menu_repository
    from .llm import generate_text
except ImportError:
    from database import menu_repository
    from llm import generate_text

# หา Path ของโฟลเดอร์ Root ของโปรเจกต์
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VECTOR_STORE_PATH = os.path.join(BASE_DIR, "vector_store")
_embedding_provider = "local"
_collections = {}
LOCAL_EMBEDDING_DIM = 256

# ===============================
# Initialize ChromaDB
# ===============================
os.makedirs(VECTOR_STORE_PATH, exist_ok=True)
chroma_client = chromadb.PersistentClient(path=VECTOR_STORE_PATH)


def _get_collection(provider: str):
    collection_name = f"food_menus_{provider}"
    if collection_name not in _collections:
        _collections[collection_name] = chroma_client.get_or_create_collection(
            collection_name,
            metadata={"embedding_provider": provider},
        )
    return _collections[collection_name]


def _tokens(text: str):
    text = text.lower()
    chunks = re.findall(r"[a-z0-9]+|[ก-๙]+", text)
    tokens = []
    for chunk in chunks:
        tokens.append(chunk)
        if len(chunk) > 1:
            tokens.extend(chunk[i:i + 2] for i in range(len(chunk) - 1))
        if len(chunk) > 2:
            tokens.extend(chunk[i:i + 3] for i in range(len(chunk) - 2))
    return tokens


def _local_embedding(text: str):
    vector = [0.0] * LOCAL_EMBEDDING_DIM
    for token in _tokens(text):
        digest = hashlib.blake2b(token.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, "big")
        index = value % LOCAL_EMBEDDING_DIM
        sign = 1.0 if (value >> 8) % 2 == 0 else -1.0
        vector[index] += sign

    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / norm for v in vector]


def _resolve_embedding_provider() -> str:
    return _embedding_provider

# ===============================
# Embedding Function
# ===============================
def embed_text(text):
    return _local_embedding(text)

# ===============================
# Check whether query is food-related
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
    menus = menu_repository.get_all()
    provider = _resolve_embedding_provider()
    collection = _get_collection(provider)
    print(f"เริ่มฝังข้อมูลลง ChromaDB ด้วย {provider} embedding...")
    
    existing_count = collection.count()
    if existing_count >= len(menus):
        print(f"✅ ข้อมูลถูกฝังไว้แล้ว ({existing_count} รายการ) ข้ามการฝังซ้ำ")
        return

    embedded_count = 0
    failed_count = 0
    for menu in menus:
        text = (
            f"ชื่อเมนู: {menu['name']}\n"
            f"ประเภท: {menu.get('category', '')}\n"
            f"ราคา: {menu.get('price', '')} บาท\n"
            f"แคลอรี่: {menu.get('calories', '')} kcal\n"
            f"ส่วนผสม: {', '.join(menu.get('ingredients', []))}\n"
            f"แท็ก: {', '.join(menu.get('tags', []))}\n"
            f"รายละเอียด: {menu.get('description', '')}"
        )
        
        embedding = embed_text(text)
        if embedding:
            meta = {
                "id": menu["id"],
                "name": menu["name"],
                "category": menu.get("category", ""),
                "price": menu.get("price", 0),
                "calories": menu.get("calories", 0),
                "ingredients": ", ".join(menu.get("ingredients", [])),
                "allergens": ", ".join(menu.get("allergens", [])) if menu.get("allergens") else "ไม่มี",
                "description": menu.get("description", ""),
                "tags": ", ".join(menu.get("tags", []))
            }
            
            collection.upsert(
                ids=[menu["id"]],
                embeddings=[embedding],
                documents=[text],
                metadatas=[meta]
            )
            print(f"✅ Embedded: {menu['name']}")
            embedded_count += 1
        else:
            failed_count += 1
    
    print(f"✅ บันทึกข้อมูลสำเร็จ {embedded_count}/{len(menus)} รายการ")
    if failed_count:
        print(f"⚠️ ฝังข้อมูลไม่สำเร็จ {failed_count} รายการ")


def ensure_vector_store():
    """
    เตรียม vector_store ให้อัตโนมัติสำหรับเครื่องใหม่หรือคนที่ clone โปรเจกต์ไปใช้
    """
    load_and_embed_menus()

# ===============================
# Query Rewriting
# ===============================
def rewrite_query(original_query: str) -> str:
    try:
        improved_query = generate_text(
            f"ปรับปรุงคำถามนี้ให้เป็นคีย์เวิร์ดสั้นๆ สำหรับค้นหาเมนูอาหารตามสั่ง (ไม่ต้องมีคำตอบรับหรือคำสร้อย): '{original_query}'"
        )
        print(f"🔄 [Query Rewriting]: '{original_query}' -> '{improved_query}'")
        return improved_query
    except Exception as e:
        print(f"⚠️ DeepSeek Query Rewriting Error: {e}")
        return original_query

# ===============================
# Semantic Search Tool (ChromaDB)
# ===============================
def search_menu(query: str, n_results: int = 3):
    if not is_food_related(query):
        return []

    provider = _resolve_embedding_provider()
    collection = _get_collection(provider)

    if collection.count() == 0:
        load_and_embed_menus()
        
    improved_query = rewrite_query(query)
    query_embedding = embed_text(improved_query)
    
    if not query_embedding:
        return []

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    
    formatted_results = []
    if results["documents"] and results["documents"][0]:
        for i in range(len(results["documents"][0])):
            formatted_results.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i]
            })
            
    return formatted_results

if __name__ == "__main__":
    print("✅ เริ่มทดสอบ Vector Store (ChromaDB)")
    ensure_vector_store()
