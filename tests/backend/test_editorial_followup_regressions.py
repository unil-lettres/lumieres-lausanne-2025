"""Regression contracts for editorial lot #300 follow-up."""
from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.apps import apps
from django.contrib.auth.models import AnonymousUser, User
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.test import RequestFactory
from django.utils import timezone
from fiches.models.search.search import QuickSearchForm
from fiches.models import Biblio, DocumentLanguage, DocumentType, NotePlace, PlaceCategory, PlaceRecord, Transcription
from fiches.search_indexes import PlaceRecordIndex
from fiches.views.search import _search_transcription_links


@pytest.fixture
def manuscript(db):
    DocumentLanguage.objects.create(name="Français", code="fr", ordering=1)
    kind = DocumentType.objects.create(id=5, name="Manuscrit", code=5)
    return Biblio.objects.create(id=101, title="Audit manuscript", document_type=kind, litterature_type="p")


@pytest.mark.django_db
def test_latest_publication_links_to_actual_latest_transcription(client, manuscript):
    older = Transcription.objects.create(manuscript_b=manuscript, access_public=True,
        access_private=False, published_date=timezone.now()-timedelta(days=2))
    latest = Transcription.objects.create(manuscript_b=manuscript, access_public=True,
        access_private=False, published_date=timezone.now())
    for path in ['/', '/publications/dernieres-transcriptions/']:
        response = client.get(path)
        assert response.status_code == 200
        body = response.content.decode()
        assert manuscript.title in body
        assert f'id="Transcription__{latest.pk}"' in body, f"Latest {latest.pk} missing; older {older.pk} used"


@pytest.mark.django_db
def test_transcription_search_hit_links_to_matching_transcription(manuscript):
    older = Transcription.objects.create(manuscript_b=manuscript, access_public=True, access_private=False)
    matching = Transcription.objects.create(manuscript_b=manuscript, access_public=True, access_private=False)
    request = RequestFactory().get('/chercher/', {'q': 'audit', 't': 'transcription'})
    request.user = AnonymousUser()
    page = Paginator([SimpleNamespace(model_name='transcription', object=matching)], 30).page(1)
    body = render_to_string('fiches/search/search_general.html', {
        'query': 'audit', 'form': QuickSearchForm(request.GET), 'page': page, 'page_obj': page,
        'paginator': page.paginator, 'selected_types': ['transcription'],
        'counts': {'biblio': 0, 'transcription': 1, 'person': 0, 'place': 0},
        'search_transcription_links': _search_transcription_links(request.user, [manuscript.pk]),
    }, request=request)
    assert manuscript.title in body
    assert f'id="Transcription__{matching.pk}"' in body, f"Hit {matching.pk} missing; older {older.pk} used"


@pytest.mark.django_db
def test_transcription_only_filter_keeps_private_owner_result(client, manuscript):
    owner = User.objects.create_user('audit_owner')
    author = User.objects.create_user('audit_author')
    trans = Transcription.objects.create(manuscript_b=manuscript, author=author,
        access_owner=owner, access_private=True, access_public=False)
    assert trans.user_access(owner)
    client.force_login(owner)
    query = {'x0_fld': 'title', 'x0_val': manuscript.title}
    ordinary = client.get('/chercher/bibliographie/', query)
    assert f'id="Transcription__{trans.pk}"' in ordinary.content.decode()
    filtered = client.get('/chercher/bibliographie/', {**query, 'dtT': '1'})
    assert filtered.status_code == 200
    assert f'id="Transcription__{trans.pk}"' in filtered.content.decode(), 'Readable private owner result disappears under dtT=1'


@pytest.mark.django_db
def test_moving_public_note_refreshes_old_and_new_place(monkeypatch):
    category = PlaceCategory.objects.create(name='Audit category')
    old = PlaceRecord.objects.create(name='Audit old place', category=category)
    new = PlaceRecord.objects.create(name='Audit new place', category=category)
    indexed = {}
    def capture(sender, instance, **kwargs):
        indexed[instance.pk] = PlaceRecordIndex().prepare(instance)['text']
    monkeypatch.setattr(apps.get_app_config('haystack').signal_processor, 'handle_save', capture)
    note = NotePlace.objects.create(owner=old, text='audituniquenotetoken', access_public=True)
    assert 'audituniquenotetoken' in indexed[old.pk]
    note.owner = new
    note.access_public = False
    note.save()
    assert 'audituniquenotetoken' not in indexed[new.pk]
    assert 'audituniquenotetoken' not in PlaceRecordIndex().prepare(old)['text']
    assert 'audituniquenotetoken' not in indexed[old.pk], 'Old place search document not refreshed'


