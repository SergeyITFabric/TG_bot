
import logging
from fastapi import FastAPI, Request
import uvicorn
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Bot
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
import os

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = "@free_time_money"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
bot_app = Application.builder().token(TOKEN).build()

TITLE, DESCRIPTION, CATEGORY, PRICE, CITY = range(5)


# Главное меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🚀 Разместить Заказ", callback_data="create_order")],
        [InlineKeyboardButton("🔍 Найти Заказ. Категории", callback_data="find_order")],
        [InlineKeyboardButton("🛠 Ресурсы: Аренда. Прокат. Рабочие.", callback_data="resources")],
        [InlineKeyboardButton("💸 Реферальная программа", callback_data="ref_program")],
        [InlineKeyboardButton("❓ Вопросы и ответы", callback_data="faq")],
        [InlineKeyboardButton("📞 Служба заботы", callback_data="support")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=reply_markup)


# Обработка кнопок меню
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "create_order":
        await query.message.reply_text("Введите заголовок заказа:")
        return TITLE
    elif data == "ref_program":
        link = f"https://t.me/free_time_money?start={query.from_user.id}"
        await query.message.reply_text(f"Ваша реферальная ссылка:
{link}")
    else:
        await query.message.reply_text("Этот раздел в разработке.")


# Сбор данных заказа
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
    await update.message.reply_text("Введите цену или бюджет заказа:")
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
        f"<b>Город:</b> {context.user_data['city']}
"
    )

    await bot_app.bot.send_message(chat_id=CHANNEL_ID, text=text, parse_mode="HTML")
    await update.message.reply_text("Ваш заказ успешно размещён!")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Создание заказа отменено.")
    return ConversationHandler.END


# FastAPI endpoint для webhook
@app.post(f"/{TOKEN}")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return {"ok": True}


@app.get("/")
async def root():
    return {"status": "ok"}


@app.on_event("startup")
async def startup():
    webhook_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}"
    await bot_app.bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook установлен на {webhook_url}")


@app.on_event("shutdown")
async def shutdown():
    await bot_app.bot.delete_webhook()


# Роуты бота
conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(menu_handler, pattern="^create_order$")],
    states={
        TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
        CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, category)],
        PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CallbackQueryHandler(menu_handler))
bot_app.add_handler(conv_handler)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
