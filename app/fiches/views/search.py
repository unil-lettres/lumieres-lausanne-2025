# -*- coding: utf-8 -*-
#
#  (c) Université de Lausanne — Lumières.Lausanne
#

# stdlib
import copy
import datetime
import calendar
import json
import shlex
from base64 import b64decode

# Django
from django.conf import settings
from django.apps import apps
from django.db import models
from django.db.models import Q
from django.http import (
    HttpResponse, Http404, HttpResponseRedirect, HttpResponseNotFound, JsonResponse
)
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.core.paginator import Paginator, InvalidPage
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import permission_required

# Project utils
from utils import dbg_logger

# Domain models
from fiches.models.documents.document import Biblio, Transcription, DocumentType
from fiches.models import UserGroup, ActivityLog, Person, Project, Society, RelationType

# Forms / search models
from fiches.models.search.search import (
    QuickSearchForm,
    BiblioExtendedSearchForm,
    JournaltitleView,   # used by filter_builder()
    SearchFilters,      # used by save_filters()
)

# Haystack (Solr) for quick search
from haystack.query import SearchQuerySet
from haystack.inputs import AutoQuery

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _accessible_transcription_ids(user):
    """
    Return a list of transcription IDs the user may access.
    Mirrors the permission logic used in the advanced search view.
    """
    qs = Transcription.objects.all()

    if not user.is_authenticated:
        qs = qs.filter(access_public=True)
    elif user.has_perm("fiches.access_unpublished_transcription"):
        # full access
        pass
    else:
        qs = qs.filter(
            models.Q(access_public=True)
            | models.Q(author=user)
            | models.Q(author2=user)
            | models.Q(access_groups__users=user)
            | models.Q(access_groups__groups__user=user)
            | models.Q(project__members=user)
            | (
                models.Q(access_public=False)
                & models.Q(access_private=False)
                & models.Q(access_groups__isnull=True)
            )
        ).distinct()

    return list(qs.values_list("id", flat=True))


# ---------------------------------------------------------------------
# Entry points / simple pages
# ---------------------------------------------------------------------
def search_index(request):
    """
    Redirect to the last used search type. Default = general.
    """
    last_type = request.session.get("search_last_type", "__general__")
    if last_type not in ("Person", "Biblio", "__general__"):
        last_type = "__general__"
    if last_type == "__general__":
        return search_general(request)
    else:
        return filter_builder(request, model_name=last_type)


def search_general(request):
    return render(request, "fiches/search/search_general.html")


