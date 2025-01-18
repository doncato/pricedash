from bs4 import BeautifulSoup
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

class Reichelt:
    """
    Scrapes reichelt
    """

    # https://www.reichelt.de/kfz-au-enbereich-c8983.html?ACTION=2&GROUPID=8983&SEARCH=*&START=1&OFFSET=100&nbc=1
    # GROUPID = Group category
    # START = Product Page
    # OFFSET = Displayed product count
    def __init__(self, session, database_connection, shop):
        self.base_url = "https://reichelt.de/"
        self.session = session
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

    def update_price(self, product_url, ean_id):
        """
        Gets price of the supplied ean using the supplied product page
        """
        r = self.session.get(product_url)

        if r.status_code < 400:
            soup = BeautifulSoup(r.text, 'html.parser')
            price_obj = soup.find("p", {"class": "productPrice"})
    
            try:
                price_val = float(price_obj.get_text("").strip().replace(",",".").replace("€",""))
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

        else:
            return False

    def populate_from_list(self, product_list_url, rand_range=(0,500)):
        """
        Calls the get_product function to each product found in the supplied list
        can be instructed to wait a random amount in between from a given range
        by setting rand_range to a tuple of (min, max) in milliseconds.
        Note: As we currently work synched this is not really necessary.
        """

        r = self.session.get(product_list_url)

        results = []

        print(r.status_code)

        if r.status_code < 400:
            # Gather Site Soup
            soup = BeautifulSoup(r.text, 'html.parser')

            productlist = soup.find(id="al_artikellist")
            products = productlist.find_all("div", {"class": "al_gallery_article"})

            for product in products:
                anchor = product.find("a", {"class":"al_artinfo_link"})
                if anchor:
                    try:
                        self.get_product(anchor.attrs['href'])
                        #print(anchor.attrs['href'].partition("?"))
                    except Exception as e:
                        print(f"Request resulted in Exception: {e}\n")
                        print("Proceeding Anyway")
                    finally:
                        sleep(randint(rand_range[0], rand_range[1])/1000)

        return True

    def get_product(self, product_url):
        """
        Gets product information of the supplied product page
        """
        r = self.session.get(product_url)

        result = {}

        print(r.status_code)

        if r.status_code < 400:
            # Gather Product Information
            soup = BeautifulSoup(r.text, 'html.parser')

            header = soup.find(id="av_articleheader")
            price = soup.find(id="av_price")
            props = soup.find(id="av_props")

            if not header or not price:
                return False

            result["name"] = header.h2.find(string=True, recursive=False).strip()
            result["description"] = header.span.meta["content"].strip() + " " +  header.span.span.text.strip()
            try:
                result["ean"] = int(header.find("meta", {"itemprop":"gtin13"}).attrs['content'].strip())
            except ValueError:
                return False

            print(f"Found Product {result['name']}")

            price_value = price.get_text("").strip().replace(",",".")
            try:
                result["price"] = float(price_value)
            except ValueError:
                pass

            properties = {}
            for propview in props.find_all("ul", {"class": "clearfix"}):
                propname = propview.find_all("li", {"class": "av_propname"})
                propvalue = propview.find_all("li", {"class": "av_propvalue"})
                if propname and propvalue:
                    properties[propname[0].string.strip()] = propvalue[0].string.strip()

            result["properties"] = properties

            # Check if Product exists in database and add it if not
            product = self.db.query(Product).filter_by(ean_id=result["ean"]).first()
            if result["ean"] and not product:
                print("...Constructing Database Product Object")
                product = Product()
                product.ean_id = result["ean"]
                product.name = result["name"]
                product.description = result["description"]
                package = result["properties"].get("Verpackung")
                if package:
                    try:
                        amount = int(package.replace("er-Pack", ""))
                    except ValueError:
                        amount = 1
                else:
                    amount = 1
                product.amount = amount
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

        else:
            return False


            
