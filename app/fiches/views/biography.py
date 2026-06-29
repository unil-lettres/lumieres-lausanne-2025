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

import re
from itertools import groupby

from django.contrib.auth.decorators import permission_required
from django.db.models import Q
from django.forms.models import inlineformset_factory
from django.http import (
    Http404,
    HttpResponse,
    HttpResponseForbidden,
    HttpResponseRedirect,
    HttpResponseServerError,
    JsonResponse,
)
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST
from utils import dbg_logger

from fiches.models import Biblio, Biography, BiographyReferenceSite, ContributionDoc, Person, Relation
from fiches.models.person.biography import (
    BiographyForm,
    NoteBiography,
    NoteFormBiography,
    Profession,
    ProfessionForm,
    RelationForm,
    SocietyMembership,
    SocietyMembershipForm,
)
from fiches.utils import (
    get_grouped_objet_activities,
    log_model_activity,
    update_object_index,
)

# ===============================================================================
# BIOGRAPHY
# ===============================================================================


def get_bio_form_def(bioForm):
    flst = {}
    for i, f in enumerate(bioForm.visible_fields()):
        flst[f.html_name] = i

    formdef = {
        "fieldsets": (
            {
                "title": None,
                "template": "fiches/edition/biography/birth_death.html",
                "fields": (
                    {"name": "birth_place"},
                    {"name": "birth_date"},
                    {"name": "death_place"},
                    {"name": "death_date"},
                ),
            },
            {
                "title": None,
                "fields": (
                    {"name": "religion"},
                    {
                        "name": "origin",
                        "tooltip_id": "ctxt-help-bio-origin",
                    },
                    {"name": "nationality"},
                    {
                        "name": "activity_places",
                        "tooltip_id": "ctxt-help-bio-activity-places",
                        "class": "single-line",
                        "sep": "<br/>",
                    },
                ),
            },
            {
                "title": None,
                "fields": (
                    {
                        "name": "public_functions",
                        "class": "single-line",
                        "sep": "<br/>",
                        "tooltip_id": "ctxt-help-bio-public-functions",
                    },
                    {"name": "comments_on_work", "class": "single-line", "sep": "<br/>"},
                    {
                        "name": None,
                        "template": "fiches/edition/biography/profession_formset.html",
                    },
                    {
                        "name": None,
                        "template": "fiches/edition/biography/society_formset.html",
                    },
                    {"name": "education", "class": "single-line unused", "sep": "<br/>"},
                    {"name": "abroad_stays", "class": "single-line unused", "sep": "<br/>"},
                ),
            },
            {
                "title": "Relations et contacts",
                "fields": (
                    {
                        "name": None,
                        "template": "fiches/edition/biography/relation_formset.html",
                    },
                ),
            },
            {"title": "Notes", "fields": ({"name": None, "template": "fiches/edition/note_formset.html"},)},
            {
                "title": None,
                "fields": ({"name": "reference_links", "class": "single-line"},),
            },
            {
                "title": None,
                "fields": (
                    {"name": "archive", "class": "single-line", "tooltip_id": "ctxt-help-bio-archive"},
                    {
                        "name": None,
                        "template": "fiches/display/person_bibliography.html",
                    },
                ),
            },
        )
    }
    for fs in formdef["fieldsets"]:
        for f in fs["fields"]:
            if f["name"]:
                try:
                    f["field"] = bioForm.visible_fields()[flst[f["name"]]]
                    fs[f["name"]] = bioForm.visible_fields()[flst[f["name"]]]
                except (KeyError, IndexError):
                    del f
    return formdef


def _sync_bio_reference_links(bio, pairs):
    """Replace the biography's reference-site links with the submitted (site, identifier) pairs.

    Editing a biography saves a new version (a fresh Biography row); the links are
    therefore (re)created on that new instance from the widget's cleaned payload.
    """
    bio.reference_links.all().delete()
    BiographyReferenceSite.objects.bulk_create(
        [
            BiographyReferenceSite(biography=bio, reference_site_id=site_id, identifier=identifier)
            for site_id, identifier in pairs
        ]
    )


DISPLAY_COLLECTOR = True


