from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
						  ConversationHandler)

import logging
import database
import notifications
import pytz
from datetime import date, datetime, timedelta

ORDER_CONFIRM_MESSAGE = 'Delivery for %s by %s\nClosing: %s\nArriving: %s\nPickup: %s\nJoin the delivery with code %s'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

logger = logging.getLogger(__name__)

ORDERING_FROM, ORDER_CLOSE, ARRIVAL_TIME, PICK_UP_POINT = range(4)

def start_delivery(bot, update, chat_data):
	chat_data[update.message.from_user.id] = {
		'chat': update.message.chat_id,
		'user': update.message.from_user.id
	}

	bot.send_message(update.message.from_user.id, 'Hi! Where are you ordering food from?')

	return ORDERING_FROM

def ordering_from(bot, update, chat_data):
	user = update.message.from_user

	chat_data[user.id]['location'] = update.message.text

	logger.info("%s Ordering from: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'What time will the order close? (Use HHMM, e.g. 1630 for 4:30pm, 0430 for 4:30am)')

	return ORDER_CLOSE

def order_close(bot, update, chat_data):
	user = update.message.from_user

	try:
		chat_data[user.id]['closes'] = datetime_from_text(update.message.text)
	except:
		update.message.reply_text(
		'Invalid close time! Please use HHMM, e.g. 1630 for 4:30pm, 0430 for 4:30am')
		return ORDER_CLOSE

	logger.info("%s Order closes: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'What time will the order arrive? (Use HHMM, e.g. 1630 for 4:30pm, 0430 for 4:30am)')

	return ARRIVAL_TIME

def arrival_time(bot, update, chat_data):
	user = update.message.from_user

	try:
		chat_data[user.id]['arrival'] = datetime_from_text(update.message.text)
	except:
		update.message.reply_text(
		'Invalid arrival time! Please use HHMM, e.g. 1630 for 4:30pm, 0430 for 4:30am')
		return ARRIVAL_TIME

	logger.info("%s Arrival time: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'Where is the pickup point?')

	return PICK_UP_POINT

def pick_up_point(bot, update, chat_data, job_queue):
	user = update.message.from_user

	chat_data[user.id]['pickup'] = update.message.text
	delivery = chat_data.pop(user.id)

	deliveryId = database.start_delivery(delivery)
	delivery['id'] = deliveryId

	logger.info("%s Pickup point: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'Thank you, your delivery has been registered!')

	# send message to group chat
	bot.send_message(
		delivery['chat'],
		ORDER_CONFIRM_MESSAGE %
		(delivery['location'], user.first_name, delivery['closes'], delivery['arrival'], delivery['pickup'], deliveryId)
	)

	job = job_queue.run_once(notifications.notify_arrival_soon, delivery['arrival'] - timedelta(minutes=15), context=delivery)
	job = job_queue.run_once(notifications.notify_arrival, delivery['arrival'], context=delivery)

	logger.info('%s\'s order: %s', user.first_name, delivery)

	return ConversationHandler.END

def cancel(bot, update):
	user = update.message.from_user

	logger.info("User %s canceled the conversation.", user.first_name)
	update.message.reply_text(
		'Alright, bye!')

	return ConversationHandler.END

def datetime_from_text(text):
	r_date = date.today().strftime(r" %Y %m %d +0800")
	r_datetime = datetime.strptime(text + r_date, r"%H%M %Y %m %d %z")
	if r_datetime < datetime.now(tz=pytz.UTC):
		r_datetime += timedelta(days=1)
	return r_datetime


start_delivery_conv_handler = ConversationHandler(
	entry_points=[CommandHandler('startdelivery', start_delivery, pass_chat_data=True)],
	states={
		ORDERING_FROM: [MessageHandler(Filters.text, ordering_from, pass_chat_data=True)],

		ORDER_CLOSE: [MessageHandler(Filters.text, order_close, pass_chat_data=True)],

		ARRIVAL_TIME: [MessageHandler(Filters.text, arrival_time, pass_chat_data=True)],

		PICK_UP_POINT: [MessageHandler(Filters.text, pick_up_point, pass_job_queue=True, pass_chat_data=True)]
	},
	fallbacks=[CommandHandler('cancel', cancel)]
)