# ---------------------------------------------------------------------
# 🔍 Quick search (header magnifying glass) — uses Solr/Haystack
# ---------------------------------------------------------------------
def quick_search(request):
    """
    General (header) search rendered in the site's UI (search_general.html).
    Supports type checkboxes via ?t=biblio&t=transcription&t=person.
    Shows per-type counts using a Solr facet on django_ct.
    """
    form = QuickSearchForm(request.GET or None)
    q = (request.GET.get("q") or "").strip()

    # Selected types (empty => all)
    selected_types = set(request.GET.getlist("t"))  # e.g. {'biblio','person'}

    model_map = {
        "biblio": Biblio,
        "transcription": Transcription,
        "person": Person,
    }
    ct_map = {
        "biblio": "fiches.biblio",
        "transcription": "fiches.transcription",
        "person": "fiches.person",
    }

    # Base SQS (query)
    sqs = SearchQuerySet().all()
    def _apply_term_filters(sqs_obj, query_string):
        if not query_string:
            return sqs_obj
        try:
            terms = shlex.split(query_string)
            if not terms:
                terms = [query_string]
        except ValueError:
            terms = [query_string]
        for term in terms:
            cleaned = term.strip()
            if cleaned:
                sqs_obj = sqs_obj.filter(content=AutoQuery(cleaned))
        return sqs_obj

    if q:
        sqs = _apply_term_filters(sqs, q)

    # Filter by selected models (if any)
    if selected_types:
        models_to_apply = [model_map[k] for k in selected_types if k in model_map]
        if models_to_apply:
            sqs = sqs.models(*models_to_apply)

    # Apply deterministic ordering once filters are set
    sort_fields = ["modelSort", "sort1", "sort2", "django_id"]
    sqs = sqs.order_by(*sort_fields)

    # --- Fast counts via facet on django_ct (for the current query q) ---
    facet_sqs = SearchQuerySet().all()
    if q:
        facet_sqs = _apply_term_filters(facet_sqs, q)
    facet_sqs = facet_sqs.facet("django_ct")
    facet_counts = facet_sqs.facet_counts() or {}
    raw = dict(facet_counts.get("fields", {}).get("django_ct", {}))

    # Normalize facet list/tuples to dict
    # Solr returns list of (value, count) tuples with Haystack.
    if isinstance(raw, list):
        ct_counts = {k: v for k, v in raw}
    else:
        ct_counts = raw  # already a dict

    counts = {
        "biblio": int(ct_counts.get(ct_map["biblio"], 0)),
        "transcription": int(ct_counts.get(ct_map["transcription"], 0)),
        "person": int(ct_counts.get(ct_map["person"], 0)),
    }

    # Pagination
    per_page = getattr(settings, "HAYSTACK_SEARCH_RESULTS_PER_PAGE", 30)
    paginator = Paginator(sqs, per_page)
    page_num = request.GET.get("page") or 1
    try:
        page = paginator.page(page_num)
    except InvalidPage:
        page = paginator.page(1)

    # Remove stale search hits (indexed objects deleted from DB).
    raw_results = list(page.object_list)
    filtered_results = []
    missing_result_ids = []
    for result in raw_results:
        obj = getattr(result, "object", None)
        if obj is None:
            missing_result_ids.append(result.pk)
        else:
            filtered_results.append(result)
    if missing_result_ids:
        page.object_list = filtered_results
        dbg_logger.warning(
            "quick_search dropped %s stale search result(s) with primary keys: %s",
            len(missing_result_ids),
            ", ".join(str(pk) for pk in missing_result_ids),
        )

    # Build querystring without the page param for the paginator tag
    params = request.GET.copy()
    if "page" in params:
        del params["page"]
    qs = params.urlencode()  # preserves multiple ?t=… entries

    return render(
        request,
        "fiches/search/search_general.html",
        {
            "form": form,
            "query": q,

            # pagination context expected by your {% paginate %} tag
            "page": page,
            "page_obj": page,          # so you don't need the {% with %} wrapper
            "paginator": paginator,
            "qs": qs,

            # type filters
            "counts": counts,
            "selected_types": selected_types,

            # keeps collector button logic working if you use it on this page
            "display_collector": True,
        },
    )


