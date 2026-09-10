# Copyright (C) 2010-2026 Université de Lausanne, SIER
# Service Infrastructure Enseignement et Recherche
# <https://www.unil.ch/lettres/fr/home/menuinst/faculte/administration-du-decanat.html>
#
# This file is part of Lumières.Lausanne.
# Lumières.Lausanne is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Admin changelist coverage for the additional user-profile information."""

import pytest
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.urls import reverse

from fiches.admin import CustomUserAdmin, fiches_admin


@pytest.mark.django_db
def test_user_changelist_displays_field_of_research(client):
    administrator = User.objects.create_superuser("admin-profile-list", password="pw")
    user = User.objects.create_user("croco-researcher")
    user.profile.field_of_research = "Projet Croco25-26"
    user.profile.save(update_fields=["field_of_research"])
    client.force_login(administrator)

    response = client.get(reverse("fiches_admin:auth_user_changelist"))

    assert response.status_code == 200
    assert "Domaine de recherche / Historique" in response.content.decode()
    assert "Projet Croco25-26" in response.content.decode()


@pytest.mark.django_db
def test_user_admin_prefetches_profiles_for_the_changelist(django_assert_num_queries):
    User.objects.create_user("profile-one")
    User.objects.create_user("profile-two")
    request = RequestFactory().get(reverse("fiches_admin:auth_user_changelist"))
    admin_obj = CustomUserAdmin(User, fiches_admin)

    with django_assert_num_queries(1):
        users = list(admin_obj.get_queryset(request))
        for user in users:
            admin_obj.field_of_research(user)


@pytest.mark.django_db
def test_user_admin_handles_a_missing_profile():
    user = User.objects.create_user("profile-missing")
    user.profile.delete()
    admin_obj = CustomUserAdmin(User, fiches_admin)

    assert admin_obj.field_of_research(User.objects.get(pk=user.pk)) == ""
