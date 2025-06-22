from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ВСТАВЬ СЮДА СВОЙ ТОКЕН
TOKEN = ""

# Главное меню
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("📨 Разместить Заказ", callback_data='create_order')],
        [InlineKeyboardButton("📁 Найти Заказ. Категории", callback_data='find_order')],
        [InlineKeyboardButton("🔧 Ресурсы: Аренда. Прокат. Рабочие.", callback_data='resources')],
        [InlineKeyboardButton("🤝 Реферальная программа", callback_data='referral')],
        [InlineKeyboardButton("❓ Вопросы и ответы", callback_data='faq')],
        [InlineKeyboardButton("👥 Служба заботы", callback_data='support')],
    ]
    return InlineKeyboardMarkup(keyboard)

# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Добро пожаловать! Выберите пункт меню:",
        reply_markup=get_main_menu()
    )

# Обработка нажатий на кнопки
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action = query.data
    if action == 'create_order':
        await query.edit_message_text("📝 Форма создания заказа (пока в разработке)")
    elif action == 'find_order':
        await query.edit_message_text("📁 Выбор категории (пока в разработке)")
    elif action == 'resources':
        await query.edit_message_text("🔧 Ресурсы: аренда, прокат, рабочие (в разработке)")
    elif action == 'referral':
        user_id = query.from_user.id
        referral_link = f"https://t.me/YOUR_BOT_USERNAME?start={user_id}"
        await query.edit_message_text(f"🤝 Ваша реферальная ссылка:\n{referral_link}")
    elif action == 'faq':
        await query.edit_message_text("❓ Часто задаваемые вопросы (в разработке)")
    elif action == 'support':
        await query.edit_message_text("👥 Связь с поддержкой: @your_support_contact")

# Запуск бота
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_menu))

    print("Бот запущен...")
    app.run_polling()

if __name__ == '__main__':
    main()
