from telegram import InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

async def start(update, context):
    await update.message.reply_text("Привет! Отправь JSON с данными товара.")

async def handle_message(update, context):
    try:
        data = eval(update.message.text)
        media = [InputMediaPhoto(media=pid) for pid in data['photos']]
        caption = (
            f"<b>{data['name']}</b>\n"
            f"{data['description']}\n"
            f"📍 {data['city']}\n"
            f"📦 {data['methods']}\n"
            f"👤 @{data['username']}"
        )
        await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media)
        await update.message.reply_html(caption)
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

def main():
    import os
    TOKEN = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()