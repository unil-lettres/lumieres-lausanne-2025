# Copyright (C) 2010-2026 Université de Lausanne, SIER
# Service Infrastructure Enseignement et Recherche
# <https://www.unil.ch/lettres/fr/home/menuinst/faculte/administration-du-decanat.html>
#
# This file is part of Lumières.Lausanne.
# Lumières.Lausanne is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""Rendered HTML contracts for public biography display pages."""

import pytest
from django.urls import reverse

from fiches.models.person.biography import Biography, Religion
from fiches.models.person.person import Person


@pytest.mark.django_db
def test_public_biography_hides_empty_fields_and_keeps_populated_fields(client):
    person = Person.objects.create(name="Sokologorsky, Yakov Ivanovitch")
    religion = Religion.objects.create(name="Orthodoxe")
    Biography.objects.create(
        person=person,
        version=0,
        valid=True,
        religion=religion,
        activity_places="<p>&nbsp;</p>",
        public_functions="<p>Biographie renseignée.</p>",
        comments_on_work="<p><br></p>",
        archive="<p>Archives renseignées.</p>",
    )

    response = client.get(reverse("biography-display", args=[person.pk]))

    assert response.status_code == 200
    html = response.content.decode()
    assert "Confession" in html
    assert "Orthodoxe" in html
    assert "Biographie renseignée." in html
    assert "Fonds d&#x27;archives" in html
    assert "Archives renseignées." in html
    for empty_label in (
        "Naissance",
        "Décès",
        "Lieu d&#x27;origine",
        "Nationalité",
        "Etat civil",
        "Commentaires sur son oeuvre/ses écrits",
        "Fonctions publiques et privées",
        "Sociétés et académies",
        "Relations et contacts",
    ):
        assert empty_label not in html


@pytest.mark.django_db
def test_public_biography_hides_visually_empty_rich_text_fields(client):
    person = Person.objects.create(name="Biographie, Vide")
    Biography.objects.create(
        person=person,
        version=0,
        valid=True,
        public_functions="<p>&nbsp;</p>",
        comments_on_work="<p><br></p>",
        archive="   ",
    )

    response = client.get(reverse("biography-display", args=[person.pk]))

    assert response.status_code == 200
    html = response.content.decode()
    assert '<div class="field_label">Biographie</div>' not in html
    assert "Commentaires sur son oeuvre/ses écrits" not in html
    assert "Fonds d&#x27;archives" not in html