def person_without_bio(request):
    if not request.user.has_perm("fiches.add_biography"):
        return HttpResponse()
    persons = (
        Person.objects.filter(
            biography__id__isnull=True,
            may_have_biography=True,
            name__isnull=False,
        )
        .filter(Q(modern=False) | Q(modern__isnull=True))
        .exclude(name="")
        .order_by("name")
        .distinct()
    )
    return render(request, "fiches/workspace/person_for_bio.html", {"persons": persons})


@require_POST
@permission_required("fiches.add_person", raise_exception=True)
def ajax_add_person(request):
    name = (request.POST.get("name") or "").strip()
    if not name:
        return JsonResponse({"success": False, "error": "empty"}, status=400)

    defaults = {"modern": False}
    person = Person.objects.filter(name__iexact=name).first()
    created = False
    if person is None:
        person, created = Person.objects.get_or_create(name=name, defaults=defaults)
    else:
        # Normalise casing to the provided value if the stored name differs.
        if person.name != name:
            person.name = name
            person.save(update_fields=["name"])
        if person.modern is None:
            person.modern = False
            person.save(update_fields=["modern"])

    return JsonResponse(
        {
            "success": True,
            "id": person.id,
            "name": person.name,
            "created": created,
        }
    )


def build_person_biblio_dict(person):
    def cd_grouper_doctype(cd):
        return cd.document.document_type

    def cd_grouper_ctype(cd):
        return cd.contribution_type.name

    refs_prim = (
        Biblio.objects.exclude(document_type__id=5)
        .filter(litterature_type="p", contributiondoc__person=person)
        .select_related()
        .order_by("document_type__id", "date", "title")
    )
    cd = (
        ContributionDoc.objects.select_related()
        .exclude(document__document_type__id=5)
        .filter(person=person, document__litterature_type="p")
        .order_by("document__document_type", "contribution_type", "document__date", "document__title")
    )

    grouped_refs_prim = [
        {
            "grouper": g[0],
            "list": [
                {"grouper": gg[0], "list": [cd_item.document for cd_item in list(gg[1])]}
                for gg in groupby(g[1], cd_grouper_ctype)
            ],
        }
        for g in groupby(cd, cd_grouper_doctype)
    ]

    # Biblio - littérature secondaire
    litt_prim = (
        Biblio.objects.exclude(contributiondoc__person=person)
        .select_related()
        .filter(litterature_type="p", subj_person=person)
        .order_by("document_type__id", "date", "title")
    )
    litt_sec = (
        Biblio.objects.select_related()
        .filter(litterature_type="s", subj_person=person)
        .order_by("document_type__id", "date", "title")
    )

    # Manuscripts
    contrib_man = (
        ContributionDoc.objects.select_related()
        .filter(document__document_type__id=5)
        .filter(person=person, document__litterature_type="p")
        .order_by("contribution_type__id", "document__date", "document__title")
    )

    return {
        "contrib_man": contrib_man,
        "ref_list": refs_prim,
        "grouped_refs_prim": grouped_refs_prim,
        "litt_prim": litt_prim,
        "litt_sec": litt_sec,
    }


def display(request, person_id, version=0):

    person = get_object_or_404(Person, pk=person_id)

    # If the user has the permission to access biography versions, use the required version number
    if request.user.has_perm("fiches.access_unvalidated_biography"):
        bio = person.get_biography(version)
    # Otherwise use the validated version of the bio.
    else:
        bio = person.get_valid_biography()

    if bio is None:
        # The person exists (e.g. just created from the tagging window) but no
        # biography has been written yet. Serve a dedicated, consultable page
        # (HTTP 200, per the client's request) instead of a 404 so a tag link is
        # never a dead end; it offers to create the fiche to users allowed to.
        return render(
            request,
            "fiches/display/biography_not_created.html",
            {"person": person, "can_create_bio": request.user.has_perm("fiches.add_biography")},
        )

    referer = request.META.get("HTTP_REFERER")
    if referer:
        edit_url = reverse("biography-edit", args=[person_id])
        display_url = reverse("biography-display", args=[person_id])
        if edit_url not in referer and display_url not in referer:
            request.session["bio_from"] = request.META.get("HTTP_REFERER")

    # Version informations
    nb_version = person.biography_set.all().count()
    version_info = {
        "need_validation": (nb_version > 1) or not bio.valid,
        "has_versions": nb_version > 1,
        "nb_versions": nb_version,
        "last_version": bio.version == (nb_version - 1),
    }

    # Relations
    relations = person.get_relations() if version == 0 else bio.relation_set.all()

    reverse_relations = person.get_reverse_relations()

    # Biblio - publications
    ctx = build_person_biblio_dict(person)

    # Activities
    activities = get_grouped_objet_activities(person)

    ctx.update(
        {
            "person": person,
            "bio": bio,
            "version_info": version_info,
            "model": Biography,
            "relations": relations,
            "reverse_relations": reverse_relations,
            "activities": activities,
            "display_collector": DISPLAY_COLLECTOR,
        }
    )

    bio_template = "fiches/display/biography2.html"

    return render(request, bio_template, ctx)


