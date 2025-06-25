import os
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Константы
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("RENDER_EXTERNAL_URL")  # Render сам задаёт этот URL
CHANNEL_USERNAME = "@free_time_money"

CATEGORIES = [
    "Сайты", "IT разработка", "Нейросети",
    "Дизайн", "Маркетинг", "Проектирование",
    "Тендеры", "Юристы"
]

TITLE, DESCRIPTION, CATEGORY, BUDGET, CITY = range(5)

# Flask app
flask_app = Flask(__name__)

# Telegram bot app
app = Application.builder().token(TOKEN).build()


# ----------- Telegram handlers -----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Разместить Заказ", callback_data='place_order')],
        [InlineKeyboardButton("Найти Заказ. Категории", callback_data='find_order')],
        [InlineKeyboardButton("Ресурсы: Аренда. Прокат. Рабочие.", callback_data='resources')],
        [InlineKeyboardButton("Реферальная программа", callback_data='referral')],
        [InlineKeyboardButton("Вопросы и ответы", callback_data='faq')],
        [InlineKeyboardButton("Служба заботы", callback_data='support')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите действие:', reply_markup=reply_markup)


async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'place_order':
        await query.message.reply_text('Введите заголовок заказа:')
        return TITLE

    if query.data == 'referral':
        link = f"https://t.me/{context.bot.username}?start={query.from_user.id}"
        await query.message.reply_text(f"Ваша реферальная ссылка:\n{link}")
        return ConversationHandler.END

    await query.message.reply_text('Функционал в разработке.')
    return ConversationHandler.END


async def title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text('Введите описание заказа:')
    return DESCRIPTION


async def description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    keyboard = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in CATEGORIES]
    await update.message.reply_text('Выберите категорию:', reply_markup=InlineKeyboardMarkup(keyboard))
    return CATEGORY


async def category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['category'] = query.data
    await query.message.reply_text('Укажите бюджет / часы работы:')
    return BUDGET


async def budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['budget'] = update.message.text
    await update.message.reply_text('Укажите город:')
    return CITY


async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['city'] = update.message.text

    title = context.user_data['title']
    desc = context.user_data['description']
    cat = context.user_data['category']
    budget = context.user_data['budget']
    city = context.user_data['city']

    text = (
        f"<b>📝 Новый заказ</b>\n\n"
        f"<b>Заголовок:</b> {title}\n"
        f"<b>Описание:</b> {desc}\n"
        f"<b>Категория:</b> #{cat}\n"
        f"<b>Бюджет:</b> {budget}\n"
        f"<b>Город:</b> #{city}"
    )

    await context.bot.send_message(
        chat_id=CHANNEL_USERNAME,
        text=text,
        parse_mode="HTML"
    )

    await update.message.reply_text("Ваш заказ опубликован!")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END


# ----------- Telegram webhook integration -----------

@flask_app.route('/')
def home():
    return "Bot is alive!"


@flask_app.post(f'/{TOKEN}')
async def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, app.bot)
    await app.process_update(update)
    return 'ok'


# ----------- Setup handlers -----------

conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(menu_handler, pattern="^place_order$")],
    states={
        TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
        CATEGORY: [CallbackQueryHandler(category)],
        BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(menu_handler))
app.add_handler(conv_handler)


# ----------- Start bot -----------

async def run_webhook():
    await app.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")
    print(f"Webhook set to {WEBHOOK_URL}/{TOKEN}")


if __name__ == '__main__':
    import asyncio

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_webhook())

    flask_app.run(host="0.0.0.0", port=10000)
