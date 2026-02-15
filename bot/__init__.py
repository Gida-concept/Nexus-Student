from flask import Flask
from bot.config import Config
from bot.models import db

# Initialize a Flask application object.
# Even though this is a Telegram bot, we use Flask here to provide the
# application context required by Flask-SQLAlchemy to manage database connections.
db_app = Flask(__name__)
db_app.config.from_object(Config)

# Initialize the database with the Flask app
db.init_app(db_app)

# Create all tables if they don't exist (for initial deployment)
# Note: In a strict production environment with schema changes,
# you would use Alembic migrations instead of db.create_all().
def init_db():
    with db_app.app_context():
        db.create_all()