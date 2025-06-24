import logging
import asyncio
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes
)
from flask import Flask

# ============ НАСТРОЙКИ ============
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
CHANNEL_USERNAME = '@YOUR_CHANNEL_USERNAME'
WELCOME_TEXT = "👋 Добро пожаловать! Выберите действие:"
CATEGORIES = ['Сайты', 'IT разработка', 'Нейросети', 'Дизайн', 'Маркетинг', 'Проектирование', 'Тендеры', 'Юристы']

# ============ ЛОГИ ============
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============ Flask ============
app_flask = Flask(__name__)

@app_flask.route("/")
def hello():
    return "Bot is running!"

# ============ Состояния ============
TITLE, DESCRIPTION, CATEGORY, BUDGET, CITY = range(5)

# ============ Кнопки меню ============
def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 Разместить заказ", callback_data="order")],
        [InlineKeyboardButton("👨‍💻 Отклики на заказы", callback_data="responses")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ============ Хендлеры ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        text=WELCOME_TEXT,
        reply_markup=main_menu_keyboard()
    )

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "order":
        await query.message.reply_text("Введите заголовок заказа:", reply_markup=ReplyKeyboardRemove())
        return TITLE
    elif query.data == "responses":
        await query.message.reply_text("Раздел в разработке.")
    elif query.data == "help":
        await query.message.reply_text("Помощь по использованию бота.")

    return ConversationHandler.END

# ============ Сбор данных ============
async def title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text
    await update.message.reply_text("Введите описание заказа:")
    return DESCRIPTION

async def description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    keyboard = [[category] for category in CATEGORIES]
    await update.message.reply_text(
        "Выберите категорию:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CATEGORY

async def category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["category"] = update.message.text
    await update.message.reply_text("Укажите бюджет или часы работы:")
    return BUDGET

async def budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["budget"] = update.message.text
    await update.message.reply_text("Укажите город:")
    return CITY

async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text

    title = context.user_data["title"]
    description = context.user_data["description"]
    category = context.user_data["category"]
    budget = context.user_data["budget"]
    city = context.user_data["city"]

    post_text = (
        f"📝 <b>{title}</b>\n\n"
        f"{description}\n\n"
        f"💼 Категория: <b>{category}</b>\n"
        f"💰 Бюджет / Часы работы: <b>{budget}</b>\n"
        f"📍 Город: <b>{city}</b>\n\n"
        f"#{category.replace(' ', '_')} #{city.replace(' ', '_')}"
    )

    await context.bot.send_message(
        chat_id=CHANNEL_USERNAME,
        text=post_text,
        parse_mode="HTML"
    )

    await update.message.reply_text("✅ Заказ опубликован в канале!", reply_markup=main_menu_keyboard())

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

# ============ Запуск ============
async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_menu))

    order_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_menu, pattern="^order$")],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, category)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(order_conv)

    print("🤖 Бот запущен...")
    await app.run_polling()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    app_flask.run(host="0.0.0.0", port=10000)
