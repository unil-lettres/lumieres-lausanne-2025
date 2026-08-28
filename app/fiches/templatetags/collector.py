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

from django import template
from django.contrib.auth.models import AnonymousUser, User

register = template.Library()


@register.filter
def editable_projects(user):
    """
    Return the list of the projects the user can edit
    """
    if not isinstance(user, (User, AnonymousUser)):
        raise template.TemplateSyntaxError("argument should be a User")

    if isinstance(user, AnonymousUser) or not hasattr(user, "profile"):
        return set()

    projs = set()
    for g in user.profile.get_usergroups():
        projs |= set(g.group_projects.all())

    return set(user.member_projects.all()) | set(user.project_set.all()) | projs
