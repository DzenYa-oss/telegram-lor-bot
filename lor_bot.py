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
    
    # Обработка ответа от администратора
    if user.id == ADMIN_ID and update.message.reply_to_message:
        original_message = update.message.reply_to_message
        
        # Проверяем, было ли исходное сообщение переслано ботом.
        if original_message.from_user and original_message.from_user.id == bot_app.bot.id:
            # Получаем ID пользователя из пересланного сообщения
            # Telegram API не предоставляет forward_from_chat для сообщений,
            # пересылаемых ботом, поэтому мы используем chat_id из update
            # и message_id из reply_to_message, чтобы найти оригинал.
            # Если бот переслал сообщение, то original_message.forward_from_chat будет None
            # Но мы можем получить user_id из reply_to_message.forward_from
            # Мы будем использовать context.user_data для сохранения id пользователя
            # чтобы избежать этой проблемы
            
            # Внимание: здесь мы полагаемся на то, что в пересланном сообщении
            # будет поле `forward_from`. Если его нет, то этот метод не сработает.
            # Я обновил код, чтобы использовать более надежный метод:
            # просто отправляем сообщение в ответ на пересланное.
            # Нам нужно сохранить chat_id в user_data, чтобы бот мог
            # его найти.
            
            # Более надежный способ - отправлять сообщение, содержащее chat_id
            # в тексте, но это менее удобно.
            
            # Временное решение:
            # Мы не можем получить chat_id пользователя из пересланного сообщения
            # так как оно не содержит forward_from. 
            # Я предлагаю изменить логику, чтобы бот отправлял вам сообщение 
            # с user_id в тексте, чтобы вы могли ответить.
            # await context.bot.send_message(
            #    chat_id=user_id, text=f"Ответ врача:\n\n{text}"
            # )
            # await update.message.reply_text("✅ Ответ отправлен пользователю!")

            # Нам нужен chat_id, чтобы отправить ответ. Давайте попробуем получить его
            # из оригинального пересланного сообщения.
            # В текущей реализации bot.forward_message не сохраняет `forward_from`.
            # Это известная проблема.
            
            # Мы исправим логику отправки сообщения, чтобы избежать этой проблемы.
            # Вместо `forward_message` мы будем отправлять обычное сообщение с user_id.
            
            # Обновляем логику отправки сообщений, чтобы было проще отвечать.
            # Этот блок кода будет работать только с новой логикой
            # поэтому мы его изменим.
            pass

    # Если это обычное сообщение от пользователя (не от админа).
    if user.id != ADMIN_ID:
        if text == "✍️ Задать вопрос":
            await update.message.reply_text("Пожалуйста, напишите свой вопрос 👇")
            return
            
        # Отправляем сообщение администратору, включая ID пользователя.
        # Это более надежный способ, чем полагаться на forward_message.
        
        # Отправляем пользователю подтверждение
        await update.message.reply_text("✅ Спасибо за вопрос! Врач обязательно посмотрит его 👨‍⚕️")
        
        # Формируем сообщение для админа, включая ID пользователя
        admin_message = f"📩 Вопрос от @{user.username or user.id} (ID: {user.id}):\n\n{text}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_message)

    # Если сообщение от администратора (не ответ на пересланное)
    # и оно не содержит user_id, то ничего не делаем.
    if user.id == ADMIN_ID and "ID:" in text:
        try:
            # Парсим user_id из текста сообщения
            user_id = int(text.split("ID: ")[1].split("\n")[0])
            reply_text = text.split("\n\n")[1]
            
            # Отправляем ответ пользователю
            await context.bot.send_message(chat_id=user_id, text=f"👨‍⚕️ Ответ врача:\n\n{reply_text}")
            await update.message.reply_text("✅ Ответ отправлен пользователю!")
        except (ValueError, IndexError):
            await update.message.reply_text("❌ Не удалось отправить ответ. Убедитесь, что сообщение содержит ID пользователя и текст ответа.")

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
