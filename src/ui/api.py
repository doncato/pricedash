from flask import render_template,send_from_directory,Blueprint,request,redirect
from datetime import datetime
from sqlalchemy import asc

from datahandler import \
    db,Unit,Price,Shop,Product, \
    get_ean,get_database_stats,search_product_by_query,get_latest_prices, \
    add_alternative,get_product_pages, \
    ProductSchema,PriceSchema

appapi = Blueprint('appapi', __name__)

@appapi.route('/api/add/alternative/<product>/<alternative>')
def api_add_alternative(product, alternative):
    result = add_alternative(db, product, alternative)

    return {"results": {"success": result}}

@appapi.route('/api/search/<query>')
def api_search(query):
    print(f"Searching... {query}")
    products_schema = ProductSchema(many=True)
    results = search_product_by_query(db, query)
    return {"results": products_schema.dump(results)}
    
@appapi.route('/api/prices/<ean>')
def api_prices(ean):
    prices_schema = PriceSchema(many=True)

    product = Product.query.get(ean)

    results = None
    if product:
        return {"results": prices_schema.dump(product.prices)}
    else:
        return {"results": {}}

