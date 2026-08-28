# Copyright (C) 2010-2026 Université de Lausanne, SIER
# Service Infrastructure Enseignement et Recherche
# <https://www.unil.ch/lettres/fr/home/menuinst/faculte/administration-du-decanat.html>
#
# This file is part of Lumières.Lausanne.
# Lumières.Lausanne is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Lumières.Lausanne is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# This copyright notice MUST APPEAR in all copies of the file.

"""End-to-end tests for the place fiche views (display + create/edit/delete)."""

from __future__ import annotations

from io import StringIO

import pytest
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.urls import reverse

from fiches.models import PlaceCategory, PlaceRecord, PlaceReferenceSite, ReferenceSite


@pytest.fixture
def category(db):
    return PlaceCategory.objects.create(name="Ville/Village")


@pytest.fixture
def geonames(db):
    return ReferenceSite.objects.create(name="GeoNames", code="geonames", base_url="https://www.geonames.org/{id}")


@pytest.fixture
def editor(db, django_user_model):
    user = django_user_model.objects.create_user(username="editor", password="pw")
    user.user_permissions.set(
        Permission.objects.filter(codename__in=["add_placerecord", "change_placerecord", "delete_placerecord"])
    )
    return user


def _management(prefix, total=0):
    return {
        f"{prefix}-TOTAL_FORMS": str(total),
        f"{prefix}-INITIAL_FORMS": "0",
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }


def _empty_formsets():
    data = {}
    for prefix in ("notes",):
        data.update(_management(prefix))
    return data


@pytest.mark.django_db
def test_display_renders(client, category):
    place = PlaceRecord.objects.create(name="Lausanne", category=category)
    response = client.get(reverse("place-display", args=[place.pk]))
    assert response.status_code == 200
    assert b"Lausanne" in response.content


@pytest.mark.django_db
def test_display_shows_category_next_to_the_title(client, category):
    """Client request 2026-07-15: the category belongs in brackets next to the label."""
    place = PlaceRecord.objects.create(name="Lausanne", category=category)

    response = client.get(reverse("place-display", args=[place.pk]))

    assert '<h2>Lausanne <span class="place-category">(Ville/Village)</span></h2>' in response.content.decode()


@pytest.mark.django_db
def test_display_shows_category_next_to_each_related_place(client, category):
    """Same request, applied to the « Lieux associés » listing."""
    place = PlaceRecord.objects.create(name="Lausanne", category=category)
    hamlet = PlaceCategory.objects.create(name="Hameau")
    place.related_places.add(PlaceRecord.objects.create(name="Vidy", category=hamlet))

    response = client.get(reverse("place-display", args=[place.pk]))

    body = response.content.decode()
    assert 'Vidy</a> <span class="place-category">(Hameau)</span>' in body


@pytest.mark.django_db
def test_create_requires_permission(client, django_user_model):
    assert client.get(reverse("place-create")).status_code == 403  # anonymous
    django_user_model.objects.create_user(username="nobody", password="pw")
    client.login(username="nobody", password="pw")
    assert client.get(reverse("place-create")).status_code == 403  # logged in, no perm


@pytest.mark.django_db
def test_create_get_renders_form(client, editor):
    client.force_login(editor)
    response = client.get(reverse("place-create"))
    assert response.status_code == 200
    assert "Nouvelle fiche lieu" in response.content.decode()


@pytest.mark.django_db
def test_create_post_sets_owner_and_redirects(client, editor, category):
    client.force_login(editor)
    data = {"name": "Lausanne", "category": category.pk, **_empty_formsets()}
    response = client.post(reverse("place-create"), data)
    place = PlaceRecord.objects.get(name="Lausanne")
    assert response.status_code == 302
    assert response.url == reverse("place-display", args=[place.pk])
    assert place.access_owner == editor


@pytest.mark.django_db
def test_create_post_saves_inlines(client, editor, category, geonames):
    client.force_login(editor)
    data = {"name": "Lausanne", "category": category.pk, **_empty_formsets()}
    data["variants"] = ["|Losanna"]
    data["reference_links"] = [f"{geonames.pk}|2659994"]
    data.update(_management("notes", 1))
    data["notes-0-text"] = "<p>capitale vaudoise</p>"
    response = client.post(reverse("place-create"), data)
    assert response.status_code == 302
    place = PlaceRecord.objects.get(name="Lausanne")
    assert place.variants.get().name == "Losanna"
    assert place.reference_links.get().identifier == "2659994"
    assert place.notes.get().text == "<p>capitale vaudoise</p>"


@pytest.mark.django_db
def test_edit_updates_place(client, editor, category):
    # `editor` holds the base permissions only — the status matrix calls that
    # "seul. propre", so the fiche must be one they authored.
    place = PlaceRecord.objects.create(name="Lausanne", category=category, creator=editor)
    client.force_login(editor)
    data = {"name": "Lausanne-Ville", "category": category.pk, **_empty_formsets()}
    response = client.post(reverse("place-edit", args=[place.pk]), data)
    assert response.status_code == 302
    place.refresh_from_db()
    assert place.name == "Lausanne-Ville"


