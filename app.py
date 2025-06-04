import os
import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager
from flask_mail import Mail


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "cryptobot-secret-key-development")

# configure the database with PostgreSQL (with fallback to SQLite)
database_url = os.environ.get("DATABASE_URL")
# If DATABASE_URL starts with "postgres://", replace it with "postgresql://"
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///crypto_bot.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
# initialize the app with the extension
db.init_app(app)

# Set up login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Configure email settings
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'Crypto Trading Bot <admin@cryptobot.com>')

# Create mail instance
mail = Mail(app)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

with app.app_context():
    # Import routes after app is created to avoid circular imports
    import routes  # noqa
    
    # Make sure to import the models here or their tables won't be created
    import models  # noqa
    
    db.create_all()

# Import and register login_manager loader
from models import User

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))
