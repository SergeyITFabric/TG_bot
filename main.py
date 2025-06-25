
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters,
    ContextTypes,
)
from fastapi import FastAPI, Request
import uvicorn

TOKEN = "7642643259:AAErZAsn4qCzaRkArbuegI8EizGE8yRv1VU"
CHANNEL_ID = "@free_time_money"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
bot_app = Application.builder().token(TOKEN).build()

(ORDER_TITLE, ORDER_DESCRIPTION, ORDER_CATEGORY, ORDER_PRICE, ORDER_CITY) = range(5)

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("Разместить Заказ", callback_data="order")],
        [InlineKeyboardButton("Найти Заказ. Категории", callback_data="categories")],
        [InlineKeyboardButton("Ресурсы: Аренда. Прокат. Рабочие.", callback_data="resources")],
        [InlineKeyboardButton("Реферальная программа", callback_data="referral")],
        [InlineKeyboardButton("Вопросы и ответы", callback_data="faq")],
        [InlineKeyboardButton("Служба заботы", callback_data="support")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Меню", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "order":
        await query.message.reply_text("Введите заголовок заказа:")
        return ORDER_TITLE

    await query.message.reply_text("Этот раздел пока в разработке.")
    return ConversationHandler.END

async def order_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["title"] = update.message.text
    await update.message.reply_text("Введите описание заказа:")
    return ORDER_DESCRIPTION

async def order_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["description"] = update.message.text
    keyboard = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in CATEGORIES]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите категорию:", reply_markup=reply_markup)
    return ORDER_CATEGORY

async def order_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    context.user_data["category"] = query.data
    await query.message.reply_text("Укажите цену заказа (например: 5000 руб):")
    return ORDER_PRICE

async def order_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["price"] = update.message.text
    await update.message.reply_text("Укажите город:")
    return ORDER_CITY

async def order_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["city"] = update.message.text

    text = (
        f"📝 <b>Новый заказ</b>

"
        f"<b>Заголовок:</b> {context.user_data['title']}
"
        f"<b>Описание:</b> {context.user_data['description']}
"
        f"<b>Категория:</b> {context.user_data['category']}
"
        f"<b>Цена:</b> {context.user_data['price']}
"
        f"<b>Город:</b> {context.user_data['city']}"
    )

    await bot_app.bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML")
    await update.message.reply_text("Ваш заказ опубликован.")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END

conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(button_handler, pattern="^order$")],
    states={
        ORDER_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_title)],
        ORDER_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_description)],
        ORDER_CATEGORY: [CallbackQueryHandler(order_category)],
        ORDER_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_price)],
        ORDER_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_city)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CallbackQueryHandler(button_handler))
bot_app.add_handler(conv_handler)

@app.on_event("startup")
async def startup_event():
    await bot_app.bot.set_webhook("https://tg-bot-hvfu.onrender.com/" + TOKEN)

@app.on_event("shutdown")
async def shutdown_event():
    await bot_app.bot.delete_webhook()

@app.post("/" + TOKEN)
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}

@app.get("/")
async def root():
    return {"status": "bot is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
