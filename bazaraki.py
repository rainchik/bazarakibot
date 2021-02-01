import logging
# import pandas as pd
from telegram.ext import Updater, CommandHandler, PicklePersistence, MessageHandler, Filters
import re

from helpers import restore_subscriptions
from callbacks import start, subscribe, unsubscribe, jobList
from settings import TOKEN, LOGLEVEL, PERSISTENCE_VOL

# Enable logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=LOGLEVEL
)

last_sended_adv = {}
logger = logging.getLogger(__name__)

def main():
    """Run bot."""
    pp = PicklePersistence(filename=PERSISTENCE_VOL + '/bazarakibot')
    try:
        updater = Updater(TOKEN, persistence=pp, use_context=True)
    except ValueError:
        logging.error("No bot TOKEN in env variables. Exiting")
        return

    dispatcher = updater.dispatcher
    #restore previos subscriptions
    restore_subscriptions(dispatcher)
    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", start))
    dispatcher.add_handler(CommandHandler("subscribe", subscribe))
    dispatcher.add_handler(MessageHandler(Filters.regex('^\/unsubscribe_.+$'), unsubscribe))
    dispatcher.add_handler(CommandHandler("list", jobList))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
