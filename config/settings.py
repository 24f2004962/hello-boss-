import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'trek-app-secret-2024')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///trekking.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ITEMS_PER_PAGE = 10 # default items per table page
