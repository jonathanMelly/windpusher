import datetime
import hashlib
import os
import time
import re
import requests
import toml

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

from requests_toolbelt.utils import dump

# load config file
with open('config.toml', 'r') as f:
    config = toml.loads(f.read())

# Start browser
options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

# Handles stations
try:
    for stationName in config:
        station = config[stationName]

        print("Requesting "+station["src"])
        driver.get(station["src"])
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        blockWarning = soup.find("div", {"id": "warning"})
        if len(blockWarning) > 0:
            print(stationName + " seems out of order, discarding update")
            continue

        measureBlock = soup.find("div", {"id": "block-mesure"})
        numbers = re.compile(r"\d+")

        wind = numbers.findall(measureBlock.find("div", {"id": "vent_vitesse"}).text).pop()
        windGust = numbers.findall(measureBlock.find("div", {"id": "vent_rafale"}).text).pop()
        windDirection = numbers.findall(measureBlock.find("div", {"id": "vent_direction"}).text).pop()

        print("station:" + stationName + "\nwind:" + wind + "\ngust:", windGust + "\ndir:", windDirection)

        apiUrl = station["target"]

        # location given here
        salt = time.time()
        uid = station["uid"]
        password = station["pwd"]

        wgHash = hashlib.md5((str(salt) + uid + password).encode()).hexdigest()

        # defining a params dict for the parameters to be sent to the API
        apiParams = {'uid': uid,
                     'salt': salt,
                     'hash': wgHash,
                     'wind_avg': wind,
                     'wind_max': windGust,
                     'wind_direction': windDirection,
                     'interval': (60*15)
                     }

        # sending get request and saving the response as response object
        r = requests.get(url=apiUrl, params=apiParams)
        print(r)
        if os.getenv("DEBUG"):
            print(dump.dump_all(r))

finally:
    driver.close()
