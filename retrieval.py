import json, chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()
chroma_client = chromadb.PersistentClient(path="./vector_store")
collection = chroma_client.get_or_create_collection("food_menus")

def load_and_embed_menus():
    with open("data/menus.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    for menu in data["menus"]:
        text = f"ชื่อเมนู: {menu['name']}\nหมวดหมู่: {menu['category']}\nราคา: {menu['price']} บาท\nแคลอรี่: {menu['calories']} kcal\nส่วนผสม: {', '.join(menu['ingredients'])}\nรายละเอียด: {menu['description']}\nแท็ก: {', '.join(menu['tags'])}"
        resp = client.embeddings.create(input=text, model="text-embedding-3-small")
        collection.add(ids=[menu["id"]], embeddings=[resp.data[0].embedding], documents=[text], metadatas=[menu])
    print(f"✅ Embedded {len(data['menus'])} menus!")

def search_menu(query: str, n_results: int = 3) -> list:
    resp = client.embeddings.create(input=query, model="text-embedding-3-small")
    results = collection.query(query_embeddings=[resp.data[0].embedding], n_results=n_results)
    return [{"text": results["documents"][0][i], "metadata": results["metadatas"][0][i]} for i in range(len(results["documents"][0]))]

if __name__ == "__main__":
    load_and_embed_menus()
