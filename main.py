
import logging
from fastapi import FastAPI, Request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ConversationHandler, MessageHandler, filters, ContextTypes
)
import uvicorn
import os

TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = '@free_time_money'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

TITLE, DESCRIPTION, CATEGORY, BUDGET, CITY = range(5)

bot_app = Application.builder().token(TOKEN).build()


@app.get('/')
async def root():
    return {"status": "ok"}


@app.post(f"/{TOKEN}")
async def telegram_webhook(req: Request):
    data = await req.json()
    await bot_app.update_queue.put(Update.de_json(data, bot_app.bot))
    return {"ok": True}


@app.on_event("startup")
async def startup():
    await bot_app.bot.set_webhook(url=f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}")
    bot_app.create_task(bot_app.start())


@app.on_event("shutdown")
async def shutdown():
    await bot_app.stop()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Разместить заказ", callback_data="new_order")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "new_order":
        await query.message.reply_text("Введите заголовок заказа:")
        return TITLE


async def title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("Введите описание заказа:")
    return DESCRIPTION


async def description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    await update.message.reply_text("Введите категорию заказа:")
    return CATEGORY


async def category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['category'] = update.message.text
    await update.message.reply_text("Введите бюджет заказа:")
    return BUDGET


async def budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['budget'] = update.message.text
    await update.message.reply_text("Введите город:")
    return CITY


async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['city'] = update.message.text

    order_message = (
        f"📝 <b>Новый заказ</b>

"
        f"<b>Заголовок:</b> {context.user_data['title']}
"
        f"<b>Описание:</b> {context.user_data['description']}
"
        f"<b>Категория:</b> {context.user_data['category']}
"
        f"<b>Бюджет:</b> {context.user_data['budget']}
"
        f"<b>Город:</b> {context.user_data['city']}"
    )

    await bot_app.bot.send_message(chat_id=CHANNEL_ID, text=order_message, parse_mode="HTML")
    await update.message.reply_text("Ваш заказ опубликован в канале!")

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Заказ отменён.")
    return ConversationHandler.END


conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(menu, pattern="^new_order$")],
    states={
        TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
        CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, category)],
        BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, budget)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(conv_handler)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv('PORT', 10000)))
