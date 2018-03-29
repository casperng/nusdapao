import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
						  ConversationHandler)

import database

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

logger = logging.getLogger(__name__)

DELIVERY_ID = range(1)

ORDER_MESSAGE_TEMPLATE = "The orders are:\n"
ORDER_ITEM_MESSAGE_TEMPLATE = "{qty} ({remarks}) - {username} [{method}]\n"
ORDER_ITEM_MESSAGE_NO_REMARKS_TEMPLATE = "{qty} - {username} [{method}]\n"

def view_orders(bot, update):
	bot.send_message(update.message.from_user.id, 'What delivery ID are you checking for?')

	return DELIVERY_ID


def delivery_id(bot, update):
	if update.message.text.lower() == 'cancel':
		return ConversationHandler.END

	deliveryId = update.message.text
	if not database.is_valid_delivery_id(deliveryId):
		update.message.reply_text(
			'Invalid delivery ID, please try again')
		return DELIVERY_ID

	orders = database.get_orders(deliveryId)
	logger.info("Orders for %s: %s", deliveryId, orders)

	reply = ORDER_MESSAGE_TEMPLATE
	for order in orders:
		if order['remarks']:
			reply += ORDER_ITEM_MESSAGE_TEMPLATE.format(**order)
		else:
			reply += ORDER_ITEM_MESSAGE_NO_REMARKS_TEMPLATE.format(**order)

	update.message.reply_text(
		reply)
	return ConversationHandler.END

def cancel(bot, update):
	return ConversationHandler.END


view_orders_conv_handler = ConversationHandler(
	entry_points=[CommandHandler('vieworders', view_orders)],
	states={
		DELIVERY_ID: [MessageHandler(Filters.text, delivery_id)],
	},
	fallbacks=[CommandHandler('cancel', cancel)]
)