import os
from fastapi import FastAPI, Request, HTTPException
from supabase import create_client
from openai import OpenAI

app = FastAPI()

# ✅ INIT
supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

@app.get("/")
def root():
    return {"status": "services running"}

# 🔹 PRESALE (Zoho webhook)
@app.post("/presale")
async def presale(req: Request):
    data = await req.json()

    wallet = data.get("wallet")
    amount = data.get("commitment_amount")

    if not wallet or not amount:
        raise HTTPException(status_code=400, detail="Missing fields")

    res = supabase.table("presale_commitments").insert({
        "wallet_address": wallet,
        "commitment_amount": amount,
        "status": "pending"
    }).execute()

    return {"ok": True, "data": res.data}

# 🔹 DREAMS (CREATE)
@app.post("/dreams")
async def create_dream(req: Request):
    data = await req.json()

    supabase.table("dreams").insert({
        "title": data.get("title"),
        "description": data.get("description"),
        "goal": data.get("goal"),
        "raised": 0
    }).execute()

    return {"ok": True}

# 🔹 LIST DREAMS
@app.get("/dreams")
def list_dreams():
    res = supabase.table("dreams").select("*").execute()
    return res.data

# 🔹 BACK DREAM (FIXED)
@app.post("/dreams/back")
async def back_dream(req: Request):
    data = await req.json()

    dream_id = data.get("dream_id")
    amount = data.get("amount")

    # get current value
    current = supabase.table("dreams").select("raised").eq("id", dream_id).single().execute()

    new_amount = current.data["raised"] + amount

    supabase.table("dreams").update({
        "raised": new_amount
    }).eq("id", dream_id).execute()

    return {"ok": True}

# 🔹 AI STORIES (UPDATED API)
@app.post("/ai/story")
async def ai_story(req: Request):
    data = await req.json()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": data["prompt"]}]
    )

    story = response.choices[0].message.content

    supabase.table("ai_stories").insert({
        "prompt": data["prompt"],
        "story": story
    }).execute()

    return {"story": story}

# 🔹 GET USER DATA (FOR TELEGRAM)
@app.get("/user/{wallet}")
def get_user(wallet: str):
    res = supabase.table("presale_commitments").select("*").eq("wallet_address", wallet).execute()
    return res.data