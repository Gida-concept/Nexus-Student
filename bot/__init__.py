from flask import Flask
from bot.config import Config
from bot.models import db

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize SQLAlchemy with the Flask app
db.init_app(app)
