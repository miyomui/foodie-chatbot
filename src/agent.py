import json
import re
import warnings
from typing import Any, Optional, TypedDict

from langchain_core._api.deprecation import (
    LangChainDeprecationWarning,
    LangChainPendingDeprecationWarning,
)

warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)
warnings.filterwarnings("ignore", category=LangChainPendingDeprecationWarning)
warnings.filterwarnings("ignore", message=".*allowed_objects.*")
warnings.filterwarnings("ignore", message=".*ConversationBufferMemory.*")
warnings.simplefilter("ignore")

# pyrefly: ignore [missing-import]
from langchain_classic.memory import ConversationBufferMemory
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph

# Relative imports
try:
    from .database import menu_repository
    from .llm import DEEPSEEK_MODEL, generate_text
    from .retrieval import search_menu
    from .tools import filter_menu, get_dish_detail, get_menu_by_tag
except ImportError:
    from database import menu_repository
    from llm import DEEPSEEK_MODEL, generate_text
    from retrieval import search_menu
    from tools import filter_menu, get_dish_detail, get_menu_by_tag

# ===============================
# Agent Tool Registry
# ===============================
tools_dict = {
    "search_menu": search_menu,
    "filter_menu": filter_menu,
    "get_dish_detail": get_dish_detail,
    "get_menu_by_tag": get_menu_by_tag
}

SYSTEM_PROMPT_TEMPLATE = PromptTemplate.from_template(
    """
คุณคือ "น้องหิวข้าว" AI Agent สำหรับแนะนำอาหารตามสั่งจากฐานข้อมูลของร้านเท่านั้น

Context Layer:
- ประวัติการสนทนาเดิม:
{chat_history}

กฎการทำงาน:
- ถ้าผู้ใช้ถามเรื่องเมนู ราคา แคลอรี่ วัตถุดิบ แท็ก หรือสารก่อภูมิแพ้ ต้องใช้ tools ก่อนตอบ
- ตอบเป็นภาษาไทย สุภาพ เป็นกันเอง และสั้นพอให้อ่านง่าย
- ห้ามแต่งชื่อเมนู ราคา แคลอรี่ วัตถุดิบ หรือสารก่อภูมิแพ้เอง ถ้าไม่มีในผลลัพธ์จาก tools ให้บอกว่าไม่พบข้อมูลพอ
- ถ้าผู้ใช้มีข้อจำกัด เช่น งบประมาณ แคลอรี่ แพ้อาหาร หรือไม่กินวัตถุดิบบางอย่าง ต้องเคารพข้อจำกัดนั้นก่อนความอร่อย
- ถ้าผู้ใช้ถามต่อเนื่อง เช่น "แล้วมีอย่างอื่นไหม" ให้ใช้ประวัติสนทนาเพื่อเข้าใจบริบทเดิม
- ก่อนตอบสุดท้าย ให้ตรวจคำตอบตัวเองว่ามีหลักฐานจาก tool หรือไม่ ถ้าไม่แน่ใจให้ตอบอย่างสุภาพว่าไม่พบข้อมูลชัดเจน
"""
)

_SESSION_MEMORIES: dict[str, ConversationBufferMemory] = {}
_AGENT_GRAPH = None


ROUTER_PROMPT_TEMPLATE = PromptTemplate.from_template(
    """
{system_prompt}

เลือก tool ที่เหมาะสมที่สุดสำหรับคำถามนี้:
1. search_menu(query, n_results): ใช้ค้นหาเมนูแบบกว้างหรือเชิงความหมาย
2. filter_menu(ingredient, max_price, category, max_calories, exclude_allergen): ใช้เมื่อมีเงื่อนไขชัดเจน
3. get_dish_detail(dish_name): ใช้เมื่อผู้ใช้ระบุชื่อเมนูชัดเจน
4. get_menu_by_tag(tag): ใช้เมื่อผู้ใช้ระบุแท็ก เช่น ยอดนิยม สุขภาพ เผ็ด ไม่เผ็ด

คำถาม: {query}

ตอบ JSON เท่านั้น:
{{"thought": "เหตุผลสั้นๆ", "tool": "ชื่อ tool", "params": {{"query": "..."}}}}
"""
)


