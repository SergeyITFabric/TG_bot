import logging
import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)
from flask import Flask

# Настройки
TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_USERNAME = os.getenv('CHANNEL_USERNAME')  # Пример: '@free_time_money'

# Категории для выбора
CATEGORIES = [
    "Сайты", "IT разработка", "Нейросети",
    "Дизайн", "Маркетинг", "Проектирование",
    "Тендеры", "Юристы"
]

# Состояния для ConversationHandler
(
    TITLE,
    DESCRIPTION,
    CATEGORY,
    BUDGET,
    CITY
) = range(5)

# Веб-сервер Flask для поддержки Render
app_web = Flask(__name__)


@app_web.route('/')
def home():
    return "Бот работает!"


# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


# Функция старта бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("➕ Разместить заказ", callback_data="create_order")],
        [InlineKeyboardButton("ℹ️ Правила", callback_data="rules")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Добро пожаловать! Выберите действие:",
        reply_markup=reply_markup
    )


# Обработка кнопок меню
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "create_order":
        await query.message.reply_text("Введите заголовок заказа:", reply_markup=ReplyKeyboardRemove())
        return TITLE

    if query.data == "rules":
        await query.message.reply_text(
            "Правила:\n\n"
            "1. Запрещено публиковать мошеннические заказы.\n"
            "2. Все сделки происходят напрямую между заказчиком и исполнителем.\n"
            "3. Биржа не несёт ответственности за результат сделки."
        )
        return ConversationHandler.END


# Этапы ввода данных
async def title_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text
    await update.message.reply_text("Опишите задание подробнее:")
    return DESCRIPTION


async def description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text

    keyboard = [
        [InlineKeyboardButton(cat, callback_data=cat)] for cat in CATEGORIES
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Выберите категорию:",
        reply_markup=reply_markup
    )
    return CATEGORY


async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["category"] = query.data
    await query.message.reply_text("Укажите бюджет или количество часов работы:")
    return BUDGET


async def budget_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["budget"] = update.message.text
    await update.message.reply_text("Укажите город:")
    return CITY


async def city_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text

    title = context.user_data["title"]
    description = context.user_data["description"]
    category = context.user_data["category"]
    budget = context.user_data["budget"]
    city = context.user_data["city"]

    text = (
        f"📝 Новый заказ!\n\n"
        f"<b>{title}</b>\n\n"
        f"{description}\n\n"
        f"💼 Категория: #{category.replace(' ', '_')}\n"
        f"📍 Город: #{city.replace(' ', '_')}\n"
        f"💰 Бюджет / Часы работы: {budget}"
    )

    await context.bot.send_message(
        chat_id=CHANNEL_USERNAME,
        text=text,
        parse_mode="HTML"
    )

    await update.message.reply_text("✅ Ваш заказ опубликован!")
    return ConversationHandler.END


# Отмена
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


# Запуск бота
async def main():
    application = Application.builder().token(TOKEN).build()

    # Хендлер для формы заказа
    order_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(menu_handler, pattern="^create_order$")
        ],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title_handler)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description_handler)],
            CATEGORY: [CallbackQueryHandler(category_handler)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget_handler)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(menu_handler, pattern="^rules$"))
    application.add_handler(order_conv)

    await application.run_polling()


if __name__ == "__main__":
    import asyncio

    loop = asyncio.get_event_loop()
    loop.create_task(main())
    app_web.run(host="0.0.0.0", port=10000)
