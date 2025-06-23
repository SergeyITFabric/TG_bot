import os
import asyncio
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Инициализация Flask
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return '✅ Бот работает. Render видит порт.'

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
    await update.message.reply_text(
        "Добро пожаловать! Выберите пункт меню:",
        reply_markup=get_main_menu()
    )

# Обработка нажатий на кнопки
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
        link = f"https://t.me/YOUR_BOT_USERNAME?start={user_id}"
        await query.edit_message_text(f"🤝 Ваша реферальная ссылка:\n{link}")
    elif action == 'faq':
        await query.edit_message_text("❓ Часто задаваемые вопросы (в разработке)")
    elif action == 'support':
        await query.edit_message_text("👥 Связь с поддержкой: @your_support_contact")

# Асинхронный запуск Telegram-бота
async def run_bot():
    token = os.getenv("BOT_TOKEN")
    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_menu))
    print("🤖 Бот запущен")
    await application.run_polling()

# Запуск Flask + Telegram параллельно
def run():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(run_bot())

    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

if __name__ == '__main__':
    run()
