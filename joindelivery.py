import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
						  ConversationHandler)

import database
import utilities
from utilities import only_allow_private_message

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

logger = logging.getLogger(__name__)

DELIVERY_ID, QUANTITY, PAYMENT_METHOD, REMARKS, CONFIRMATION = range(5)


@only_allow_private_message
def join_delivery(bot, update, user_data):
	utilities.pop_all_keys(user_data)
	user_data['userid'] = update.message.from_user.id
	user_data['username'] = update.message.from_user.first_name
	user_data['confirmation'] = False

	bot.send_message(update.message.from_user.id, 'What delivery ID are you ordering for? Send /cancel to cancel this request anytime')

	return DELIVERY_ID


@only_allow_private_message
def delivery_id(bot, update, user_data):
	user = update.message.from_user

	deliveryId = update.message.text
	if not database.is_valid_delivery_id(deliveryId):
		update.message.reply_text(
			'Invalid delivery ID. Please enter a valid ID')
		return DELIVERY_ID

	if not database.is_order_open(deliveryId):
		update.message.reply_text(
			'Sorry, the order has already closed!')
		return ConversationHandler.END

	logger.info("%s for delivery: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'How many of this item(' + 'OOL' + ') are you getting? (Please enter a numerical figure, additional comments can be filled in under remarks)')

	user_data['deliveryId'] = update.message.text

	return QUANTITY


@only_allow_private_message
def quantity(bot, update, user_data):
	user = update.message.from_user

	logger.info("%s for quantity: %s", user.first_name, update.message.text)

	user_data['qty'] = update.message.text

	if user_data['confirmation']:
		return send_confirmation(bot, update, user_data)

	update.message.reply_text(
		'What is your payment method?')

	return PAYMENT_METHOD


@only_allow_private_message
def payment_method(bot, update, user_data):
	user = update.message.from_user

	logger.info("%s payment method: %s", user.first_name, update.message.text)

	user_data['method'] = update.message.text

	if user_data['confirmation']:
		return send_confirmation(bot, update, user_data)

	update.message.reply_text(
		'Any remarks? Type "no" if you have none')

	return REMARKS


@only_allow_private_message
def remarks(bot, update, user_data):
	user = update.message.from_user

	remarks = update.message.text
	if remarks.lower() == 'no':
		remarks = ''

	user_data['remarks'] = remarks
	logger.info("%s payment remarks: %s", user.first_name, remarks)

	return send_confirmation(bot, update, user_data)


def register_order(bot, update, user_data):
	database.add_order(user_data)
	update.message.reply_text(
		'Your order has been registered!')
	return ConversationHandler.END


@only_allow_private_message
def edit_choice(bot, update, user_data):
	choice = update.message.text
	if choice == '/yes':
		return register_order(bot, update, user_data)
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


def send_confirmation(bot, update, user_data):
	user_data['confirmation'] = True
	text = "Reply /yes to confirm your details, or click on the headers to edit them:\n" \
		   "/quantity: " + user_data['qty'] + "\n" \
		   "/remarks: " + user_data['remarks'] + "\n" \
		   "payment /method: " + user_data['method']
	update.message.reply_text(text)
	return CONFIRMATION


def cancel_prompt(bot, update):
	bot.send_message(update.message.from_user.id, "Perhaps you meant to /cancel the current joindelivery request?")


@only_allow_private_message
def cancel(bot, update):
	update.message.reply_text(
		"Your request to join the delivery has been cancelled!")
	return ConversationHandler.END


join_delivery_conv_handler = ConversationHandler(
	entry_points=[CommandHandler('startordering', join_delivery, pass_user_data=True)],
	states={
		DELIVERY_ID: [MessageHandler(Filters.text, delivery_id, pass_user_data=True),
					  CommandHandler('cancel', cancel)],

		QUANTITY: [MessageHandler(Filters.text, quantity, pass_user_data=True),
				   CommandHandler('cancel', cancel)],

		PAYMENT_METHOD: [MessageHandler(Filters.text, payment_method, pass_user_data=True),
						 CommandHandler('cancel', cancel)],

		REMARKS: [MessageHandler(Filters.text, remarks, pass_user_data=True),
				  CommandHandler('cancel', cancel)],

		CONFIRMATION: [CommandHandler('yes', edit_choice, pass_user_data=True),
					   CommandHandler('quantity', edit_choice, pass_user_data=True),
					   CommandHandler('remarks', edit_choice, pass_user_data=True),
					   CommandHandler('method', edit_choice, pass_user_data=True)]
	},
	fallbacks=[CommandHandler('cancel', cancel),
			   MessageHandler(Filters.all, cancel_prompt)],
	per_chat=False
)