# ---------------------------------------------------------------------
# 🔍➕ Advanced bibliographic search (kept as DB filters for now)
# ---------------------------------------------------------------------
def biblio_extended_search(request):
    user = request.user
    context = {"display_collector": True}

    # Build project queryset once, permission-aware
    project_qs = Project.objects.filter(publish=True)
    if user.is_authenticated:
        if user.has_perm("fiches.view_unpublished_project"):
            project_qs = Project.objects.all()
        else:
            project_qs = Project.objects.filter(
                models.Q(publish=True) | models.Q(members=user)
            ).distinct()

    doSearch = len(request.GET) > 0
    if doSearch:
        # Merge GET with form initial values (legacy behavior)
        get_dict = request.GET.copy()
        for fld_name, fld in BiblioExtendedSearchForm.base_fields.items():
            if getattr(fld, "initial", None):
                get_dict.setdefault(fld_name, fld.initial)
        form = BiblioExtendedSearchForm(get_dict)
    else:
        form = BiblioExtendedSearchForm()

    # ✅ override proj queryset AFTER instantiation
    form.fields["proj"].queryset = project_qs.order_by("name")
    context.update({"form": form})

    search_action = request.GET.get("search_action")

    if doSearch and form.is_valid():
        cd = form.cleaned_data
        q = models.Q()

        def q_op(q_acc, q1, op):
            if op == "or":
                return q_acc | q1
            elif op == "and":
                return q_acc & q1
            else:
                return q_acc & ~q1  # 'not'

        # Free-text expressions
        fld_map = {
            "title": ("title", "short_title"),
            "authors": "contributiondoc__person__name",
            "person": "subj_person__name",
            "place": "place",
            "edit": "publisher",
        }
        for xidx in range(4):
            val = cd.get(f"x{xidx}_val")
            op = cd.get(f"x{xidx}_op", "and")
            fld = fld_map.get(cd.get(f"x{xidx}_fld"))
            if not fld or not val:
                continue
            if not isinstance(fld, tuple):
                fld = (fld,)
            q1 = models.Q(**{f"{fld[0]}__icontains": val})
            for f in fld[1:]:
                q1 |= models.Q(**{f"{f}__icontains": val})
            q = q_op(q, q1=q1, op=op)

        # Document types + "transcription only"
        doctype = cd.get("dt")
        DOCTYPE_MANUSCRIPT_ID = 5  # TODO: move to settings if needed
        onlyTrans = request.GET.get("dtT")
        if onlyTrans == "1":
            context.update({"onlyTrans": onlyTrans})
            if not doctype:
                doctype = DocumentType.objects.filter(pk=DOCTYPE_MANUSCRIPT_ID)

        if doctype:
            if onlyTrans != "1":
                q &= models.Q(document_type__in=doctype)
            else:
                doctype = doctype.exclude(id=DOCTYPE_MANUSCRIPT_ID)
                q_trans = models.Q(transcription__isnull=False)
                if not user.is_authenticated:
                    q_trans &= models.Q(transcription__access_public=True)
                elif not user.has_perm("fiches.access_unpublished_transcription"):
                    q_trans &= (
                        models.Q(transcription__access_public=True)
                        | (
                            models.Q(transcription__author=user)
                            | models.Q(transcription__author2=user)
                            | models.Q(transcription__access_groups__users=user)
                            | models.Q(transcription__access_groups__groups__user=user)
                            | models.Q(transcription__project__members=user)
                            | (
                                models.Q(transcription__access_public=False)
                                & models.Q(transcription__access_private=False)
                                & models.Q(transcription__access_groups__isnull=True)
                            )
                        )
                    )
                q &= (
                    models.Q(document_type__in=doctype)
                    | (models.Q(document_type__id=DOCTYPE_MANUSCRIPT_ID) & q_trans)
                )

        # For template logic
        user_accessible_trans = _accessible_transcription_ids(user) if onlyTrans != "1" else True
        context.update({"user_accessible_trans": user_accessible_trans or [-1]})


        # Publication date (aaaa.mm)
        if cd.get("date_from") or cd.get("date_to"):
            date_from_y, date_from_m = (str(cd.get("date_from", "")).split(".") + [""])[:2]
            try:
                date_from_y = int(date_from_y)
            except ValueError:
                date_from_y = None
            try:
                date_from_m = int(date_from_m)
                if not 0 < date_from_m < 13:
                    date_from_m = None
            except ValueError:
                date_from_m = None
            date_from = datetime.date(date_from_y or 1, date_from_m or 1, 1)

            date_to_y, date_to_m = (str(cd.get("date_to", "")).split(".") + [""])[:2]
            try:
                date_to_y = int(date_to_y) or 9999
            except ValueError:
                date_to_y = 9999
            try:
                date_to_m = int(date_to_m) or 12
                if not 0 < date_to_m < 13:
                    date_to_m = 12
            except ValueError:
                date_to_m = 12
            date_to = datetime.date(
                date_to_y, date_to_m, calendar.monthrange(date_to_y, date_to_m)[1]
            )
            q &= models.Q(date__range=(date_from, date_to))

        # Modification date (activity log)
        if cd.get("mdate_from") or cd.get("mdate_to"):
            mdate_from = cd.get("mdate_from") or datetime.date(1, 1, 1)
            mdate_to = cd.get("mdate_to") or datetime.date(9999, 1, 1)
            biblio_ids_from_log = ActivityLog.objects.filter(
                model_name="Biblio", date__range=(mdate_from, mdate_to)
            ).values_list("object_id", flat=True)
            trans_ids_from_log = ActivityLog.objects.filter(
                model_name="Transcription", date__range=(mdate_from, mdate_to)
            ).values_list("object_id", flat=True)
            q &= (
                models.Q(pk__in=list(biblio_ids_from_log))
                | models.Q(transcription__pk__in=list(trans_ids_from_log))
            )

        # Language (primary or secondary)
        if cd.get("l"):
            q &= (models.Q(language=cd.get("l")) | models.Q(language_sec=cd.get("l")))

        # Depot
        if cd.get("depot"):
            q &= models.Q(depot=cd.get("depot"))

        # Literature type
        if cd.get("ltype"):
            q &= models.Q(litterature_type__in=cd.get("ltype"))

        # Projects
        proj = cd.get("proj")
        if proj:
            q = q_op(q, q1=models.Q(project__in=proj), op=cd.get("proj_op", "and"))
            if cd.get("proj_op", "and") == "and":
                q &= models.Q(project__isnull=False)

        # Journal
        if cd.get("journal"):
            q &= models.Q(journal_title=cd.get("journal"))

        # Society
        if cd.get("society"):
            q &= models.Q(subj_society=cd.get("society"))

        # Manuscript type
        if cd.get("mtype"):
            q &= models.Q(manuscript_type=cd.get("mtype"))

        # ---- Apply base filters
        dbg_logger.debug(q)
        results = Biblio.objects.filter(q).order_by("document_type") if q.children else Biblio.objects.all()

        # ---- Keyword filters (chain after base qs)
        kw_filter_applied = False
        for xidx in range(4):
            op, pkw, skw = (
                cd.get(f"kw{xidx}_op", "and"),
                cd.get(f"kw{xidx}_p"),
                cd.get(f"kw{xidx}_s"),
            )
            if skw:
                kw_filter_applied = True
                if op == "and":
                    results = results.filter(subj_secondary_kw=skw)
                elif op == "or":
                    results = results | results.filter(subj_secondary_kw=skw)
                elif op == "not":
                    results = results.exclude(subj_secondary_kw=skw)
            elif pkw:
                kw_filter_applied = True
                if op == "and":
                    results = results.filter(subj_primary_kw=pkw)
                elif op == "or":
                    results = results | results.filter(subj_primary_kw=pkw)
                elif op == "not":
                    results = results.exclude(subj_primary_kw=pkw)

        if not q.children and not kw_filter_applied:
            results = Biblio.objects.none()

        # ---- Grouping & sorting
        sort_map = {"a": "first_author_name", "d": "date", "-d": "-date", "t": "title"}
        grp = cd.get("grp", "d")
        if grp == "d":
            sort_fields = ["document_type", "first_author_name"]
            context.update({"grpby_1": "doctype", "grpby_2": "author"})
        elif grp == "a":
            sort_fields = ["first_author_name", "document_type"]
            context.update({"grpby_1": "author", "grpby_2": "doctype"})
        else:
            sort_fields = []
        sort_fields.append(sort_map.get(cd.get("sort"), "date"))
        sort_fields.append("pages")
        results = results.distinct().order_by(*sort_fields)

        # ---- Pagination or actions
        if search_action is None:
            paginator = Paginator(results, int(cd.get("nbi") or 25))
            try:
                page = paginator.page(request.GET.get("page", 1))
            except InvalidPage:
                raise Http404
            context.update(
                {
                    "page": page,
                    "paginator": paginator,
                    "qs": request.META.get("QUERY_STRING", "").replace(f"&page={page.number}", ""),
                }
            )
        else:
            qs = request.META.get("QUERY_STRING", "").replace(
                f"&page={int(request.GET.get('page', 1))}", ""
            )
            context.update(
                {
                    "results": results,
                    "usergroups": UserGroup.objects.all().order_by("name"),
                    "qs": qs,
                    "qswoaction": qs.replace(f"search_action={search_action}&", ""),
                }
            )

    return render(
        request,
        "fiches/search/biblio_extended.html"
        if search_action != "trans_access"
        else "fiches/search/actions/trans_access.html",
        context,
    )

