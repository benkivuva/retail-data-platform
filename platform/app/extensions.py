"""Flask extensions instantiated once and bound to the app in create_app."""
from flask_caching import Cache

cache = Cache()