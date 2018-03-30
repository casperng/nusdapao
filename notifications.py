from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
						  ConversationHandler)

import os
import logging
import database
import utilities
from datetime import date, datetime, timedelta

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

logger = logging.getLogger(__name__)


def notify_close(bot, job):
    text = 'Orders for your delivery have closed!\n'
    orders = database.get_orders(job.context['id'])

    bot.send_message(
        job.context['user'],
        text + utilities.build_view_orders_string(orders))


def notify_arrival_soon(bot, job):
    text = 'The order for {location} will arrive in {arrival_time} minutes! The pickup point is at {pickup}'.format(
        **job.context, arrival_time=os.environ.get('ARRIVAL_ADVANCE_NOTIFICATION_TIME', '15'))

    def notify_user(userid):
        bot.send_message(userid, text=text)

    users = database.get_users(job.context['id'])
    logger.info("Notifying users of arrival soon %s", users)

    for user in users:
        notify_user(user)

def notify_arrival(bot, job):
    text = 'The order for {location} is arriving! The pickup point is at {pickup}'.format(**job.context)

    def notify_user(userid):
        bot.send_message(userid, text=text)

    users = database.get_users(job.context['id'])
    logger.info("Notifying users of arrival %s", users)

    for user in users:
        notify_user(user)