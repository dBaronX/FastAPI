import os
import requests
from telegram.ext import ApplicationBuilder, CommandHandler

API = os.environ["FASTAPI_URL"]
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

# 🔹 START
async def start(update, context):
    await update.message.reply_text("Welcome to dBaronX 🚀")

# 🔹 DREAMS
async def dreams(update, context):
    res = requests.get(f"{API}/dreams").json()

    if not res:
        await update.message.reply_text("No dreams available.")
        return

    text = "\n".join([
        f"{d['title']} ({d['raised']}/{d['goal']})"
        for d in res
    ])

    await update.message.reply_text(text)

# 🔹 AI STORY
async def story(update, context):
    prompt = " ".join(context.args)

    if not prompt:
        await update.message.reply_text("Usage: /story your idea")
        return

    res = requests.post(f"{API}/ai/story", json={"prompt": prompt}).json()
    await update.message.reply_text(res["story"])

# 🔹 PRESALE
async def presale(update, context):
    await update.message.reply_text(
        "Submit here: https://dbaronx.com/presale"
    )

# 🔹 MY COMMITMENT
async def mycommitment(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /mycommitment <wallet>")
        return

    wallet = context.args[0]
    res = requests.get(f"{API}/user/{wallet}").json()

    if not res:
        await update.message.reply_text("No data found.")
        return

    await update.message.reply_text(str(res))

# 🔹 RUN BOT
def run():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dreams", dreams))
    app.add_handler(CommandHandler("story", story))
    app.add_handler(CommandHandler("presale", presale))
    app.add_handler(CommandHandler("mycommitment", mycommitment))

    app.run_polling()

if __name__ == "__main__":
    run()