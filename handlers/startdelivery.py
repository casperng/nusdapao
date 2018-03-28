
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
						  ConversationHandler)

import logging

CACHE = {}

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

logger = logging.getLogger(__name__)


ORDERING_FROM, ORDER_CLOSE, ARRIVAL_TIME, PICK_UP_POINT = range(4)

def initiate_convo(bot, update):
	CACHE[update.message.from_user.id] = {'chat': update.message.chat_id}

	bot.send_message(update.message.from_user.id, 'Hi! Where are you ordering food from?')

	return ORDERING_FROM

def ordering_from(bot, update):
	user = update.message.from_user
	if user.id not in CACHE:
		return ConversationHandler.END

	CACHE[user.id]['from'] = update.message.text

	logger.info("%s Ordering from: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'What time will the order close?')

	return ORDER_CLOSE

def order_close(bot, update):
	user = update.message.from_user
	if user.id not in CACHE:
		return ConversationHandler.END

	CACHE[user.id]['closes'] = update.message.text

	logger.info("%s Order closes: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'What time will the order arrive?')

	return ARRIVAL_TIME

def arrival_time(bot, update):
	user = update.message.from_user
	if user.id not in CACHE:
		return ConversationHandler.END

	CACHE[user.id]['arrival'] = update.message.text
	logger.info("%s Arrival time: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'Where is the pickup point?')

	return PICK_UP_POINT

def pick_up_point(bot, update):
	user = update.message.from_user
	if user.id not in CACHE:
		return ConversationHandler.END

	CACHE[user.id]['pickup'] = update.message.text

	logger.info("%s Pickup point: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'Thank you, your delivery has been registered!')

	logger.info('%s\'s order: %s', user.first_name, CACHE[user.id])

	return ConversationHandler.END

def cancel(bot, update):
	user = update.message.from_user
	CACHE.pop(user.id, None)

	logger.info("User %s canceled the conversation.", user.first_name)
	update.message.reply_text(
		'Alright, bye!')

	return ConversationHandler.END


conv_handler = ConversationHandler(
	entry_points=[CommandHandler('startdelivery', initiate_convo)],
	states={
		ORDERING_FROM: [MessageHandler(Filters.text, ordering_from)],

		ORDER_CLOSE: [MessageHandler(Filters.text, order_close)],

		ARRIVAL_TIME: [MessageHandler(Filters.text, arrival_time)],

		PICK_UP_POINT: [MessageHandler(Filters.text, pick_up_point)]
	},
	fallbacks=[CommandHandler('cancel', cancel)]
)