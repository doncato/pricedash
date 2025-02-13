from dotenv import load_dotenv
from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
import os

from ui.views import appview
from ui.api import appapi
from datahandler import db,init_units

def run():
    print("Starting...");

    # Load backup Variables from .env
    load_dotenv(".env")   

    # Create the database
    app = Flask(
        __name__,
        template_folder="ui/templates/",
        static_folder="../public"
    )

    # Set Secret key
    app.secret_key = os.environ.get('SECRET_KEY') if os.environ.get('SECRET_KEY') else "development"

    # Register Blueprint
    app.register_blueprint(appapi)
    app.register_blueprint(appview)

    # Setup SQL Access URI
    app.config["SQLALCHEMY_DATABASE_URI"] = "mariadb://{user}:{passwd}@{host}:{port}/{db}?ssl_ca={ssl_ca}&ssl_cert={ssl_cert}&ssl_key={ssl_key}".format(
        user =  os.environ.get("DB_USER") if os.environ.get("DB_USER") else "ecstasee",
        passwd = os.environ.get("DB_PASSWORD") if os.environ.get("DB_PASSWORD") else "ecstasee",
        host = os.environ.get("DB_HOST") if os.environ.get("DB_HOST") else "localhost",
        port = os.environ.get("DB_PORT") if os.environ.get("DB_PORT") else "3306",
        db = os.environ.get("DB_DATABASE") if os.environ.get("DB_DATABASE") else "ecstasee",
        ssl_ca = os.environ.get("DB_SSL_CA") if os.environ.get("DB_SSL_CA") else "",
        ssl_cert = os.environ.get("DB_SSL_CERT") if os.environ.get("DB_SSL_CERT") else "",
        ssl_key = os.environ.get("DB_SSL_KEY") if os.environ.get("DB_SSL_KEY") else ""
    )



    # Create Object for Bootstrap Flask
    bootstrap = Bootstrap5(app)

    # Flask-WTF
    csrf = CSRFProtect(app)

    # Hook App settings into db
    db.init_app(app)
        
    with app.app_context():
        db.create_all()
        init_units(db)

    # Initialize the units table

    print("Startup Complete.");

    # Start the app
    app.run(host="0.0.0.0")

if __name__ == "__main__":
    run()
