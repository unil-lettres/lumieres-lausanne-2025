from django.test import TestCase
from django.urls import reverse


class PersonListSearchTemplateTest(TestCase):
    def test_person_list_keeps_inherited_menu_javascript(self):
        response = self.client.get(reverse("list-person"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dropdown menu functionality")
        self.assertContains(response, "jquery-1.8.2.min.js")
