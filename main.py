import os
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Flask для Render
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return '✅ Flask работает. Telegram-бот тоже.'

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

# Обработка /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать! Выберите пункт меню:", reply_markup=get_main_menu())

# Обработка кнопок
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(f"Вы выбрали: {query.data}")

# Telegram бот
async def run_bot():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ Не задан BOT_TOKEN")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_menu))

    print("🤖 Telegram-бот запущен...")
    await app.run_polling()

# Flask-сервер в фоновом потоке
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# Старт
if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    asyncio.run(run_bot())
