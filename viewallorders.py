import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
						  ConversationHandler)

import database
import utilities

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
					level=logging.INFO)

logger = logging.getLogger(__name__)


def view_all_orders(bot, update):
    deliveries = database.get_all_orders()
    logger.info("View all deliveries: %s", deliveries)
    text = utilities.build_view_all_orders_string(deliveries)
    logger.info("All orders: " + text)
    bot.send_message(update.message.from_user.id,
                     text)
