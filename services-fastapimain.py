#  apps/services-fastapi/services-fastapimain.py

@app.post("/payment/confirm")
async def confirm_payment(req: Request):
    data = await req.json()

    # Example: update presale or dreams
    supabase.table("presale_commitments").update({
        "status": "paid"
    }).eq("payment_id", data["paymentId"]).execute()

    return {"ok": True}