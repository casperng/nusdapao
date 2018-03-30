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
    return ConversationHandler.END


view_all_orders_conv_handler = ConversationHandler(
	entry_points=[CommandHandler('viewallorders', view_all_orders)],
	states={
	},
	per_chat=False
)