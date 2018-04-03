from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
						  ConversationHandler)

import logging
import database
import notifications
import utilities
from utilities import only_allow_private_message
import pytz
import os
from datetime import date, datetime, timedelta

ORDER_CONFIRM_MESSAGE = 'Delivery for {dish} from {location} by {username} {usertag}\n' \
						'Price: {price} (+{markup} delivery fee)\n' \
						'Closing: {closes}\n' \
						'Arriving: {arrival}\n' \
						'Pickup: {pickup}\n' \
						'Join the delivery with code {id}'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

logger = logging.getLogger(__name__)

ORDERING_FROM, DISH, PRICE, MARK_UP, ORDER_CLOSE, ARRIVAL_TIME, PICK_UP_POINT, CONFIRMATION = range(8)


def start_delivery(bot, update, user_data):
	utilities.pop_all_keys(user_data)
	user_data['chat'] = update.message.chat_id
	user_data['user'] = update.message.from_user.id
	user_data['username'] = update.message.from_user.first_name
	user_data['usertag'] = update.message.from_user.username or ''
	if user_data['usertag']:
		user_data['usertag'] = '@' + user_data['usertag']
	user_data['confirmation'] = False

	logger.info("Current user_data: %s", user_data)

	bot.send_message(update.message.from_user.id, 'Hi! Where are you ordering food from? Send /cancel to cancel this request anytime')

	return ORDERING_FROM


@only_allow_private_message
def ordering_from(bot, update, user_data):
	user = update.message.from_user

	user_data['location'] = update.message.text

	logger.info("Current user_data: %s", user_data)
	logger.info("%s Ordering from: %s", user.first_name, update.message.text)

	if user_data['confirmation']:
		return send_confirmation(bot, update, user_data)

	update.message.reply_text(
		'What food are you delivering?')

	return DISH


@only_allow_private_message
def dish(bot, update, user_data):
	user = update.message.from_user

	user_data['dish'] = update.message.text

	logger.info("Current user_data: %s", user_data)
	logger.info("%s dish: %s", user.first_name, update.message.text)

	if user_data['confirmation']:
		return send_confirmation(bot, update, user_data)

	update.message.reply_text(
		'What is the price in dollars?')

	return PRICE


@only_allow_private_message
def price(bot, update, user_data):
	user = update.message.from_user

	try:
		user_data['price'] = cents_from_text(update.message.text)
	except:
		update.message.reply_text("Please enter a valid price in dollars!")
		return PRICE

	logger.info("%s Price: %s", user.first_name, update.message.text)

	if user_data['confirmation']:
		return send_confirmation(bot, update, user_data)

	update.message.reply_text(
		'What is the markup in dollars?')

	return MARK_UP


@only_allow_private_message
def mark_up(bot, update, user_data):
	user = update.message.from_user

	try:
		user_data['markup'] = cents_from_text(update.message.text)
	except:
		update.message.reply_text("Please enter a valid markup in dollars!")
		return MARK_UP

	logger.info("%s Markup: %s", user.first_name, update.message.text)

	if user_data['confirmation']:
		return send_confirmation(bot, update, user_data)

	update.message.reply_text(
		'What time will the order CLOSE? (Use HHMM, e.g. 1630 for 4:30pm, 0430 for 4:30am)')

	return ORDER_CLOSE


@only_allow_private_message
def order_close(bot, update, user_data):
	user = update.message.from_user

	try:
		user_data['closes'] = datetime_from_text(update.message.text)
	except:
		update.message.reply_text(
		'Invalid close time! Please use HHMM, e.g. 1630 for 4:30pm, 0430 for 4:30am')
		return ORDER_CLOSE

	logger.info("Current user_data: %s", user_data)
	logger.info("%s Order closes: %s", user.first_name, update.message.text)

	if user_data['confirmation']:
		return send_confirmation(bot, update, user_data)

	update.message.reply_text(
		'What time will the order ARRIVE? (Use HHMM, e.g. 1630 for 4:30pm, 0430 for 4:30am)')

	return ARRIVAL_TIME


@only_allow_private_message
def arrival_time(bot, update, user_data):
	user = update.message.from_user

	try:
		user_data['arrival'] = datetime_from_text(update.message.text)
	except:
		update.message.reply_text(
		'Invalid arrival time! Please use HHMM, e.g. 1630 for 4:30pm, 0430 for 4:30am')
		return ARRIVAL_TIME

	logger.info("Current user_data: %s", user_data)
	logger.info("%s Arrival time: %s", user.first_name, update.message.text)

	if user_data['confirmation']:
		return send_confirmation(bot, update, user_data)

	update.message.reply_text(
		'Where is the pickup point?')

	return PICK_UP_POINT


@only_allow_private_message
def pick_up_point(bot, update, user_data):
	user = update.message.from_user

	user_data['pickup'] = update.message.text

	return send_confirmation(bot, update, user_data)