@pytest.mark.django_db
def test_edit_uses_the_specific_place_fiche_title(client, editor, category):
    place = PlaceRecord.objects.create(name="Lausanne", category=category, creator=editor)
    client.force_login(editor)

    body = client.get(reverse("place-edit", args=[place.pk])).content.decode()

    assert "Modification de la fiche lieu" in body


@pytest.mark.django_db
def test_delete_place(client, editor, category):
    place = PlaceRecord.objects.create(name="Lausanne", category=category, creator=editor)
    client.force_login(editor)
    response = client.post(reverse("place-delete", args=[place.pk]))
    assert response.status_code == 302
    assert not PlaceRecord.objects.filter(pk=place.pk).exists()


@pytest.mark.django_db
def test_delete_place_refuses_get(client, editor, category):
    place = PlaceRecord.objects.create(name="Lausanne", category=category, creator=editor)
    client.force_login(editor)

    response = client.get(reverse("place-delete", args=[place.pk]))

    assert response.status_code == 405
    assert PlaceRecord.objects.filter(pk=place.pk).exists()


@pytest.mark.django_db
def test_display_renders_place_delete_as_a_csrf_post_form(client, editor, category):
    place = PlaceRecord.objects.create(name="Lausanne", category=category, creator=editor)
    client.force_login(editor)

    body = client.get(reverse("place-display", args=[place.pk])).content.decode()

    assert f'<form action="{reverse("place-delete", args=[place.pk])}" method="post"' in body
    assert 'name="csrfmiddlewaretoken"' in body
    assert '<a href="#" title="Supprimer la fiche"' in body
    assert '<button type="submit" title="Supprimer la fiche"' not in body


@pytest.mark.django_db
def test_edit_refuses_a_fiche_authored_by_someone_else(client, editor, category, django_user_model):
    """Status matrix: "modifier — seul. propre" without change_any_placerecord."""
    other = django_user_model.objects.create_user(username="someone-else", password="pw")
    place = PlaceRecord.objects.create(name="Lausanne", category=category, creator=other)
    client.force_login(editor)

    assert client.get(reverse("place-edit", args=[place.pk])).status_code == 403


@pytest.mark.django_db
def test_delete_refuses_a_fiche_authored_by_someone_else(client, editor, category, django_user_model):
    other = django_user_model.objects.create_user(username="someone-else", password="pw")
    place = PlaceRecord.objects.create(name="Lausanne", category=category, creator=other)
    client.force_login(editor)

    assert client.post(reverse("place-delete", args=[place.pk])).status_code == 403
    assert PlaceRecord.objects.filter(pk=place.pk).exists()


@pytest.mark.django_db
def test_change_any_permission_lifts_the_ownership_restriction(client, editor, category, django_user_model):
    """Chercheurs / doctorants / directeurs hold change_any_placerecord."""
    other = django_user_model.objects.create_user(username="someone-else", password="pw")
    place = PlaceRecord.objects.create(name="Lausanne", category=category, creator=other)
    editor.user_permissions.add(Permission.objects.get(codename="change_any_placerecord"))
    client.force_login(editor)

    assert client.get(reverse("place-edit", args=[place.pk])).status_code == 200


@pytest.mark.django_db
def test_related_place_autocomplete_commits_mouse_selection(client, editor, category):
    """A clicked result becomes a chip immediately, without a second add click."""
    place = PlaceRecord.objects.create(name="Lausanne", category=category, creator=editor)
    client.force_login(editor)

    body = client.get(reverse("place-edit", args=[place.pk])).content.decode()

    assert "selectFirst: true, clickFire: true" in body
    assert "dynamiclist_widget.addToList($button[0], fieldName)" in body
    assert "data.reverse()" not in body
    assert ".blur(function () { $(this).search(); })" not in body
    assert ".fieldWrapper.related_places .dynamiclist_helper_addbut { display: none; }" in body


@pytest.mark.django_db
def test_duplicate_related_place_values_save_as_one_relation(client, editor, category):
    place = PlaceRecord.objects.create(name="Lausanne", category=category, creator=editor)
    related = PlaceRecord.objects.create(name="Renens", category=category)
    client.force_login(editor)

    data = {
        "name": place.name,
        "category": category.pk,
        "related_places": [f"{related.pk}|Renens", f"{related.pk}|Renens"],
        **_empty_formsets(),
    }
    response = client.post(reverse("place-edit", args=[place.pk]), data)

    assert response.status_code == 302
    assert list(place.related_places.values_list("pk", flat=True)) == [related.pk]


