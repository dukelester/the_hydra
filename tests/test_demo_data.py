from django.core.management import call_command
from django.test import TestCase

from apps.projects.models import Project
from apps.sources.models import SourceDocument


class DemoDataTests(TestCase):
    def test_load_demo_data_covers_five_countries(self):
        call_command("load_demo_data", reset=True)
        demo = Project.objects.filter(is_demo=True)
        self.assertGreaterEqual(demo.count(), 20)
        self.assertEqual(
            set(demo.values_list("country", flat=True)),
            {"KE", "TZ", "BI", "CD", "NG"},
        )
        expected = {
            "KE": ("KES", "Kisumu"),
            "TZ": ("TZS", "Dar es Salaam"),
            "BI": ("BIF", "Bujumbura"),
            "CD": ("CDF", "Kinshasa"),
            "NG": ("NGN", "Lagos"),
        }
        for code, (currency, county) in expected.items():
            qs = demo.filter(country=code)
            self.assertGreaterEqual(qs.count(), 3, code)
            self.assertTrue(qs.filter(name__contains="[DEMO]").exists(), code)
            self.assertTrue(qs.filter(currency=currency).exists(), code)
            self.assertTrue(qs.filter(county=county).exists(), code)
            self.assertTrue(qs.filter(is_featured=True).exists(), code)
        self.assertTrue(SourceDocument.objects.filter(is_demo=True, title__contains="[DEMO]").exists())
        self.assertFalse(demo.filter(description__icontains="corruption").exists())
