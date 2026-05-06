import os
import uuid

import gradio as gr

from src.agent import foodie_agent, reset_memory
from src.retrieval import ensure_vector_store


def _new_session_id() -> str:
    return uuid.uuid4().hex


def respond(message, history, session_id):
    session_id = session_id or _new_session_id()
    answer = foodie_agent(message, session_id=session_id)
    history = history or []
    history = [
        *history,
        {"role": "user", "content": message},
        {"role": "assistant", "content": answer},
    ]
    return "", history, session_id


def clear_chat(session_id):
    if session_id:
        reset_memory(session_id)
    return [], _new_session_id()


def prepare_startup():
    print("🔎 Preparing vector_store...")
    ensure_vector_store()
    print("✅ vector_store พร้อมใช้งาน")


with gr.Blocks(title="Foodie Chatbot") as demo:
    session_state = gr.State(value=None)
    gr.Markdown("# Foodie Chatbot")
    chatbot = gr.Chatbot(height=560)
    message = gr.Textbox(
        placeholder="หิวอะไรอยู่คะ?",
        show_label=False,
        autofocus=True,
    )
    clear = gr.Button("ล้างบทสนทนา")

    message.submit(
        respond,
        inputs=[message, chatbot, session_state],
        outputs=[message, chatbot, session_state],
    )
    clear.click(
        clear_chat,
        inputs=[session_state],
        outputs=[chatbot, session_state],
    )


if __name__ == "__main__":
    prepare_startup()
    demo.launch(
        server_name=os.getenv("GRADIO_SERVER_NAME", "0.0.0.0"),
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
    )
