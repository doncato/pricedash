from .models import alternatives_table,Unit,Product,Shop,Price,ProductPage
from sqlalchemy import or_, func, select, asc
from sqlalchemy.sql import text
from sqlalchemy.exc import OperationalError

# Note: This module / file mainly exists because I have not researched how to
# implement custom helpers to the database class but if someone knows how, it
# could and should be done

def init_units(db):
    """
    Adds hardcoded descriptors for common units to the units database
    """
    units = ["g", "kg", "l", "ml", "pcs"]

    existing_units = {
        unit.name for unit in db.session.query(Unit).filter(Unit.name.in_(units)).all()
    }

    new_units = [Unit(name=unit) for unit in units if unit not in existing_units]

    if new_units:
        try:
            db.session.bulk_save_objects(new_units)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()

def add_alternative(db, product_id, alternative_id):
    """
    Adds the alternative as an alternative to the product
    returns True on success, False on failure
    """

    if product_id == alternative_id:
        # Refusing to accept product as alternative to itself
        return False

    product = get_ean(product_id)
    alternative = get_ean(alternative_id)

    if product and alternative:
        # Check if relation already exists with both ids swapped
        # one check is redundant but for symmetry who cares
        result = db.session.query(alternatives_table).filter(
            or_(
                (alternatives_table.c.product_id == product_id) &
                (alternatives_table.c.alternative_id == alternative_id),
                (alternatives_table.c.product_id == alternative_id) &
                (alternatives_table.c.alternative_id == product_id)
            )
        ).first()

        if not result:
            product.alternatives.append(alternative)
            db.session.add(product)
            db.session.commit()
        else:
            print("Nothing new; Ignoring")
        return True
    else:
        return False

def get_database_stats(db):
    """
    Returns cosmectic information regarding the current state of the database
    """
    try:
        db.session.execute(text('SELECT 1'));
        product_count = db.session.query(func.count(Product.ean_id)).scalar()
        shop_count = db.session.query(func.count(Shop.id)).scalar()
        price_count = db.session.query(func.count(Price.id)).scalar()

        stats = {
            "Prices": price_count,
            "Products": product_count,
            "Shops": shop_count
        }

        return (True, stats)
    except OperationalError as e:
        print(f"Database connection failed: {e}")
        return (False, {})

def search_product_by_query(db, query, *args, limit=5):
    """
    Searches saved products by a query which is abitrary text. Number of results
    can be configured
    """

    query = f"%{query}%"

    """
    queried_products = db.session.query(Product).filter(
        or_(
            Product.ean_id.ilike(query),
            Product.name.ilike(query),
            Product.description.ilike(query)
        )
    ).limit(limit).all()
    """

    qp = (
        select(Product)
        .where(or_(
            Product.ean_id.ilike(query),
            Product.name.ilike(query),
            Product.description.ilike(query)
        ))
    ).alias('qp')

    stmt = (
        select(
            qp.c.ean_id,
            qp.c.name,
            qp.c.description,
            qp.c.amount,
            qp.c.unit_id,
            qp.c.image
        )
        .join(Price, Price.ean_id == qp.c.ean_id)
        .group_by(qp.c.ean_id)
        .order_by(func.count(qp.c.ean_id).desc())
        .limit(limit)
    )

    results = db.session.execute(stmt).all()

    return results

def get_ean(ean):
    """
    Obtains a Product object by it's ean, which is the PK for products
    """
    return Product.query.get(ean)

def get_shop_by_id(shop_id):
    """
    Gets a shop by it's id
    """
    try:
        shop_id = int(shop_id)
    except ValueError:
        return None
    else:
        return Shop.query.get(shop_id)

def get_unit(unit):
    """
    Obtains an unit by it's name / id (which is the same)
    """
    return Unit.query.get(unit)

def get_product_pages(db, ean):
    """
    Gets all product pages of product
    Returns dict with the shop as key and the url as value
    """
    stmt = select(
        ProductPage.shop_id,
        ProductPage.url
    ).where(
        ProductPage.ean_id==ean
    )

    results = db.session.execute(stmt).all()

    return dict(results)

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

    result = db.session.execute(stmt).all()

    return result

def get_latest_pricerange(db, ean):
    """
    Gets the minimum and maximum range from the latest prices
    """
    prices = get_latest_prices(db, ean)
    return(prices[0], prices[-1])