@pytest.mark.django_db
@pytest.mark.parametrize("relation", ["anonymous", "owner", "author", "other", "direct_group", "django_group", "change_any_transcription", "access_unpublished_transcription"])
@pytest.mark.parametrize("private,public", [(False, True), (False, False), (True, False), (True, True)])
def test_filter_matches_display_access(client, manuscript, relation, private, public):
    from django.contrib.auth.models import Group, Permission
    from fiches.models import UserGroup
    from fiches.transcription_links import readable_transcriptions
    owner = User.objects.create_user("owner")
    author = User.objects.create_user("author")
    user = AnonymousUser() if relation == "anonymous" else (
        owner if relation == "owner" else author if relation == "author" else User.objects.create_user("reader")
    )
    trans = Transcription.objects.create(manuscript_b=manuscript, access_owner=owner,
        author=author, access_private=private, access_public=public)
    if relation in ("direct_group", "django_group"):
        access = UserGroup.objects.create(name="Readers", sort=1)
        trans.access_groups.add(access)
        if relation == "direct_group":
            access.users.add(user)
        else:
            group = Group.objects.create(name="Readers")
            access.groups.add(group)
            user.groups.add(group)
    if relation.endswith("transcription"):
        user.user_permissions.add(Permission.objects.get(codename=relation))
    expected = (user.has_perm("fiches.change_any_transcription") or
        user.has_perm("fiches.access_unpublished_transcription") or trans.user_access(user))
    assert readable_transcriptions(user).filter(pk=trans.pk).exists() == expected
    if user.is_authenticated:
        client.force_login(user)
    response = client.get('/chercher/bibliographie/', {'x0_fld': 'title', 'x0_val': manuscript.title, 'dtT': '1'})
    assert response.status_code == 200
    assert (f'id="Transcription__{trans.pk}"' in response.content.decode()) == expected


@pytest.mark.django_db
def test_exact_target_does_not_fall_back_or_bypass_context(manuscript):
    public = Transcription.objects.create(manuscript_b=manuscript, access_public=True, access_private=False)
    private = Transcription.objects.create(manuscript_b=manuscript, access_private=True)
    other = Biblio.objects.create(title="Other", document_type=manuscript.document_type, litterature_type="p")
    mismatched = Transcription.objects.create(manuscript_b=other, access_public=True, access_private=False)
    for exact, extra in [(private, {}), (mismatched, {}), (public, {'nolink': True}),
            (public, {'search_transcription_links': {}}), (public, {'user_accessible_trans': []})]:
        body = render_to_string('fiches/bibliography_references/biblio_template.html', {
            'ref': manuscript, 'reference_transcription': exact, 'user': AnonymousUser(), **extra})
        assert 'id="Transcription__' not in body


@pytest.mark.django_db
def test_note_partial_save_uses_persisted_owner(monkeypatch):
    category = PlaceCategory.objects.create(name='Audit category')
    old = PlaceRecord.objects.create(name='Old', category=category)
    new = PlaceRecord.objects.create(name='New', category=category)
    indexed = {}
    def capture(sender, instance, **kwargs):
        indexed[instance.pk] = PlaceRecordIndex().prepare(instance)['text']
    monkeypatch.setattr(apps.get_app_config('haystack').signal_processor, 'handle_save', capture)
    note = NotePlace.objects.create(owner=old, text='partialnotetoken', access_public=True)
    note.owner = new
    note.access_public = False
    note.save(update_fields=['access_public'])
    note.refresh_from_db()
    assert note.owner_id == old.pk
    assert 'partialnotetoken' not in indexed[old.pk]
    note.owner = new
    note.access_public = True
    note.save()
    assert 'partialnotetoken' not in indexed[old.pk]
    assert 'partialnotetoken' in indexed[new.pk]


@pytest.mark.django_db
def test_link_map_and_exact_targets_have_bounded_queries(manuscript, django_assert_num_queries):
    from fiches.transcription_links import readable_transcription_links
    from fiches.templatetags.fiches_extras import bibliography_transcription_link
    reader = User.objects.create_user('bounded_reader')
    reader.has_perm('fiches.change_any_transcription')
    public = [Transcription.objects.create(manuscript_b=manuscript,
        access_public=True, access_private=False) for _ in range(10)]
    restricted = [Transcription.objects.create(manuscript_b=manuscript,
        access_public=False, access_private=False) for _ in range(10)]
    with django_assert_num_queries(1):
        links = readable_transcription_links(reader, [manuscript.pk])
    assert links[manuscript.pk] == public[0].pk
    with django_assert_num_queries(0):
        for trans in public + restricted:
            context = {'user': reader, 'reference_transcription': trans,
                       'search_transcription_links': links}
            expected = trans.pk if trans in public else None
            assert bibliography_transcription_link(context, manuscript) == expected
    other = Biblio.objects.create(title='Other bounded', document_type=manuscript.document_type,
                                 litterature_type='p')
    assert bibliography_transcription_link({'user': reader,
        'reference_transcription': public[0], 'search_transcription_links': links}, other) is None