# ---------------------------------------------------------------------
# Legacy filter builder / generic search endpoints (left as-is)
# ---------------------------------------------------------------------
RESULT_DISPLAY_COLUMNS = {
    "Person": {
        "name": "on",
        "relation": "on",
        "prof": "auto",
        "birth": "auto",
        "death": "auto",
        "society": "auto",
        "religion": "auto",
        "journal_articles": "auto",
    }
}


def filter_builder(request, model_name="Person", sfid=None):
    request.session["search_last_type"] = model_name
    context = {
        "fiche_type": "search",
        "model_name": model_name,
        "journals": JournaltitleView.objects.all(),
    }
    if model_name.lower() == "person":
        context.update({"societies": Society.objects.all()})
    elif model_name.lower() == "biblio":
        context.update({"doctypes": DocumentType.objects.all()})

    if request.session.get("display_settings") is None:
        request.session["display_settings"] = copy.deepcopy(RESULT_DISPLAY_COLUMNS)
    defaults = RESULT_DISPLAY_COLUMNS.get(model_name, {}) or {}
    display_columns = defaults.copy()
    display_columns.update(request.session["display_settings"].get(model_name, {}))

    context.update({"display_settings": display_columns, "display_collector": True})

    ext_template = "".join(("fiches/search/search_base", request.COOKIES.get("layoutversion", "2"), ".html"))
    context.update({"ext_template": ext_template})

    return render(request, "fiches/search/filters_%s.html" % model_name.lower(), context)


