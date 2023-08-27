import datetime
import hashlib
import os
import time
import re
import requests

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

from dotenv import load_dotenv

from requests_toolbelt.utils import dump

options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

try:
    load_dotenv()

    driver.get('https://letskite.ch/spots/31/kitesurf/baie-dallaman')
    html = driver.page_source
    soup = BeautifulSoup(html,"html.parser")

    blockMesure = soup.find("div", {"id": "block-mesure"})

    numbers = re.compile(r"\d+")

    wind = numbers.findall(blockMesure.find("div", {"id": "vent_vitesse"}).text).pop()
    windGust = numbers.findall(blockMesure.find("div", {"id": "vent_rafale"}).text).pop()
    windDirection = numbers.findall(blockMesure.find("div", {"id": "vent_direction"}).text).pop()

    print("wind:"+wind+"\ngust:", windGust+"\ndir:", windDirection)

    wgUrl = "http://www.windguru.cz/upload/api.php"

    # location given here
    salt = time.time()
    uid = os.getenv("UID")
    password = os.getenv("PASSWORD")

    wghash = hashlib.md5((str(salt) + uid + password).encode()).hexdigest()

    # defining a params dict for the parameters to be sent to the API
    apiParams = {'uid': uid,
                 'salt': salt,
                 'hash': wghash,
                 'wind_avg': wind,
                 'wind_max': windGust,
                 'wind_direction': windDirection
                 }

    # sending get request and saving the response as response object
    r = requests.get(url=wgUrl, params=apiParams)

    print(dump.dump_all(r))
    print(r)

finally:
    driver.close()