def to_be_validated(request):
    if not request.user.has_perm("fiches.validate_biography"):
        return HttpResponseForbidden("Acc�s non autoris�")
    tobevalidated = Biography.objects.filter(valid=False, version=0).order_by("person__name")
    return render(request, "fiches/workspace/biography_avalider.html", {"tobevalidated": tobevalidated})


def create(request, person_id):
    if not request.user.has_perm("fiches.add_biography"):
        return HttpResponseForbidden("Acc�s non autoris�")
    return edit(request, person_id, create_bio=True)


@never_cache
def edit(request, person_id, version=0, create_bio=False):
    if not request.user.has_perm("fiches.change_biography"):
        return HttpResponseForbidden("Accès non autorisé")

    person = get_object_or_404(Person, pk=person_id)

    if create_bio:
        bio = Biography()
        bio.person = person
        bio.valid = False

    else:
        bio = person.get_biography(version=version)
        if bio is None:
            raise Http404()

    # ------------------------- Formsets ---------------------------------------#
    NoteFormset = inlineformset_factory(Biography, NoteBiography, extra=0, form=NoteFormBiography)

    def get_notebioformset_qs(bio):
        if not getattr(bio, "pk", None):
            return NoteBiography.objects.none()
        note_qs = NoteBiography.objects.filter(owner_id=bio.pk)

        if not request.user.is_staff:
            note_qs = note_qs.filter(
                Q(access_owner=request.user)
                | (Q(access_groups__isnull=True) | Q(access_groups__in=request.user.usergroup_set.all()))
            ).distinct()
        if not request.user.has_perm("fiches.can_publish_note"):
            note_qs = note_qs.filter(~Q(access_public=True)).distinct()
        return note_qs

    RelationFormset = inlineformset_factory(Biography, Relation, form=RelationForm, extra=1, fields="__all__")
    SocietyFormset = inlineformset_factory(
        Biography, SocietyMembership, form=SocietyMembershipForm, extra=1, fields="__all__"
    )
    ProfessionFormset = inlineformset_factory(Biography, Profession, form=ProfessionForm, extra=1, fields="__all__")

    exclude_from_duplication = ("NoteBiography", "SocietyMembership", "Profession", "Relation")

    if request.method == "POST":
        bioForm = BiographyForm(request.POST, request.FILES, instance=bio)
        note_qs = get_notebioformset_qs(bio)
        noteFormset = NoteFormset(request.POST, instance=bio, queryset=note_qs)
        relationFormset = RelationFormset(request.POST, instance=bio)
        societyFormset = SocietyFormset(request.POST, instance=bio)
        professionFormset = ProfessionFormset(request.POST, instance=bio)

        # store the old notes id
        prev_version_note_ids = []
        for note in note_qs:
            prev_version_note_ids.append(note.id)

        if (
            bioForm.is_valid()
            and relationFormset.is_valid()
            and professionFormset.is_valid()
            and societyFormset.is_valid()
        ):
            bio = bioForm.save(commit=False)
            id_prev_version = bio.id
            if create_bio:
                bio.save()
            else:
                bio.id = None
                bio.version = 0
                bio.save()
                person.renum_bio()

            _sync_bio_reference_links(bio, bioForm.cleaned_data.get("reference_links", []))

            posted_data = request.POST.copy()
            for excluded_modelname in exclude_from_duplication:
                formset_prefix = "%s_set" % excluded_modelname.lower()
                for i in range(0, int(posted_data["%s-INITIAL_FORMS" % formset_prefix])):
                    posted_data["%s-%s-id" % (formset_prefix, i)] = ""
                posted_data["%s-INITIAL_FORMS" % formset_prefix] = 0

            # Write to the activity log
            log_model_activity(bio.person, request.user)

            noteFormset = NoteFormset(posted_data, instance=bio, queryset=get_notebioformset_qs(bio))
            if noteFormset.is_valid():
                noteFormset.save()
            else:
                dbg_logger.debug("noteFormset invalid")

            # we must also duplicate the notes the user cannot access
            if not create_bio:
                for note in NoteBiography.objects.filter(owner=id_prev_version).exclude(id__in=prev_version_note_ids):
                    print("Found note the user has no access")
                    note.id = None
                    note.owner = bio
                    note.save()

            relationFormset = RelationFormset(posted_data, instance=bio)
            if relationFormset.is_valid():
                for form in relationFormset.forms:
                    if form.is_valid():
                        if form.cleaned_data.get("related_person", None):
                            r = form.save(commit=False)
                            if form.cleaned_data.get("DELETE", True):
                                if r.id:
                                    r.delete()
                                else:
                                    r = None
                            else:
                                r.related_person.save()
                                form.save()
                    else:
                        dbg_logger.debug("relationFormset.form not valid")

            else:
                dbg_logger.debug("relationFormset.errors -> %s " % relationFormset.errors)

            societyFormset = SocietyFormset(posted_data, instance=bio)
            if societyFormset.is_valid():
                societyFormset.save()

            else:
                dbg_logger.debug("societyFormset is not valid")

            professionFormset = ProfessionFormset(posted_data, instance=bio)
            if professionFormset.is_valid():
                professionFormset.save()

            # Update Haystack index
            update_object_index(person)

            if request.POST.get("__continue", "") == "on":
                return HttpResponseRedirect(reverse("biography-edit", args=[person_id]))
            else:
                return HttpResponseRedirect(reverse("biography-display", args=[person_id]))

        else:
            # bioForm is not valid
            dbg_logger.debug("bioForm.errors -> %s" % bioForm.errors)

    # request.method == 'GET'
    else:
        bioForm = BiographyForm(instance=bio)
        noteFormset = NoteFormset(instance=bio, queryset=get_notebioformset_qs(bio))
        relationFormset = RelationFormset(instance=bio)
        societyFormset = SocietyFormset(instance=bio)
        professionFormset = ProfessionFormset(instance=bio)

    bio_formdef = get_bio_form_def(bioForm)

    public_notes = None
    if getattr(bio, "pk", None) and not request.user.has_perm("fiches.can_publish_note"):
        public_notes = NoteBiography.objects.filter(owner_id=bio.pk, access_public=True)

    # Biblio - publications
    ctx = build_person_biblio_dict(person)

    ext_template = "fiches/edition/edit_base2.html"
    ctx.update(
        {
            "edition": True,
            "ext_template": ext_template,
            "person_id": person_id,
            "form": bioForm,
            "model": Biography,
            "new_object": create_bio,
            "bio_formdef": bio_formdef,
            "noteFormset": noteFormset,
            "publicNotes": public_notes,
            "relationFormset": relationFormset,
            "societyFormset": societyFormset,
            "professionFormset": professionFormset,
            "prev_url": request.META.get("HTTP_REFERER", None),
            "reverse_relations": person.get_reverse_relations(),
            "can_add_person": request.user.has_perm("fiches.add_person"),
        }
    )
    return render(request, "fiches/edition/biography.html", ctx)


