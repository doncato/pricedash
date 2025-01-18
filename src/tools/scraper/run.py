import httpx
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker
import sqlalchemy
from selenium import webdriver
import os,sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir,'../../'))

if src_dir not in sys.path:
    sys.path.append(src_dir)

from datahandler.models import Shop


from sites import Conrad, Reichelt, Voelkner

search = {
    "conrad": [
        #"https://www.conrad.de/de/c/batterien-14716.html",
        #"https://www.conrad.de/de/c/taschenrechner-40107.html",
        #"https://www.conrad.de/de/c/taschenrechner-40107.html?page=2",
        #"https://www.conrad.de/de/c/schraubenzieher-17600.html",
        #"https://www.conrad.de/de/c/zangen-17604.html",
        #"https://www.conrad.de/de/o/handsaegen-1516022.html",
        #"https://www.conrad.de/de/o/pinzetten-1511030.html",
        #"https://www.conrad.de/de/c/schneidwerkzeuge-feilen-17598.html",
        #"https://www.conrad.de/de/o/loetzinn-1508075.html"
    ],
    "reichelt": [
        #"https://www.reichelt.de/taschenrechner-c7147.html?&nbc=1&OFFSET=100",
        #"https://www.reichelt.de/multimeter-digital-c4058.html?&nbc=1&OFFSET=100",
        #"https://www.reichelt.de/ladeger-te-f-r-usb-ger-te-c5158.html?&nbc=1&OFFSET=100",
        #"https://www.reichelt.de/festspannungsnetzteile-c4946.html?&nbc=1&OFFSET=100",
        #"https://www.reichelt.de/l-tzinn-c557.html?&nbc=1&OFFSET=100"
    ],
    "voelkner": [
        #"https://www.voelkner.de/categories/13148_13192_17518/Werkstatt/Handwerkzeuge/Abisolierwerkzeuge.html",
        #"https://www.voelkner.de/categories/13148_13192_13817/Werkstatt/Handwerkzeuge/Schraubendreher.html",
        #"https://www.voelkner.de/categories/13148_13192_13960/Werkstatt/Handwerkzeuge/Zangen.html",
        #"https://www.voelkner.de/categories/13148_13192_13862/Werkstatt/Handwerkzeuge/Werkzeugkoffer.html",
        #"https://www.voelkner.de/categories/13148_13192_13920/Werkstatt/Handwerkzeuge/Steckschluessel.html",
        #"https://www.voelkner.de/categories/13148_13192_13718/Werkstatt/Handwerkzeuge/Schneidwerkzeuge.html",
        #"https://www.voelkner.de/categories/13148_13192_13341/Werkstatt/Handwerkzeuge/Drehmomentschluessel.html",
        #"https://www.voelkner.de/categories/13148_13192_13430/Werkstatt/Handwerkzeuge/Hammer.html",
        #"https://www.voelkner.de/categories/13148_13192_13513/Werkstatt/Handwerkzeuge/Handbohrmaschinen.html",
        #"https://www.voelkner.de/categories/13148_13192_13590/Werkstatt/Handwerkzeuge/Handsaegen.html",
        #"https://www.voelkner.de/categories/13148_13192_13659/Werkstatt/Handwerkzeuge/Einziehspiralen-Kabelziehstruempfe.html",
        #"https://www.voelkner.de/categories/13148_13192_13772/Werkstatt/Handwerkzeuge/Schraubenschluessel-Ringschluessel.html",
        #"https://www.voelkner.de/categories/13148_13192_13895/Werkstatt/Handwerkzeuge/Spezialwerkzeuge.html",
        #"https://www.voelkner.de/categories/13148_13192_13945/Werkstatt/Handwerkzeuge/Tacker-Nagler.html",
        #"https://www.voelkner.de/categories/13148_13192_17403/Werkstatt/Handwerkzeuge/Feilen.html",
        #"https://www.voelkner.de/categories/13148_13192_17460/Werkstatt/Handwerkzeuge/Schlagwerkzeug.html",
        #"https://www.voelkner.de/categories/13148_13192_100998/Werkstatt/Handwerkzeuge/Biegewerkzeuge.html",
        #"https://www.voelkner.de/categories/13148_13192_101581/Werkstatt/Handwerkzeuge/Gewindeschneider.html",
        #"https://www.voelkner.de/categories/13140_16382_13164_13749_17373/Computer-Buero/Buero/Buerogeraete/Rechner-Kassensysteme/Taschenrechner.html",
        #"https://www.voelkner.de/categories/13148_13214_13719/Werkstatt/Messtechnik/Multimeter.html",
        #"https://www.voelkner.de/categories/13148_13203_13717/Werkstatt/Loettechnik/Loetzinn.html"
    ]
}

def main():
    load_dotenv(".env")  
    
    # Setup SQL Connection
    db_uri = "mariadb://{user}:{passwd}@{host}:{port}/{db}?ssl_ca={ssl_ca}&ssl_cert={ssl_cert}&ssl_key={ssl_key}".format(
        user =  os.environ.get("DB_USER") if os.environ.get("DB_USER") else "ecstasee",
        passwd = os.environ.get("DB_PASSWORD") if os.environ.get("DB_PASSWORD") else "ecstasee",
        host = os.environ.get("DB_HOST") if os.environ.get("DB_HOST") else "localhost",
        port = os.environ.get("DB_PORT") if os.environ.get("DB_PORT") else "3306",
        db = os.environ.get("DB_DATABASE") if os.environ.get("DB_DATABASE") else "ecstasee",
        ssl_ca = os.environ.get("DB_SSL_CA") if os.environ.get("DB_SSL_CA") else "",
        ssl_cert = os.environ.get("DB_SSL_CERT") if os.environ.get("DB_SSL_CERT") else "",
        ssl_key = os.environ.get("DB_SSL_KEY") if os.environ.get("DB_SSL_KEY") else ""
    )

    engine = sqlalchemy.create_engine(db_uri)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Setup HTTP Session Client
    headers = {
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0"
    }
    session = httpx.Client(http2=True, timeout=15.0, follow_redirects=True)
    session.headers = headers

    driver = webdriver.Firefox()

    conrad_shop_obj = db.query(Shop).filter_by(id=19).first() # Id of buerklin shop
    conrad = Conrad(driver, db, conrad_shop_obj)

    reichelt_shop_obj = db.query(Shop).filter_by(id=15).first() # Id of reichelt shop
    reich = Reichelt(session, db, reichelt_shop_obj)

    voelkner_shop_obj = db.query(Shop).filter_by(id=18).first() # Id of voelkner shop
    voelk = Voelkner(driver, db, voelkner_shop_obj)

    conrad.update_stored()
    voelk.update_stored()
    reich.update_stored()
    
    """
    for i in range(0, len(search["conrad"])):
        try:
            r = conrad.populate_from_list(search["conrad"][i])
            print(f'{i}/{len(search["conrad"])} {r}')
        except Exception as e:
            print(f"Error occured: {e}")
    for i in range(0, len(search["reichelt"])):
        try:
            r = reich.populate_from_list(search["reichelt"][i])
            print(f'{i}/{len(search["reichelt"])} {r}')
        except Exception as e:
            print(f"Error occured: {e}")
    for i in range(0, len(search["voelkner"])):
        try:
            r = voelk.populate_from_list(search["voelkner"][i])
            print(f'{i}/{len(search["voelkner"])} {r}')
        except Exception as e:
            print(f"Error occured: {e}")
    """

    session.close()
    driver.close()

if __name__ == "__main__":
    main()
