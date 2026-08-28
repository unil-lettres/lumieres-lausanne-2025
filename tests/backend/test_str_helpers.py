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

"""Batch tests for small 1-3 stmt gaps — mostly __str__ on unsaved instances."""

import types

import pytest
from django.contrib.auth.models import User
from unittest.mock import patch

from fiches.models.content.finding import Finding
from fiches.models.content.free_content import FreeContent
from fiches.models.content.image import Image
from fiches.models.content.news import News
from fiches.models.content.publication import Publication
from fiches.models.contributions import get_contribution_doc_model, get_contribution_man_model
from fiches.models.contributions.keyword import PrimaryKeyword, SecondaryKeyword
from fiches.models.contributiontype import ContributionType
from fiches.models.core.user_group import UserGroup
from fiches.models.core.user_profile import UserProfile
from fiches.models.documents.attached_document import AttachedDocument
from fiches.models.misc.notes import NoteBase
from fiches.models.person.biography import NoteBiography
from fiches.templatetags.utils import django_version
from fiches.widgets import PersonWidget, StaticList


# ---------------------------------------------------------------------------
# content models __str__  (1 stmt each)
# ---------------------------------------------------------------------------


def test_finding_str():
    assert str(Finding(title="Trouvaille")) == "Trouvaille"


def test_free_content_str():
    assert str(FreeContent(title="Contenu libre")) == "Contenu libre"


def test_image_str_no_image():
    img = Image.__new__(Image)
    img.image = None
    assert str(img) == "No image"


def test_image_str_with_name():
    img = Image.__new__(Image)
    img.image = types.SimpleNamespace(name="uploads/2024/photo.jpg")
    assert str(img) == "photo.jpg"


def test_news_str():
    assert str(News(title="Actualité")) == "Actualité"


def test_publication_str():
    assert str(Publication(title="Revue")) == "Revue"


# ---------------------------------------------------------------------------
# contributiontype / keyword / user_group  (1-2 stmts each)
# ---------------------------------------------------------------------------


def test_contribution_type_str():
    assert str(ContributionType(name="Auteur", code=0)) == "Auteur"


def test_user_group_str():
    assert str(UserGroup(name="Éditeurs")) == "Éditeurs"


def test_primary_keyword_str():
    assert str(PrimaryKeyword(word="Lumières")) == "Lumières"


def test_secondary_keyword_str():
    pk = PrimaryKeyword(word="Philosophie")
    sk = SecondaryKeyword(word="empirisme", primary_keyword=pk)
    assert str(sk) == "empirisme (Philosophie)"


# ---------------------------------------------------------------------------
# AttachedDocument.__str__  (lines 38-40)
# ---------------------------------------------------------------------------


def test_attached_document_str_with_title():
    doc = AttachedDocument.__new__(AttachedDocument)
    doc.title = "Mon rapport"
    assert str(doc) == "Mon rapport"


def test_attached_document_str_no_title():
    doc = AttachedDocument.__new__(AttachedDocument)
    doc.title = ""
    doc.file = types.SimpleNamespace(name="files/2024/rapport.pdf")
    assert str(doc) == "rapport.pdf"


# ---------------------------------------------------------------------------
# NoteBase.__str__  (line 48) — via NoteBiography (concrete subclass)
# ---------------------------------------------------------------------------


def test_note_base_str_strips_tags():
    note = NoteBiography.__new__(NoteBiography)
    note.text = "<p>Texte de la note biographique</p>"
    result = str(note)
    assert "Texte" in result
    assert "<p>" not in result


# ---------------------------------------------------------------------------
# UserProfile.__str__  (line 36)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_user_profile_str():
    # post_save signal auto-creates UserProfile on User creation
    user = User.objects.create_user(username="profile_str_u", password="x")
    profile = UserProfile.objects.get(user=user)
    assert str(profile) == "profile_str_u"


# ---------------------------------------------------------------------------
# contributions/__init__ lazy model loaders  (lines 26, 30)
# ---------------------------------------------------------------------------


def test_get_contribution_doc_model():
    from fiches.models.documents.document import ContributionDoc
    assert get_contribution_doc_model() is ContributionDoc


def test_get_contribution_man_model():
    from fiches.models.documents.document import ContributionMan
    assert get_contribution_man_model() is ContributionMan


# ---------------------------------------------------------------------------
# templatetags/utils.django_version  (line 29)
# ---------------------------------------------------------------------------


def test_django_version_returns_string():
    result = django_version()
    assert isinstance(result, str)
    assert "." in result  # e.g. "5.2.14"


# ---------------------------------------------------------------------------
# PersonWidget.render exception path  (lines 99-100)
# ---------------------------------------------------------------------------


def test_person_widget_render_format_value_exception_falls_back():
    widget = PersonWidget()
    with patch.object(widget, "format_value", side_effect=ValueError("boom")):
        html = widget.render("person", "42|Name")
    # label = str("42|Name").strip("|") = "42|Name" (no leading/trailing |)
    assert "person" in html


# ---------------------------------------------------------------------------
# ACModel.user_access — UserGroup direct + indirect group membership (lines 76, 80)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_user_access_via_usergroup_direct_membership():
    from fiches.models.misc.object_collection import ObjectCollection

    owner = User.objects.create_user(username="ac_owner2", password="x")
    member = User.objects.create_user(username="ac_member2", password="x")
    ug = UserGroup.objects.create(name="AccessGroup2", sort=1)
    ug.users.add(member)
    coll = ObjectCollection.objects.create(
        name="AC Coll2", owner=owner, access_owner=owner, access_private=False
    )
    coll.access_groups.add(ug)
    assert coll.user_access(member) is True  # line 76


@pytest.mark.django_db
def test_user_access_via_django_group_indirect_membership():
    from django.contrib.auth.models import Group
    from fiches.models.misc.object_collection import ObjectCollection

    owner = User.objects.create_user(username="ac_owner3", password="x")
    member = User.objects.create_user(username="ac_member3", password="x")
    django_grp = Group.objects.create(name="DjangoGroup3")
    member.groups.add(django_grp)
    ug = UserGroup.objects.create(name="AccessGroup3", sort=1)
    ug.groups.add(django_grp)
    coll = ObjectCollection.objects.create(
        name="AC Coll3", owner=owner, access_owner=owner, access_private=False
    )
    coll.access_groups.add(ug)
    assert coll.user_access(member) is True  # line 80


# ---------------------------------------------------------------------------
# UserProfile.get_usergroups  (lines 48-50) — DB
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_user_profile_get_usergroups_empty():
    user = User.objects.create_user(username="profile_grp_u", password="x")
    profile = UserProfile.objects.get(user=user)  # auto-created by post_save signal
    assert list(profile.get_usergroups()) == []
