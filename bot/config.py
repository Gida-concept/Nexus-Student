import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))
    DATABASE_URL = os.getenv('DATABASE_URL')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @classmethod
    def validate(cls):
        required_vars = ['BOT_TOKEN', 'DATABASE_URL', 'GROQ_API_KEY']
        for var in required_vars:
            if not getattr(cls, var):
                raise ValueError(f"Missing required configuration: {var}")
            print(f"✓ {var}: {'*' * 10}")

try:
    Config.validate()
    print("✅ All configuration validated successfully!")
except ValueError as e:
    print(f"❌ Configuration Error: {e}")
    import sys
    sys.exit(1)
