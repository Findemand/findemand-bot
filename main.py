import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler, filters,
                          ContextTypes, ConversationHandler, CallbackQueryHandler)
from datetime import datetime
from models import Base, User, Product
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import BOT_TOKEN, CHANNEL_USERNAME, MODERATOR_USERNAMES

NAME, PHOTOS, DESCRIPTION, CITY, DELIVERY = range(5)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
engine = create_engine('sqlite:///data.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

CITIES = ['Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Казань']

def get_or_create_user(session, tg_user):
    user = session.query(User).filter_by(telegram_id=tg_user.id).first()
    if not user:
        user = User(telegram_id=tg_user.id, username=tg_user.username)
        session.add(user)
        session.commit()
    return user

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    user = get_or_create_user(session, update.effective_user)
    await update.message.reply_text("Вы зарегистрированы. Используйте /sell, чтобы подать объявление.")

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    context.user_data['photos'] = []
    await update.message.reply_text("Введите название товара:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Загрузите до 3 фото. Когда закончите — напишите 'Готово'")
    return PHOTOS

async def get_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        context.user_data['photos'].append(file_id)
        if len(context.user_data['photos']) == 3:
            await update.message.reply_text("Теперь введите описание товара:")
            return DESCRIPTION
        else:
            await update.message.reply_text("Фото получено. Загрузите ещё или напишите 'Готово'")
    elif update.message.text.lower() == 'готово':
        if context.user_data['photos']:
            await update.message.reply_text("Введите описание товара:")
            return DESCRIPTION
        else:
            await update.message.reply_text("Нужно загрузить хотя бы одно фото.")
    else:
        await update.message.reply_text("Это не фото. Пожалуйста, загрузите изображение.")

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    keyboard = [[InlineKeyboardButton(city, callback_data=city)] for city in CITIES]
    await update.message.reply_text("Выберите город:", reply_markup=InlineKeyboardMarkup(keyboard))
    return CITY

async def get_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data['city'] = query.data
    context.user_data['delivery'] = {'meetup': False, 'delivery': False}
    keyboard = [
        [InlineKeyboardButton("☐ Личная встреча", callback_data='meetup')],
        [InlineKeyboardButton("☐ Доставка", callback_data='delivery')],
        [InlineKeyboardButton("Готово", callback_data='done')],
    ]
    await query.edit_message_text("Выберите способ передачи:", reply_markup=InlineKeyboardMarkup(keyboard))
    return DELIVERY

async def set_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice = query.data

    if choice == 'done':
        data = context.user_data
        if not all([data.get('name'), data.get('description'), data.get('city')]) or            not data.get('photos') or not (data['delivery']['meetup'] or data['delivery']['delivery']):
            await query.edit_message_text("❗️Не все поля заполнены. Попробуйте заново с /sell")
            return ConversationHandler.END

        session = Session()
        user = get_or_create_user(session, update.effective_user)
        product = Product(
            user_id=user.id,
            name=data['name'],
            description=data['description'],
            city=data['city'],
            delivery_meetup=data['delivery']['meetup'],
            delivery_shipping=data['delivery']['delivery'],
            photo_ids=','.join(data['photos']),
            status='pending'
        )
        session.add(product)
        session.commit()

        caption = (f"🛍️ <b>{product.name}</b>
"
                   f"📦 <b>Описание:</b> {product.description}
"
                   f"📍 <b>Город:</b> {product.city}
"
                   f"🚚 <b>Способ передачи:</b> {'Личная встреча' if product.delivery_meetup else ''} {'Доставка' if product.delivery_shipping else ''}
"
                   f"👤 <b>Продавец:</b> @{update.effective_user.username}")

        media = [InputMediaPhoto(media=pid) for pid in data['photos']]
        media[0].caption = caption
        media[0].parse_mode = 'HTML'

        for mod in MODERATOR_USERNAMES:
            await context.bot.send_media_group(chat_id=mod, media=media)
            await context.bot.send_message(chat_id=mod, text=f"Одобрить объявление? /approve_{product.id} или /reject_{product.id}")

        await query.edit_message_text("Анкета отправлена модератору на проверку.")
        return ConversationHandler.END

    context.user_data['delivery'][choice] = not context.user_data['delivery'][choice]
    status = context.user_data['delivery']
    keyboard = [
        [InlineKeyboardButton(f"{'✅' if status['meetup'] else '☐'} Личная встреча", callback_data='meetup')],
        [InlineKeyboardButton(f"{'✅' if status['delivery'] else '☐'} Доставка", callback_data='delivery')],
        [InlineKeyboardButton("Готово", callback_data='done')],
    ]
    await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
    return DELIVERY

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    text = update.message.text
    if text.startswith('/approve_'):
        pid = int(text.split('_')[1])
        product = session.query(Product).get(pid)
        if product:
            product.status = 'approved'
            session.commit()
            photos = product.photo_ids.split(',')
            caption = (f"🛍️ <b>{product.name}</b>
"
                       f"📦 <b>Описание:</b> {product.description}
"
                       f"📍 <b>Город:</b> {product.city}
"
                       f"🚚 <b>Способ передачи:</b> {'Личная встреча' if product.delivery_meetup else ''} {'Доставка' if product.delivery_shipping else ''}
"
                       f"👤 <b>Продавец:</b> @{product.user.username}")
            media = [InputMediaPhoto(media=p) for p in photos]
            media[0].caption = caption
            media[0].parse_mode = 'HTML'
            await context.bot.send_media_group(chat_id=CHANNEL_USERNAME, media=media)
            await update.message.reply_text("Объявление опубликовано в канал.")

async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = Session()
    text = update.message.text
    if text.startswith('/reject_'):
        pid = int(text.split('_')[1])
        product = session.query(Product).get(pid)
        if product:
            product.status = 'rejected'
            session.commit()
            await update.message.reply_text("Объявление отклонено.")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler('sell', sell)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHOTOS: [MessageHandler(filters.PHOTO | filters.TEXT, get_photos)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            CITY: [CallbackQueryHandler(get_city)],
            DELIVERY: [CallbackQueryHandler(set_delivery)],
        },
        fallbacks=[],
    )

    app.add_handler(CommandHandler('start', start))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^/approve_\d+$'), approve))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^/reject_\d+$'), reject))

    app.run_polling()
