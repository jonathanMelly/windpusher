import hashlib
import os
import time
import re
import requests
import toml

from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from bs4 import BeautifulSoup

from requests_toolbelt.utils import dump

from dotenv import load_dotenv

# load config file
with open('config.toml', 'r') as f:
    config = toml.loads(f.read())

load_dotenv()

if os.getenv("DEBUG") is not None:
    print("DEBUG MODE ON")

# Start browser
options = Options()
options.add_argument('--headless')

proxy = os.getenv('PROXY')
if proxy is not None:
    options.add_argument(f'--proxy-server={proxy}')

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
                print(f"Missing root measure block, skipping station {station}")
                if os.getenv("DEBUG") is not None:
                    print(f"html:{html}")
                continue

            # Keys are the one used for windguruz api
            blocks = {"wind_avg": "vent_vitesse",
                      "wind_max": "vent_rafale",
                      "wind_direction": "vent_direction"}
            values = {}

            for blockName, blockValue in blocks.items():
                element = measureBlock.find("div", {"id": blockValue})
                if element is None:
                    print("missing block " + blockName)
                    values[blockName] = None
                else:
                    value = numbersRe.search(element.text)
                    if value is not None:
                        values[blockName] = value.group()
                    else:
                        print("no usable data found for measure " + blockName + " in content [" + element.text +
                              "] (value for this part won’t be uploaded)")
                        values[blockName] = None

            print(f"station: {stationName} : {values}")

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
                         'interval': (60 * 15)
                         }

            for blockName, _ in blocks.items():
                if values[blockName] is not None:
                    apiParams[blockName] = values[blockName]

            if os.getenv("NO_PUSH") is None:
                # sending get request and saving the response as response object
                r = requests.get(url=apiUrl, params=apiParams)
                print(r)
                if os.getenv("DEBUG"):
                    print(dump.dump_all(r))
            else:
                print("Skipping PUSH TO " + apiUrl)

        except Exception as error:
            print("something went wrong:", error)

finally:
    driver.close()
