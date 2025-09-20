import os
import asyncio
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Переменные окружения.
# Не забудь добавить их в настройки Render (Environment Variables).
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Инициализация Flask-приложения.
flask_app = Flask(__name__)

# Инициализация Telegram Application.
# Мы не используем updater, так как работаем с вебхуками.
bot_app = Application.builder().token(TOKEN).build()

# --- Хэндлеры (обработчики команд и сообщений) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправляет приветственное сообщение с кнопкой."""
    keyboard = [[KeyboardButton("✍️ Задать вопрос")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text(
        "👋 Добро пожаловать! Я ассистент врача.\n\n"
        "Нажмите кнопку ниже или просто напишите свой вопрос доктору:",
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовые сообщения от пользователя."""
    user = update.effective_user
    text = update.message.text

    if text == "✍️ Задать вопрос":
        await update.message.reply_text("Пожалуйста, напишите свой вопрос 👇")
        return

    # Отправляем сообщение администратору.
    await update.message.reply_text("✅ Спасибо за вопрос! Врач обязательно посмотрит его 👨‍⚕️")
    msg = f"📩 Вопрос от @{user.username or user.id}:\n\n{text}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

# Регистрируем хэндлеры в нашем приложении.
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# --- Webhook ---

# Этот маршрут будет принимать POST-запросы от Telegram.
@flask_app.route("/", methods=["POST"])
async def webhook_handler():
    """Обрабатывает входящие обновления от Telegram."""
    async with bot_app:
        await bot_app.process_update(
            Update.de_json(request.get_json(force=True), bot_app.bot)
        )
    return "ok"

# --- Запуск приложения ---

if __name__ == '__main__':
    # Эта команда запускает Flask-сервер в режиме отладки.
    # В реальном приложении на Render он будет запускаться Gunicorn или Uvicorn.
    flask_app.run(port=8000)
