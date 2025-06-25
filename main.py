import os
from fastapi import FastAPI, Request
from telegram import Update, BotCommand
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    CallbackQueryHandler, ContextTypes, ConversationHandler
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

TOKEN = os.getenv('BOT_TOKEN')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')  # Например, https://tg-bot-abc.onrender.com

CHANNEL_USERNAME = '@free_time_money'

# Создание приложения Telegram
bot_app = Application.builder().token(TOKEN).build()

# Создание FastAPI
app = FastAPI()

# ====================
# === Меню для бота ===
# ====================

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
    await update.message.reply_text('Добро пожаловать! Выберите действие:', reply_markup=reply_markup)


# ============================
# === Обработчик Callbacks ====
# ============================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'place_order':
        await query.message.reply_text('Введите заголовок заказа:')
        return TITLE

    elif query.data == 'find_order':
        await query.message.reply_text('Функция поиска заказа в разработке.')

    elif query.data == 'resources':
        await query.message.reply_text('Ресурсы: аренда, прокат, рабочие.')

    elif query.data == 'referral':
        referral_link = f"https://t.me/{context.bot.username}?start={query.from_user.id}"
        await query.message.reply_text(f"Ваша реферальная ссылка: {referral_link}")

    elif query.data == 'faq':
        await query.message.reply_text('Здесь будут часто задаваемые вопросы.')

    elif query.data == 'support':
        await query.message.reply_text('Напишите в поддержку @YourSupportUsername')

    return ConversationHandler.END


# ===============================
# === Конструктор заказа ====
# ===============================

TITLE, DESCRIPTION, CATEGORY, PRICE, CITY = range(5)

async def title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text
    await update.message.reply_text('Введите описание заказа:')
    return DESCRIPTION

async def description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    await update.message.reply_text('Введите категорию заказа:')
    return CATEGORY

async def category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['category'] = update.message.text
    await update.message.reply_text('Введите бюджет заказа:')
    return PRICE

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['price'] = update.message.text
    await update.message.reply_text('Введите город:')
    return CITY

async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['city'] = update.message.text

    order_text = (
        f"📝 <b>Новый заказ</b>\n\n"
        f"<b>Заголовок:</b> {context.user_data['title']}\n"
        f"<b>Описание:</b> {context.user_data['description']}\n"
        f"<b>Категория:</b> {context.user_data['category']}\n"
        f"<b>Бюджет:</b> {context.user_data['price']}\n"
        f"<b>Город:</b> {context.user_data['city']}"
    )

    await context.bot.send_message(chat_id=CHANNEL_USERNAME, text=order_text, parse_mode='HTML')
    await update.message.reply_text('Ваш заказ размещен!')

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Операция отменена.')
    return ConversationHandler.END


# ===============================
# === Регистрация handlers ====
# ===============================

conv_handler = ConversationHandler(
    entry_points=[CallbackQueryHandler(button_handler, pattern='place_order')],
    states={
        TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, title)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
        CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, category)],
        PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, price)],
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
)

bot_app.add_handler(CommandHandler('start', start))
bot_app.add_handler(CallbackQueryHandler(button_handler))
bot_app.add_handler(conv_handler)


# ==========================
# === Вебхук и запуск ====
# ==========================

@app.on_event("startup")
async def on_startup():
    webhook_path = f"/{TOKEN}"
    await bot_app.bot.set_webhook(url=WEBHOOK_URL + webhook_path)
    print(f"Webhook установлен на {WEBHOOK_URL + webhook_path}")


@app.on_event("shutdown")
async def on_shutdown():
    await bot_app.bot.delete_webhook()


@app.post(f"/{TOKEN}")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.update_queue.put(update)
    return {"ok": True}


# Точка входа локально
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=10000)
