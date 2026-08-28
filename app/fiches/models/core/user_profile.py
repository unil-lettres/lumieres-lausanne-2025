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

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from fiches.models.core.shared import get_usergroups_for_user  # Import shared logic


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    field_of_research = models.TextField(_("Domaine de recherche / Historique"), blank=True)
    shib_uniqueID = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.user.username

    def get_usergroups(self):
        """
        Use the shared utility function to get all UserGroup this user is a member of.
        """
        return get_usergroups_for_user(self.user)

    def get_contrib_coll(self):
        """
        Get contributable collections for this user.
        """
        from fiches.models.misc.object_collection import ObjectCollection  # Lazy import

        return (
            ObjectCollection.objects.exclude(owner=self.user)
            .exclude(access_private=True)
            .filter(change_groups__in=self.get_usergroups())
            .distinct()
        )

    class Meta:
        verbose_name = "Informations supplémentaires"
        verbose_name_plural = "Informations supplémentaires"
        app_label = "fiches"


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Automatically creates or updates a UserProfile whenever a User is saved.
    """
    if created:
        UserProfile.objects.create(user=instance)
    else:
        instance.profile.save()
