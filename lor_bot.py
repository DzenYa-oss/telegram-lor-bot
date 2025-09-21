import os
import asyncio
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Переменные окружения ---
# Не забудь добавить их в настройки Render (Environment Variables).
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
# --- Инициализация Flask-приложения ---
flask_app = Flask(__name__)
# --- Инициализация Telegram Application ---
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
    # Если сообщение от администратора, и оно является ответом на другое сообщение.
    if user.id == ADMIN_ID and update.message.reply_to_message:
        original_message = update.message.reply_to_message
        # Проверяем, было ли исходное сообщение переслано ботом.
        if original_message.forward_from and original_message.forward_from.id == bot_app.bot.id:
            # Получаем ID пользователя из пересланного сообщения.
            user_to_reply_id = original_message.forward_from_chat.id
            # Отправляем ответ пользователю.
            await context.bot.send_message(
                chat_id=user_to_reply_id,
                text=f"👨‍⚕️ Ответ врача:\n\n{text}"
            )
            await update.message.reply_text("✅ Ответ отправлен пользователю!")
            return
    # Если это обычное сообщение от пользователя (не от админа и не ответ на пересланное).
    if user.id != ADMIN_ID:
        if text == "✍️ Задать вопрос":
            await update.message.reply_text("Пожалуйста, напишите свой вопрос 👇")
            return
        # Отправляем сообщение администратору, пересылая исходное сообщение.
        # Это нужно, чтобы администратор мог "ответить" на него и бот знал, кому отправлять ответ.
        await update.message.reply_text("✅ Спасибо за вопрос! Врач обязательно посмотрит его 👨‍⚕️")
        await context.bot.forward_message(
            chat_id=ADMIN_ID,
            from_chat_id=user.id,
            message_id=update.message.message_id
        )
# Регистрируем хэндлеры в нашем приложении.
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
# --- Webhook ---
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
