import os
import asyncio
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters
)

# Состояния формы заказа
(TITLE, DESCRIPTION, CATEGORY, BUDGET, CITY) = range(5)
CATEGORIES = ["Сайты", "IT разработка", "Нейросети", "Дизайн", "Маркетинг", "Проектирование", "Тендеры", "Юристы"]

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

# Обработка главного меню
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'create_order':
        await query.message.reply_text("Введите заголовок заказа:", reply_markup=ReplyKeyboardRemove())
        return TITLE
    await query.edit_message_text(f"Вы выбрали: {query.data}")

# Последовательность заполнения полей формы
async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("Введите описание заказа:")
    return DESCRIPTION

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    category_buttons = [[c] for c in CATEGORIES]
    await update.message.reply_text("Выберите категорию:", reply_markup=ReplyKeyboardMarkup(category_buttons, one_time_keyboard=True))
    return CATEGORY

async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['category'] = update.message.text
    await update.message.reply_text("Укажите бюджет или количество часов:", reply_markup=ReplyKeyboardRemove())
    return BUDGET

async def get_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['budget'] = update.message.text
    await update.message.reply_text("Введите город:")
    return CITY

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['city'] = update.message.text

    title = context.user_data['title']
    description = context.user_data['description']
    category = context.user_data['category']
    budget = context.user_data['budget']
    city = context.user_data['city']

    channel_username = os.getenv("CHANNEL_USERNAME")
    if not channel_username:
        await update.message.reply_text("Ошибка: не задано имя канала.")
        return ConversationHandler.END

    post = f"<b>{title}</b>\n\n{description}\n\n<b>Бюджет / Часы:</b> {budget}\n<b>Город:</b> {city}\n\n#{category.replace(' ', '')} #{city.replace(' ', '')}"
    await context.bot.send_message(chat_id=channel_username, text=post, parse_mode='HTML')

    await update.message.reply_text("Ваш заказ опубликован!", reply_markup=get_main_menu())
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.", reply_markup=get_main_menu())
    return ConversationHandler.END

# Публикация меню в канал и закрепление
async def post_menu_to_channel(application):
    channel_username = os.getenv("CHANNEL_USERNAME")
    if not channel_username:
        print("⚠️ Не указана переменная CHANNEL_USERNAME")
        return

    keyboard = get_main_menu()
    message = await application.bot.send_message(
        chat_id=channel_username,
        text="Это закреплённое приветственное сообщение. Оно сверху. Под ним — кнопки меню. \U0001F447\n\nВыберите действие:",
        reply_markup=keyboard
    )
    await application.bot.pin_chat_message(chat_id=channel_username, message_id=message.message_id, disable_notification=True)

# Запуск Telegram-бота
async def run_bot():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("❌ Не задан BOT_TOKEN")
        return

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_menu))

    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_menu, pattern='^create_order$')],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_category)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_budget)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(order_conv)

    print("🤖 Инициализация Telegram-бота...")
    await app.initialize()
    await app.start()
    await post_menu_to_channel(app)
    await app.updater.start_polling()

# Запуск Flask
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

# Главный вход
if __name__ == '__main__':
    threading.Thread(target=run_flask).start()
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())
    loop.run_forever()
