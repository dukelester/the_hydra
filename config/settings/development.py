"""Local / development settings."""

from .base import *  # noqa: F401,F403
from .base import BASE_DIR, RUNNING_TESTS, env, env_bool

DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = list({*ALLOWED_HOSTS, "localhost", "127.0.0.1", "testserver", "web"})

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

if not RUNNING_TESTS:
    use_postgres = bool(env("POSTGRES_HOST")) and not env_bool("USE_SQLITE", False)
    if not use_postgres:
        DATABASES = {  # noqa: F811
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }
