import logging
import os
from telegram import Update, InputMediaPhoto, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получаем токен из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[KeyboardButton("Создать анкету")]]
    keyboard = ReplyKeyboardMarkup(buttons, resize_keyboard=True)
    await update.message.reply_text("Привет! Нажми кнопку ниже, чтобы создать анкету.", reply_markup=keyboard)

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "Создать анкету":
        await update.message.reply_text("Пожалуйста, отправьте название товара.")
        context.user_data["step"] = "title"
    elif context.user_data.get("step") == "title":
        context.user_data["title"] = text
        await update.message.reply_text("Отправьте описание товара.")
        context.user_data["step"] = "description"
    elif context.user_data.get("step") == "description":
        context.user_data["description"] = text
        await update.message.reply_text("Теперь отправьте до 3 фотографий.")
        context.user_data["step"] = "photos"
        context.user_data["photos"] = []
    else:
        await update.message.reply_text("Пожалуйста, следуйте инструкциям.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("step") == "photos":
        photo = update.message.photo[-1].file_id
        context.user_data["photos"].append(photo)

        if len(context.user_data["photos"]) >= 3:
            await send_preview(update, context)
        else:
            await update.message.reply_text("Фото получено. Добавьте ещё или отправьте /done.")
    else:
        await update.message.reply_text("Пожалуйста, начните с /start.")

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("step") == "photos":
        await send_preview(update, context)
    else:
        await update.message.reply_text("Нечего завершать.")

async def send_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = context.user_data
    caption = f"<b>{data['title']}</b>\n\n{data['description']}"
    media = [InputMediaPhoto(media=pid) for pid in data["photos"]]

    if media:
        media[0].caption = caption
        media[0].parse_mode = "HTML"
        await update.message.reply_media_group(media=media)

    context.user_data.clear()

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    app.run_polling()