import logging
from telegram import Update, InputMediaPhoto
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler
)

import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ASK_NAME, ASK_PHOTOS, ASK_DESCRIPTION, ASK_CITY, ASK_METHODS, ASK_USERNAME = range(6)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data["photos"] = []
    await update.message.reply_text("Введите название товара:")
    return ASK_NAME

async def name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Отправьте до 3 фото товара:")
    return ASK_PHOTOS

async def photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["photos"].append(update.message.photo[-1].file_id)
    if len(context.user_data["photos"]) >= 3:
        await update.message.reply_text("Введите описание товара:")
        return ASK_DESCRIPTION
    await update.message.reply_text("Фото принято. Ещё? Или введите /skip.")
    return ASK_PHOTOS

async def skip_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите описание товара:")
    return ASK_DESCRIPTION

async def description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    await update.message.reply_text("Укажите город:")
    return ASK_CITY

async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["city"] = update.message.text
    await update.message.reply_text("Укажите способ передачи (личная встреча, доставка):")
    return ASK_METHODS

async def methods(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["methods"] = update.message.text
    await update.message.reply_text("Укажите ваш Telegram @username:")
    return ASK_USERNAME

async def username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["username"] = update.message.text
    data = context.user_data
    caption = (
        caption = (
            f"<b>{data['name']}</b>"
            f"{data['description']}\n"
            f"📍 {data['city']}\n"
            f"📦 {data['methods']}"
        )
"
"
"
"
        f"👤 @{data['username']}"
    )
    if data["photos"]:
        media = [InputMediaPhoto(pid) for pid in data["photos"]]
        media[0].caption = caption
        media[0].parse_mode = "HTML"
        await context.bot.send_media_group(chat_id="@findemand", media=media)
    else:
        await update.message.reply_text(caption, parse_mode="HTML")
    await update.message.reply_text("Отправлено на модерацию!")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Анкета отменена.")
    return ConversationHandler.END

def main():
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ASK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, name)],
            ASK_PHOTOS: [
                MessageHandler(filters.PHOTO, photos),
                CommandHandler("skip", skip_photos)
            ],
            ASK_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
            ASK_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, city)],
            ASK_METHODS: [MessageHandler(filters.TEXT & ~filters.COMMAND, methods)],
            ASK_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, username)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.run_polling()

if __name__ == "__main__":
    main()