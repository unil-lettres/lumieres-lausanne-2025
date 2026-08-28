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

A place's search document embeds data from satellite models — its name variants
and its external reference links (identifier, référentiel + identifier and full
permalink). Those live in separate models, so Haystack's realtime signal
processor (which only reacts to ``PlaceRecord`` saves) never refreshes a place
when one of them changes. These receivers re-index the parent place whenever a
satellite row is created, updated or deleted, delegating to the active signal
processor (a no-op under the test backend, ``BaseSignalProcessor``).
"""

from django.apps import apps
from django.db.models.deletion import ProtectedError
from django.db.models.signals import post_delete, post_save, pre_delete
from django.dispatch import receiver

from fiches.models import Person, PlaceRecord, PlaceReferenceSite, PlaceVariant
from fiches.person_references import person_reference_groups
from fiches.place_references import place_reference_groups


@receiver(post_save, sender=PlaceVariant)
@receiver(post_delete, sender=PlaceVariant)
@receiver(post_save, sender=PlaceReferenceSite)
@receiver(post_delete, sender=PlaceReferenceSite)
def reindex_place_for_satellite_change(sender, instance, **kwargs):
    """Re-index the parent place so satellite changes reach the search backend."""
    try:
        place = PlaceRecord.objects.get(pk=instance.place_id)
    except PlaceRecord.DoesNotExist:
        return  # place removed (cascade delete) — its own signal drops the doc
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