def validate(request, person_id, version=0):
    """Validate the version of a biography."""
    if not request.user.has_perm("fiches.validate_biography"):
        return HttpResponseForbidden("Accès non autorisé")

    person = get_object_or_404(Person, pk=person_id)
    bio = person.get_biography(version=version)
    if bio is None:
        raise Http404()

    # Delete other versions
    person.biography_set.all().exclude(id=bio.id).delete()

    # Set flags of the new validated version
    bio.version = 0
    bio.valid = True
    bio.save()

    # Update Haystack index
    update_object_index(person)
    return HttpResponseRedirect(reverse("biography-display", args=[person.id]))


def delete(request, person_id, version=0):
    """Delete a biography version and call renum_bio on the person instance."""
    if not request.user.has_perm("fiches.delete_biography"):
        return HttpResponseForbidden("Accès non autorisé")

    person = get_object_or_404(Person, pk=person_id)
    bio = person.get_biography(version=version)
    if bio is None:
        raise Http404()

    try:
        version = int(version)
    except (ValueError, TypeError):
        version = 0

    nb_versions = person.biography_set.count()
    if nb_versions == 1 or bio.valid:
        return_url = request.session.get("bio_from") or reverse("search-person")
    else:
        if version > 0:
            version -= 1
        return_url = reverse("biography-display", args=[person.id, version])

    bio.delete()
    person.renum_bio()

    # Update Haystack index
    update_object_index(person)

    return HttpResponseRedirect(return_url)


