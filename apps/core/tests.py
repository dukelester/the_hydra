from pathlib import Path

from django.conf import settings
from django.test.runner import DiscoverRunner


def load_tests(loader, standard_tests, pattern):
    start_dir = Path(settings.BASE_DIR) / "tests"
    discovered = loader.discover(str(start_dir), pattern="test*.py", top_level_dir=str(settings.BASE_DIR))
    standard_tests.addTests(discovered)
    return standard_tests
