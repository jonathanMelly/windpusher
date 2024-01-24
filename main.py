import hashlib
import os
import time
import re
import requests
import toml

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType
from bs4 import BeautifulSoup

from requests_toolbelt.utils import dump

from dotenv import load_dotenv

# load config file
with open('config.toml', 'r') as f:
    config = toml.loads(f.read())

load_dotenv()

zyte = Proxy({
    'proxyType': ProxyType.MANUAL,
    'socksProxy': os.getenv("ZYTE_API_KEY")+':proxy.crawlera.com:8011',
    'socksVersion': 5,
})

# Start browser
options = Options()
options.add_argument('--headless')
#options.add_argument('ignore-certificate-errors')
#options.add_argument('--ignore-ssl-errors')
options.proxy = zyte

driver = webdriver.Chrome(options=options)

# Handles stations
try:
    numbersRe = re.compile(r"\d+(\.\d+)?")

    for stationName in config:
        try:
            station = config[stationName]

            print("Requesting " + station["src"])
            driver.get(station["src"])
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            blockWarning = soup.find("div", {"id": "warning"})
            if blockWarning is not None and blockWarning.text.strip() != "":
                print(stationName + " seems out of order, discarding update")
                continue

            measureBlock = soup.find("div", {"id": "block-mesure"})
            if measureBlock is None:
                print("Missing measure block, skipping")
                continue

            blocks = {"wind": "vent_vitesse",
                      "windGust": "vent_rafale",
                      "windDirection": "vent_direction"}
            values = {}
            for blockName, blockValue in blocks.items():
                element = measureBlock.find("div", {"id": blockValue})
                if element is None:
                    print("missing block " + blockName + ", skipping station")
                    continue
                else:
                    value = numbersRe.search(element.text)
                    if value is not None:
                        values[blockName] = value.group()
                    else:
                        print("no data for measure " + blockName + ", discarding station")
                        continue

            wind = values["wind"]
            windGust = values["windGust"]
            windDirection = values["windDirection"]

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
                         'interval': (60 * 15)
                         }

            if os.getenv("NO_PUSH") is None:
                # sending get request and saving the response as response object
                r = requests.get(url=apiUrl, params=apiParams)
                print(r)
                if os.getenv("DEBUG"):
                    print(dump.dump_all(r))
            else:
                print("Skipping PUSH TO "+apiUrl)

        except Exception as error:
            print("something went wrong:", error)

finally:
    driver.close()
