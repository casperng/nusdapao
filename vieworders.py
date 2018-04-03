import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
						  ConversationHandler)

import database
import utilities

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

logger = logging.getLogger(__name__)

DELIVERY_ID = range(1)

def view_orders(bot, update):
	bot.send_message(update.message.from_user.id, 'What delivery ID are you checking for? Send /cancel to cancel this request anytime')

	return DELIVERY_ID


def delivery_id(bot, update):
	deliveryId = update.message.text
	if not database.is_valid_delivery_id(deliveryId):
		update.message.reply_text(
			'Invalid delivery ID, please enter another ID')
		return DELIVERY_ID

	orders = database.get_orders(deliveryId)
	logger.info("Orders for %s: %s", deliveryId, orders)

	update.message.reply_text(
		utilities.build_view_orders_string(orders))
	return ConversationHandler.END


def cancel_prompt(bot, update):
	bot.send_message(update.message.from_user.id, "Perhaps you meant to /cancel the current vieworders request?")


def cancel(bot, update):
	update.message.reply_text(
		"Your request to view orders has been cancelled!")
	return ConversationHandler.END


view_orders_conv_handler = ConversationHandler(
	entry_points=[CommandHandler('vieworders', view_orders)],
	states={
		DELIVERY_ID: [MessageHandler(Filters.text, delivery_id),
					  CommandHandler('cancel', cancel)],
	},
	fallbacks=[CommandHandler('cancel', cancel),
			   MessageHandler(Filters.all, cancel_prompt)],
	per_chat=False
)