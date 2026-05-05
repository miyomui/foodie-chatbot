from src.agent import foodie_agent

if __name__ == "__main__":
    print("=== 🍜 ยินดีต้อนรับสู่ Agentic Foodie Chatbot (Professional Edition) ===")
    while True:
        query = input("\nหิวหรือยังคะ? ถามมาได้เลย (หรือพิมพ์ 'exit' เพื่อออก): ")
        if query.lower() == 'exit':
            break
        
        answer = foodie_agent(query)
        print(f"\n[Agent]: {answer}")
