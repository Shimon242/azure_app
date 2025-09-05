# /var/www/html/todo_app/todo_app.wsgi
import sys
import os

# Add project directory to path
sys.path.insert(0, '/var/www/html/todo_app')

from app import app as application
