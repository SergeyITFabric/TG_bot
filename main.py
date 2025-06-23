import os
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Flask HTTP-сервер для Render
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return '✅ Бот активен и работает на Render'

# Функция меню
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
    await update.message.reply_text(
        "Добро пожаловать! Выберите пункт меню:",
        reply_markup=get_main_menu()
    )

# Обработка кнопок
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data

    if action == 'create_order':
        await query.edit_message_text("📝 Форма создания заказа (в разработке)")
    elif action == 'find_order':
        await query.edit_message_text("📁 Выбор категории (в разработке)")
    elif action == 'resources':
        await query.edit_message_text("🔧 Ресурсы: аренда, прокат, рабочие (в разработке)")
    elif action == 'referral':
        user_id = query.from_user.id
        referral_link = f"https://t.me/YOUR_BOT_USERNAME?start={user_id}"
        await query.edit_message_text(f"🤝 Ваша реферальная ссылка:\n{referral_link}")
    elif action == 'faq':
        await query.edit_message_text("❓ Часто задаваемые вопросы (в разработке)")
    elif action == 'support':
        await query.edit_message_text("👥 Связь с поддержкой: @your_support_contact")

# Асинхронный запуск Telegram-бота
async def run_telegram_bot():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ BOT_TOKEN не задан")
        return

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_menu))

    print("🤖 Telegram-бот запущен и ожидает сообщения...")
    await application.run_polling()

# Запуск Flask и Telegram параллельно
def start_bot():
    asyncio.run(run_telegram_bot())

if __name__ == '__main__':
    # Стартуем Telegram-бот в фоновом потоке
    Thread(target=start_bot).start()

    # Запускаем Flask-сервер (требуется Render)
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)
