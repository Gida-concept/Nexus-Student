import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    ADMIN_USER_ID = int(os.getenv('ADMIN_USER_ID', 0))
    DATABASE_URL = os.getenv('DATABASE_URL')
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    PAYSTACK_SECRET_KEY = os.getenv('PAYSTACK_SECRET_KEY')
    PAYSTACK_PUBLIC_KEY = os.getenv('PAYSTACK_PUBLIC_KEY')
    CLOUDINARY_URL = os.getenv('CLOUDINARY_URL')
    PERPLEXICA_API_URL = os.getenv('PERPLEXICA_API_URL')
    ENABLE_PAYMENTS = os.getenv('ENABLE_PAYMENTS', 'false').lower() == 'true'
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @classmethod
    def validate(cls):
        required_vars = [
            'BOT_TOKEN',
            'DATABASE_URL',
            'GROQ_API_KEY',
            'PAYSTACK_SECRET_KEY',
            'PAYSTACK_PUBLIC_KEY',
            'CLOUDINARY_URL',
            'PERPLEXICA_API_URL'
        ]
        for var in required_vars:
            if not getattr(cls, var):
                raise ValueError(f"Missing required configuration: {var}")

Config.validate()