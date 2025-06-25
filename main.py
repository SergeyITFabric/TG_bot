
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from fastapi import FastAPI, Request
import uvicorn

TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
CHANNEL_ID = "@free_time_money"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# States
TITLE, DESCRIPTION, CATEGORY, BUDGET, CITY = range(5)

# Categories
CATEGORIES = ["Сайты", "IT разработка", "Нейросети", "Дизайн", "Маркетинг", "Проектирование", "Тендеры", "Юристы"]

# FastAPI app
app = FastAPI()

# Telegram bot
bot_app = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Разместить Заказ", callback_data="create_order")],
        [InlineKeyboardButton("Найти Заказ. Категории", callback_data="find_order")],
        [InlineKeyboardButton("Ресурсы: Аренда. Прокат. Рабочие.", callback_data="resources")],
        [InlineKeyboardButton("Реферальная программа", callback_data="referral")],
        [InlineKeyboardButton("Вопросы и ответы", callback_data="faq")],
        [InlineKeyboardButton("Служба заботы", callback_data="support")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "create_order":
        await query.message.reply_text("Введите заголовок заказа:")
        return TITLE

async def title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text
    await update.message.reply_text("Введите описание заказа:")
    return DESCRIPTION

async def description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    keyboard = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in CATEGORIES]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите категорию:", reply_markup=reply_markup)
    return CATEGORY

async def category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["category"] = query.data
    await query.message.reply_text("Введите бюджет заказа:")
    return BUDGET

async def budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["budget"] = update.message.text
    await update.message.reply_text("Введите город:")
    return CITY

async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text

    text = (
        "📝 <b>Новый заказ</b>\n\n"
        f"<b>Заголовок:</b> {context.user_data['title']}\n"
        f"<b>Описание:</b> {context.user_data['description']}\n"
        f"<b>Категория:</b> {context.user_data['category']}\n"
        f"<b>Бюджет:</b> {context.user_data['budget']}\n"
        f"<b>Город:</b> {context.user_data['city']}\n\n"
        "❗ Напишите в комментариях ваше предложение"
    )
    await bot_app.bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML")
    await update.message.reply_text("Ваш заказ опубликован!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CallbackQueryHandler(button, pattern="^create_order$"))

conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(button, pattern="^create_order$")],
    states={
        TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
        CATEGORY: [CallbackQueryHandler(category)],
        BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

bot_app.add_handler(conv_handler)

@app.post(f"/{TOKEN}")
async def telegram_webhook(req: Request):
    await bot_app.initialize()
    await bot_app.process_update(
        Update.de_json(await req.json(), bot_app.bot)
    )
    return {"ok": True}

@app.get("/")
async def root():
    return {"message": "Bot is running"}

if __name__ == "__main__":
    import asyncio
    loop = asyncio.get_event_loop()
    loop.create_task(bot_app.initialize())
    uvicorn.run(app, host="0.0.0.0", port=10000)
