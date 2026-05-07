import datetime
from types import SimpleNamespace

from django.test import SimpleTestCase

from fiches.templatetags.fiches_extras import date_biblio


class BibliographyDateDisplayTest(SimpleTestCase):
    def test_date_biblio_preserves_bracketed_date_components(self):
        biblio = SimpleNamespace(
            date=datetime.date(1761, 11, 1),
            date_f="[%m]-[%Y]",
        )

        self.assertEqual(date_biblio(biblio, "date"), "[novembre] [1761]")
