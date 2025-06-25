
import logging
from fastapi import FastAPI, Request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ConversationHandler,
    MessageHandler, ContextTypes, filters
)
import uvicorn

TOKEN = "7642643259:AAErZAsn4qCzaRkArbuegI8EizGE8yRv1VU"
CHANNEL_ID = "@free_time_money"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
bot_app = Application.builder().token(TOKEN).build()

# States
TITLE, DESCRIPTION, CATEGORY, PRICE, CITY = range(5)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Разместить Заказ", callback_data="create_order")],
        [InlineKeyboardButton("Реферальная программа", callback_data="ref_program")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Привет! Выберите действие:", reply_markup=reply_markup)

# Callback handler
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "create_order":
        await query.message.reply_text("Введите заголовок заказа:")
        return TITLE
    elif query.data == "ref_program":
        user_id = query.from_user.id
        ref_link = f"https://t.me/YOUR_BOT_USERNAME?start={user_id}"
        await query.message.reply_text(f"Ваша реферальная ссылка:
{ref_link}")
        return ConversationHandler.END

# Conversation steps
async def title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text
    await update.message.reply_text("Введите описание заказа:")
    return DESCRIPTION

async def description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    await update.message.reply_text("Введите категорию заказа:")
    return CATEGORY

async def category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["category"] = update.message.text
    await update.message.reply_text("Введите бюджет заказа:")
    return PRICE

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["price"] = update.message.text
    await update.message.reply_text("Введите город:")
    return CITY

async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        f"<b>Бюджет:</b> {context.user_data['price']}
"
        f"<b>Город:</b> {context.user_data['city']}"
    )
    await bot_app.bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML")
    await update.message.reply_text("Ваш заказ опубликован!")
    return ConversationHandler.END

# Cancel
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

# Webhook
@app.post(f"/{TOKEN}")
async def telegram_webhook(req: Request):
    data = await req.json()
    await bot_app.update_queue.put(Update.de_json(data, bot_app.bot))
    return {"ok": True}

@app.get("/")
async def root():
    return {"message": "Bot is running"}

# Handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CallbackQueryHandler(menu_handler, pattern="^(create_order|ref_program)$"))

conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(menu_handler, pattern="create_order")],
    states={
        TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
        CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, category)],
        PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
bot_app.add_handler(conv_handler)

@app.on_event("startup")
async def startup():
    await bot_app.bot.set_webhook("https://YOUR_RENDER_URL.onrender.com/" + TOKEN)
    await bot_app.initialize()
    await bot_app.start()

@app.on_event("shutdown")
async def shutdown():
    await bot_app.stop()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
