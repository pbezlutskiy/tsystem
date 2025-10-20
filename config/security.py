# config/security.py
import os
from dotenv import load_dotenv

load_dotenv()

class SecurityConfig:
    TINKOFF_TOKEN = os.getenv('TINKOFF_TOKEN')
    TINKOFF_SANDBOX_TOKEN = os.getenv('TINKOFF_SANDBOX_TOKEN')
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    @classmethod
    def validate_tokens(cls):
        if not cls.TINKOFF_TOKEN:
            raise ValueError("TINKOFF_TOKEN not set in environment")