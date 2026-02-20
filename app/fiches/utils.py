# -*- coding: utf-8 -*-
import sys
from django.apps import apps
from django.utils.encoding import smart_str
from itertools import groupby
from django.db import models
from django.utils.safestring import mark_safe

# Logging utility
import logging
dbg_logger = logging.getLogger(__name__)

def log_model_activity(obj, user):
    ActivityLog = apps.get_model('fiches', 'ActivityLog')
    model_name = obj.__class__.__name__
    object_id = obj.pk
    act = ActivityLog(model_name=model_name, object_id=object_id, user=user)
    act.save()

def get_last_model_activity(model_instance):
    ActivityLog = apps.get_model('fiches', 'ActivityLog')
    try:
        act = ActivityLog.objects.filter(
            model_name=model_instance.__class__.__name__,
            object_id=model_instance.pk
        ).latest('date')
    except ActivityLog.DoesNotExist:
        act = None
    return act

def get_grouped_objet_activities(obj):
    ActivityLog = apps.get_model('fiches', 'ActivityLog')
    activities = ActivityLog.objects.activities(object=obj).select_related().order_by('-date')
    grouped_activities = [
        tuple(g[1])[0] for g in groupby(activities, lambda x: f"{x.user.id}{x.date.date()}")
    ]
    return grouped_activities

# Remove haystack-related functions
def update_object_index(obj):
    """Stub for update_object_index if not using Haystack."""
    dbg_logger.debug("update_object_index is disabled")
    return False

def remove_object_index(obj):
    """Stub for remove_object_index if not using Haystack."""
    dbg_logger.debug("remove_object_index is disabled")
    return False

import unicodedata
def supprime_accent(ligne):
    """ Remove accents from the text """
    ligne = smart_str(ligne)
    return ''.join((c for c in unicodedata.normalize('NFD', ligne) if unicodedata.category(c) != 'Mn'))

def query_fiche(queries_dict, model_name, app_label='fiches', qs=None):
    def construct_search(field_name):
        if field_name.startswith('^'):
            return f"{field_name[1:]}__istartswith"
        elif field_name.startswith('=='):
            return f"{field_name[2:]}__exact"
        elif field_name.startswith('='):
            return f"{field_name[1:]}__iexact"
        elif field_name.startswith('@'):
            return f"{field_name[1:]}__icontains"
        elif field_name.startswith('$'):
            return f"{field_name[1:]}__iendswith"
        elif field_name.startswith('~'):
            return f"{field_name[1:]}__range"
        elif field_name.startswith('_null_'):
            return f"{field_name[6:]}__isnull"
        else:
            return f"{field_name}__icontains"

    q = models.Q()
    for qry in queries_dict:
        if qry['f'].startswith('~'):
            qry['v'] = qry['v'].split(",")
        if qry['f'].startswith('_null_'):
            qry['v'] = qry['v'] == 'true'
        q &= models.Q(**{construct_search(smart_str(qry['f'])): qry['v']})

    if qs is None:
        model = apps.get_model(app_label, model_name)
        qs = model._default_manager.all()

    return qs.filter(q)


def user_can_change_documentfile(user, docfile):
    """
    Return True when the user may edit the given DocumentFile.
    Ownership or the broad ``change_any_documentfile`` permission grant access.
    Otherwise the user needs the standard change permission and access to the file.
    """
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(docfile, "access_owner_id", None) == getattr(user, "id", None):
        return True
    if user.has_perm("fiches.change_any_documentfile"):
        return True
    if not docfile.user_access(user, any_login=True):
        return False
    return user.has_perm("fiches.change_documentfile")


def user_can_delete_documentfile(user, docfile):
    """
    Return True when the user may delete the given DocumentFile.
    Ownership or the broad ``delete_any_documentfile`` permission grant access.
    Otherwise the user needs the standard delete permission and access to the file.
    """
    if not getattr(user, "is_authenticated", False):
        return False
    if getattr(docfile, "access_owner_id", None) == getattr(user, "id", None):
        return True
    if user.has_perm("fiches.delete_any_documentfile"):
        return True
    if not docfile.user_access(user, any_login=True):
        return False
    return user.has_perm("fiches.delete_documentfile")


def get_default_publisher_user():
    """
    Return the preferred fallback user for legacy publication attribution.
    Current business rule: default to Béatrice (username: blovis) when present.
    """
    User = apps.get_model("auth", "User")

    preferred_usernames = ["blovis"]
    user = User.objects.filter(username__in=preferred_usernames).order_by("id").first()
    if user:
        return user

    return (
        User.objects.filter(first_name__icontains="bea")
        .order_by("id")
        .first()
    )
