from selenium.webdriver.chrome.options import Options
from selenium import webdriver

options = Options()
options.add_argument('--headless')
#options.add_argument('--proxy-server=127.0.0.1:8888')

driver = webdriver.Chrome(options=options)

print(driver.get('https://ip.oxylabs.io/location'))