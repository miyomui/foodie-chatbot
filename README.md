# NongHiwKhaow 🍽️ (น้องหิวข้าว)



*น้องหิวข้าว* เป็น AI Agent ที่ถูกออกแบบมาเพื่อมอบประสบการณ์การเลือกเมนูอาหารตามสั่งที่เหนือระดับ ขับเคลื่อนด้วยสถาปัตยกรรม **Agentic RAG** แบบเต็มรูปแบบ ตอบโจทย์ทั้งการออกแบบที่สวยงาม ใช้งานง่าย และวิศวกรรมซอฟต์แวร์ที่เน้นประสิทธิภาพและความรวดเร็ว (High-Performance Streaming)
## 🎥 สาธิตการใช้งาน (Demo)
![Demo น้องหิวข้าว AI](assets/demo.webp)
---

## 🌟 จุดเด่นของสถาปัตยกรรม (Architectural Highlights)

ระบบนี้ไม่ได้เป็นเพียงแค่ Prompt หุ้ม LLM แต่เป็น **Autonomous Agent** ที่มีกระบวนการคิดและตัดสินใจ:

1. **ReAct Loop (Thought-Action-Observation):** ใช้ `LangGraph` เป็นกลไกหลักควบคุม State Machine เพื่อให้ AI วางแผนการใช้เครื่องมือ (Router), เรียกใช้เครื่องมือ (Action), และสังเกตผลลัพธ์ (Observation) ก่อนตอบคำถาม
2. **Real-time Streaming & Memory:** ปรับปรุง Agent ให้สามารถสตรีมข้อความตอบกลับแบบพิมพ์ดีด (Typewriter Effect) ได้ทันที ลดเวลา Latency ลงมหาศาล พร้อมระบบจดจำบทสนทนา (Conversation Memory) อย่างต่อเนื่อง
3. **Repository Pattern:** หุ้มการเข้าถึงข้อมูลเมนู (`menus.json`) ผ่าน `MenuRepository` ทำให้โค้ดสะอาดและพร้อมสเกลไปใช้ฐานข้อมูลอย่าง SQLite หรือ PostgreSQL ในอนาคต
4. **Hybrid Tooling:** มีเครื่องมือที่หลากหลายให้ AI เลือกใช้:
   - 🔍 `search_menu`: ค้นหาเชิงความหมายผ่าน **ChromaDB** Vector Store (RAG)
   - 🎯 `filter_menu`: กรองข้อมูลเชิงลึก (ราคา, แคลอรี่, สารก่อภูมิแพ้)
   - 📖 `get_dish_detail`: ดึงข้อมูลเมนูเจาะจง
   - 🏷️ `get_menu_by_tag`: ดึงข้อมูลตามหมวดหมู่ (เช่น สุขภาพ, ยอดนิยม)
5. **Modern Vibrant UI:** ปรับโฉม Frontend ใหม่ทั้งหมด สู่ดีไซน์พรีเมียมสีส้มสดใส (Vibrant Tamsang) เน้น Typography ที่สวยงาม ใช้งานง่าย พร้อมแสดงเบื้องหลังการคิดของ AI อย่างโปร่งใส

---

## 🚀 Quick Start

### 1. เตรียมไฟล์ `.env`
สร้างไฟล์ `.env` ที่ root ของโปรเจกต์:
```env
DEEPSEEK_API_KEY=your_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

### 2. รันด้วย Docker Compose (แนะนำ)
เพียงคำสั่งเดียว ระบบจะสร้าง Vector DB, โหลดข้อมูล และรัน FastAPI Server พร้อม UI ให้ทันที:
```cmd
docker compose up -d --build
```

### 3. เข้าใช้งานเว็บแอปพลิเคชัน
- หน้าหลัก (Smart Menu Finder): `http://localhost:7860/`
- หน้าแชท (Agent Chat): `http://localhost:7860/chat`

---

## 🛠️ โครงสร้างโปรเจกต์ (Project Structure)

```text
foodie-chatbot/
├── assets/
│   └── demo.webp          # วิดีโอสาธิตการใช้งาน
├── data/
│   └── menus.json         # ฐานข้อมูลเมนูตั้งต้น (Data Source)
├── src/
│   ├── agent.py           # LangGraph State Machine & Prompts
│   ├── database.py        # MenuRepository (Data Access Layer)
│   ├── llm.py             # LLM API Client (DeepSeek) รองรับ Streaming
│   ├── retrieval.py       # ChromaDB Vector Store & Embedding
│   └── tools.py           # LangChain Tools สำหรับ Agent
├── templates/
│   ├── index.html         # Smart Menu Finder Landing Page
│   └── chat.html          # Free-form Agent Chat Experience
├── app.py                 # FastAPI Web Server & SSE Streaming
├── run_agent.py           # CLI Interface (ทดสอบ Agent ผ่าน Terminal)
├── docker-compose.yml
└── requirements.txt
```

---

## 💡 เบื้องหลังการทำงาน (How it works)

เมื่อผู้ใช้พิมพ์คำถาม เช่น *"มีเมนูไก่ที่ไม่เผ็ด แคลอรี่ต่ำกว่า 400 ไหม?"*
1. **[Router Node]** AI จะวิเคราะห์คำถามและเลือกใช้ `filter_menu` โดยส่งพารามิเตอร์ `{"ingredient": "ไก่", "max_calories": 400, "tag": "ไม่เผ็ด"}`
2. **[Tool Node]** เครื่องมือจะไปดึงข้อมูลจาก `MenuRepository` และส่งผลลัพธ์กลับมา (Observation)
3. **[Streaming Response]** AI จะเริ่มสตรีมคำตอบที่เรียบเรียงอย่างสละสลวยส่งกลับไปยังผู้ใช้ทันที (Real-time Typewriter Effect)
4. **[Frontend]** ผู้ใช้จะเห็นคำตอบค่อยๆ พิมพ์ขึ้นมา และสามารถกดดู **"ดูเบื้องหลังการคิดของ AI"** เพื่อดู Log การทำงานอย่างละเอียดได้ตลอดเวลา

---

## 👥 Team Members

- [miyomui](https://github.com/miyomui)
- [techindetc-ux](https://github.com/techindetc-ux)
- [Ploy-ari](https://github.com/Ploy-ari)
- [ffourwheel](https://github.com/ffourwheel)

*Created for Advanced Agentic AI Course*
