
import logging
import os

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from flask import Flask

# Настройки
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "@free_time_money"

# Категории
CATEGORIES = [
    "Сайты",
    "IT разработка",
    "Нейросети",
    "Дизайн",
    "Маркетинг",
    "Проектирование",
    "Тендеры",
    "Юристы",
]

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Flask для рендера
app_flask = Flask(__name__)

# Состояния ConversationHandler
TITLE, DESCRIPTION, CATEGORY, BUDGET, CITY = range(5)


# Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_menu(update, context)


# Отправка меню
async def send_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("Разместить заказ", callback_data="place_order")],
        [InlineKeyboardButton("Правила", callback_data="rules")],
        [InlineKeyboardButton("Поддержка", callback_data="support")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text(
            "Добро пожаловать! Выберите действие:", reply_markup=reply_markup
        )
    elif update.callback_query:
        await update.callback_query.message.edit_text(
            "Добро пожаловать! Выберите действие:", reply_markup=reply_markup
        )


# Обработка нажатий
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "place_order":
        await query.message.reply_text("Введите заголовок заказа:", reply_markup=ReplyKeyboardRemove())
        return TITLE

    if query.data == "rules":
        await query.message.reply_text("Правила сервиса...")
        return ConversationHandler.END

    if query.data == "support":
        await query.message.reply_text("Поддержка: @your_support_username")
        return ConversationHandler.END


# Сбор данных
async def title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text
    await update.message.reply_text("Введите описание заказа:")
    return DESCRIPTION


async def description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    keyboard = [[cat] for cat in CATEGORIES]
    await update.message.reply_text(
        "Выберите категорию:", reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CATEGORY


async def category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["category"] = update.message.text
    await update.message.reply_text("Укажите бюджет или количество часов работы:")
    return BUDGET


async def budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["budget"] = update.message.text
    await update.message.reply_text("Укажите город:")
    return CITY


async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text

    # Публикация
    order_text = (
        f"📝 <b>Новый заказ</b>

"
        f"<b>{context.user_data['title']}</b>

"
        f"{context.user_data['description']}

"
        f"<b>Бюджет:</b> {context.user_data['budget']}
"
        f"<b>Город:</b> {context.user_data['city']}

"
        f"#{context.user_data['category'].replace(' ', '_')} #{context.user_data['city'].replace(' ', '_')}"
    )

    await context.bot.send_message(
        chat_id=CHANNEL_USERNAME,
        text=order_text,
        parse_mode="HTML"
    )

    await update.message.reply_text("✅ Ваш заказ опубликован!", reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


# Ошибка
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Действие отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    application = Application.builder().token(TOKEN).build()

    # Меню
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(menu_handler))

    # Заказ
    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_handler, pattern="^place_order$")],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, category)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
    )
    application.add_handler(conv_handler)

    # Запуск
    application.run_polling()


# Flask healthcheck
@app_flask.route("/")
def index():
    return "Bot is running!"


if __name__ == "__main__":
    main()
