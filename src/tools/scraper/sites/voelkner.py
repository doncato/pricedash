#from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime,timedelta
from time import sleep
from random import randint
import os,sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir,'../../../'))

if src_dir not in sys.path:
    sys.path.append(src_dir)

from helper.data import get_latest_prices
from datahandler.models import Product, Price, Shop, Unit, ProductPage

class Voelkner:
    """
    Scrapes Voelkner
    """

    def __init__(self, driver, database_connection, shop):
        self.base_url = "https://voelkner.de/"
        self.driver = driver
        self.wait = wait = WebDriverWait(self.driver, timeout=10)
        self.shop = shop
        self.db = database_connection
        self.to_crawl = [] # List of urls to crawl
        self.crawled = [] # List of eans already crawled 

    def update_stored(self, rand_range=(0,500)):
        """
        Iterates through the stored product pages for this shop and updates
        their prices on each page
        """

        now = datetime.now()

        limit = timedelta(hours=24)

        pages = self.db.query(ProductPage).filter_by(shop_id=self.shop.id).all()

        for page in pages:
            latest = [price for price in get_latest_prices(self.db, page.ean_id) if price.shop_id == self.shop.id]
            delta = (now - latest[0][2]) if latest else None

            if delta is not None and delta < limit:
                print(f"{page.ean_id} Recent value exists; skipping")
            else:
                print(f"{page.ean_id}... Updating")
                try:
                    self.update_price(page.url, page.ean_id)
                except Exception as e:
                    print(f"Request resulted in Exception: {e}\n")
                    print("Proceeding Anyway")
                finally:
                    sleep(randint(rand_range[0], rand_range[1])/1000)

    def populate_from_list(self, product_list_url, rand_range=(0,500)):
        """
        Calls the get_product function to each product found in the supplied list
        can be instructed to wait a random amount in between from a given range
        by setting rand_range to a tuple of (min, max) in milliseconds.
        Note: As we currently work synched this is not really necessary.
        """

        self.driver.get(product_list_url)

        # Accept fucking cookies
        try:
            cookie = self.driver.find_element(By.XPATH, "//button[normalize-space(text())='Alle ablehnen']")
            cookie.click()
        except:
            print("No cookie banner found")

        results = []

        search_container = self.driver.find_element(By.CSS_SELECTOR, "#js_search_listing_results")

        search_results = search_container.find_elements(By.XPATH, "./*")

        for child in search_results:
            link = child.find_element(By.XPATH, ".//div/div/div/div[2]/div/div[2]/div/div[1]/a").get_attribute("href")
            results.append(link)

        for result in results:
            try:
                print(result)
                self.get_product(result)
            except Exception as e:
                print(f"Request resulted in Exception: {e}\n")
                print("Proceeding Anyway")
            finally:
                sleep(randint(rand_range[0], rand_range[1])/1000)

        return True

    def update_price(self, product_url, ean_id):
        """
        Gets price of the supplied ean using the supplied product page
        """
        self.driver.get(product_url)

        price_obj = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located(((By.CSS_SELECTOR, 'span[itemprop="price"]')))
        )

        try:
            price_val = float(price_obj.get_attribute('content'))
        except ValueError:
            print("Price invalid")
            return False

        # Register Price in Database
        print("...Constructing Database Price Object")
        price = Price()
        price.ean_id = ean_id
        price.value = price_val
        price.shop_id = self.shop.id
        price.date = datetime.now()

        self.db.add(price)
        self.db.commit()

        return True

    def get_product(self, product_url):
        """
        Gets product information of the supplied product page
        """
        self.driver.get(product_url)

        # Accept fucking cookies
        try:
            cookie = self.driver.find_element(By.XPATH, "//button[normalize-space(text())='Alle ablehnen']")
            cookie.click()
        except:
            print("No cookie banner found")

        result = {}

        sleep(randint(0, 650)/1000)

        title = self.driver.find_element(By.CSS_SELECTOR, 'h1#js_heading')
        h3 = self.driver.find_element(By.XPATH, '//h3[text()="Beschreibung"]')
        beschreibung = h3.find_element(By.XPATH, "following-sibling::p")
        price = self.driver.find_element(By.CSS_SELECTOR, 'span[itemprop="price"]')
        props_expander = self.driver.find_element(By.CSS_SELECTOR, '#tech_data')
        props_expander.click()
        sleep(randint(125,325)/1000)
        props = self.driver.find_element(By.CSS_SELECTOR, "table.product__tech_data")
        self.wait.until(lambda d: props.is_displayed())
        ean_label = props.find_element(By.XPATH, "//td[text()='EAN:']")
        ean_value = ean_label.find_element(By.XPATH, "following-sibling::td")

        result["name"] = title.text.strip()[:255]
        result["description"] = beschreibung.text.strip()[:1023]
        try:
            result["price"] = float(price.get_attribute('content'))
        except ValueError:
            print("Price invalid")
            return False

        try:
            result["ean"] = int(ean_value.text.strip())
        except ValueError:
            print("Ean Invalid")
            return False

        try:
            contents = props.find_element(By.XPATH, "//td[normalize-space(text())='Inhalt:']")
        except NoSuchElementException:
            contents = None

        if contents:
            try:
                package = contents.find_element(By.XPATH, "following-sibling::td").text.strip().replace("St.","").strip()
                result["amount"] = int(package)
            except ValueError:
                result["amount"] = 1
        else:
            result["amount"] = 1

        print(f"Found Product {result['name']}")

        # Check if Product exists in database and add it if not
        product = self.db.query(Product).filter_by(ean_id=result["ean"]).first()
        if result["ean"] and not product:
            print("...Constructing Database Product Object")
            product = Product()
            product.ean_id = result["ean"]
            product.name = result["name"]
            product.description = result["description"]
            product.amount = result["amount"]
            product.unit = self.db.query(Unit).filter_by(name="pcs").first()

            self.db.add(product)
            self.db.commit()
        else:
            print(f"...EAN exists: result['ean']")

        # Check if product page is registered and add it if not
        # TODO: Also update product page if necessary
        page = self.db.query(ProductPage).filter_by(ean_id=result["ean"], shop_id=self.shop.id).first()
        if not page:
            print("...Constructing Databasse ProductPage Object")
            page = ProductPage()
            page.ean = product
            page.shop = self.shop
            page.url = product_url.partition("?")[0]

            self.db.add(page)
            self.db.commit()

        # Register Price in Database
        print("...Constructing Database Price Object")
        price = Price()
        price.ean = product
        price.value = result["price"]
        price.shop_id = self.shop.id
        price.date = datetime.now()

        self.db.add(price)
        self.db.commit()

        return True

            
