import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder
app = ApplicationBuilder().token(TOKEN).build()
app.run_polling()

# Получение токена из переменной окружения
TOKEN = os.getenv("BOT_TOKEN")

# Этапы анкеты
PRODUCT_NAME, PHOTOS, DESCRIPTION, CITY, DELIVERY_METHOD, USERNAME, CONFIRM = range(7)

# Города и способы передачи
CITIES = ["Москва", "Санкт-Петербург", "Екатеринбург", "Новосибирск"]
DELIVERY_OPTIONS = ["Личная встреча", "Доставка"]

# Временное хранилище
user_data = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Давайте создадим анкету. Введите название товара:")
    return PRODUCT_NAME

async def product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    context.user_data["photos"] = []
    await update.message.reply_text("Отправьте до 3 фотографий товара.")
    return PHOTOS

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file_id = photo.file_id
    photos = context.user_data["photos"]

    if len(photos) < 3:
        photos.append(file_id)
        if len(photos) == 3:
            await update.message.reply_text("Теперь введите описание товара.")
            return DESCRIPTION
        else:
            await update.message.reply_text("Добавьте ещё фото или нажмите /skip если достаточно.")
            return PHOTOS
    else:
        await update.message.reply_text("Вы уже отправили 3 фото. Введите описание товара.")
        return DESCRIPTION

async def skip_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Теперь введите описание товара.")
    return DESCRIPTION

async def description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    keyboard = [[InlineKeyboardButton(city, callback_data=city)] for city in CITIES]
    await update.message.reply_text("Выберите город:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CITY

async def select_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["city"] = query.data

    keyboard = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in DELIVERY_OPTIONS]
    await query.edit_message_text("Выберите способ передачи:", reply_markup=InlineKeyboardMarkup(keyboard))
    return DELIVERY_METHOD

async def delivery_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["delivery"] = query.data

    await query.edit_message_text("Укажите ваш @username.")
    return USERNAME

async def username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["username"] = update.message.text

    # Подтверждение
    data = context.user_data
    caption = (
        f"<b>{data['name']}</b>\n"
        f"📍 {data['city']}\n"
        f"🚚 Способ: {data['delivery']}\n"
        f"💬 {data['description']}\n"
        f"👤 Продавец: {data['username']}"
    )

    media = [InputMediaPhoto(media=pid) for pid in data["photos"]]

    if media:
        media[0].caption = caption
        media[0].parse_mode = "HTML"
        await update.message.reply_media_group(media)
    else:
        await update.message.reply_text(caption, parse_mode="HTML")

    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Анкета отменена.")
    return ConversationHandler.END

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            PRODUCT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_name)],
            PHOTOS: [
                MessageHandler(filters.PHOTO, photo_handler),
                CommandHandler("skip", skip_photos)
            ],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, description)],
            CITY: [CallbackQueryHandler(select_city)],
            DELIVERY_METHOD: [CallbackQueryHandler(delivery_method)],
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, username)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.run_polling()