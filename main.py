from fastapi import FastAPI, Request
import uvicorn
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    Update,
)
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)
import os

TOKEN = "7642643259:AAErZAsn4qCzaRkArbuegI8EizGE8yRv1VU"
CHANNEL_ID = "@free_time_money"

app = FastAPI()

application = Application.builder().token(TOKEN).build()

(
    TITLE,
    DESCRIPTION,
    CATEGORY,
    PRICE,
    CITY,
) = range(5)

# Главное меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("Разместить Заказ")],
        [KeyboardButton("Найти Заказ. Категории")],
        [KeyboardButton("Ресурсы: Аренда. Прокат. Рабочие.")],
        [KeyboardButton("Реферальная программа")],
        [KeyboardButton("Вопросы и ответы")],
        [KeyboardButton("Служба заботы")],
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, resize_keyboard=True, one_time_keyboard=False
    )
    await update.message.reply_text(
        "Добро пожаловать в биржу фриланса Free Time Money!", reply_markup=reply_markup
    )


# Команда разместить заказ
async def order_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите заголовок заказа:")
    return TITLE


async def order_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["title"] = update.message.text
    await update.message.reply_text("Введите описание заказа:")
    return DESCRIPTION


async def order_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    await update.message.reply_text("Выберите категорию заказа:")
    return CATEGORY


async def order_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["category"] = update.message.text
    await update.message.reply_text("Укажите бюджет заказа:")
    return PRICE


async def order_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["price"] = update.message.text
    await update.message.reply_text("Укажите город:")
    return CITY


async def order_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text

    text = (
        f"📝 <b>Новый заказ</b>\n\n"
        f"<b>Заголовок:</b> {context.user_data['title']}\n"
        f"<b>Описание:</b> {context.user_data['description']}\n"
        f"<b>Категория:</b> {context.user_data['category']}\n"
        f"<b>Бюджет:</b> {context.user_data['price']}\n"
        f"<b>Город:</b> {context.user_data['city']}"
    )

    await application.bot.send_message(
        chat_id=CHANNEL_ID, text=text, parse_mode="HTML"
    )
    await update.message.reply_text("Ваш заказ успешно размещён!")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END


# Реферальная программа
async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ref_link = f"https://t.me/free_time_money_bot?start={user_id}"
    await update.message.reply_text(f"Ваша реферальная ссылка: {ref_link}")


# Вебхук обработчик
@app.post(f"/{TOKEN}")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}


@app.get("/")
async def root():
    return {"message": "Бот работает"}


@app.on_event("startup")
async def on_startup():
    webhook_url = f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/{TOKEN}"
    await application.bot.set_webhook(webhook_url)
    print(f"Webhook установлен: {webhook_url}")


@app.on_event("shutdown")
async def on_shutdown():
    await application.bot.delete_webhook()


# Регистрируем обработчики
conv_handler = ConversationHandler(
    entry_points=[MessageHandler(filters.Regex("Разместить Заказ"), order_start)],
    states={
        TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_title)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_description)],
        CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_category)],
        PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_price)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, order_city)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.Regex("Реферальная программа"), referral))
application.add_handler(conv_handler)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
