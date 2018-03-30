import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)

import database

import utilities

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

DELIVERY_ID, ITEM_INDEX = range(2)

ORDER_MESSAGE_TEMPLATE = "Give the number of the order that you want to remove:\n"
ORDER_ITEM_MESSAGE_TEMPLATE = "{qty} ({remarks}) - {username} [{method}]\n"
ORDER_ITEM_MESSAGE_NO_REMARKS_TEMPLATE = "{qty} - {username} [{method}]\n"

def remove_order(bot, update):
    bot.send_message(update.message.from_user.id, 'What delivery ID are you removing an order from?')

    return DELIVERY_ID


def delivery_id(bot, update, user_data):
    utilities.pop_all_keys(user_data)
    deliveryId = update.message.text
    if not database.is_open_delivery_id(deliveryId):
        update.message.reply_text(
            'Invalid delivery ID, please try again. Check if the delivery has closed')
        return DELIVERY_ID

    orders = database.get_user_orders(deliveryId, update.message.from_user.id)
    logger.info("Remove order for %s: %s", deliveryId, orders)

    reply = ORDER_MESSAGE_TEMPLATE
    order_list = {}
    i = 1
    for order in orders:
        if order['remarks']:
            reply += str(i) + '. ' + ORDER_ITEM_MESSAGE_TEMPLATE.format(**order)
        else:
            reply += str(i) + '. ' + ORDER_ITEM_MESSAGE_NO_REMARKS_TEMPLATE.format(**order)
        order_list[i] = order
        i += 1

    user_data['order_list'] = order_list

    logger.info("Order list: %s", order_list)

    update.message.reply_text(
        reply)
    return ITEM_INDEX

def item_index(bot, update, user_data):
    try:
        order = user_data['order_list'][int(update.message.text)]
    except Exception as e:
        logger.error(str(e))
        update.message.reply_text(
            "Invalid item number. Please try again")
        return ITEM_INDEX

    database.delete_user_order(update.message.from_user.id, order['id'])
    update.message.reply_text(
        "Your order has been removed!")

    return ConversationHandler.END

def cancel(bot, update):
    update.message.reply_text(
        "Your order removal has been cancelled!")
    return ConversationHandler.END


remove_order_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('removeorder', remove_order)],
    states={
        DELIVERY_ID: [MessageHandler(Filters.text, delivery_id, pass_user_data=True),
                      CommandHandler('cancel', cancel)],
        ITEM_INDEX: [MessageHandler(Filters.text, item_index, pass_user_data=True),
                     CommandHandler('cancel', cancel)],
    },
    fallbacks=[CommandHandler('cancel', cancel)],
	per_chat=False
)
