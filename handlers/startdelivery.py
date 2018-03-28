
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
						  ConversationHandler)

import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

logger = logging.getLogger(__name__)


ORDERING_FROM, ORDER_CLOSE, ARRIVAL_TIME, PICK_UP_POINT = range(4)

def initiate_convo(bot, update):
	update.message.reply_text(
		'Hi! Where are you ordering food from?')

	return ORDERING_FROM

def ordering_from(bot, update):
	user = update.message.from_user
	logger.info("%s Ordering from: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'What time will the order close?')

	return ORDER_CLOSE

def order_close(bot, update):
	user = update.message.from_user
	logger.info("%s Order closes: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'What time will the order arrive?')

	return ARRIVAL_TIME

def arrival_time(bot, update):
	user = update.message.from_user
	logger.info("%s Arrival time: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'Where is the pickup point?')

	return PICK_UP_POINT

def pick_up_point(bot, update):
	user = update.message.from_user
	logger.info("%s Pickup point: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'Thank you, your delivery has been registered!')

	return ConversationHandler.END
