import os, secrets, asyncio
from collections import deque
from typing import Any
import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app=FastAPI(title="Jarvis")
app.mount("/web",StaticFiles(directory="web"),name="web")
tasks=deque()
results={}
lock=asyncio.Lock()

class Chat(BaseModel):
    message:str
class Decision(BaseModel):
    approved:bool
class AgentResult(BaseModel):
    task_id:str
    result:str

def check(token,expected):
    if not expected or not token or not secrets.compare_digest(token,expected):
        raise HTTPException(401,"Unauthorized")

@app.get("/")
def home():
    return FileResponse("web/index.html")

@app.post("/api/chat")
async def chat(body:Chat, authorization:str|None=Header(default=None)):
    check(authorization.removeprefix("Bearer ") if authorization else None,os.getenv("JARVIS_ACCESS_TOKEN"))
    key=os.getenv("OPENAI_API_KEY")
    if not key: return {"reply":"AI xizmati hali sozlanmagan. Railway’da OPENAI_API_KEY kiriting."}
    tool={"type":"function","name":"desktop_action","description":"Kompyuterda bajariladigan amal. Har doim aniq va kichik amal tanla.","parameters":{"type":"object","properties":{"action":{"type":"string","enum":["open_url","launch_app","type_text","hotkey"]},"value":{"type":"string"}},"required":["action","value"],"additionalProperties":False},"strict":True}
    async with httpx.AsyncClient(timeout=60) as c:
        r=await c.post("https://api.openai.com/v1/responses",headers={"Authorization":f"Bearer {key}"},json={"model":os.getenv("OPENAI_MODEL","gpt-4.1-mini"),"instructions":"Sen foydalanuvchining shaxsiy Jarvis yordamchisisan. O‘zbekcha javob ber. Internet qidiruvi uchun web_search ishlat. Kompyuter amali kerak bo‘lsa desktop_action chaqir; u foydalanuvchi tasdiqlamaguncha bajarilmaydi. Fayl o‘chirish, to‘lov yoki xabar yuborishni taklif qilma.", "input":body.message,"tools":[{"type":"web_search"},tool]})
        r.raise_for_status(); data=r.json()
    pending=[]
    for item in data.get("output",[]):
        if item.get("type")=="function_call" and item.get("name")=="desktop_action":
            import json
            task_id=secrets.token_urlsafe(12)
            async with lock: results[task_id]={"args":json.loads(item["arguments"]),"status":"approval"}
            pending.append({"id":task_id,**results[task_id]["args"]})
    reply=data.get("output_text","")
    if pending: reply += "\nKompyuter amalini bajarish uchun quyidagi tasdiqlash tugmasini bosing."
    return {"reply":reply,"pending":pending}

@app.post("/api/desktop/{task_id}")
async def approve(task_id:str,body:Decision,authorization:str|None=Header(default=None)):
    check(authorization.removeprefix("Bearer ") if authorization else None,os.getenv("JARVIS_ACCESS_TOKEN"))
    async with lock:
        t=results.get(task_id)
        if not t or t["status"]!="approval": raise HTTPException(404,"Task not found")
        t["status"]="queued" if body.approved else "denied"
        if body.approved: tasks.append({"id":task_id,**t["args"]})
    return {"status":t["status"]}

@app.post("/agent/next")
async def agent_next(x_jarvis_agent_key:str|None=Header(default=None)):
    check(x_jarvis_agent_key,os.getenv("JARVIS_AGENT_KEY"))
    async with lock: return tasks.popleft() if tasks else {"id":None}

@app.post("/agent/result")
async def agent_result(body:AgentResult,x_jarvis_agent_key:str|None=Header(default=None)):
    check(x_jarvis_agent_key,os.getenv("JARVIS_AGENT_KEY"))
    async with lock:
        if body.task_id in results: results[body.task_id].update(status="done",result=body.result)
    return {"ok":True}
