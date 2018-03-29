from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
						  ConversationHandler)

import logging
import database
import notifications
from datetime import date, datetime, timedelta

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

logger = logging.getLogger(__name__)

def notify_arrival_soon(bot, job):
    text = 'The order for {location} will arrive in 15 minutes! The pickup point is at {pickup}'.format(**job.delivery)

    def notify_user(userid):
        bot.send_message(userid, text=text)

    users = database.get_users(job.context['id'])
    map(notify_user, users)


def notify_arrival(bot, job):
    text = 'The order for {location} is arriving! The pickup point is at {pickup}'.format(**job.delivery)

    def notify_user(userid):
        bot.send_message(userid, text=text)

    users = database.get_users(job.context['id'])
    map(notify_user, users)