def register_delivery(bot, update, user_data, job_queue):
	user = update.message.from_user
	delivery = { k: v for k, v in user_data.items() }

	deliveryId = database.start_delivery(delivery)
	delivery['id'] = deliveryId

	logger.info("%s Pickup point: %s", user.first_name, update.message.text)
	update.message.reply_text(
		'Thank you, your delivery has been registered! Its ID is %s' % str(deliveryId))

	job1 = job_queue.run_once(
		notifications.notify_close,
		delivery['closes'].astimezone().replace(tzinfo=None),
		context=delivery,
		name=str(delivery['id']) + '_close_job')
	job2 = job_queue.run_once(
		notifications.notify_arrival_soon,
		delivery['arrival'].astimezone().replace(tzinfo=None) - timedelta(
			minutes=int(os.environ.get('ARRIVAL_ADVANCE_NOTIFICATION_TIME', '15'))),
		context=delivery)
	job3 = job_queue.run_once(
		notifications.notify_arrival,
		delivery['arrival'].astimezone().replace(tzinfo=None),
		context=delivery)

	logger.info('%s\'s delivery: %s', user.first_name, delivery)

	deliveries = database.get_all_orders()
	text = utilities.build_view_all_orders_string(deliveries)
	bot.send_message(user_data['chat'],
					 text)

	return ConversationHandler.END


@only_allow_private_message
def edit_choice(bot, update, user_data, job_queue):
	choice = update.message.text
	if choice == '/yes':
		return register_delivery(bot, update, user_data, job_queue)
	elif choice == '/dish':
		update.message.reply_text("Please enter the new dish")
		return DISH
	elif choice == '/from':
		update.message.reply_text("Please enter the new location")
		return ORDERING_FROM
	elif choice == '/closing':
		update.message.reply_text("Please enter the new closing time")
		return ORDER_CLOSE
	elif choice == '/arriving':
		update.message.reply_text("Please enter the new arrival time")
		return ARRIVAL_TIME
	elif choice == '/pickup':
		update.message.reply_text("Please enter the new pickup location")
		return PICK_UP_POINT
	elif choice == '/markup':
		update.message.reply_text("Please enter the new markup in cents")
		return MARK_UP
	elif choice == '/price':
		update.message.reply_text("Please enter the new price in cents")
		return PRICE
	else:
		update.message.reply_text("Invalid command, please try again")
		return CONFIRMATION


def send_confirmation(bot, update, user_data):
	user_data['confirmation'] = True
	userid = update.message.from_user.id
	text = "Reply /yes to confirm your details, or click on the headers to edit them:\n" \
		   "/from: " + user_data['location'] + "\n" \
		   "/dish: " + user_data['dish'] + "\n" \
		   "/price: " + utilities.cents_to_dollars_string(user_data['price']) + "\n" \
		   "/markup: " + utilities.cents_to_dollars_string(user_data['markup']) + "\n" \
		   "/closing: " + utilities.build_date_string(user_data['closes']) + "\n" \
		   "/arriving: " + utilities.build_date_string(user_data['arrival']) + "\n" \
		   "/pickup: " + user_data['pickup']
	update.message.reply_text(text)
	return CONFIRMATION


def cancel_prompt(bot, update):
	bot.send_message(update.message.from_user.id, "Perhaps you meant to /cancel the current startdelivery request?")


@only_allow_private_message
def cancel(bot, update):
	user = update.message.from_user
	logger.info("User %s canceled the conversation.", user.first_name)
	update.message.reply_text(
		"Your request to start a delivery has been cancelled!")
	return ConversationHandler.END


def cents_from_text(text):
	if text[0] == '$':
		text = text[1:]
	price_dollars = float(text)
	return int(price_dollars * 100)


def datetime_from_text(text):
	r_date = date.today().strftime(r" %Y %m %d +0800")
	r_datetime = datetime.strptime(text + r_date, r"%H%M %Y %m %d %z")
	if r_datetime < datetime.now(tz=pytz.UTC):
		r_datetime += timedelta(days=1)
	return r_datetime


start_delivery_conv_handler = ConversationHandler(
	entry_points=[CommandHandler('startdelivery', start_delivery, pass_user_data=True)],
	states={
		DISH: [MessageHandler(Filters.text, dish, pass_user_data=True),
			   CommandHandler('cancel', cancel)],

		ORDERING_FROM: [MessageHandler(Filters.text, ordering_from, pass_user_data=True),
						CommandHandler('cancel', cancel)],

		PRICE: [MessageHandler(Filters.text, price, pass_user_data=True),
				CommandHandler('cancel', cancel)],

		MARK_UP: [MessageHandler(Filters.text, mark_up, pass_user_data=True),
				  CommandHandler('cancel', cancel)],

		ORDER_CLOSE: [MessageHandler(Filters.text, order_close, pass_user_data=True),
					  CommandHandler('cancel', cancel)],

		ARRIVAL_TIME: [MessageHandler(Filters.text, arrival_time, pass_user_data=True),
					   CommandHandler('cancel', cancel)],

		PICK_UP_POINT: [MessageHandler(Filters.text, pick_up_point, pass_user_data=True),
						CommandHandler('cancel', cancel)],

		CONFIRMATION: [CommandHandler('yes', edit_choice, pass_job_queue=True, pass_user_data=True),
					   CommandHandler('dish', edit_choice, pass_job_queue=True, pass_user_data=True),
					   CommandHandler('pickup', edit_choice, pass_job_queue=True, pass_user_data=True),
					   CommandHandler('arriving', edit_choice, pass_job_queue=True, pass_user_data=True),
					   CommandHandler('closing', edit_choice, pass_job_queue=True, pass_user_data=True),
					   CommandHandler('markup', edit_choice, pass_job_queue=True, pass_user_data=True),
					   CommandHandler('price', edit_choice, pass_job_queue=True, pass_user_data=True),
					   CommandHandler('from', edit_choice, pass_job_queue=True, pass_user_data=True)]
	},
	fallbacks=[CommandHandler('cancel', cancel),
			   MessageHandler(Filters.all, cancel_prompt)],
	per_chat=False
)