import os
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Flask-сервер для Render
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return '✅ Telegram-бот работает через Flask + PTB'

# Главное меню
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📝 Разместить Заказ", callback_data='create_order')],
        [InlineKeyboardButton("🔍 Найти Заказ. Категории", callback_data='find_order')],
        [InlineKeyboardButton("🛠 Ресурсы: Аренда. Прокат. Рабочие.", callback_data='resources')],
        [InlineKeyboardButton("🤝 Реферальная программа", callback_data='referral')],
        [InlineKeyboardButton("❓ Вопросы и ответы", callback_data='faq')],
        [InlineKeyboardButton("❤️ Служба заботы", callback_data='support')],
    ]
    return InlineKeyboardMarkup(keyboard)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Добро пожаловать! Выберите пункт меню:", reply_markup=get_main_menu())

# Обработка кнопок
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(f"Вы выбрали: {query.data}")

# Публикация меню в канал и закрепление
async def post_menu_to_channel(application):
    channel_username = os.getenv("CHANNEL_USERNAME")  # Пример: @free_time_money
    if not channel_username:
        print("⚠️ Не указана переменная CHANNEL_USERNAME")
        return

    keyboard = get_main_menu()
    message = await application.bot.send_message(
        chat_id=channe_
