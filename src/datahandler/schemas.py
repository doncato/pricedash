from marshmallow_sqlalchemy import SQLAlchemySchema, auto_field
from marshmallow import fields
from .models import Product,Price,Shop


class ProductSchema(SQLAlchemySchema):
    class Meta:
        model = Product
        include_relationships = True
        load_instance = True

    ean_id = auto_field()
    name = auto_field()
    description = auto_field()
    
class ShopSchema(SQLAlchemySchema):
    class Meta:
        model = Shop
        include_relationships = True
        load_instance = True

    name = auto_field()
    address = auto_field()

class PriceSchema(SQLAlchemySchema):
    class Meta:
        model = Price
        include_relationships = True
        load_instance = True

    group = fields.Nested(ShopSchema, attribute="shop", data_key="group")
    x = fields.DateTime(attribute="date")
    y = fields.Float(attribute="value")