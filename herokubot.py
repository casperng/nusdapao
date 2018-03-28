import logging
import os

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters



if __name__ == "__main__":
	# Set these variable to the appropriate values
	TOKEN = os.environ.get('BOT_TOKEN')
	NAME = nusdapao

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
	dp.add_handler(MessageHandler(Filters.text, echo))
	dp.add_handler(error)

	# Start the webhook
	updater.start_webhook(listen="0.0.0.0",
						  port=int(PORT),
						  url_path=TOKEN)
	updater.bot.setWebhook("https://{}.herokuapp.com/{}".format(NAME, TOKEN))

updater.idle()