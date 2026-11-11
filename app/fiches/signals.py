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

"""Search-index signals for place named entities.

A place's search document embeds data from satellite models — its name variants,
its public notes and its external reference links (identifier, référentiel +
identifier and full permalink). Those live in separate models, so Haystack's realtime signal
processor (which only reacts to ``PlaceRecord`` saves) never refreshes a place
when one of them changes. These receivers re-index the parent place whenever a
satellite row is created, updated or deleted, delegating to the active signal
processor. Test settings use an in-process search backend: BaseSignalProcessor
alone does not disable direct calls to handle_save.
"""

from django.apps import apps
from django.db.models.deletion import ProtectedError
from django.db.models.signals import post_delete, post_save, pre_delete, pre_save
from django.dispatch import receiver

from fiches.models import NotePlace, Person, PlaceRecord, PlaceReferenceSite, PlaceVariant
from fiches.person_references import person_reference_groups
from fiches.place_references import place_reference_groups


@receiver(pre_save, sender=NotePlace)
def remember_previous_note_place(sender, instance, using, raw=False, **kwargs):
    """Capture persisted ownership before a note is moved (including imports)."""
    instance._previous_indexed_place_id = None
    if not raw and instance.pk:
        instance._previous_indexed_place_id = sender.objects.using(using).filter(
            pk=instance.pk
        ).values_list("owner_id", flat=True).first()


@receiver(post_save, sender=NotePlace)
@receiver(post_delete, sender=NotePlace)
@receiver(post_save, sender=PlaceVariant)
@receiver(post_delete, sender=PlaceVariant)
@receiver(post_save, sender=PlaceReferenceSite)
@receiver(post_delete, sender=PlaceReferenceSite)
def reindex_place_for_satellite_change(sender, instance, **kwargs):
    """Re-index the parent place so satellite changes reach the search backend."""
    if kwargs.get("raw"):
        return
    place_id = instance.owner_id if isinstance(instance, NotePlace) else instance.place_id
    place_ids = {place_id}
    if isinstance(instance, NotePlace):
        place_ids.add(getattr(instance, "_previous_indexed_place_id", None))
    for place in PlaceRecord.objects.using(kwargs.get("using")).filter(pk__in=place_ids):
        apps.get_app_config("haystack").signal_processor.handle_save(PlaceRecord, place)


@receiver(pre_delete, sender=Person)
def protect_referenced_person_deletion(sender, instance, **kwargs):
    """Reject hard deletion when it would orphan or erase editorial links."""
    groups = person_reference_groups(instance)
    if not groups:
        return
    protected_objects = [obj for group in groups for obj in group["objects"]]
    labels = ", ".join(f'{group["label"]}: {group["count"]}' for group in groups)
    raise ProtectedError(
        f'La personne « {instance.name} » est encore référencée ({labels}).',
        protected_objects,
    )


@receiver(pre_delete, sender=PlaceRecord)
def protect_referenced_place_deletion(sender, instance, **kwargs):
    """Reject every deletion path that would orphan a persisted place tag."""
    groups = place_reference_groups(instance)
    if not groups:
        return
    protected_objects = [obj for group in groups for obj in group["objects"]]
    labels = ", ".join(f'{group["label"]}: {group["count"]}' for group in groups)
    raise ProtectedError(
        f'Le lieu « {instance.name} » est encore référencé ({labels}).',
        protected_objects,
    )
