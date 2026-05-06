import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from openai import OpenAI


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

_client = None
_chat_model = None
_llm_available = True


def _get_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=_require_api_key(), base_url=DEEPSEEK_BASE_URL)
    return _client


def _require_api_key() -> str:
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError("ไม่พบ DEEPSEEK_API_KEY ในไฟล์ .env")
    return api_key


def get_chat_model():
    global _chat_model
    if _chat_model is None:
        _chat_model = ChatOpenAI(
            model=DEEPSEEK_MODEL,
            api_key=_require_api_key(),
            base_url=DEEPSEEK_BASE_URL,
            temperature=float(os.getenv("DEEPSEEK_TEMPERATURE", "0.2")),
            timeout=float(os.getenv("DEEPSEEK_TIMEOUT", "60")),
        )
    return _chat_model


def generate_text(prompt: str, *, response_format=None) -> str:
    global _llm_available
    if not _llm_available:
        raise RuntimeError("DeepSeek ถูกปิดใช้ชั่วคราวใน session นี้หลังเรียกไม่สำเร็จ")

    request = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }
    if response_format:
        request["response_format"] = response_format

    try:
        resp = _get_client().chat.completions.create(**request)
    except Exception:
        _llm_available = False
        raise

    content = resp.choices[0].message.content
    if not content:
        raise RuntimeError("DeepSeek ไม่ได้ส่งข้อความตอบกลับ")
    return content.strip()

def generate_text_stream(prompt: str, *, response_format=None):
    global _llm_available
    if not _llm_available:
        raise RuntimeError("DeepSeek ถูกปิดใช้ชั่วคราวใน session นี้หลังเรียกไม่สำเร็จ")

    request = {
        "model": DEEPSEEK_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "stream": True,
    }
    if response_format:
        request["response_format"] = response_format

    try:
        resp = _get_client().chat.completions.create(**request)
        for chunk in resp:
            content = chunk.choices[0].delta.content
            if content:
                yield content
    except Exception:
        _llm_available = False
        raise
