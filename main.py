import os
from fastapi import FastAPI, Request, HTTPException, Depends
from supabase import create_client
from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.util import get_remote_address
from ai_router import generate_story

load_dotenv()

PORT = int(os.getenv("PORT", 8000))

app = FastAPI(title="dBaronX Services")

limiter = Limiter(key_func=get_remote_address)

def rate_limit():
    return limiter

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Missing SUPABASE_URL or SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/")
def root():
    return {
        "status": "dBaronX services running",
        "environment": os.getenv("ENVIRONMENT", "production")
    }

@app.post("/presale")
async def presale(req: Request, _=Depends(rate_limit)):
    data = await req.json()
    wallet = data.get("wallet")
    amount = data.get("commitment_amount")

    if not wallet or not amount:
        raise HTTPException(status_code=400, detail="Missing wallet or amount")

    res = supabase.table("presale_commitments").insert({
        "wallet_address": wallet,
        "commitment_amount": amount,
        "status": "pending"
    }).execute()

    return {"ok": True, "data": res.data}

@app.post("/dreams")
async def create_dream(req: Request, _=Depends(rate_limit)):
    data = await req.json()
    title = data.get("title")
    goal = data.get("goal")

    if not title or not goal:
        raise HTTPException(status_code=400, detail="Missing title or goal")

    res = supabase.table("dreams").insert({
        "title": title,
        "description": data.get("description"),
        "goal": goal,
        "raised": 0
    }).execute()

    return {"ok": True, "data": res.data}

@app.get("/dreams")
def list_dreams():
    res = supabase.table("dreams").select("*").execute()
    return res.data

@app.post("/dreams/back")
async def back_dream(req: Request, _=Depends(rate_limit)):
    data = await req.json()
    dream_id = data.get("dream_id")
    amount = data.get("amount")

    if not dream_id or not amount:
        raise HTTPException(status_code=400, detail="Missing dream_id or amount")

    current = supabase.table("dreams").select("raised").eq("id", dream_id).single().execute()

    if not current.data:
        raise HTTPException(status_code=404, detail="Dream not found")

    new_amount = current.data["raised"] + amount

    supabase.table("dreams").update({"raised": new_amount}).eq("id", dream_id).execute()

    return {"ok": True}

@app.post("/ai/story")
async def ai_story(req: Request, _=Depends(rate_limit)):
    data = await req.json()
    prompt = data.get("prompt")

    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt required")

    story, provider = generate_story(prompt)

    supabase.table("ai_stories").insert({
        "prompt": prompt,
        "story": story,
        "provider": provider
    }).execute()

    return {"story": story, "provider": provider}

@app.get("/user/{wallet}")
def get_user(wallet: str):
    res = supabase.table("presale_commitments").select("*").eq("wallet_address", wallet).execute()
    return res.data

@app.post("/payment/confirm")
async def confirm_payment(req: Request):
    data = await req.json()
    return {"ok": True}

if name == "main":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)