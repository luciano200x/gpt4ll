from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from contextlib import contextmanager

# Create an options object
options = Options()

options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--incognito")
options.add_argument('--disable-blink-features=AutomationControlled')
driver = webdriver.Chrome(options=options)

# Create a context manager for the driver
@contextmanager
def get_driver():
    driver = webdriver.Chrome(options=options)
    try:
        yield driver
    finally:
        driver.quit()    

def get_page_text(link:str, driver) -> str:
    try:
        # Open a URL
        driver.get(link)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        return soup.get_text()        
    except:
        return 'text lookup failed'