@pytest.mark.django_db
def test_director_can_post_changes_to_someone_elses_place_after_role_sync(client, category, django_user_model):
    """Exercise the exact POST that Béatrice reported as « Accès non autorisé ».

    The permission-level tests prove the role has the right; this cross-layer
    check proves the edit view accepts and persists a director's actual save.
    """
    directors = Group.objects.create(name="directeurs")
    call_command("sync_status_roles", apply=True, stdout=StringIO())
    director = django_user_model.objects.create_user(username="director-post", password="pw")
    director.groups.add(directors)
    other = django_user_model.objects.create_user(username="original-author", password="pw")
    place = PlaceRecord.objects.create(name="Lausanne", category=category, creator=other)
    client.force_login(director)

    response = client.post(
        reverse("place-edit", args=[place.pk]),
        {"name": "Lausanne corrigée", "category": category.pk, **_empty_formsets()},
    )

    assert response.status_code == 302
    place.refresh_from_db()
    assert place.name == "Lausanne corrigée"
    assert place.creator == other


@pytest.mark.django_db
def test_creator_is_stamped_on_creation(client, editor, category):
    """ "Auteur de la fiche" is filled in automatically, like on the biblio fiche."""
    client.force_login(editor)
    data = {"name": "Yverdon", "category": category.pk, **_empty_formsets()}

    client.post(reverse("place-create"), data)

    assert PlaceRecord.objects.get(name="Yverdon").creator == editor


@pytest.mark.django_db
def test_display_shows_author_and_last_modification(client, editor, category):
    """Client request 2026-07-15: the same two auto-filled fields as the biblio fiche.

    Also covers the activity-log wiring: the modification line can only be
    rendered because saving a place now writes an ActivityLog entry, which it
    never did before.
    """
    editor.first_name, editor.last_name = "Damiano", "Bardelli"
    editor.save()
    client.force_login(editor)
    client.post(reverse("place-create"), {"name": "Yverdon", "category": category.pk, **_empty_formsets()})
    place = PlaceRecord.objects.get(name="Yverdon")

    body = client.get(reverse("place-display", args=[place.pk])).content.decode()

    assert "Auteur de la fiche" in body
    assert "Damiano Bardelli" in body
    assert "Dernière modification" in body
    assert f"({editor.username})" in body


@pytest.mark.django_db
def test_place_autocomplete_searches_by_name(client, editor, category):
    PlaceRecord.objects.create(name="Fribourg", category=category)
    PlaceRecord.objects.create(name="Lausanne", category=category)
    client.force_login(editor)
    body = client.get(reverse("place-autocomplete"), {"q": "frib"}).content.decode()
    assert "Fribourg" in body
    assert "Lausanne" not in body


@pytest.mark.django_db
def test_related_places_saved_via_widget(client, editor, category):
    other = PlaceRecord.objects.create(name="Genève", category=category)
    client.force_login(editor)
    data = {"name": "Lausanne", "category": category.pk, **_empty_formsets()}
    data["related_places"] = [f"{other.id}|Genève"]
    response = client.post(reverse("place-create"), data)
    assert response.status_code == 302
    assert other in PlaceRecord.objects.get(name="Lausanne").related_places.all()


@pytest.mark.django_db
def test_editing_a_place_reference_identifier_replaces_it_in_place(client, editor, category, geonames):
    """Cover the complete form round-trip, not only the shared widget HTML."""
    place = PlaceRecord.objects.create(name="Lausanne", category=category, creator=editor)
    PlaceReferenceSite.objects.create(
        place=place,
        reference_site=geonames,
        identifier="wrong-id",
    )
    client.force_login(editor)

    response = client.post(
        reverse("place-edit", args=[place.pk]),
        {
            "name": place.name,
            "category": category.pk,
            "reference_links": [f"{geonames.pk}|2659994"],
            **_empty_formsets(),
        },
    )

    assert response.status_code == 302
    assert list(place.reference_links.values_list("identifier", flat=True)) == ["2659994"]


@pytest.mark.django_db
def test_workspace_shows_place_creation_for_admin(client, editor):
    client.force_login(editor)
    response = client.get(reverse("workspace-main"))
    assert response.status_code == 200
    assert "Créer une fiche lieu".encode() in response.content
    assert reverse("place-create").encode() in response.content


@pytest.mark.django_db
def test_workspace_hides_place_creation_without_perm(client, django_user_model):
    user = django_user_model.objects.create_user(username="plain", password="pw")
    client.force_login(user)
    response = client.get(reverse("workspace-main"))
    assert response.status_code == 200
    assert "Créer une fiche lieu".encode() not in response.content


@pytest.mark.django_db
def test_display_shows_create_button_for_admin(client, editor, category):
    place = PlaceRecord.objects.create(name="Lausanne", category=category)
    client.force_login(editor)
    response = client.get(reverse("place-display", args=[place.pk]))
    assert reverse("place-create").encode() in response.content


@pytest.mark.django_db
def test_display_hides_create_button_for_anonymous(client, category):
    place = PlaceRecord.objects.create(name="Lausanne", category=category)
    response = client.get(reverse("place-display", args=[place.pk]))
    assert reverse("place-create").encode() not in response.content
