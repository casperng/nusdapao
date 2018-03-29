import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)

import database

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

DELIVERY_ID = range(1)

def close_order(bot, update):
    user_id = update.message.from_user.id
    deliveries = database.get_user_deliveries(user_id)

    if len(deliveries) == 1:
        database.close_order_for_delivery(user_id, deliveries[0]['deliveryid'])
        update.message.reply_text(
            'Orders for your delivery have been closed!')
        return ConversationHandler.END

    bot.send_message(user_id, 'What delivery ID are you closing orders for?')

    return DELIVERY_ID


def delivery_id(bot, update, chat_data):
    deliveryId = update.message.text
    if not database.is_valid_delivery_id(deliveryId):
        update.message.reply_text(
            'Invalid delivery ID, please try again.')
        return DELIVERY_ID

    database.close_order_for_delivery(update.message.from_user.id, deliveryId)

    update.message.reply_text(
        'Orders for your delivery have been closed!')
    return ConversationHandler.END


def cancel(bot, update):
    update.message.reply_text(
        "Your request to close orders has been cancelled!")
    return ConversationHandler.END


close_order_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('closeorder', close_order)],
    states={
        DELIVERY_ID: [MessageHandler(Filters.text, delivery_id)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)