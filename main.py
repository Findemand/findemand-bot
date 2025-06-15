import logging
from telegram import Update, InputMediaPhoto, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters, ConversationHandler

TOKEN = "7670617089:AAF-Mj6RwmnOBMjxdvOcOTA8ca8T4A5M9hs"
PHOTO, TEXT, CONFIRM = range(3)

user_data_store = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь до 3 фото товара.")
    user_data_store[update.effective_chat.id] = {"photos": [], "text": ""}
    return PHOTO

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    photo = update.message.photo[-1].file_id
    user_data_store[chat_id]["photos"].append(photo)

    if len(user_data_store[chat_id]["photos"]) >= 3:
        await update.message.reply_text("Теперь отправь описание товара.")
        return TEXT
    else:
        await update.message.reply_text(f"Принято {len(user_data_store[chat_id]['photos'])}/3. Ещё фото?")
        return PHOTO

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data_store[chat_id]["text"] = update.message.text

    buttons = [[KeyboardButton("✅ Опубликовать"), KeyboardButton("❌ Отмена")]]
    markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True)

    await update.message.reply_media_group(
        [InputMediaPhoto(pid) for pid in user_data_store[chat_id]["photos"]]
    )
    await update.message.reply_text(f"Описание:\n{user_data_store[chat_id]['text']}", reply_markup=markup)

    return CONFIRM

async def handle_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if update.message.text == "✅ Опубликовать":
        await update.message.reply_text("Товар опубликован!")
    else:
        await update.message.reply_text("Отменено.")
    user_data_store.pop(chat_id, None)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Диалог завершён.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, handle_photo)],
            TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)],
            CONFIRM: [MessageHandler(filters.TEXT, handle_confirm)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)

    app.run_polling()  # можно заменить на .run_webhook(...) при необходимости

if __name__ == "__main__":
    main()