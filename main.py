
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CallbackQueryHandler, CommandHandler, ContextTypes,
    ConversationHandler, MessageHandler, filters
)
from fastapi import FastAPI, Request
import uvicorn
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = "@free_time_money"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

(ASK_TITLE, ASK_DESCRIPTION, ASK_CATEGORY, ASK_PRICE, ASK_CITY) = range(5)

categories = [
    "Сайты", "IT разработка", "Нейросети", "Дизайн",
    "Маркетинг", "Проектирование", "Тендеры", "Юристы"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Разместить Заказ", callback_data="create_order")],
        [InlineKeyboardButton("Найти Заказ. Категории", callback_data="find_order")],
        [InlineKeyboardButton("Ресурсы: Аренда. Прокат. Рабочие.", callback_data="resources")],
        [InlineKeyboardButton("Реферальная программа", callback_data="referral")],
        [InlineKeyboardButton("Вопросы и ответы", callback_data="faq")],
        [InlineKeyboardButton("Служба заботы", callback_data="support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите действие:', reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "create_order":
        await query.message.reply_text("Введите заголовок заказа:")
        return ASK_TITLE
    else:
        await query.message.reply_text("Этот раздел в разработке.")
        return ConversationHandler.END

async def ask_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text
    await update.message.reply_text("Введите описание заказа:")
    return ASK_DESCRIPTION

async def ask_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    keyboard = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in categories]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите категорию:", reply_markup=reply_markup)
    return ASK_CATEGORY

async def save_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["category"] = query.data
    await query.message.reply_text("Введите бюджет заказа:")
    return ASK_PRICE

async def ask_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["price"] = update.message.text
    await update.message.reply_text("Введите город:")
    return ASK_CITY

async def publish_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text
    title = context.user_data["title"]
    description = context.user_data["description"]
    category = context.user_data["category"]
    price = context.user_data["price"]
    city = context.user_data["city"]

    text = (
        f"📝 <b>Новый заказ</b>
"
        f"<b>Заголовок:</b> {title}
"
        f"<b>Описание:</b> {description}
"
        f"<b>Категория:</b> {category}
"
        f"<b>Бюджет:</b> {price}
"
        f"<b>Город:</b> {city}

"
        f"#{category.replace(' ', '_')} #{city.replace(' ', '_')}"
    )

    await context.bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML")
    await update.message.reply_text("Ваш заказ опубликован!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(bot_app.initialize())
    await bot_app.bot.set_webhook(url=WEBHOOK_URL)

@app.on_event("shutdown")
async def shutdown_event():
    await bot_app.shutdown()

@app.post(f"/{TOKEN}")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}

bot_app = Application.builder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(button, pattern="^create_order$")],
    states={
        ASK_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_description)],
        ASK_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_category)],
        ASK_CATEGORY: [CallbackQueryHandler(save_category)],
        ASK_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_city)],
        ASK_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, publish_order)]
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(conv_handler)
bot_app.add_handler(CallbackQueryHandler(button))

WEBHOOK_URL = os.getenv("WEBHOOK_URL")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)
