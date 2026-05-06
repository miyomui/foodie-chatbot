import os
import uuid

import gradio as gr
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn

from src.agent import foodie_agent, reset_memory
from src.retrieval import ensure_vector_store

app = FastAPI(title="NongHiwKhaow")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

import queue
import threading
import json
import asyncio
from fastapi.responses import StreamingResponse

import io
from contextlib import redirect_stdout

@app.post("/api/chat")
async def api_chat(request: Request):
    data = await request.json()
    message = data.get("message", "")
    session_id = data.get("session_id") or uuid.uuid4().hex
    
    f = io.StringIO()
    with redirect_stdout(f):
        answer = foodie_agent(message, session_id=session_id)
        
    logs = f.getvalue()
    return {"answer": answer, "session_id": session_id, "logs": logs}


@app.post("/api/chat_stream")
async def api_chat_stream(request: Request):
    data = await request.json()
    message = data.get("message", "")
    session_id = data.get("session_id") or uuid.uuid4().hex
    
    q = queue.Queue()
    
    class QueueWriter:
        def __init__(self, old_stdout):
            self.old_stdout = old_stdout

        def write(self, text):
            if text:
                q.put({"type": "log", "content": text})
                self.old_stdout.write(text)
                self.old_stdout.flush()
                
        def flush(self):
            self.old_stdout.flush()

    def run_agent():
        import sys
        import traceback
        old_stdout = sys.stdout
        sys.stdout = QueueWriter(old_stdout)
        try:
            ans = foodie_agent(message, session_id=session_id)
            q.put({"type": "answer", "content": ans, "session_id": session_id})
        except Exception as e:
            error_trace = traceback.format_exc()
            old_stdout.write(f"\n Error in foodie_agent:\n{error_trace}\n")
            old_stdout.flush()
            q.put({"type": "error", "content": str(e)})
        finally:
            sys.stdout = old_stdout
            q.put(None)

    threading.Thread(target=run_agent).start()

    async def event_stream():
        while True:
            try:
                item = q.get_nowait()
                if item is None:
                    break
                yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
            except queue.Empty:
                await asyncio.sleep(0.05)
                
    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/chat", response_class=HTMLResponse)
async def read_chat():
    with open("templates/chat.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)


def prepare_startup():
    print("[System] Preparing vector store...")
    ensure_vector_store()
    print("[System] Vector store is ready.")


if __name__ == "__main__":
    prepare_startup()
    uvicorn.run(
        app,
        host=os.getenv("GRADIO_SERVER_NAME", "0.0.0.0"),
        port=int(os.getenv("GRADIO_SERVER_PORT", "7860")),
    )
