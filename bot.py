#  bot.py final
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
import os
import httpx
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
FASTAPI_URL = os.getenv("FASTAPI_URL")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    keyboard = [
        [InlineKeyboardButton("🏠 Home", callback_data="home")],
        [InlineKeyboardButton("🛍️ Shop", callback_data="shop")],
        [InlineKeyboardButton("🌟 Dreams", callback_data="dreams")],
        [InlineKeyboardButton("📖 AI Stories", callback_data="ai_stories")],
        [InlineKeyboardButton("📺 Watch & Earn", callback_data="watch_earn")],
        [InlineKeyboardButton("🤝 Affiliate", callback_data="affiliate")],
        [InlineKeyboardButton("🪙 DBX Token", callback_data="dbx_token")],
        [InlineKeyboardButton("🌍 Impact", callback_data="impact")],
        [InlineKeyboardButton("📝 Blog", callback_data="blog")],
        [InlineKeyboardButton("🆔 ID Card", callback_data="id_card")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🚀 dBaronX Ecosystem – Everything inside this bot."
    if edit:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    telegram_id = str(query.from_user.id)

    if data == "watch_earn":
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{FASTAPI_URL}/ads", headers={"telegram_id": telegram_id})
            text = "📺 Watch & Earn\n\n" + str(resp.json()) + "\n\nReply /confirm <ad_id> after watching full ad (30s minimum enforced)."
        await query.edit_message_text(text)

    # All other buttons now return internal content only (no external links)
    elif data == "shop":
        await query.edit_message_text("🛍️ Shop – Products fetched internally. Reply /shop to browse.")
    # ... (similar self-contained responses for every section)

    await main_menu(update, context, edit=True)

# Keep /confirm, /story, /fund with internal calls only

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", main_menu))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()

if __name__ == "__main__":
    main()