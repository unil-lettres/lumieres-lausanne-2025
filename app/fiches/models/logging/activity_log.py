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

# models/activity_log.py

from django.db import models, connection, transaction
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from django.apps import apps


class ObjectActivities(models.Manager):
    """
    Add a Manager method to filter the activities related to a specific object.
    """

    def activities(self, **kwargs):
        qs = super().get_queryset()
        if "object" in kwargs:
            obj = kwargs["object"]
            try:
                qs = qs.filter(model_name=obj.__class__.__name__, object_id=obj.id)
            except:
                qs = qs.none()
        return qs


class ActivityLog(models.Model):
    object_id = models.IntegerField()
    model_name = models.CharField(verbose_name=_("Type d'objet"), max_length=256)
    user = models.ForeignKey(User, verbose_name=_("Utilisateur"), on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True)
    p_orphan = models.BooleanField(default=False, blank=True, editable=False)

    objects = ObjectActivities()

    @property
    def object_info(self):
        try:
            model = apps.get_model("fiches", self.model_name)
            obj = model.objects.get(pk=self.object_id)
            model_name = model._meta.verbose_name

            return {"model_name": model_name, "object_name": str(obj), "object": obj}
        except:
            return None

    def get_object(self):
        try:
            model = apps.get_model("fiches", self.model_name)
            return model.objects.get(pk=self.object_id)
        except:
            return None

    @staticmethod
    def sanitize():
        """
        Find any orphan entries (related to non-existing/deleted objects)
        and set p_orphan = True where objects no longer exist.
        """
        cursor = connection.cursor()
        model_names = [m["model_name"] for m in ActivityLog.objects.values("model_name").distinct()]

        for model_name in model_names:
            model = apps.get_model("fiches", model_name)
            object_table = model._meta.db_table
            activity_table = ActivityLog._meta.db_table
            query = f"""
                UPDATE `{activity_table}`
                LEFT JOIN `{object_table}` ON (`{object_table}`.`id` = `{activity_table}`.`object_id`)
                SET `{activity_table}`.`p_orphan` = 1
                WHERE `{activity_table}`.`model_name` = '{model_name}'
                AND `{object_table}`.`id` IS NULL;
            """
            cursor.execute(query)
            # Using commit() since commit_unless_managed() is removed in newer Djangos
            transaction.commit()

    def __str__(self):
        name = self.user.get_full_name() or self.user.username
        return f"{name} - {self.date.isoformat()}"

    class Meta:
        verbose_name = _("Activité")
