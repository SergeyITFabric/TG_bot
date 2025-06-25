import os
from fastapi import FastAPI, Request
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from telegram.constants import ParseMode

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = "@free_time_money"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Пример: https://your-app.onrender.com

app = FastAPI()

application = Application.builder().token(TOKEN).build()

# Этапы заполнения заказа
TITLE, DESCRIPTION, CATEGORY, PRICE, CITY = range(5)

CATEGORIES = [
    "Сайты", "IT разработка", "Нейросети", "Дизайн",
    "Маркетинг", "Проектирование", "Тендеры", "Юристы"
]

# -------- Меню --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Разместить Заказ", callback_data="new_order")],
        [InlineKeyboardButton("Найти Заказ. Категории", callback_data="find_order")],
        [InlineKeyboardButton("Ресурсы: Аренда. Прокат. Рабочие.", callback_data="resources")],
        [InlineKeyboardButton("Реферальная программа", callback_data="referral")],
        [InlineKeyboardButton("Вопросы и ответы", callback_data="faq")],
        [InlineKeyboardButton("Служба заботы", callback_data="support")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Меню", reply_markup=reply_markup)

# -------- Кнопки меню --------
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "new_order":
        await query.message.reply_text("Введите заголовок заказа:")
        return TITLE

    elif query.data == "find_order":
        await query.message.reply_text("Функция в разработке.")
    elif query.data == "resources":
        await query.message.reply_text("Раздел ресурсов в разработке.")
    elif query.data == "referral":
        link = await context.bot.create_chat_invite_link(chat_id=CHANNEL_ID)
        await query.message.reply_text(
            f"Ваша реферальная ссылка:\n{link.invite_link}"
        )
    elif query.data == "faq":
        await query.message.reply_text("Раздел FAQ в разработке.")
    elif query.data == "support":
        await query.message.reply_text("Служба заботы: @username_support")

    return ConversationHandler.END

# -------- Форма заказа --------
async def title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text("Введите описание заказа:")
    return DESCRIPTION


async def description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    keyboard = [[InlineKeyboardButton(cat, callback_data=cat)] for cat in CATEGORIES]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите категорию:", reply_markup=reply_markup)
    return CATEGORY


async def category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['category'] = query.data
    await query.message.reply_text("Введите бюджет заказа (например: 5000 руб):")
    return PRICE


async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['price'] = update.message.text
    await update.message.reply_text("Введите город:")
    return CITY


async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['city'] = update.message.text

    order_text = (
        f"<b>📝 Новый заказ</b>\n\n"
        f"<b>Заголовок:</b> {context.user_data['title']}\n"
        f"<b>Описание:</b> {context.user_data['description']}\n"
        f"<b>Категория:</b> {context.user_data['category']}\n"
        f"<b>Бюджет:</b> {context.user_data['price']}\n"
        f"<b>Город:</b> {context.user_data['city']}"
    )

    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=order_text,
        parse_mode=ParseMode.HTML
    )

    await update.message.reply_text("Ваш заказ опубликован в канале!")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено.")
    return ConversationHandler.END


# -------- Handlers --------
conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(menu_handler, pattern="^new_order$")],
    states={
        TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
        CATEGORY: [CallbackQueryHandler(category)],
        PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

application.add_handler(CommandHandler("start", start))
application.add_handler(conv_handler)
application.add_handler(CallbackQueryHandler(menu_handler))

# -------- FastAPI --------
@app.on_event("startup")
async def on_startup():
    await application.bot.set_webhook(f"{WEBHOOK_URL}/{TOKEN}")


@app.on_event("shutdown")
async def on_shutdown():
    await application.bot.delete_webhook()


@app.post(f"/{TOKEN}")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.update_queue.put(update)
    return "OK"


# -------- Запуск --------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
