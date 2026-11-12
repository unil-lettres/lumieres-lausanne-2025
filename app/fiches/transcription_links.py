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

from django.db.models import Q

from fiches.models import Transcription


class TranscriptionLinks(dict):
    """Request-local readable targets, including exact versions of a manuscript."""

    def __init__(self):
        super().__init__()
        self.readable_ids = {}


def readable_transcription_links(user, manuscript_ids):
    """Resolve all readable targets in one query, using the display-page rules."""
    links = TranscriptionLinks()
    targets = readable_transcriptions(user).filter(
        manuscript_b_id__in=manuscript_ids
    ).order_by("id").values_list("pk", "manuscript_b_id")
    for transcription_id, manuscript_id in targets:
        links.setdefault(manuscript_id, transcription_id)
        links.readable_ids[transcription_id] = manuscript_id
    return links


def readable_transcriptions(user):
    """SQL equivalent of display permission + ACModel.user_access (any_login=False)."""
    queryset = Transcription.objects.all()
    if user.has_perm("fiches.change_any_transcription") or user.has_perm("fiches.access_unpublished_transcription"):
        return queryset
    public = Q(access_private=False, access_public=True)
    if not user.is_authenticated:
        return queryset.filter(public)
    return queryset.filter(
        Q(access_owner=user) | public | (
            Q(access_private=False) & (
                Q(access_groups__users=user) | Q(access_groups__groups__user=user)
            )
        )
    ).distinct()
