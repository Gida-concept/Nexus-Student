import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Central configuration object for both the Bot and Webhook App."""

    # === Telegram Bot Configuration ===
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))

    # === Database Configuration ===
    DATABASE_URL = os.getenv('DATABASE_URL')

    # === External Service API Keys ===
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
    PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY')
    CLOUDINARY_URL = os.getenv('CLOUDINARY_URL')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

    # === Application Feature Flags ===
    ENABLE_PAYMENTS = os.getenv('ENABLE_PAYMENTS', 'false').lower() == 'true'

    # === SQLAlchemy Configuration (Shared) ===
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @classmethod
    def validate(cls):
        """Validate that all required configuration is present."""
        required_vars = [
            'BOT_TOKEN',
            'DATABASE_URL',
            'GROQ_API_KEY',
            'PAYSTACK_SECRET_KEY',
            'PAYSTACK_PUBLIC_KEY',
            'CLOUDINARY_URL',
            'GEMINI_API_KEY'
        ]

        for var in required_vars:
            if not getattr(cls, var):
                raise ValueError(f"Missing required configuration: {var}")
