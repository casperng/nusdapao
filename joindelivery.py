import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
						  ConversationHandler)

import database

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

logger = logging.getLogger(__name__)

CACHE = {}

DELIVERY_ID, QUANTITY, PAYMENT_METHOD, REMARKS = range(4)

def join_delivery_conv_handler(bot, update):
	CACHE[update.message.from_user.id] = {
		'userid': update.message.from_user.id,
		'username': update.message.from_user.first_name
	}

	bot.send_message(update.message.from_user.id, 'What delivery ID are you ordering for?')

	return DELIVERY_ID


def delivery_id(bot, update):
	user = update.message.from_user
	if user.id not in CACHE:
		return ConversationHandler.END

	deliveryId = update.message.text
	if not database.is_valid_delivery_id(deliveryId):
		update.message.reply_text(
			'Invalid delivery ID, please try again')
		return DELIVERY_ID

	logger.info("%s for delivery: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'How many of this item are you getting?')

	CACHE[user.id]['deliveryId'] = update.message.text

	return QUANTITY

def quantity(bot, update):
	user = update.message.from_user
	if user.id not in CACHE:
		return ConversationHandler.END

	logger.info("%s for quantity: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'What is your payment method?')

	CACHE[user.id]['qty'] = update.message.text

	return PAYMENT_METHOD

def payment_method(bot, update):
	user = update.message.from_user
	if user.id not in CACHE:
		return ConversationHandler.END

	logger.info("%s payment method: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'Any remarks? Type "no" if you have none')

	CACHE[user.id]['method'] = update.message.text

	return REMARKS

def remarks(bot, update):
	user = update.message.from_user
	if user.id not in CACHE:
		return ConversationHandler.END

	remarks = update.message.text
	if remarks.lower() == 'no':
		remarks = ''

	CACHE[user.id]['remarks'] = remarks
	order = CACHE.pop(user.id)

	database.add_order(order)

	logger.info("%s payment method: %s", user.first_name, order)
	update.message.reply_text(
		'Your order has been registered!')

	return ConversationHandler.END

def cancel(bot, update):
	return ConversationHandler.END


join_delivery_conv_handler = ConversationHandler(
	entry_points=[CommandHandler('joindelivery', join_delivery_conv_handler)],
	states={
		DELIVERY_ID: [MessageHandler(Filters.text, delivery_id)],
		QUANTITY: [MessageHandler(Filters.text, quantity)],
		PAYMENT_METHOD: [MessageHandler(Filters.text, payment_method)],
		REMARKS: [MessageHandler(Filters.text, remarks)],
	},
	fallbacks=[CommandHandler('cancel', cancel)]
)