def do_search(request):
    def get_Q(params):
        q = models.Q()
        for p in params:
            if p["type"] == "date" and p["op"] in ("lt", "gt"):
                try:
                    if p["op"] == "lt":
                        p["val"] = datetime.date(int(p["val"]), 12, 31)
                    else:
                        p["val"] = datetime.date(int(p["val"]), 1, 1)
                except ValueError:
                    continue

            if p["type"] == "number":
                try:
                    p["val"] = int(p["val"])
                except ValueError:
                    continue

            if isinstance(p["val"], str):
                p["val"] = p["val"]

            if p["op"] == "isnull":
                p["val"] = bool(p["val"])

            if not p["attr"].startswith("subject"):
                q &= models.Q(**{f"{p['attr']}__{p['op']}": p["val"]})
            else:
                field_list = ("title", "subj_primary_kw__word", "subj_secondary_kw__word", "subj_person__name")
                if p["attr"] == "subjecta":
                    try:
                        raw_val = p["val"]
                        p["val"] = b64decode(raw_val.split("|")[0])
                        field_list = raw_val.split("|")[1].split(",")
                    except Exception:
                        p["val"] = ""
                        field_list = []
                for f in field_list:
                    q |= models.Q(**{f"{f}__icontains": p["val"]})
        return q

    qparam = request.GET.get("q", "")
    try:
        qparam = b64decode(qparam)
    except Exception:
        pass
    query_def = json.loads(qparam)

    order_by = request.GET.get("o") or "title"
    if order_by == "author":
        order_by = "first_author_name"

    model_name = query_def.get("model_name")
    if model_name is None:
        raise Http404

    if request.session.get("display_settings") is None:
        request.session["display_settings"] = copy.deepcopy(RESULT_DISPLAY_COLUMNS)
    defaults = RESULT_DISPLAY_COLUMNS.get(model_name) or {}
    display_columns = defaults.copy()
    session_columns = request.session["display_settings"].get(model_name, {})
    if session_columns:
        display_columns.update(session_columns)

    model = apps.get_model("fiches", query_def["model_name"])
    result_qs = None
    journal_filter_value = ""

    for f_def in query_def["filters"]:
        dbg_logger.debug(f_def)
        f_q = get_Q(f_def["params"])
        dbg_logger.debug(f_q)
        if result_qs is None:
            result_qs = model.objects.filter(f_q)
        else:
            if f_def["op"] == "and":
                result_qs = model.objects.filter(f_q) & result_qs
            else:
                result_qs = model.objects.filter(f_q) | result_qs

        if display_columns.get(f_def["cl"]) != "off":
            display_columns[f_def["cl"]] = "on"

        if f_def.get("cl") == "journal_articles":
            for param in f_def.get("params", []):
                journal_filter_value = param.get("val", "")
                break

    try:
        result_list = result_qs.order_by(order_by).distinct()
    except Exception:
        result_list = []

    nb_val = result_list.count()

    for key, value in list(display_columns.items()):
        display_columns[key] = bool(value == "on" or value is True)

    return render(
        request,
        "fiches/search/results_%s.html" % model_name.lower(),
        {
            "object_list": result_list,
            "nb_val": nb_val,
            "display": display_columns,
            "display_collector": True,
            "journal_filter_value": journal_filter_value,
        },
    )