def relations_list(request, person_id=None):
    try:
        person = get_object_or_404(Person, pk=person_id)

        re_digit_list = re.compile(r"^\d+$|^(\d+,)+\d+$")
        only_relations = request.GET.get("r", "")
        only_relations = only_relations.split(",") if re_digit_list.match(only_relations) else ""

        only_people = request.GET.get("p", "")
        only_people = only_people.split(",") if re_digit_list.match(only_people) else ""

        rel = person.get_relations(only_people=only_people, only_relations=only_relations)
        rrel = person.get_reverse_relations(only_people=only_people, only_relations=only_relations)
        relation_list = [
            {
                "id": r.related_person.id,
                "name": str(r.related_person),
                "type": r.relation_type,
                "rel": r.related_person.has_relations(exclude_people=[person_id]),
            }
            for r in rel
        ] + [
            {
                "id": r.bio.person.id,
                "name": str(r.bio.person),
                "type": r.relation_type.reverse_name,
                "rel": r.bio.person.has_relations(exclude_people=[person_id]),
            }
            for r in rrel
        ]

        return render(
            request,
            "fiches/list/biography_relations_list.html",
            {
                "person": person,
                "relation_list": relation_list,
            },
        )
    except Exception as e:
        return HttpResponseServerError(f"Error: {str(e)}")


RELATION_MAX_RECURSION_DEPTH = 5


def _get_all_relations(person, excluded_rels=None, depth=0, only_people=None, only_relations=None):
    if excluded_rels is None:
        excluded_rels = []
    if only_people is None:
        only_people = []
    if only_relations is None:
        only_relations = []
    rel = person.get_relations(only_people=only_people, only_relations=only_relations)
    rrel = person.get_reverse_relations(only_people=only_people, only_relations=only_relations)
    relation_list = [
        {
            "id": r.id,
            "dst_name": str(r.related_person),
            "src_name": person.name,
            "type": r.relation_type,
            "p": r.related_person,
        }
        for r in rel
        if r.id not in excluded_rels
    ] + [
        {
            "id": r.id,
            "dst_name": str(r.bio.person),
            "src_name": person.name,
            "type": r.relation_type.reverse_name,
            "p": r.bio.person,
        }
        for r in rrel
        if r.id not in rel and r.id not in excluded_rels
    ]

    excluded_rels += [r["id"] for r in relation_list]
    if depth < RELATION_MAX_RECURSION_DEPTH:
        depth += 1
        extended_list = []
        for r in relation_list:
            if r["p"].has_relations():
                tmp_list = _get_all_relations(
                    r["p"], excluded_rels=excluded_rels, only_people=only_people, only_relations=only_relations
                )
                excluded_rels += [r["id"] for r in tmp_list]
                extended_list += tmp_list
        relation_list += extended_list

    return relation_list


def relation_dot(request=None, person_id=None, max_depth=3):
    person = get_object_or_404(Person, pk=person_id)

    only_people = []
    only_relations = []

    relation_list = _get_all_relations(person, only_people=only_people, only_relations=only_relations)

    dot_relations = "\n".join(
        '    "%s" -> "%s" [ label = "%s (%s)" ];' % (r["src_name"], r["dst_name"], r["type"], r["id"])
        for r in relation_list
    )

    output = "digraph essais {\n" + dot_relations + "\n}\n"
    return output
