import logging
import requests
import uuid
import os
from bs4 import BeautifulSoup as bs
import pandas as pd
from random import randrange
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext, PicklePersistence
import re

regex = re.compile(r'^(?:http)s?://(www.)?bazaraki.com/.+', re.IGNORECASE)


# Enable logging
loglevel = os.getenv('LOGLEVEL', 'INFO')
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=loglevel
)
TOKEN = os.getenv('TOKEN')
WEBSITE_DOMAIN = "https://www.bazaraki.com"
last_sended_adv = {}


logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('''Hi! BazarakiBot welkomes you!
Use /subscribe and URL to subscribe to Bazaraki advs
Use /list to show current subscription
Use /unsubscribe and subscriptionID to unsubscribe''')

def subscribe(update: Update, context: CallbackContext) -> None:
    print(update)
    print(context)
    chat_id = update.message.chat_id
    if not context.args:
      update.message.reply_text("Please send me the link, for example https://www.bazaraki.com/real-estate/")
    else:
      link = context.args[0]
      #validate baxaraki link
      if re.match(regex, link) is not None:
        subsID = str(chat_id)+'_'+str(uuid.uuid4())[:6]
        context.user_data[subsID] = link
        update.message.reply_text('You are subscribed. Subscription ID: ' + subsID)
        subsctiption_job(context,{'chat_id':chat_id,'link':link},subsID)
        # context.job_queue.run_repeating(prepare_message, interval=60, first=1, context={'chat_id':chat_id,'link':link}, name=subsID)
      else:
        update.message.reply_text('Please send me the RIGHT link with filter, for example https://www.bazaraki.com/real-estate/')

def restore_subscriptions(dispatcher):
  user_data = dispatcher.user_data
  logging.debug(user_data)
  if len(user_data) > 0:
    logging.info("Restoring subscriptions...")
    for chat_id in user_data:
      for subs_id in user_data[chat_id]:
        link = user_data[chat_id][subs_id]
        subsctiption_job(dispatcher,{'chat_id':chat_id,'link':link},subs_id)

def subsctiption_job(dispatcher,context,subsid):
  dispatcher.job_queue.run_repeating(prepare_message, interval=60, first=1, context=context, name=subsid)


def prepare_message(context):
    """Send the message."""
    job = context.job
    global last_sended_adv
    # print(last_sended_adv)
    last_advs_list = parse(job.context['link'])
    if job.name not in last_sended_adv.keys():
      last_adv = last_advs_list[-1]
      last_sended_adv[job.name] = last_adv['adv_href']
      adv_to_send = last_adv
      send_message(context, adv_to_send)
    else:
      last_index_in_list = len(last_advs_list) - 1
      for dict_ in [x for x in last_advs_list if x["adv_href"] == last_sended_adv[job.name]]:
        last_sended_adv_index = (last_advs_list.index(dict_))
      
      if last_sended_adv_index < last_index_in_list:
        unsended_advs = last_advs_list[last_sended_adv_index + 1:last_index_in_list + 1]
        for adv_to_send in unsended_advs:
          last_sended_adv[job.name] = adv_to_send['adv_href']
          send_message(context, adv_to_send)
      else:
        logging.info('Job ' + str(job.name) + ' No new advs')
  
def send_message(context,adv_to_send):
    job = context.job
    context.bot.send_message(job.context['chat_id'], parse_mode='HTML', text=("<a href='{}{}'> {} </a>".format(WEBSITE_DOMAIN,adv_to_send['adv_href'],adv_to_send['adv_title'])))
    logging.info('Job ' + str(job.name) + ' Sending message: ' + str(adv_to_send) )

def parse(url):
    r = requests.get(url)
    soup = bs(r.text, "html.parser")
    last_advs_list = []
    adv_simple_block = soup.find_all('ul', class_="list-simple__output js-list-simple__output")
    for block in adv_simple_block:
      adv_list_block = block.find_all('div', class_='list-announcement-block')
      for one_adv in adv_list_block:

        adv_title = one_adv.find('a', class_='announcement-block__title')['content']
        adv_href = one_adv.find('a', class_='announcement-block__title')['href']

        adv_attrs = {"adv_title" : adv_title,         
                    "adv_href" : adv_href}

        last_advs_list.append(adv_attrs)
    
    last_advs_list.reverse()
    # return last 60 advs
    return last_advs_list

def unsubscribe(update: Update, context: CallbackContext) -> None:
    """Remove the job if the user changed their mind."""
    # chat_id = update.message.chat_id
    if len(context.args) > 0:
      subsID = context.args[0]
      job_removed = remove_job_if_exists(subsID, context)
      text = 'Subscription cancelled!' if job_removed else 'You have no subscription'
    else:
      text = "Please send me subscriptionID from /list"
    update.message.reply_text(text)

def remove_job_if_exists(name, context):
    """Remove job with given name. Returns whether job was removed."""
    # current_jobs = context.job_queue.get_jobs_by_name(name)
    current_jobs = context.user_data
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
        del current_jobs[name]
    return True

def jobList(update: Update, context: CallbackContext) -> None:
    """List of subscriptions."""
    message = ""
    # print(type(context.job_queue.jobs()))
    if len(context.job_queue.jobs()) > 0:
      for job in context.job_queue.jobs():
        message = message + "/unsubscribe " + job.name + "\n"
    else:
      message = "No active subscribtions"
    print(context.user_data)
    chat_id = update.message.chat_id
    # print(message)
    context.bot.send_message(chat_id, parse_mode='HTML', text=message)

    # update.message.reply_text(message)

def main():
    """Run bot."""
    pp = PicklePersistence(filename='bazarakibot')
    updater = Updater(TOKEN, persistence=pp, use_context=True)

    dispatcher = updater.dispatcher
    #restore previos subscriptions
    restore_subscriptions(dispatcher)
    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", start))
    dispatcher.add_handler(CommandHandler("subscribe", subscribe))
    dispatcher.add_handler(CommandHandler("unsubscribe", unsubscribe))
    dispatcher.add_handler(CommandHandler("list", jobList))
    
    

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
    # parse('https://www.bazaraki.com/car-motorbikes-boats-and-parts/cars-trucks-and-vans/lemesos-district-limassol/')