import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler, ContextTypes

TOKEN = "7670617089:AAF-Mj6RwmnOBMjxdvOcOTA8ca8T4A5M9hs"
CHANNEL_ID = "@findemand"
MODERATOR_USERNAME = "@mokeano"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PHOTO, NAME, DESCRIPTION, CITY, DELIVERY, CONFIRM = range(6)
user_data_store = {}

cities = ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань"]
city_buttons = [[InlineKeyboardButton(city, callback_data=city)] for city in cities]
delivery_buttons = [
    [InlineKeyboardButton("Личная встреча", callback_data="meeting")],
    [InlineKeyboardButton("Доставка", callback_data="delivery")],
    [InlineKeyboardButton("Готово", callback_data="done")]
]

def get_keyboard(buttons):
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Загрузите до 3 фото товара.")
    user_data_store[update.message.from_user.id] = {"photos": []}
    return PHOTO

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo = update.message.photo[-1].file_id
    user_data_store[user_id]["photos"].append(photo)
    if len(user_data_store[user_id]["photos"]) >= 3:
        await update.message.reply_text("Введите название товара.")
        return NAME
    await update.message.reply_text("Фото добавлено. Отправьте ещё или напишите /next для продолжения.")
    return PHOTO

async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите название товара.")
    return NAME

async def handle_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.message.from_user.id]["name"] = update.message.text
    await update.message.reply_text("Введите описание товара.")
    return DESCRIPTION

async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data_store[update.message.from_user.id]["description"] = update.message.text
    await update.message.reply_text("Выберите город:", reply_markup=get_keyboard(city_buttons))
    return CITY

async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data_store[query.from_user.id]["city"] = query.data
    await query.edit_message_text("Выберите способ передачи:", reply_markup=get_keyboard(delivery_buttons))
    return DELIVERY

async def handle_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    delivery_methods = user_data_store[user_id].get("delivery", [])
    if query.data != "done":
        if query.data not in delivery_methods:
            delivery_methods.append(query.data)
        await query.edit_message_text("Выберите способ передачи:", reply_markup=get_keyboard(delivery_buttons))
        return DELIVERY
    user_data_store[user_id]["delivery"] = delivery_methods
    return await confirm_submission(update, context)

async def confirm_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = user_data_store[user_id]
    caption = (
        f"🛍 <b>{data['name']}</b>\n"
        f"{data['description']}\n"
        f"📍 {data['city']}\n"
        f"🚚 {' и '.join(data['delivery'])}\n"
        f"👤 @{query.from_user.username}"
    )
    media = [InputMediaPhoto(media=pid) for pid in data["photos"]]
    context.bot_data[user_id] = (media, caption)
    await query.edit_message_text("Заявка отправлена на модерацию.")
    await context.bot.send_media_group(chat_id=MODERATOR_USERNAME, media=media)
    await context.bot.send_message(chat_id=MODERATOR_USERNAME, text=caption, parse_mode="HTML")
    await context.bot.send_message(chat_id=MODERATOR_USERNAME, text=f"Одобрить: /approve_{user_id}")
    return ConversationHandler.END

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmd = update.message.text
    if not cmd.startswith("/approve_"):
        return
    user_id = int(cmd.split("_")[1])
    media, caption = context.bot_data.get(user_id, (None, None))
    if media:
        await context.bot.send_media_group(chat_id=CHANNEL_ID, media=media)
        await context.bot.send_message(chat_id=CHANNEL_ID, text=caption, parse_mode="HTML")
        await update.message.reply_text("Объявление одобрено и опубликовано.")
    else:
        await update.message.reply_text("Ошибка: данные не найдены.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PHOTO: [MessageHandler(filters.PHOTO, handle_photo), CommandHandler("next", skip_photo)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_name)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description)],
            CITY: [CallbackQueryHandler(handle_city)],
            DELIVERY: [CallbackQueryHandler(handle_delivery)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^/approve_"), approve))
    app.run_polling()

if __name__ == "__main__":
    main()