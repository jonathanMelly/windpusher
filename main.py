import hashlib
import os
import time
import re
import requests
import toml

from bs4 import BeautifulSoup

from requests_toolbelt.utils import dump

from dotenv import load_dotenv

# load config file
with open('config.toml', 'r') as f:
    config = toml.loads(f.read())

load_dotenv()


def get(url):
    api_response = requests.post(
        "https://api.zyte.com/v1/extract",
        auth=(os.getenv("ZYTE_API_KEY"), ""),
        json={
            "url": url,
            # "httpResponseBody": True,
            'browserHtml': True
        },
    )
    if api_response.status_code != 200:
        api_response.raise_for_status()

    # For responseBody
    # http_response_body: bytes = b64decode(api_response.json()["httpResponseBody"])

    return api_response.json()["browserHtml"]


# Handles stations
try:
    numbersRe = re.compile(r"\d+(\.\d+)?")

    for stationName in config:
        try:
            station = config[stationName]

            print("Requesting " + station["src"])
            html = get(station["src"])
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
            skip = False
            for blockName, blockValue in blocks.items():
                element = measureBlock.find("div", {"id": blockValue})
                if element is None:
                    print("missing block " + blockName + ", skipping station")
                    skip = True
                    continue
                else:
                    value = numbersRe.search(element.text)
                    if value is not None:
                        values[blockName] = value.group()
                    else:
                        print("no data for measure " + blockName + ", discarding station")
                        skip = True
                        continue

            if skip is True:
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
                print("Skipping PUSH TO " + apiUrl)

        except Exception as error:
            print("something went wrong:", error)

finally:
    pass
