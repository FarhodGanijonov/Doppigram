import os

import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
import messenger

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from messenger.middlewere import JWTAuthMiddleware
from messenger.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        URLRouter(websocket_urlpatterns)
    ),
})
