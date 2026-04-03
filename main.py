import os
from fastapi import FastAPI, Request, HTTPException
from supabase import create_client
from dotenv import load_dotenv
from slowapi import Limiter
from slowapi.util import get_remote_address
from ai_router import generate_story

# 🔹 LOAD ENV
load_dotenv()

app = FastAPI()

# 🔹 RATE LIMITER
limiter = Limiter(key_func=get_remote_address)

# 🔹 INIT SUPABASE
supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)

# 🔹 ROOT
@app.get("/")
def root():
    return {"status": "dBaronX services running 🚀"}

# =========================
# 🔹 PRESALE (ZOHO WEBHOOK)
# =========================
@app.post("/presale")
@limiter.limit("10/minute")
async def presale(req: Request):
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

# =========================
# 🔹 DREAMS (CREATE)
# =========================
@app.post("/dreams")
@limiter.limit("10/minute")
async def create_dream(req: Request):
    data = await req.json()

    title = data.get("title")
    goal = data.get("goal")

    if not title or not goal:
        raise HTTPException(status_code=400, detail="Missing fields")

    supabase.table("dreams").insert({
        "title": title,
        "description": data.get("description"),
        "goal": goal,
        "raised": 0
    }).execute()

    return {"ok": True}

# =========================
# 🔹 LIST DREAMS
# =========================
@app.get("/dreams")
def list_dreams():
    res = supabase.table("dreams").select("*").execute()
    return res.data

# =========================
# 🔹 BACK DREAM
# =========================
@app.post("/dreams/back")
@limiter.limit("10/minute")
async def back_dream(req: Request):
    data = await req.json()

    dream_id = data.get("dream_id")
    amount = data.get("amount")

    if not dream_id or not amount:
        raise HTTPException(status_code=400, detail="Missing fields")

    current = supabase.table("dreams").select("raised").eq("id", dream_id).single().execute()

    if not current.data:
        raise HTTPException(status_code=404, detail="Dream not found")

    new_amount = current.data["raised"] + amount

    supabase.table("dreams").update({
        "raised": new_amount
    }).eq("id", dream_id).execute()

    return {"ok": True}

# =========================
# 🔹 AI STORIES (MULTI-AI)
# =========================
@app.post("/ai/story")
@limiter.limit("20/minute")
async def ai_story(req: Request):
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

    return {
        "story": story,
        "provider": provider
    }

# =========================
# 🔹 USER LOOKUP (TELEGRAM)
# =========================
@app.get("/user/{wallet}")
def get_user(wallet: str):
    res = supabase.table("presale_commitments").select("*").eq("wallet_address", wallet).execute()
    return res.data