FINAL_ANSWER_PROMPT = PromptTemplate.from_template(
    """
{system_prompt}

คำถามผู้ใช้:
{query}

ผลลัพธ์จาก tool:
{observation}

เขียนคำตอบสุดท้ายให้ผู้ใช้ โดย:
- ใช้เฉพาะข้อมูลจากผลลัพธ์ tool
- ถ้าพบหลายเมนู ให้แนะนำ 3-5 รายการที่ตรงที่สุด
- ระบุราคา แคลอรี่ หรือข้อควรระวังเมื่อมีข้อมูล
- ไม่ต้องแสดงรหัส (ID) ของเมนู
- ถ้าผลลัพธ์ว่างหรือไม่ชัดเจน ให้บอกสุภาพว่าไม่พบข้อมูลพอและขอเงื่อนไขเพิ่ม
"""
)


class FoodieAgentState(TypedDict, total=False):
    query: str
    system_prompt: str
    plan: dict
    observation: str
    answer: str
    final_answer: str


def _as_menu(item):
    if isinstance(item, dict) and "metadata" in item:
        return item["metadata"]
    return item


def _format_menu_line(menu):
    name = menu.get("name", "ไม่ทราบชื่อเมนู")
    price = menu.get("price", "-")
    calories = menu.get("calories", "-")
    description = menu.get("description", "")
    return f"- {name} ราคา {price} บาท ประมาณ {calories} kcal: {description}"


