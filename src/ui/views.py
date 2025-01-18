from flask import render_template,send_from_directory,Blueprint,request,redirect
from datetime import datetime
from werkzeug.utils import secure_filename
import os
from sqlalchemy import asc

from datahandler import \
    db,Unit,Price,Shop,Product, \
    get_ean,get_database_stats,search_product_by_query,get_latest_prices, \
    add_alternative,get_product_pages, \
    ProductSchema,PriceSchema
from ui.forms import ShopForm,ProductForm,PurchaseForm,ImageUploadForm
from helpers.barcode import read_barcodes

appview = Blueprint('appview', __name__)

@appview.route('/public/')
def public(path):
    return send_from_directory(app.static_folder, path)

@appview.route('/overview/')
def overview():
    query = request.args.get('q') if request.args.get('q') else ""
    if query:
        results = search_product_by_query(db, query, limit=50)
    else: 
        results = []
    return render_template("overview.html", query=query, results=results)

@appview.route('/api/add/alternative/<product>/<alternative>')
def api_add_alternative(product, alternative):
    result = add_alternative(db, product, alternative)

    return {"results": {"success": result}}

@appview.route('/api/search/<query>')
def api_search(query):
    print(f"Searching... {query}")
    products_schema = ProductSchema(many=True)
    results = search_product_by_query(db, query)
    return {"results": products_schema.dump(results)}
    
@appview.route('/api/prices/<ean>')
def api_prices(ean):
    prices_schema = PriceSchema(many=True)

    product = Product.query.get(ean)

    results = None
    if product:
        return {"results": prices_schema.dump(product.prices)}
    else:
        return {"results": {}}

@appview.route('/add/photo', methods=['GET', 'POST'])
def photo():
    form = ImageUploadForm()

    found_codes = ()

    if form.validate_on_submit():
        data = form.photo.data
        #filename = str(datetime.now().timestamp()) # File extension gets lost here
        filename = secure_filename(data.filename)
        path = os.path.join('public/uploads', filename)
        data.save(path)
        found_codes = read_barcodes(path)

    return render_template("add_photo.html", form=form, codes=found_codes)

@appview.route('/add/purchase', methods=['GET', 'POST'])
def add_purchase():
    shops = db.session.execute(db.select(Shop).order_by(asc(Shop.name))).scalars()
    
    form = PurchaseForm()
    form.shop.choices = [('-1', 'None')] + [(shop.id, shop.name) for shop in shops]

    if request.method == 'GET' and request.args.get('ean'):
        try:
            ean = int(request.args.get('ean'))
        except ValueError:
            pass
        else:
            form.ean.data = ean

    # Todo: There is currently no concept what happens when the product
    # is not currently registered

    if form.validate_on_submit():
        price = Price()
        price.ean = get_ean(form.ean.data)
        price.value = form.price.data
        price.shop_id = form.shop.data.id
        price.date = form.date.data

        db.session.add(price)
        db.session.commit()

        return redirect(f'/view/product/{price.ean.ean_id}', code=303)

    return render_template("add_purchase.html", form=form)

@appview.route('/add/shop', methods=['GET', 'POST'])
def add_shop():
    shops = db.session.execute(db.select(Shop).order_by(asc(Shop.name))).scalars()

    form = ShopForm()
    form.parent.choices = [('-1', 'None')] + [(shop.id, shop.name) for shop in shops]

    if form.validate_on_submit():
        shop = Shop()
        shop.name = form.name.data
        shop.parent = form.parent.data
        shop.address = form.address.data
        shop.long = form.long.data
        shop.lat = form.lat.data
        
        db.session.add(shop)
        db.session.commit()

    return render_template("add.html", form=form)

@appview.route('/add/product', methods=['GET', 'POST'])
def add_product():
    units = db.session.execute(db.select(Unit)).scalars()

    form = ProductForm()
    form.unit.choices = [(unit.name, unit.name) for unit in units]

    if request.method == 'GET' and request.args.get('ean'):
        try:
            ean = int(request.args.get('ean'))
        except ValueError:
            pass
        else:
            form.ean.data = ean

    if form.validate_on_submit():
        product = Product()
        product.ean_id = form.ean.data
        product.name = form.name.data
        product.description = form.description.data
        product.amount = form.amount.data
        product.unit = form.unit.data
        product.image = form.image.data

        db.session.add(product)
        db.session.commit()

        return redirect(f'/view/product/{product.ean_id}', code=303)

    return render_template("add.html", form=form)

@appview.route('/view/product/<ean>')
def view_product(ean):
    price_overview = get_latest_prices(db, ean)
    product_pages = get_product_pages(db, ean)
    now = datetime.now()
    product = get_ean(ean)
    alts = product.alternatives + product.alternative_of
    alternatives = []
    for alt in alts:
        prices = get_latest_prices(db, alt.ean_id)
        alternatives.append((alt, prices[0], prices[-1]))
    return render_template(
        "view_product.html",
        alternatives = alternatives,
        product=product,
        prices=price_overview,
        pages=product_pages,
        now=now
    )

@appview.route('/')
def index():
    return render_template("index.html", db_status=get_database_stats(db))
    
