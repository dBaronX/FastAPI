#  bot.py final

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import os
import requests
from dotenv import load_dotenv

load_dotenv()

API = os.getenv("FASTAPI_URL")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not API:
    raise Exception("FASTAPI_URL not set")
if not TOKEN:
    raise Exception("TELEGRAM_BOT_TOKEN not set")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to dBaronX!\n\n"
        "Commands:\n"
        "/presale - Join DBX Presale\n"
        "/dreams - View crowdfunding dreams\n"
        "/story <prompt> - Generate AI story\n"
        "/mycommitment <wallet> - Check your presale\n"
        "/earn - Get daily ads"
    )

async def presale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Join DBX Presale:\nhttps://dbaronx.com/presale")

async def dreams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get(f"{API}/dreams")
        res.raise_for_status()
        data = res.json()
        text = "Dreams:\n\n"
        for d in data:
            text += f"{d['title']}\nRaised: {d['raised']}\nGoal: {d['goal']}\n\n"
        await update.message.reply_text(text)
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /story your idea here")
        return
    prompt = " ".join(context.args)
    try:
        res = requests.post(f"{API}/ai/story", json={"prompt": prompt})
        res.raise_for_status()
        data = res.json()
        await update.message.reply_text(f"{data.get('provider', 'AI')}: {data.get('story', 'No story returned')}")
    except Exception as e:
        await update.message.reply_text(f"Error generating story: {str(e)}")

async def mycommitment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /mycommitment <wallet>")
        return
    wallet = context.args[0]
    try:
        res = requests.get(f"{API}/user/{wallet}")
        res.raise_for_status()
        data = res.json()
        await update.message.reply_text(f"Wallet: {data.get('wallet_address')}\nAmount: {data.get('commitment_amount')}\nStatus: {data.get('status')}")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def earn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = str(update.effective_user.id)
    try:
        res = requests.get(f"{API}/ads", headers={"telegram_id": telegram_id})
        res.raise_for_status()
        ads = res.json()
        await update.message.reply_text(f"Here are your daily ads. Watch one and reply /confirm <ad_id>\n\n{ads}")
    except Exception as e:
        await update.message.reply_text(f"Error fetching ads: {str(e)}")

def run():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("presale", presale))
    app.add_handler(CommandHandler("dreams", dreams))
    app.add_handler(CommandHandler("story", story))
    app.add_handler(CommandHandler("mycommitment", mycommitment))
    app.add_handler(CommandHandler("earn", earn))
    print("🤖 dBaronX Bot running...")
    app.run_polling()

if __name__ == "__main__":
    run()