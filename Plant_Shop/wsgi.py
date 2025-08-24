import os

from django.core.wsgi import get_wsgi_application

try:
    from load_env import load_environment
    load_environment()
except ImportError:
    pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Plant_Shop.settings')

application = get_wsgi_application()