def _json_text(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def _limit_results(items, limit: int = 8):
    if not isinstance(items, list):
        return items
    return items[:limit]


def _tool_result(payload: Any, total: Optional[int] = None) -> str:
    if payload is None:
        return "ไม่พบข้อมูล"

    if isinstance(payload, list):
        menus = [_as_menu(item) for item in payload]
        result = {
            "total_found": total if total is not None else len(menus),
            "returned": len(menus),
            "menus": menus,
        }
        return _json_text(result)

    return _json_text(payload)


@tool("search_menu")
def search_menu_tool(query: str, n_results: int = 5) -> str:
    """ค้นหาเมนูจากความหมายของคำถาม เช่น อยากกินอะไรเผ็ด เมนูแนะนำ หรืออาหารที่ใกล้เคียง."""
    results = search_menu(query=query, n_results=n_results)
    return _tool_result(_limit_results(results, n_results), total=len(results))


@tool("filter_menu")
def filter_menu_tool(
    ingredient: Optional[str] = None,
    max_price: Optional[int] = None,
    category: Optional[str] = None,
    max_calories: Optional[int] = None,
    exclude_allergen: Optional[str] = None,
) -> str:
    """กรองเมนูตามวัตถุดิบ งบประมาณ ประเภท แคลอรี่สูงสุด หรือสารก่อภูมิแพ้ที่ต้องหลีกเลี่ยง."""
    results = filter_menu(
        ingredient=ingredient,
        max_price=max_price,
        category=category,
        max_calories=max_calories,
        exclude_allergen=exclude_allergen,
    )
    return _tool_result(_limit_results(results), total=len(results))


@tool("get_dish_detail")
def get_dish_detail_tool(dish_name: str) -> str:
    """ดึงรายละเอียดเมนูแบบเจาะจงเมื่อรู้ชื่อเมนูชัดเจน."""
    return _tool_result(get_dish_detail(dish_name))


@tool("get_menu_by_tag")
def get_menu_by_tag_tool(tag: str) -> str:
    """ดึงเมนูตามแท็ก เช่น ยอดนิยม สุขภาพ เผ็ด ไม่เผ็ด หรือไม่มีอาหารทะเล."""
    results = get_menu_by_tag(tag)
    return _tool_result(_limit_results(results), total=len(results))


LANGCHAIN_TOOLS = [
    search_menu_tool,
    filter_menu_tool,
    get_dish_detail_tool,
    get_menu_by_tag_tool,
]
LANGCHAIN_TOOL_MAP = {item.name: item for item in LANGCHAIN_TOOLS}


def _fallback_answer(query, context):
    if isinstance(context, dict):
        return (
            f"ได้เลยค่ะ เมนูที่ตรงที่สุดคือ {context.get('name')} 🍽️\n"
            f"ราคา {context.get('price')} บาท ประมาณ {context.get('calories')} kcal\n"
            f"{context.get('description')}"
        )

    if isinstance(context, list) and context:
        menus = [_as_menu(item) for item in context[:3]]
        lines = "\n".join(_format_menu_line(menu) for menu in menus)
        return f"แนะนำเมนูที่น่าจะตรงกับ “{query}” ค่ะ 🍜\n{lines}"

    fallback_menus = menu_repository.get_all()[:3]
    lines = "\n".join(_format_menu_line(menu) for menu in fallback_menus)
    return f"ตอนนี้ยังไม่เจอเมนูที่ตรงมาก ๆ แต่ลองดูเมนูยอดนิยมเหล่านี้ก่อนได้ค่ะ\n{lines}"


def _extract_max_number(query, suffixes):
    for suffix in suffixes:
        match = re.search(rf"(?:ไม่เกิน|ต่ำกว่า|ภายใน)?\s*(\d+)\s*{suffix}", query)
        if match:
            return int(match.group(1))
    return None


def _local_router(user_query):
    menus = menu_repository.get_all()

    for menu in menus:
        if menu["name"] in user_query:
            return {
                "thought": "พบชื่อเมนูชัดเจนในคำถาม",
                "tool": "get_dish_detail",
                "params": {"dish_name": menu["name"]},
            }

    for tag in ["สุขภาพ", "ยอดนิยม", "ไม่เผ็ด", "เผ็ด", "ไม่มีอาหารทะเล", "หวานมัน"]:
        if tag in user_query:
            return {
                "thought": "พบแท็กเมนูในคำถาม",
                "tool": "get_menu_by_tag",
                "params": {"tag": tag},
            }

    params = {}
    max_price = _extract_max_number(user_query, ["บาท", "บ"])
    max_calories = _extract_max_number(user_query, ["แคลอรี่", "kcal", "แคล"])
    if max_price:
        params["max_price"] = max_price
    if max_calories:
        params["max_calories"] = max_calories

    for ingredient in ["หมู", "ไก่", "กุ้ง", "ปู", "ปลา", "ไข่", "เนื้อ", "ผัก", "ทะเล"]:
        if ingredient in user_query:
            params["ingredient"] = ingredient
            break

    if "แพ้" in user_query or "ไม่เอา" in user_query or "ไม่มี" in user_query:
        if "ทะเล" in user_query or "อาหารทะเล" in user_query:
            params["exclude_allergen"] = "อาหารทะเล"
        elif "ไข่" in user_query:
            params["exclude_allergen"] = "ไข่"
        elif "กลูเตน" in user_query:
            params["exclude_allergen"] = "กลูเตน"

    if params:
        return {
            "thought": "พบเงื่อนไขที่กรองด้วยข้อมูลเมนูได้",
            "tool": "filter_menu",
            "params": params,
        }

    return {
        "thought": "ใช้การค้นหาเมนูแบบ local fallback",
        "tool": "search_menu",
        "params": {"query": user_query},
    }


def get_memory(session_id: str = "default") -> ConversationBufferMemory:
    if session_id not in _SESSION_MEMORIES:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _SESSION_MEMORIES[session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                input_key="input",
                output_key="output",
                return_messages=False,
            )
    return _SESSION_MEMORIES[session_id]


def reset_memory(session_id: str = "default") -> None:
    memory = _SESSION_MEMORIES.get(session_id)
    if memory:
        memory.clear()


def _build_system_prompt(memory: ConversationBufferMemory) -> str:
    memory_vars = memory.load_memory_variables({})
    return SYSTEM_PROMPT_TEMPLATE.format(
        chat_history=memory_vars.get("chat_history") or "ยังไม่มีประวัติการสนทนา"
    )


def _message_text(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or item))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def _extract_agent_answer(agent_result: dict) -> str:
    messages = agent_result.get("messages", [])
    for message in reversed(messages):
        message_type = getattr(message, "type", "")
        content = _message_text(getattr(message, "content", ""))
        tool_calls = getattr(message, "tool_calls", None)
        if message_type in {"ai", "assistant"} and content and not tool_calls:
            return content.strip()
    return _message_text(agent_result.get("output", "")).strip()


def _extract_tool_evidence(agent_result: dict) -> str:
    evidence = []
    for message in agent_result.get("messages", []):
        message_type = getattr(message, "type", "")
        if message_type == "tool":
            tool_name = getattr(message, "name", "tool")
            evidence.append(f"[{tool_name}]\n{_message_text(getattr(message, 'content', ''))}")
    return "\n\n".join(evidence)


