import logging
import uuid
import re
from telegram import Update
from telegram.ext import CallbackContext
from helpers import subsctiption_job,remove_job_if_exists
from settings import REGEX

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('''Hi! BazarakiBot welcomes you!
Use /subscribe https://www.bazaraki.com/real-estate/ (URL to subscribe to Bazaraki advs) 
Use /list - to show current subscription
Use /unsubscribe and subscriptionID to unsubscribe''')

def subscribe(update: Update, context: CallbackContext) -> None:
    logging.debug(update)
    chat_id = update.message.chat_id
    if not context.args:
      update.message.reply_text("Please send me the link, for example https://www.bazaraki.com/real-estate/")
    else:
      link = context.args[0]
      #validate baxaraki link
      if re.match(REGEX, link) is not None:
        subsID = str(uuid.uuid4())[:6]
        if chat_id not in context.bot_data:
          context.bot_data[chat_id] = {}
        context.bot_data[chat_id][subsID] = {"link" : link, "lastId": ""}
        update.message.reply_text('You are subscribed. Subscription ID: ' + subsID)

        subsctiption_job(context,subsID,chat_id)
        # context.job_queue.run_repeating(prepare_message, interval=60, first=1, context={'chat_id':chat_id,'link':link}, name=subsID)
      else:
        update.message.reply_text('Please send me the RIGHT link with filter, for example https://www.bazaraki.com/real-estate/')

def unsubscribe(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    args = update.message.text.split("_")[1]
    if len(args) > 0:
      subsID = args
      job_removed = remove_job_if_exists(subsID, context, chat_id)
      text = 'Subscription ' + subsID + ' cancelled!' if job_removed else 'You have no subscription'
    else:
      text = "Please send me subscriptionID from /list"
    update.message.reply_text(text)

def jobList(update: Update, context: CallbackContext) -> None:
    """List of subscriptions."""
    message = ""
    i = 0
    chat_id = update.message.chat_id
    if len(context.job_queue.jobs()) > 0:
      for job in context.job_queue.jobs():
        if job.context['chat_id'] == chat_id:
          i += 1
          message = message + "/unsubscribe_" + job.name + " " + context.bot_data[chat_id][job.name]['link'] + "\n"
    if i == 0:
      message = "No active subscribtions"
    logging.debug(context.bot_data)
    context.bot.send_message(chat_id, parse_mode='HTML', text=message)

def fullList(update: Update, context: CallbackContext) -> None:
    """Full list of subscriptions."""
    chat_id = update.message.chat_id
    message = context.bot_data
    logging.debug(context.bot_data)
    context.bot.send_message(chat_id, parse_mode='HTML', text=message)

__all__ = ['start','subscribe', 'unsubscribe','jobList']
