
import logging
import os
from telegram import (
    Update,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)
from flask import Flask

# Включаем логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Переменные окружения
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

# Состояния для ConversationHandler
TITLE, DESCRIPTION, CATEGORY, BUDGET, CITY = range(5)

# Flask
app_flask = Flask(__name__)

@app_flask.route("/")
def index():
    return "Бот работает."

# Меню кнопок
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📝 Разместить заказ", callback_data="create_order")],
        [InlineKeyboardButton("📜 Правила", callback_data="rules")],
        [InlineKeyboardButton("ℹ️ О сервисе", callback_data="about")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args and args[0] == "create_order":
        await update.message.reply_text(
            "Вы выбрали размещение заказа. Введите заголовок заказа:",
            reply_markup=ReplyKeyboardRemove()
        )
        return TITLE

    await update.message.reply_text(
        "Добро пожаловать! Выберите пункт меню:",
        reply_markup=get_main_menu()
    )
    return ConversationHandler.END

# Обработка меню
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'create_order':
        await query.message.reply_text(
            "Введите заголовок заказа:",
            reply_markup=ReplyKeyboardRemove()
        )
        return TITLE

    await query.edit_message_text(
        f"Вы выбрали: {query.data}",
        reply_markup=get_main_menu()
    )
    return ConversationHandler.END

# Сбор данных заказа
async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text
    await update.message.reply_text("Введите описание заказа:")
    return DESCRIPTION

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    await update.message.reply_text("Введите категорию (Сайты, IT разработка, Нейросети, Дизайн, Маркетинг, Проектирование, Тендеры, Юристы):")
    return CATEGORY

async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["category"] = update.message.text
    await update.message.reply_text("Введите бюджет / часы работы:")
    return BUDGET

async def get_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["budget"] = update.message.text
    await update.message.reply_text("Введите город:")
    return CITY

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text

    order_text = (
        f"📝 Новый заказ!

"
        f"**{context.user_data['title']}**

"
        f"{context.user_data['description']}

"
        f"🏷 Категория: {context.user_data['category']}
"
        f"💰 Бюджет: {context.user_data['budget']}
"
        f"📍 Город: {context.user_data['city']}"
    )

    await update.message.reply_text("Ваш заказ опубликован!")

    await context.bot.send_message(
        chat_id=CHANNEL_USERNAME,
        text=order_text,
        parse_mode="Markdown"
    )

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# Публикация закрепленного поста
async def post_menu_to_channel(application):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Разместить заказ", url="https://t.me/FTM_menu_user_Bot?start=create_order")],
        [InlineKeyboardButton("📜 Правила", url="https://t.me/FTM_menu_user_Bot")],
        [InlineKeyboardButton("ℹ️ О сервисе", url="https://t.me/FTM_menu_user_Bot")]
    ])
    message = await application.bot.send_message(
        chat_id=CHANNEL_USERNAME,
        text="Это закрепленное сообщение. Выберите действие:",
        reply_markup=keyboard
    )
    await application.bot.pin_chat_message(
        chat_id=CHANNEL_USERNAME,
        message_id=message.message_id,
        disable_notification=True
    )

# Основной запуск
async def run_bot():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))

    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_menu, pattern="^create_order$")],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_category)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_budget)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_city)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(order_conv)
    application.add_handler(CallbackQueryHandler(handle_menu))

    await post_menu_to_channel(application)
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot())
    app_flask.run(host="0.0.0.0", port=10000)
