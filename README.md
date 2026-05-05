# 🍜 Foodie Chatbot: Professional AI Agentic RAG
> **"Beyond search, we think. Beyond answering, we care."**

โปรเจกต์ AI Agent สำหรับแนะนำอาหารตามสั่งระดับ Professional พัฒนาด้วยเทคนิค **Agentic RAG (Retrieval-Augmented Generation)** โดยใช้ Gemini 2.5/Flash เป็นสมองหลักในการตัดสินใจและโต้ตอบ

---

## 🛠️ สถาปัตยกรรมระบบ (System Workflow)

ระบบของเราทำงานเป็นวงจร **ReAct (Reasoning + Acting)** เพื่อให้ได้คำตอบที่แม่นยำและสมเหตุสมผลที่สุด:

<div align="center">
  <img src="images/workflow.png" alt="Foodie Agent Workflow" width="350">
</div>

---

## 🌟 ฟีเจอร์เด่น (Key Features)

### 1. 🧠 Smart Agent Routing
Agent สามารถวิเคราะห์เจตนา (Intent) ของผู้ใช้ และเลือกใช้เครื่องมือที่เหมาะสมที่สุดแบบ Dynamic เช่น:
- **Semantic Search**: ค้นหาเมนูที่มีความหมายใกล้เคียงกับความต้องการ
- **Filter Tool**: กรองตามงบประมาณ, วัตถุดิบ หรือประเภทอาหาร
- **Detail Retrieval**: ดึงข้อมูลเชิงลึกของเมนูเฉพาะอย่าง

### 2. 🥗 Health-Conscious Intelligence (Wow! ⭐)
ระบบมีความฉลาดด้านสุขภาพและโภชนาการ:
- **Allergen Avoidance**: กรองเมนูที่มีสารก่อภูมิแพ้ (เช่น แพ้อาหารทะเล, แพ้ไข่)
- **Calorie Control**: ค้นหาเมนูภายในระดับแคลอรี่ที่กำหนด

### 3. 🔍 Advanced Retrieval Techniques
- **Query Rewriting**: แปลงประโยคพูดของมนุษย์ให้เป็นคีย์เวิร์ดที่แม่นยำก่อนค้นหา
- **Vector Store (ChromaDB)**: เก็บข้อมูลในรูปแบบ Vector เพื่อการค้นหาเชิงความหมาย (Semantic)

### 4. 💬 Natural Language Generation (NLG)
- ปรับแต่งคำตอบจากข้อมูลดิบให้เป็นประโยคที่สุภาพ เป็นกันเอง และมี Emoji ประกอบตามบริบท

---

## 📂 โครงสร้างไฟล์ในโปรเจกต์ (Professional Structure)

```text
foodie-chatbot/
├── src/                    # 🧠 Source Code หลัก
│   ├── __init__.py
│   ├── agent.py            # ReAct Loop & Logic หลัก
│   ├── retrieval.py        # Vector Search & Embedding
│   ├── tools.py            # Agent Skills (Filter/Detail/Tags)
│   └── database.py         # Data Access Layer
├── data/                   # 📂 ข้อมูลดิบ
│   └── menus.json          # ฐานข้อมูลเมนูอาหาร
├── images/                 # 🖼️ Assets ประกอบ
│   └── workflow.png        # แผนภาพการทำงาน
├── vector_store/           # 💾 ฐานข้อมูลเวกเตอร์ (ChromaDB)
├── run_agent.py            # 🚀 จุดรันโปรเจกต์หลัก (Entry Point)
├── requirements.txt        # รายการ Library ที่ต้องใช้
├── .env                    # เก็บ API Key (Private)
└── README.md               # เอกสารชี้แจงโปรเจกต์
```

---

## 🚀 วิธีการติดตั้งและรันโปรเจกต์

1. **เตรียมสภาพแวดล้อม**
   ```bash
   python -m venv venv
   # Windows: venv\Scripts\activate | Mac: source venv/bin/activate
   ```

2. **ติดตั้ง Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **ตั้งค่า API Key**
   - สร้างไฟล์ `.env` ไว้ที่ Root Folder
   - ใส่คีย์ของคุณ: `GEMINI_API_KEY=your_key_here`

4. **เตรียมฐานข้อมูลเวกเตอร์** (รันเฉพาะครั้งแรก)
   ```bash
   python -m src.retrieval
   ```

5. **เริ่มใช้งาน Chatbot**
   ```bash
   python run_agent.py
   ```

---

## 🗺️ แผนการพัฒนาในอนาคต (Roadmap)

- [ ] **LangChain/LangGraph Integration**: จัดการ State และ Memory ให้ซับซ้อนยิ่งขึ้น
- [ ] **Interactive Web UI**: พัฒนาหน้าจอ Chat ด้วย Gradio หรือ Streamlit
- [ ] **Voice Order**: เพิ่มระบบสั่งอาหารด้วยเสียง (Speech-to-Text)

---

## 👥 สมาชิกทีม (Team Members)

- https://github.com/miyomui
- https://github.com/techindetc-ux
- https://github.com/Ploy-ari
- https://github.com/ffourwheel

---
*Created with ❤️ for Advanced Agentic AI Course*
