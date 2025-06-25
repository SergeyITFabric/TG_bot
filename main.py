
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from fastapi import FastAPI, Request
import uvicorn
import os

# Настройки
TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = "@free_time_money"

# Логирование
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Шаги ConversationHandler
TITLE, DESCRIPTION, CATEGORY, BUDGET, CITY = range(5)

app = FastAPI()
bot_app = Application.builder().token(TOKEN).build()

# Главное меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("🚀 Разместить заказ", callback_data="create_order")],
        [InlineKeyboardButton("📂 Найти заказ. Категории", callback_data="find_order")],
        [InlineKeyboardButton("🏗️ Ресурсы: Аренда. Прокат. Рабочие", callback_data="resources")],
        [InlineKeyboardButton("💰 Реферальная программа", callback_data="referral")],
        [InlineKeyboardButton("❓ Вопросы и ответы", callback_data="faq")],
        [InlineKeyboardButton("👩‍💻 Служба заботы", callback_data="support")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать в биржу фриланса!", reply_markup=reply_markup)

# Обработка кнопок меню
async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "create_order":
        await query.message.reply_text("Введите заголовок заказа:")
        return TITLE
    elif query.data == "referral":
        await query.message.reply_text(f"Ваша реферальная ссылка: https://t.me/free_time_money?start={query.from_user.id}")
        return ConversationHandler.END
    else:
        await query.message.reply_text("Раздел в разработке.")
        return ConversationHandler.END

# Пошаговый ввод заказа
async def title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["title"] = update.message.text
    await update.message.reply_text("Введите описание заказа:")
    return DESCRIPTION

async def description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["description"] = update.message.text
    await update.message.reply_text("Укажите категорию:")
    return CATEGORY

async def category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["category"] = update.message.text
    await update.message.reply_text("Укажите бюджет заказа:")
    return BUDGET

async def budget(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["budget"] = update.message.text
    await update.message.reply_text("Укажите город:")
    return CITY

async def city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["city"] = update.message.text

    order_text = (
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

    await bot_app.bot.send_message(chat_id=CHANNEL_ID, text=order_text, parse_mode="HTML")
    await update.message.reply_text("Ваш заказ опубликован в канале!")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

# Webhook
@app.post(f"/{TOKEN}")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.process_update(update)
    return "ok"

@app.get("/")
async def read_root():
    return {"status": "ok"}

@app.on_event("startup")
async def startup() -> None:
    await bot_app.bot.set_webhook(f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}")

@app.on_event("shutdown")
async def shutdown() -> None:
    await bot_app.bot.delete_webhook()

# Хендлеры
conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(menu_handler, pattern="create_order")],
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
bot_app.add_handler(CallbackQueryHandler(menu_handler))
bot_app.add_handler(conv_handler)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
