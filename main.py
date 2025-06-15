import logging
from telegram import Update, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Токен бота
TOKEN = "7670617089:AAF-Mj6RwmnOBMjxdvOcOTA8ca8T4A5M9hs"

# Включаем логирование
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь название товара и фото.")

# Получение фото и текста
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user_data = context.user_data

    if message.text and not message.photo:
        user_data['title'] = message.text
        await message.reply_text("Отправь до 3 фотографий.")
    elif message.photo:
        user_data.setdefault('photos', [])
        user_data['photos'].append(message.photo[-1].file_id)
        if len(user_data['photos']) >= 3:
            await confirm_submission(update, context)

# Подтверждение
async def confirm_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("✅ Опубликовать", callback_data="confirm")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    await update.message.reply_text("Опубликовать анкету?", reply_markup=InlineKeyboardMarkup(keyboard))

# Обработка кнопок
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data = context.user_data

    if query.data == "confirm":
        caption = f"📦 <b>{user_data.get('title', '')}</b>"
        media = [InputMediaPhoto(media=pid, caption=caption if i == 0 else '') for i, pid in enumerate(user_data.get("photos", []))]

        await context.bot.send_media_group(chat_id="@findemand", media=media)
        await query.edit_message_text("✅ Анкета опубликована.")
    else:
        await query.edit_message_text("❌ Отменено.")

# Основная функция
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_message))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()

if __name__ == "__main__":
    main()