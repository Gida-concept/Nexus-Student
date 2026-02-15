from flask import Flask
from bot.config import Config
from .routes import webhook_bp
import logging

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask app for Paystack webhooks."""
    app = Flask(__name__)
    app.config.from_object(Config)

    # Register blueprints
    app.register_blueprint(webhook_bp, url_prefix='/')

    return app

# Create the app instance
app = create_app()

if __name__ == '__main__':
    logger.info("Starting Paystack Webhook Listener...")
    app.run(host='0.0.0.0', port=5000)
