import os
import asyncio
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# === Переменные окружения ===
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Flask-приложение для Render + Gunicorn
flask_app = Flask(__name__)

# Telegram Application
bot_app = Application.builder().token(TOKEN).build()

# --- Хэндлеры ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("✍️ Задать вопрос")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Добро пожаловать! Я бот-врач.\nНажмите кнопку или напишите вопрос:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    if text == "✍️ Задать вопрос":
        await update.message.reply_text("Пожалуйста, напишите свой вопрос 👇")
        return

    await update.message.reply_text("✅ Спасибо за вопрос! Врач обязательно посмотрит его 👨‍⚕️")
    msg = f"📩 Вопрос от @{user.username or user.id}:\n\n{text}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

# Регистрируем хэндлеры
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- Webhook обработчик ---
@flask_app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    await bot_app.process_update(update)
    return "ok"

# Инициализация бота
loop = asyncio.get_event_loop()
loop.create_task(bot_app.initialize())
loop.create_task(bot_app.start())

async def set_webhook():
    await bot_app.bot.set_webhook(url=f"https://<YOUR_RENDER_DOMAIN>/{TOKEN}")

loop.create_task(set_webhook())
