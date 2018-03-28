import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
						  ConversationHandler)

import database

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

logger = logging.getLogger(__name__)

DELIVERY_ID = range(1)

def view_orders(bot, update):
	bot.send_message(update.message.from_user.id, 'What delivery ID are you checking for?')

	return DELIVERY_ID


def delivery_id(bot, update):
	deliveryId = update.message.text
	if not database.is_valid_delivery_id(deliveryId):
		update.message.reply_text(
			'Invalid delivery ID, please try again')
		return DELIVERY_ID

	orders = database.get_orders(deliveryId)
	logger.info("Orders", orders)

	update.message.reply_text(
		orders)
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