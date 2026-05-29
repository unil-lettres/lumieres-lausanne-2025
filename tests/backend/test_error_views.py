from django.test import RequestFactory, SimpleTestCase

from fiches.views import server_error


class ServerErrorViewTest(SimpleTestCase):
    def test_server_error_renders_500_template(self):
        request = RequestFactory().get("/fiches_admin/fiches/project/16/change/")

        response = server_error(request)

        self.assertEqual(response.status_code, 500)
        self.assertIn("Erreur 500", response.content.decode())