def _parse_json_object(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise


def _router_node(state: FoodieAgentState) -> FoodieAgentState:
    prompt = ROUTER_PROMPT_TEMPLATE.format(
        system_prompt=state["system_prompt"],
        query=state["query"],
    )
    try:
        router_text = generate_text(prompt, response_format={"type": "json_object"})
        plan = _parse_json_object(router_text)
    except Exception as e:
        print(f"⚠️ Router Error: {e}. ใช้ local router แทน.")
        plan = _local_router(state["query"])

    print(f"🤔 [Thought]: {plan.get('thought', '-')}")
    return {"plan": plan}


def _tool_node(state: FoodieAgentState) -> FoodieAgentState:
    plan = state.get("plan") or {}
    tool_name = plan.get("tool")
    params = plan.get("params") or {}
    tool_item = LANGCHAIN_TOOL_MAP.get(tool_name)

    if not tool_item:
        observation = "ไม่พบเครื่องมือที่เหมาะสม"
    else:
        print(f"🛠️ [Action]: Call {tool_name} with {params}")
        observation = tool_item.invoke(params)

    print(f"👁️ [Observation]: {observation[:220]}{'...' if len(observation) > 220 else ''}")
    return {"observation": observation}


def _get_agent_graph():
    global _AGENT_GRAPH
    if _AGENT_GRAPH is None:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            graph = StateGraph(FoodieAgentState)
            graph.add_node("router", _router_node)
            graph.add_node("tool", _tool_node)
            graph.add_edge(START, "router")
            graph.add_edge("router", "tool")
            graph.add_edge("tool", END)
            _AGENT_GRAPH = graph.compile()
    return _AGENT_GRAPH


def _run_langgraph_agent(user_query: str, memory: ConversationBufferMemory) -> str:
    system_prompt = _build_system_prompt(memory)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = _get_agent_graph().invoke({
            "query": user_query,
            "system_prompt": system_prompt,
        })
    return result.get("observation") or ""


def generate_answer_stream(query, context):
    """
    สร้างคำตอบแบบเป็นธรรมชาติจาก Context ที่ได้ (Wow ⭐) รองรับ Streaming
    """
    if context is None or context == []:
        yield _fallback_answer(query, context)
        return

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
        from .llm import generate_text_stream
        for chunk in generate_text_stream(prompt):
            yield chunk
    except Exception as e:
        print(f"⚠️ Answer Generation Error: {e}. ใช้คำตอบแบบ local fallback.")
        yield _fallback_answer(query, context)

def _run_local_agent_stream(user_query: str):
    plan = _local_router(user_query)
    print(f"🤔 [Thought]: {plan['thought']}")

    tool_name = plan.get("tool")
    params = plan.get("params", {})

    if tool_name in tools_dict:
        print(f"🛠️ [Action]: Call {tool_name} with {params}")
        observation = tools_dict[tool_name](**params)
    else:
        observation = "ไม่พบเครื่องมือที่เหมาะสม"

    print(f"👁️ [Observation]: พบข้อมูล {len(observation) if isinstance(observation, list) else '1'} รายการ")
    for chunk in generate_answer_stream(user_query, observation):
        yield chunk

def foodie_agent_stream(user_query, session_id: str = "default"):
    """
    Main Streaming LangChain Agent Loop with memory and tools.
    """
    print(f"\n[User]: {user_query}")
    print(f"🤖 [Model]: {DEEPSEEK_MODEL}")

    memory = get_memory(session_id)
    system_prompt = _build_system_prompt(memory)
    try:
        observation = _run_langgraph_agent(user_query, memory)
        print(f"🧠 [Memory]: ใช้ ConversationBufferMemory session={session_id}")
        prompt = FINAL_ANSWER_PROMPT.format(
            system_prompt=system_prompt,
            query=user_query,
            observation=observation,
        )
        from .llm import generate_text_stream
        
        full_answer = ""
        for chunk in generate_text_stream(prompt):
            full_answer += chunk
            yield chunk
            
    except Exception as e:
        print(f"⚠️ LangGraph Agent Error: {e}. ใช้ local fallback แทน.")
        full_answer = ""
        for chunk in _run_local_agent_stream(user_query):
            full_answer += chunk
            yield chunk

    memory.save_context({"input": user_query}, {"output": full_answer})

def foodie_agent(user_query, session_id: str = "default") -> str:
    """
    Synchronous wrapper for foodie_agent_stream
    """
    return "".join(list(foodie_agent_stream(user_query, session_id)))

if __name__ == "__main__":
    while True:
        query = input("\nหิวหรือยังคะ? ถามมาได้เลย (หรือพิมพ์ 'exit' เพื่อออก): ")
        if query.lower() == 'exit':
            break
        
        # We can test streaming in the CLI easily!
        print("\n[Agent]: ", end="", flush=True)
        for chunk in foodie_agent_stream(query):
            print(chunk, end="", flush=True)
        print("\n")
