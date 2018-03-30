import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
						  ConversationHandler)

import database

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

logger = logging.getLogger(__name__)

DELIVERY_ID, QUANTITY, PAYMENT_METHOD, REMARKS = range(4)

def join_delivery(bot, update, chat_data):
	chat_data[update.message.from_user.id] = {
		'userid': update.message.from_user.id,
		'username': update.message.from_user.first_name
	}

	bot.send_message(update.message.from_user.id, 'What delivery ID are you ordering for? Send /cancel to cancel this request anytime')

	return DELIVERY_ID

def delivery_id(bot, update, chat_data):
	user = update.message.from_user

	deliveryId = update.message.text
	if not database.is_open_delivery_id(deliveryId):
		update.message.reply_text(
			'Invalid delivery ID, please try again. Check that it hasn\'t closed')
		return DELIVERY_ID

	if not database.is_order_open(deliveryId):
		update.message.reply_text(
			'Sorry, the order has already closed!')
		return ConversationHandler.END

	logger.info("%s for delivery: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'How many of this item are you getting?')

	chat_data[user.id]['deliveryId'] = update.message.text

	return QUANTITY

def quantity(bot, update, chat_data):
	user = update.message.from_user

	logger.info("%s for quantity: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'What is your payment method?')

	chat_data[user.id]['qty'] = update.message.text

	return PAYMENT_METHOD

def payment_method(bot, update, chat_data):
	user = update.message.from_user

	logger.info("%s payment method: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'Any remarks? Type "no" if you have none')

	chat_data[user.id]['method'] = update.message.text

	return REMARKS

def remarks(bot, update, chat_data):
	user = update.message.from_user

	remarks = update.message.text
	if remarks.lower() == 'no':
		remarks = ''

	chat_data[user.id]['remarks'] = remarks
	order = chat_data.pop(user.id)

	database.add_order(order)

	logger.info("%s payment method: %s", user.first_name, order)
	update.message.reply_text(
		'Your order has been registered!')

	return ConversationHandler.END

def cancel(bot, update):
	update.message.reply_text(
		"Your request to join the delivery has been cancelled!")
	return ConversationHandler.END


join_delivery_conv_handler = ConversationHandler(
	entry_points=[CommandHandler('joindelivery', join_delivery, pass_chat_data=True)],
	states={
		DELIVERY_ID: [MessageHandler(Filters.text, delivery_id, pass_chat_data=True),
					  CommandHandler('cancel', cancel)],
		QUANTITY: [MessageHandler(Filters.text, quantity, pass_chat_data=True),
				   CommandHandler('cancel', cancel)],
		PAYMENT_METHOD: [MessageHandler(Filters.text, payment_method, pass_chat_data=True),
						 CommandHandler('cancel', cancel)],
		REMARKS: [MessageHandler(Filters.text, remarks, pass_chat_data=True),
				  CommandHandler('cancel', cancel)],
	},
	fallbacks=[CommandHandler('cancel', cancel)]
)