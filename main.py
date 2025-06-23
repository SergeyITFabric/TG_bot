import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Получаем токен из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")

# Инициализация Flask
app_web = Flask(__name__)

@app_web.route("/")
def home():
    return "✅ Telegram бот работает на Render!"

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

# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать! Выберите пункт меню:",
        reply_markup=get_main_menu()
    )

# Обработка нажатий
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

# Telegram-бот в отдельном потоке
def run_telegram_bot():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_menu))
    print("🤖 Бот запущен...")
    application.run_polling()

if __name__ == '__main__':
    # Запускаем телеграм-бота в отдельном потоке
    threading.Thread(target=run_telegram_bot).start()

    # Flask Web Server (Render требует открытый порт)
    port = int(os.environ.get("PORT", 10000))  # Render подставляет PORT
    app_web.run(host="0.0.0.0", port=port)
