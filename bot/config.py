import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Central configuration object for the Bot."""

    # === Telegram Bot Configuration ===
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))

    # === Database Configuration ===
    DATABASE_URL = os.getenv('DATABASE_URL')

    # === External Service API Keys ===
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')

    # === SQLAlchemy Configuration ===
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @classmethod
    def validate(cls):
        """Validate that all required configuration is present."""
        required_vars = [
            'BOT_TOKEN',
            'DATABASE_URL',
            'GROQ_API_KEY',
        ]

        for var in required_vars:
            value = getattr(cls, var)
            if not value:
                raise ValueError(f"Missing required configuration: {var}")
            print(f"✓ {var}: {'*' * 10}")

# Validate configuration when imported
try:
    Config.validate()
    print("✅ All configuration validated successfully!")
except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    import sys
    sys.exit(1)
