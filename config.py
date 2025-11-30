import os
import logging

if not os.path.exists('logs'):
    os.makedirs('logs')

SECRET_KEY = os.urandom(24)
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
DATABASE_FILE = 'database.db'

HOST = os.environ.get('HOST', '0.0.0.0')
PORT = int(os.environ.get('PORT', 5000))

LOG_LEVEL_NAME = os.environ.get('LOG_LEVEL', 'INFO')
LOG_LEVEL = getattr(logging, LOG_LEVEL_NAME.upper(), logging.INFO)
LOG_FILE = 'logs/app.log'  
LOG_ENCODING = 'utf-8'     