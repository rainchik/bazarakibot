import re
import os

REGEX = re.compile(r'^(?:http)s?://(www\.)?bazaraki\.com/.+', re.IGNORECASE)
TOKEN = os.getenv('TOKEN')
WEBSITE_DOMAIN = "https://www.bazaraki.com"
LOGLEVEL = os.getenv('LOGLEVEL', 'INFO')
POLLING_INTERVAL = os.getenv('POLLING_INTERVAL', 300) #Sec
PERSISTENCE_VOL = os.getenv('PERSISTENCE_VOL', '.')