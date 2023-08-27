from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)

try:
    driver.get('https://letskite.ch/spots/31/kitesurf/baie-dallaman')
    html = driver.page_source
    soup = BeautifulSoup(html,"html.parser")

    blockMesure = soup.find("div", {"id": "block-mesure"})

    wind = blockMesure.find("div", {"id": "vent_vitesse"}).text
    windGust = blockMesure.find("div", {"id": "vent_rafale"}).text
    windDirection = blockMesure.find("div", {"id": "vent_direction"}).text

    print(wind, windGust, windDirection)


finally:
    driver.close()
