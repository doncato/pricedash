from sqlalchemy import or_, func, select, asc
from sqlalchemy.sql import text
from sqlalchemy.exc import OperationalError
import os,sys

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.abspath(os.path.join(current_dir,'../../../'))

if src_dir not in sys.path:
    sys.path.append(src_dir)

from datahandler.models import Price, Shop

def get_latest_prices(db, ean):
    """
    Gets latest associated prices of the given product
    """

    # The following SQL Statement gets the latest price of a product for each shop
    """
    WITH found_prices AS (
	    SELECT price.value AS value, shop.name AS name, ROW_NUMBER() OVER(PARTITION BY shop.id ORDER BY price.date DESC) AS row_number
	    FROM price
	    INNER JOIN shop
	    ON price.shop_id=shop.id
	    WHERE price.ean_id=4316268629836
    )
    SELECT value, name
    FROM found_prices
    WHERE row_number = 1;
    """

    found_prices = (
        select(
            Price.value.label('value'),
            Price.date.label('date'),
            Shop.name.label('name'),
            Shop.id.label('shop_id'),
            func.row_number().over(
                partition_by=Shop.id,
                order_by=Price.date.desc()
            ).label('row_number')
        )
        .join(Shop, Price.shop_id == Shop.id)
        .where(Price.ean_id == ean)
        .cte('found_prices')
    )

    stmt = (
        select(
            found_prices.c.value,
            found_prices.c.name,
            found_prices.c.date,
            found_prices.c.shop_id,
        )
        .where(found_prices.c.row_number == 1)
        .order_by(asc(found_prices.c.value))
    )

    result = db.execute(stmt).all()

    return result