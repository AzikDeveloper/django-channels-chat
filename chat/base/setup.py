from django.conf import settings
from .exceptions import ChatConfigurationError

CHAT_USER_FIELDS = {}
CHAT_USER_SESSION_EXPIRATION = 30
CHAT_DEBUG = False

if hasattr(settings, "CHAT_USER_FIELDS"):
    CHAT_USER_FIELDS = settings.CHAT_USER_FIELDS
else:
    raise ChatConfigurationError("You should set CHAT_USER_FIELDS in settings.py")

if hasattr(settings, "CHAT_USER_SESSION_EXPIRATION"):
    CHAT_USER_SESSION_EXPIRATION = settings.CHAT_USER_SESSION_EXPIRATION

if hasattr(settings, "CHAT_DEBUG"):
    CHAT_DEBUG = settings.CHAT_DEBUG
