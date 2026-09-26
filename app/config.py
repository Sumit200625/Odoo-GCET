# app/config.py
import os

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'stocksense-hackathon-super-secret-key-2026'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'stocksense.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

config = {
    'default': Config
}
