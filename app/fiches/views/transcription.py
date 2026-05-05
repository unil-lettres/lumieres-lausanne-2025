#    Copyright (C) 2010-2012 Université de Lausanne, RISET
#    < http://www.unil.ch/riset/ >
#
#    This file is part of Lumières.Lausanne.
#    Lumières.Lausanne is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Lumières.Lausanne is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#    This copyright notice MUST APPEAR in all copies of the file.
#

"""
Views for managing Transcription objects in the fiches app.

Includes display, creation, editing, and deletion of transcriptions,
as well as handling related notes and permissions.
"""

import json
import re
from functools import lru_cache
from html.parser import HTMLParser
from urllib.parse import quote, unquote, urlparse
from urllib.parse import quote as urlquote

from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.forms.models import inlineformset_factory
from django.http import (
    Http404,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseRedirect,
    HttpResponseServerError,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from fiches.forms import NoteFormTranscription, TranscriptionForm
from fiches.models import Transcription
from fiches.models.documents import Biblio, NoteTranscription
from fiches.utils import (
    get_last_model_activity,
    log_model_activity,
    update_object_index,
    get_default_publisher_user,
)
import requests
from utils import dbg_logger

# ==============================================================================#
# ----------- TRANSCRIPTION ----------------------------------------------------#
# ==============================================================================#
FICHE_TYPE_NAME = "Transcription"

DISPLAY_COLLECTOR = True


PATRINUM_MANIFEST_RE = re.compile(
    r"^https://patrinum\.ch/record/(?P<record_id>\d+)/export/iiif_manifest/?$"
)


class PatrinumOpenGraphImageParser(HTMLParser):
    """Collect Patrinum preview images from record-page Open Graph metadata."""

    def __init__(self, record_id):
        super().__init__()
        self.record_id = str(record_id)
        self.image_urls = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "meta":
            return

        attr_dict = dict(attrs)
        if attr_dict.get("property") != "og:image":
            return

        content = attr_dict.get("content", "")
        if f"/record/{self.record_id}/files/" in content:
            self.image_urls.append(content)


def patrinum_image_url_to_info_json(image_url, record_id):
    path = urlparse(image_url).path
    marker = f"/record/{record_id}/files/"
    if marker not in path:
        return None

    filename = path.split(marker, 1)[1]
    if not filename:
        return None

    filename = quote(unquote(filename), safe="")
    return (
        "https://patrinum.ch/nanna/api/multimedia/image/v2/"
        f"recid:{record_id}-{filename}/info.json"
    )


@lru_cache(maxsize=128)
def get_patrinum_tile_sources(iiif_url):
    """
    Build IIIF Image API info.json URLs when Patrinum blocks manifest export.

    Patrinum record pages expose one Open Graph image per page and their image
    API endpoints are CORS-enabled. The manifest export endpoint may return
    403, so display pages can preload the same sequence from the record page.
    """
    match = PATRINUM_MANIFEST_RE.match(iiif_url or "")
    if not match:
        return []

    record_id = match.group("record_id")
    response = requests.get(
        f"https://patrinum.ch/record/{record_id}",
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=8,
    )
    response.raise_for_status()

    parser = PatrinumOpenGraphImageParser(record_id)
    parser.feed(response.text)

    tile_sources = []
    seen = set()
    for image_url in parser.image_urls:
        info_url = patrinum_image_url_to_info_json(image_url, record_id)
        if info_url and info_url not in seen:
            tile_sources.append(info_url)
            seen.add(info_url)

    return tile_sources


def get_facsimile_tile_sources(iiif_url):
    if not iiif_url:
        return []

    try:
        return get_patrinum_tile_sources(iiif_url)
    except requests.RequestException:
        dbg_logger.exception("Unable to derive Patrinum facsimile tile sources")
        return []


def index(request):
    """Redirects to the bibliography search page with predefined query parameters."""
    return HttpResponseRedirect(
        "".join((reverse("search-biblio"), "?dtT=1&cl1=1&cl3=1&cl4=1"))
    )


def display(request, trans_id):
    """
    Display a Transcription object and its related notes.

    Args:
        request: The HTTP request object.
        trans_id: The primary key of the Transcription to display.

    Returns:
        HttpResponse rendering the transcription display template.
    """
    trans = get_object_or_404(Transcription, pk=trans_id)
    trans_user_access = request.user.has_perm(
        "fiches.access_unpublished_transcription"
    ) or trans.user_access(request.user)
    last_activity = get_last_model_activity(trans)
    facsimile_tile_sources = get_facsimile_tile_sources(trans.facsimile_iiif_url)

    note_qs = NoteTranscription.objects.filter(owner=trans)
    if request.user.is_authenticated and not request.user.is_staff:
        note_qs = note_qs.filter(
            Q(access_public=True)
            | Q(access_owner=request.user)
            | (
                Q(access_groups__isnull=True)
                | Q(access_groups__in=request.user.usergroup_set.all())
            )
        ).distinct()

    context = {
        "trans": trans,
        "last_activity": last_activity,
        # 'man': trans.manuscript,  # If unused, remove or uncomment if needed
        "model": Transcription,
        "trans_user_access": trans_user_access,
        "display_collector": DISPLAY_COLLECTOR,
        "note_qs": note_qs,
        "facsimile_tile_sources_json": json.dumps(facsimile_tile_sources),
    }

    ext_template = (
        f"fiches/display/display_base{request.COOKIES.get('layoutversion', '2')}.html"
    )
    context.update({"ext_template": ext_template})

    return render(request, "fiches/display/transcription.html", context)


@permission_required(perm="fiches.add_transcription")
def create(request, man_id=None, doc_id=None):
    """
    Create a new Transcription object, requiring either a manuscript ID or a document ID.

    Args:
        request: The HTTP request object.
        man_id: The ID of the Manuscript (optional).
        doc_id: The ID of the Document (optional).

    Returns:
        HttpResponseBadRequest if neither or both IDs are provided, otherwise calls edit to create the transcription.
    """
    if not (bool(man_id) ^ bool(doc_id)):
        return HttpResponseBadRequest(
            "one and only one of 'man_id', 'doc_id' is required"
        )
    return edit(request, man_id=man_id, doc_id=doc_id, trans_id=None, new_trans=True)


@permission_required(perm="fiches.delete_transcription")
def delete(request, trans_id):
    """
    Delete a Transcription and redirect to the related bibliography if possible.

    If the related Biblio does not exist, show a clear error message.
    """
    # XXX: maybe not mandatory for biblio delete.
    trans = get_object_or_404(Transcription, pk=trans_id)
    biblio = trans.manuscript_b
    if biblio and getattr(biblio, "id", None):
        response = HttpResponseRedirect(
            reverse("display-bibliography", args=[biblio.id])
        )
    else:
        # Show a user-friendly error if the related bibliography is missing
        return HttpResponseServerError(
            "No related bibliography for this transcription or it has been deleted."
        )
    trans.delete()
    return response


@never_cache
@permission_required(perm="fiches.change_transcription")
def edit(
    request, trans_id=None, man_id=None, doc_id=None, new_trans=False, del_trans=False
):
    """
    Edit or create a Transcription object.

    Ensures the object is saved before being used in formsets or related fields. Handles both GET and POST requests.
    """
    if new_trans:
        # man = get_object_or_404(Manuscript, pk=man_id) if man_id else None # If unused, remove or uncomment if needed
        doc = get_object_or_404(Biblio, pk=doc_id) if doc_id else None
        trans = Transcription(
            manuscript_b=doc,
            author=request.user,
            access_owner=request.user,
            access_public=False,
        )
        trans.access_owner = request.user
        trans.save()  # Ensure the instance is saved before using in formsets
    else:
        trans = get_object_or_404(Transcription, pk=trans_id)
        doc = trans.manuscript_b

    last_activity = get_last_model_activity(trans)

    context = {"model": Transcription}

    trans_user_access = (
        new_trans
        or request.user.has_perm("fiches.access_unpublished_transcription")
        or trans.user_access(request.user)
    )
    access_public_original = trans.access_public
    published_date_original = trans.published_date
    published_by_original = trans.published_by

    # user needs the publish_transcription permission to modify a published transcription
    if trans.access_public and not request.user.has_perm(
        "fiches.publish_transcription"
    ):
        return HttpResponseForbidden(
            "Vous ne disposez pas des permissions nécessaires pour modifier une transcription publiée"
        )

    # Dynamically set extra: 1 if no notes exist, 0 otherwise
    note_count = (
        NoteTranscription.objects.filter(owner=trans).count() if trans.pk else 0
    )
    NoteFormset = inlineformset_factory(
        Transcription,
        NoteTranscription,
        extra=1 if note_count == 0 else 0,
        form=NoteFormTranscription,
    )

    def get_notetransformset_qs(bio):
        note_qs = NoteTranscription.objects.filter(owner=bio)
        if not request.user.is_staff:
            note_qs = note_qs.filter(
                Q(access_owner=request.user)
                | (
                    Q(access_groups__isnull=True)
                    | Q(access_groups__in=request.user.usergroup_set.all())
                )
            ).distinct()
        if not request.user.has_perm("fiches.can_publish_note"):
            note_qs = note_qs.filter(~Q(access_public=True)).distinct()
        return note_qs

    if request.method == "POST":
        trans_form = TranscriptionForm(request.POST, instance=trans)
        if not request.user.has_perm("fiches.change_transcription_ownership"):
            form_data = trans_form.data.copy()
            form_data.update({"author": "%s" % (trans.author.id)})
            form_data.update(
                {"author2": "%s" % (trans.author2.id) if trans.author2 else None}
            )
            trans_form.data = form_data

        note_formset = NoteFormset(
            request.POST, instance=trans, queryset=get_notetransformset_qs(trans)
        )
        if trans_form.is_valid():
            can_publish_transcription = request.user.has_perm(
                "fiches.publish_transcription"
            ) or getattr(request.user, "status_equipe", False)
            trans = trans_form.save(commit=False)
            trans.access_owner = trans.author
            default_publisher = get_default_publisher_user()

            # Publication metadata rules:
            # - when transcription is not public, keep publication metadata unchanged
            # - when it is public, ensure legacy rows have a default publisher
            # - preserve existing publication date across public/off/public toggles
            if not can_publish_transcription:
                trans.published_date = published_date_original
                trans.published_by = published_by_original
            elif not trans.access_public:
                trans.published_date = published_date_original
                trans.published_by = published_by_original
            else:
                # Transition to public: set initial publication date if absent.
                if not access_public_original and not trans.published_date:
                    trans.published_date = timezone.now()

                # Legacy fallback for missing publisher on already-published records.
                if trans.published_date and not trans.published_by:
                    if published_date_original and not published_by_original:
                        trans.published_by = default_publisher or request.user
                    elif not access_public_original:
                        trans.published_by = request.user
                    else:
                        trans.published_by = default_publisher or request.user

            # Track who performed the latest transcription update.
            trans.modified_date = timezone.now()
            trans.modified_by = request.user

            if not request.user.has_perm("fiches.publish_transcription"):
                trans.access_public = access_public_original
            trans.save()
            trans_form.save_m2m()
            trans_form.save_reviewers(trans)

            # Write to the activity log
            log_model_activity(trans, request.user)

            # Update global search index (haystack)
            update_object_index(trans)

            note_formset = NoteFormset(
                request.POST, instance=trans, queryset=get_notetransformset_qs(trans)
            )
            if note_formset.is_valid():
                note_formset.save()
                if request.POST.get("__continue", "") == "on":
                    url = reverse("transcription-edit", args=[trans.id])
                    # if ( request.REQUEST.get('__position') ):
                    if request.GET.get("__position"):
                        # url += "?__position=" + urlquote(request.REQUEST.get('__position'))
                        url += "?__position=" + urlquote(request.GET.get("__position"))
                    return HttpResponseRedirect(url)
                else:
                    return HttpResponseRedirect(
                        reverse("transcription-display", args=[trans.id])
                    )
            else:
                # noteFormset invalid
                dbg_logger.debug("noteFormset invalid")
        else:
            # transForm invalid
            dbg_logger.debug("transForm invalid: %s" % trans_form.errors)

    else:
        # Dealing with GET
        trans_form = TranscriptionForm(instance=trans)
        note_formset = NoteFormset(
            instance=trans, queryset=get_notetransformset_qs(trans)
        )

    if not trans_user_access:
        raise Http404()

    public_notes = None
    if trans is not None and not request.user.has_perm("fiches.can_publish_note"):
        public_notes = NoteTranscription.objects.filter(owner=trans).filter(
            access_public=True
        )

    context.update(
        {
            "transcription": trans,
            "last_activity": last_activity,
            "new_object": new_trans,
            "transForm": trans_form,
            "noteFormset": note_formset,
            "publicNotes": public_notes,
            #'savedPosition': request.REQUEST.get('__position', '')
            "savedPosition": request.GET.get("__position", ""),
        }
    )

    ext_template = "".join(
        ("fiches/edition/edit_base", request.COOKIES.get("layoutversion", "2"), ".html")
    )
    context.update({"ext_template": ext_template})

    return render(request, "fiches/edition/transcription.html", context)
