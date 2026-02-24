import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super_secure_hackathon_key_aes256'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://user:pass@localhost:5432/health'
