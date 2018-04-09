import logging
import os

from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram.error import (TelegramError, Unauthorized, BadRequest,
                            TimedOut, ChatMigrated, NetworkError)
import startdelivery, joindelivery, vieworders, removeorder, closeorder, viewallorders

def start(bot, update):
	update.effective_message.reply_text("Hi there! Please type / and click on a command from the list!")

def error(bot, update, error):
	try:
		raise error
	except Unauthorized:
		if update.message.from_user.id != update.message.chat_id:
			bot.send_message(update.message.chat_id,
							 "You have to start a conversation with me first!",
							 reply_markup=InlineKeyboardMarkup([[
								 InlineKeyboardButton(text="Start!",
													  url="https://telegram.me/" + os.environ.get('BOT_NAME', 'nusdapao_bot'))
							 ]]))
		return
	except BadRequest:
		# handle malformed requests - read more below!
		return
	except TimedOut:
		# handle slow connection problems
		return
	except NetworkError:
		# handle other connection problems
		return
	except ChatMigrated as e:
		# the chat_id of a group has changed, use e.new_chat_id instead
		return
	except TelegramError as e:
		logger.error(str(e))
		# handle all other telegram related errors
		return


if __name__ == "__main__":
	# Set these variable to the appropriate values
	TOKEN = os.environ.get('BOT_TOKEN')
	NAME = 'nusdapao'

	# Port is given by Heroku
	PORT = os.environ.get('PORT')

	# Enable logging
	logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
						level=logging.INFO)
	logger = logging.getLogger(__name__)

	# Set up the Updater
	updater = Updater(TOKEN)
	dp = updater.dispatcher

	# Add handlers
	dp.add_handler(CommandHandler('start', start))
	dp.add_handler(startdelivery.start_delivery_conv_handler)
	dp.add_handler(joindelivery.join_delivery_conv_handler)
	dp.add_handler(vieworders.view_orders_conv_handler)
	dp.add_handler(removeorder.remove_order_conv_handler)
	dp.add_handler(closeorder.close_order_conv_handler)
	dp.add_handler(CommandHandler('viewallorders', viewallorders.view_all_orders)),
	dp.add_error_handler(error)

	# Start the webhook
	updater.start_webhook(listen="0.0.0.0",
						  port=int(PORT),
						  url_path=TOKEN)
	updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(NAME, TOKEN))

updater.idle()
