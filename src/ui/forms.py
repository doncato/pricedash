from flask_wtf import FlaskForm, CSRFProtect
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import IntegerField, DecimalField, DateTimeLocalField, StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
import math

from datahandler import db,Unit,Shop,get_shop_by_id,get_unit,get_ean

def ean_validator(form, field):
    """
    Validates wether entered data is a valid EAN based on it's checksum
    """
    # Get the entered data into an array of digits
    digits = list(map(int, str(field.data)))

    # Determine the beginning weight by checking whether digit number is odd
    odd_length = len(digits) % 2 != 0

    fullsum = 0
    fullsum += 3 * sum(digits[1 if odd_length else 0:-1:2])
    fullsum += sum(digits[0 if odd_length else 1:-1:2])

    # Calculate checksum digit
    chcksum = math.ceil(fullsum / 10)*10 - fullsum

    # Compare calculated checksum digit with given last digit
    if chcksum is not digits[-1]:
        raise ValidationError("Invalid EAN")

def product_exists(form, field):
    """
    Validates wether the entered EAN is already in database.
    Fails validation if the EAN does NOT exist
    """
    ean = field.data

    if not get_ean(ean):
        raise ValidationError("Product not in Database")

class ShopForm(FlaskForm):
    name = StringField("Shop Name", validators=[DataRequired()])
    address = StringField("Address")
    parent = SelectField("Parent Shop", coerce=get_shop_by_id)
    long = DecimalField("Longitude")
    lat = DecimalField("Latitude")
    submit = SubmitField('Submit')

class ProductForm(FlaskForm):
    ean = IntegerField("EAN", validators=[DataRequired(), ean_validator], render_kw={'id': 'formProductEan'})
    name = StringField("Product Name", validators=[DataRequired()])
    description = StringField("Description")
    amount = DecimalField("Amount", validators=[DataRequired()])
    unit = SelectField("Unit", validators=[DataRequired()], coerce=get_unit)
    image = StringField("Image")
    submit = SubmitField('Submit')

class PurchaseForm(FlaskForm):
    shop = SelectField("Shop", validators=[DataRequired()], coerce=get_shop_by_id)
    date = DateTimeLocalField("Time of Purchase")
    submit = SubmitField('Next')

class ProductPriceForm(FlaskForm):
    ean = StringField("EAN", validators=[DataRequired(), ean_validator, product_exists], render_kw={'class': 'productSearch'})
    price = DecimalField("Price", validators=[DataRequired()])
    submit = SubmitField('Submit')

class ImageUploadForm(FlaskForm):
    photo = FileField(validators=[FileRequired(), FileAllowed(['jpg', 'png'], 'Unsupported Image format :(')])
    submit = SubmitField('Upload')