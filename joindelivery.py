import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
						  ConversationHandler)

import database

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

logger = logging.getLogger(__name__)

DELIVERY_ID, QUANTITY, PAYMENT_METHOD, REMARKS, CONFIRMATION = range(5)


def join_delivery(bot, update, chat_data):
	chat_data[update.message.from_user.id] = {
		'userid': update.message.from_user.id,
		'username': update.message.from_user.first_name
	}

	chat_data['confirmation'] = False

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

	chat_data[user.id]['qty'] = update.message.text

	if chat_data['confirmation']:
		return send_confirmation(bot, update, chat_data)

	update.message.reply_text(
		'What is your payment method?')

	return PAYMENT_METHOD


def payment_method(bot, update, chat_data):
	user = update.message.from_user

	logger.info("%s payment method: %s", user.first_name, update.message.text)

	chat_data[user.id]['method'] = update.message.text

	if chat_data['confirmation']:
		return send_confirmation(bot, update, chat_data)

	update.message.reply_text(
		'Any remarks? Type "no" if you have none')

	return REMARKS


def remarks(bot, update, chat_data):
	user = update.message.from_user

	remarks = update.message.text
	if remarks.lower() == 'no':
		remarks = ''

	chat_data[user.id]['remarks'] = remarks
	logger.info("%s payment remarks: %s", user.first_name, remarks)

	return send_confirmation(bot, update, chat_data)


def register_order(bot, update, chat_data):
	user = update.message.from_user
	order = chat_data.pop(user.id)
	database.add_order(order)
	update.message.reply_text(
		'Your order has been registered!')
	return ConversationHandler.END


def edit_choice(bot, update, chat_data):
	choice = update.message.text
	if choice == '/yes':
		return register_order(bot, update, chat_data)
	elif choice == '/quantity':
		update.message.reply_text("Please enter the new quantity")
		return QUANTITY
	elif choice == '/remarks':
		update.message.reply_text("Please enter the new remarks, type \"no\" if you have none")
		return REMARKS
	elif choice == '/method':
		update.message.reply_text("Please enter the new payment method")
		return PAYMENT_METHOD
	else:
		update.message.reply_text("Invalid command, please try again")
		return CONFIRMATION


def send_confirmation(bot, update, chat_data):
	chat_data['confirmation'] = True
	userid = update.message.from_user.id
	text = "Reply /yes to confirm your details, or click on the headers to edit them:\n" \
		   "/quantity: " + chat_data[userid]['qty'] + "\n" \
		   "/remarks: " + chat_data[userid]['remarks'] + "\n" \
		   "payment /method: " + chat_data[userid]['method']
	update.message.reply_text(text)
	return CONFIRMATION


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

		CONFIRMATION: [CommandHandler('yes', edit_choice, pass_chat_data=True),
					   CommandHandler('quantity', edit_choice, pass_chat_data=True),
					   CommandHandler('remarks', edit_choice, pass_chat_data=True),
					   CommandHandler('method', edit_choice, pass_chat_data=True)]
	},
	fallbacks=[CommandHandler('cancel', cancel)]
)