import logging
import requests

from bs4 import BeautifulSoup as bs
from settings import WEBSITE_DOMAIN, POLLING_INTERVAL

def restore_subscriptions(dispatcher):
  bot_data = dispatcher.bot_data
  if len(bot_data) > 0:
    logging.info("Restoring subscriptions...")
    logging.info(bot_data)
    for chat_id in bot_data:
      for subs_id in bot_data[chat_id]:
        subsctiption_job(dispatcher,subs_id,chat_id)
  else:
    dispatcher.bot_data = {}

def subsctiption_job(dispatcher,subsid,chat_id):
  dispatcher.job_queue.run_repeating(prepare_message, interval=POLLING_INTERVAL, first=1, context={'dispatcher':dispatcher,'chat_id':chat_id}, name=subsid)


def prepare_message(context):
    """Send the message."""
    job = context.job
    chat_id = job.context['chat_id']

    last_sended_adv = job.context['dispatcher'].bot_data[chat_id][job.name]['lastId']
    last_advs_list = parse(job.context['dispatcher'].bot_data[chat_id][job.name]['link'])
    if len(last_sended_adv) == 0:
      last_adv = last_advs_list[-1]
      job.context['dispatcher'].bot_data[chat_id][job.name]['lastId'] = last_adv['adv_href']
      adv_to_send = last_adv
      send_message(context, adv_to_send, chat_id)
    else:
      try:
        last_index_in_list = len(last_advs_list) - 1
        for dict_ in [x for x in last_advs_list if x["adv_href"] == last_sended_adv]:
          last_sended_adv_index = (last_advs_list.index(dict_))
        
        if last_sended_adv_index < last_index_in_list:
          unsended_advs = last_advs_list[last_sended_adv_index + 1:last_index_in_list + 1]
          for adv_to_send in unsended_advs:
            job.context['dispatcher'].bot_data[chat_id][job.name]['lastId'] = adv_to_send['adv_href']
            send_message(context, adv_to_send,chat_id)
        else:
          logging.info('User: ' + str(job.context['chat_id']) + ' Job: ' + str(job.name) + ' No new advs')
      except:
        last_adv = last_advs_list[-1]
        job.context['dispatcher'].bot_data[chat_id][job.name]['lastId'] = last_adv['adv_href']
        adv_to_send = last_adv
        send_message(context, adv_to_send, chat_id)


def send_message(context,adv_to_send,chat_id):
    job = context.job

    context.bot.send_message(chat_id, 
                             parse_mode='HTML', 
                             text=("<a href='{}{}'> {} </a>".format(WEBSITE_DOMAIN,adv_to_send['adv_href'],adv_to_send['adv_title']))
                             )
    logging.info('User: ' + chat_id + ' Job: ' + str(job.name) + ' Sending message: ' + str(adv_to_send) )

def parse(url):
  # fix different default type_view
    if "?" in url:
      if "type_view" in url:
        pass
      else:
        url = url + '&type_view=line'
    else:
      if url.endswith('/'):
        url = url + '?type_view=line'
      elif "type_view" in url:
        pass
      else :
        url = url + '/?type_view=line'
        
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


def remove_job_if_exists(subsID, context,chat_id):
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(subsID)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
        del context.bot_data[chat_id][subsID]
    return True

__all__ = ['restore_subscriptions','subsctiption_job','remove_job_if_exists']
