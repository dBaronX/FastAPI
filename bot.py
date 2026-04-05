import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

API = os.environ.get("FASTAPI_URL")

 if not API: raise Exception("FASTAPI_URL not set")
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

 if not TOKEN: raise Exception(TELEGRAM_BOT_TOKEN not set")
 
# BASIC COMMANDS
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🚀 Welcome to dBaronX\n\n"
        "Commands:\n"
        "/presale - Join DBX presale\n"
        "/dreams - View crowdfunding dreams\n"
        "/story <prompt> - Generate AI story\n"
        "/mycommitment <wallet> - Check your presale"
    )

async def presale(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 Join DBX Presale:\n"
        "https://dbaronx.com/presale"
    )

async def dreams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get(f"{API}/dreams").json()

        if not res:
            await update.message.reply_text("No dreams available.")
            return

        text = "🌍 Dreams:\n\n"
        for d in res:
            text += f"{d['title']}\n{d['raised']}/{d['goal']}\n\n"

        await update.message.reply_text(text)

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def story(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = " ".join(context.args)

    if not prompt:
        await update.message.reply_text("Usage: /story your idea")
        return

    try:
        res = requests.post(
            f"{API}/ai/story",
            json={"prompt": prompt}
        ).json()

        await update.message.reply_text(
            f"🤖 ({res['provider']})\n\n{res['story']}"
        )

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

async def mycommitment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /mycommitment <wallet>")
        return

    wallet = context.args[0]

    try:
        res = requests.get(f"{API}/user/{wallet}").json()

        if not res:
            await update.message.reply_text("No commitment found.")
            return

        data = res[0]

        await update.message.reply_text(
            f"💰 Commitment:\n\n"
            f"Wallet: {data['wallet_address']}\n"
            f"Amount: ${data['commitment_amount']}\n"
            f"Status: {data['status']}"
        )

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# RUN BOT
def run():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("presale", presale))
    app.add_handler(CommandHandler("dreams", dreams))
    app.add_handler(CommandHandler("story", story))
    app.add_handler(CommandHandler("mycommitment", mycommitment))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    run()