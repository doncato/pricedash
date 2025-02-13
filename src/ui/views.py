from flask import render_template,send_from_directory,Blueprint,request,redirect
from datetime import datetime,timezone
from werkzeug.utils import secure_filename
import os
from sqlalchemy import asc

from datahandler import \
    db,Unit,Price,Shop,Product, \
    get_ean,get_database_stats,search_product_by_query,get_latest_prices, \
    add_alternative,get_product_pages, \
    ProductSchema,PriceSchema
from ui.forms import ShopForm,ProductForm,ProductPriceForm,PurchaseForm,ImageUploadForm
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
        print(results)
    else: 
        results = []
    return render_template("overview.html", query=query, results=results)

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

    ean = None
    if request.args.get('ean'):
        try:
            ean = int(request.args.get('ean'))
        except ValueError:
            ean = None

    if form.validate_on_submit():
        shop = form.shop.data.id
        date = form.date.data

        return redirect(f'/add/productprice/{shop}?date={int(date.timestamp())}&ean={ean}', code=303)

    return render_template("add_purchase.html", form=form)

@appview.route('/add/productprice/<shop>', methods=['GET', 'POST'])
def add_productprice(shop):
    if not shop:
        return redirect('/add/purchase', code=303)

    shop_name = Shop.query.get(shop)
    units = db.session.execute(db.select(Unit)).scalars()


    date = datetime.fromtimestamp(int(request.args.get('date')), tz=timezone.utc)
    if not date:
        date = datetime.now(tz=timezone.utc)

    form = ProductPriceForm()
    productform = ProductForm()
    photoform = ImageUploadForm()

    productform.unit.choices = [(unit.name, unit.name) for unit in units]
    
    if request.method == 'GET' and request.args.get('ean'):
        try:
            ean = int(request.args.get('ean'))
        except ValueError:
            pass
        else:
            form.ean.data = ean

    if form.validate_on_submit():
        price = Price()
        price.ean = get_ean(int(form.ean.data))
        price.value = form.price.data
        price.shop_id = shop
        price.date = date

        db.session.add(price)
        db.session.commit()

        return redirect(f'/add/productprice/{shop}?date={int(date.timestamp())}', code=303)

    if productform.validate_on_submit():
        product = Product()
        product.ean_id = productform.ean.data
        product.name = productform.name.data
        product.description = productform.description.data
        product.amount = productform.amount.data
        product.unit = productform.unit.data
        product.image = productform.image.data

        db.session.add(product)
        db.session.commit()

        return redirect(f'/add/productprice/{shop}?date={int(date.timestamp())}&ean={product.ean_id}', code=303)

    if photoform.validate_on_submit():
        data = photoform.photo.data
        #filename = str(datetime.now().timestamp()) # File extension gets lost here
        filename = secure_filename(data.filename)
        path = os.path.join('public/uploads', filename)
        data.save(path)
        found_code = next(iter(read_barcodes(path)))

        return redirect(f'/add/productprice/{shop}?date={int(date.timestamp())}&ean={found_code}', code=303)



    return render_template("add_productprice.html", form=form, productform=productform, photoform=photoform, shop=shop_name.name, date=date.strftime("%d.%m.%Y %H:%M"))

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

    return render_template("add_product.html", form=form)

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
    
