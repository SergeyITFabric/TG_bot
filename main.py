import os
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Flask сервер
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return '✅ Telegram-бот работает!'

# Главное меню
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📨 Разместить Заказ", callback_data='create_order')],
        [InlineKeyboardButton("📁 Найти Заказ. Категории", callback_data='find_order')],
        [InlineKeyboardButton("🔧 Ресурсы: Аренда. Прокат. Рабочие.", callback_data='resources')],
        [InlineKeyboardButton("🤝 Реферальная программа", callback_data='referral')],
        [InlineKeyboardButton("❓ Вопросы и ответы", callback_data='faq')],
        [InlineKeyboardButton("👥 Служба заботы", callback_data='support')],
    ]
    return InlineKeyboardMarkup(keyboard)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать! Выберите пункт меню:", reply_markup=get_main_menu())

# Кнопки
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(f"Вы выбрали: {query.data}")

# Асинхронный запуск Telegram-бота (НЕ через asyncio.run)
async def run_bot():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN не указан.")
        return
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_menu))
    print("🤖 Telegram-бот запущен.")
    await app.run_polling()

# Flask в потоке
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# Точка входа
if __name__ == '__main__':
    # Стартуем Flask отдельно
    threading.Thread(target=run_flask).start()

    # Используем уже активный loop и запускаем бот в фоне
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())
    loop.run_forever()