def save_settings(request):
    new_display_settings = json.loads(request.POST.get("display_settings", "{}"))

    if request.session.get("display_settings") is None:
        request.session["display_settings"] = copy.deepcopy(RESULT_DISPLAY_COLUMNS)

    session_settings = request.session["display_settings"]
    for model_name, model_settings in new_display_settings.items():
        # Start from the defaults, overlay any existing session values, then the
        # freshly submitted data, so partial payloads do not wipe known keys.
        merged = copy.deepcopy(RESULT_DISPLAY_COLUMNS.get(model_name, {}))
        merged.update(session_settings.get(model_name, {}))
        merged.update(model_settings)

        if model_name == "Person" and "birth" in model_settings and "death" not in model_settings:
            merged["death"] = model_settings["birth"]

        session_settings[model_name] = merged

    request.session["display_settings"] = session_settings
    request.session.modified = True

    return JsonResponse({"display_settings": session_settings})


def save_filters(request):
    q = request.GET.get("q", "")
    query_def = json.loads(q)
    sf_id = request.GET.get("sfid")
    sf = SearchFilters.objects.get_or_create(pk=sf_id)
    # TODO: persist query_def to the model (left as legacy placeholder)


def relations(request):
    try:
        person_id = int(request.GET.get("p", ""))
    except Exception:
        return HttpResponseNotFound()
    person = get_object_or_404(Person, pk=person_id)
    relation_type = RelationType.objects.all()

    return render(
        request,
        "fiches/search/relations.html",
        {"person": person, "JQUI": True, "relation_type": relation_type},
    )


@require_POST
@permission_required(perm="fiches.change_any_transcription")
def transcriptions_change_access(request):
    public = "access_public" in request.POST
    private = "access_private" in request.POST
    groups = UserGroup.objects.filter(id__in=request.POST.getlist("access_groups"))
    for biblio in Biblio.objects.filter(id__in=request.POST.getlist("transcriptions")):
        for transcription in biblio.transcription_set.all():
            transcription.access_public = public
            transcription.access_private = private
            transcription.access_groups.clear()
            transcription.access_groups.add(*groups)
            transcription.save()
    return HttpResponseRedirect(reverse("search-biblio") + "?" + request.POST.get("searchparams", ""))


def list_persons(request):
    first_letter = request.GET.get("q")
    filter_params = {"may_have_biography": True, "biography__isnull": False}
    if first_letter:
        filter_params["name__istartswith"] = first_letter
    persons = Person.objects.filter(**filter_params).order_by("name").distinct()
    return render(request, "fiches/search/list_persons.html", {"persons": persons, "first_letter": first_letter})

def req_search_view(request):
    """Compat alias kept for legacy imports."""
    # You can also return quick_search(request) if you prefer:
    # return quick_search(request)
    return search_general(request)
