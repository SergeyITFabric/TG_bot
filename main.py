import os
import logging
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from flask import Flask
import threading

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Переменные
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@free_time_money"

CATEGORIES = [
    "Сайты", "IT разработка", "Нейросети",
    "Дизайн", "Маркетинг", "Проектирование",
    "Тендеры", "Юристы"
]

(
    ORDER_TITLE, ORDER_DESCRIPTION, ORDER_CATEGORY,
    ORDER_BUDGET, ORDER_CITY
) = range(5)

# Главное меню
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("Разместить Заказ", callback_data="place_order")],
        [InlineKeyboardButton("Найти Заказ. Категории", callback_data="find_order")],
        [InlineKeyboardButton("Ресурсы: Аренда. Прокат. Рабочие.", callback_data="resources")],
        [InlineKeyboardButton("Реферальная программа", callback_data="referral")],
        [InlineKeyboardButton("Вопросы и ответы", callback_data="faq")],
        [InlineKeyboardButton("Служба заботы", callback_data="support")],
    ]
    return InlineKeyboardMarkup(keyboard)

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать! Выберите действие:",
        reply_markup=main_menu_keyboard()
    )

# Обработка нажатий
async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "place_order":
        await query.message.reply_text("Введите заголовок заказа:", reply_markup=ReplyKeyboardRemove())
        return ORDER_TITLE

    elif data == "find_order":
        await query.message.reply_text("Функционал в разработке.")

    elif data == "resources":
        await query.message.reply_text("Функционал в разработке.")

    elif data == "referral":
        link = f"https://t.me/{context.bot.username}?start={query.from_user.id}"
        await query.message.reply_text(
            f"Ваша реферальная ссылка:\n{link}"
        )

    elif data == "faq":
        await query.message.reply_text("Функционал в разработке.")

    elif data == "support":
        await query.message.reply_text("Функционал в разработке.")

    return ConversationHandler.END

# Шаги создания заказа
async def order_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text
    await update.message.reply_text("Введите описание заказа:")
    return ORDER_DESCRIPTION

async def order_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    keyboard = [[cat] for cat in CATEGORIES]
    await update.message.reply_text(
        "Выберите категорию:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return ORDER_CATEGORY

async def order_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["category"] = update.message.text
    await update.message.reply_text("Введите бюджет или часы работы:")
    return ORDER_BUDGET

async def order_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["budget"] = update.message.text
    await update.message.reply_text("Введите город:")
    return ORDER_CITY

async def order_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text

    title = context.user_data["title"]
    description = context.user_data["description"]
    category = context.user_data["category"]
    budget = context.user_data["budget"]
    city = context.user_data["city"]

    text = f"""
📝 <b>Новый заказ</b>

<b>Заголовок:</b> {title}
<b>Описание:</b> {description}
<b>Категория:</b> #{category}
<b>Бюджет / Часы:</b> {budget}
<b>Город:</b> #{city}
"""

    await context.bot.send_message(
        chat_id=CHANNEL_USERNAME,
        text=text,
        parse_mode="HTML"
    )

    await update.message.reply_text("Ваш заказ опубликован!", reply_markup=main_menu_keyboard())
    return ConversationHandler.END

# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Flask для Render
app = Flask(__name__)

@app.route("/")
def index():
    return "Бот запущен."

def run_flask():
    app.run(host="0.0.0.0", port=10000)

# Запуск бота
async def main():
    application = Application.builder().token(TOKEN).build()

    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_callback, pattern="^place_order$")],
        states={
            ORDER_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_title)],
            ORDER_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_description)],
            ORDER_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_category)],
            ORDER_BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_budget)],
            ORDER_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_city)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(menu_callback))
    application.add_handler(order_conv)

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
