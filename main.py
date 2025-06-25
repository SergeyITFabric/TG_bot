
import logging
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
import os

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Переменные
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
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

# Состояния ConversationHandler
TITLE, DESCRIPTION, CATEGORY, BUDGET, CITY, CONFIRM = range(6)

# Главное меню
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("Разместить заказ", callback_data="place_order")],
        [InlineKeyboardButton("Правила", callback_data="rules")],
        [InlineKeyboardButton("Поддержка", callback_data="support")],
    ]
    return InlineKeyboardMarkup(keyboard)


# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать! Выберите действие:", reply_markup=get_main_menu()
    )


# Обработка кнопок меню
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "place_order":
        await query.message.reply_text("Введите заголовок заказа:", reply_markup=ReplyKeyboardRemove())
        return TITLE
    elif query.data == "rules":
        await query.message.reply_text("Правила использования сервиса...")
    elif query.data == "support":
        await query.message.reply_text("Свяжитесь с поддержкой: @admin_username")
    return ConversationHandler.END


async def title_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text
    await update.message.reply_text("Опишите ваш заказ:")
    return DESCRIPTION


async def description_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    keyboard = [[cat] for cat in CATEGORIES]
    await update.message.reply_text(
        "Выберите категорию:", reply_markup=InlineKeyboardMarkup.from_button_list(keyboard)
    )
    return CATEGORY


async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["category"] = update.message.text
    await update.message.reply_text("Укажите бюджет или количество часов:")
    return BUDGET


async def budget_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["budget"] = update.message.text
    await update.message.reply_text("Укажите город:")
    return CITY


async def city_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text

    summary = (
        f"📝 <b>Новый заказ</b>

"
        f"<b>Заголовок:</b> {context.user_data['title']}
"
        f"<b>Описание:</b> {context.user_data['description']}
"
        f"<b>Категория:</b> {context.user_data['category']}
"
        f"<b>Бюджет / Часы:</b> {context.user_data['budget']}
"
        f"<b>Город:</b> {context.user_data['city']}

"
        f"#{context.user_data['category'].replace(' ', '_')} #{context.user_data['city'].replace(' ', '_')}"
    )

    await context.bot.send_message(
        chat_id=CHANNEL_USERNAME,
        text=summary,
        parse_mode="HTML",
    )

    await update.message.reply_text("Ваш заказ опубликован!", reply_markup=get_main_menu())
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu_handler, pattern="^place_order$")],
        states={
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title_handler)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description_handler)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, category_handler)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget_handler)],
            CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city_handler)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(menu_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
