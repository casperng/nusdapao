import logging
from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)

import database

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

DELIVERY_ID = range(1)


def close_order(bot, update, job_queue):
    user_id = update.message.from_user.id
    deliveries = database.get_user_deliveries(user_id)

    if len(deliveries) == 1:
        deliveryid = deliveries[0]['deliveryid']
        database.close_order_for_delivery(user_id, deliveryid)
        notify_closed_for_delivery(job_queue, deliveryid)
        return ConversationHandler.END

    bot.send_message(user_id, 'What delivery ID are you closing orders for? Send /cancel to cancel this request anytime')

    return DELIVERY_ID


def delivery_id(bot, update, job_queue):
    deliveryid = update.message.text
    if not database.is_valid_delivery_id(deliveryid):
        update.message.reply_text(
            'Invalid delivery ID, please try again.')
        return DELIVERY_ID

    database.close_order_for_delivery(update.message.from_user.id, deliveryid)
    notify_closed_for_delivery(job_queue, deliveryid)

    update.message.reply_text(
        'Orders for your delivery have been closed!')
    return ConversationHandler.END


def notify_closed_for_delivery(job_queue, deliveryid):
    job = job_queue.get_jobs_by_name(str(deliveryid) + '_close_job')[0]
    job.run(job_queue.bot)


def cancel(bot, update):
    update.message.reply_text(
        "Your request to close orders has been cancelled!")
    return ConversationHandler.END


close_order_conv_handler = ConversationHandler(
    entry_points=[CommandHandler('closeorder', close_order, pass_job_queue=True)],
    states={
        DELIVERY_ID: [MessageHandler(Filters.text, delivery_id, pass_job_queue=True),
                      CommandHandler('cancel', cancel)],
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)