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

"""Custom footnote assets must invalidate a previously cached plugin URL."""

from hashlib import sha256
from pathlib import Path
import re

from ckeditor import widgets
from django.test import SimpleTestCase


class FootnoteAssetTests(SimpleTestCase):
    def test_editor_registers_content_version_before_loading_plugin(self):
        plugin = Path(widgets.__file__).parent / "static/ckeditor/ckeditor/plugins/footnote/plugin.js"
        version = sha256(plugin.read_bytes()).hexdigest()[:16]
        for config in ["transcription_ckeditor", "project_ckeditor", "envelope_ckeditor"]:
            body = widgets.CKEditorWidget(config_name=config).render("text", "<p>Témoin</p>", {"id": "test_editor"})
            self.assertIn(f'"plugin.js?v={version}"', body)
            self.assertLess(body.index("CKEDITOR.plugins.addExternal"), body.index("CKEDITOR.replace"))
            self.assertIn('&lt;p&gt;Témoin&lt;/p&gt;', body)
            self.assertNotIn("CKEDITOR.timestamp =", body)

    def test_non_footnote_editor_does_not_register_the_plugin(self):
        body = widgets.CKEditorWidget(config_name="note_ckeditor").render("text", "", {"id": "test_editor"})
        self.assertNotIn("addExternal", body)
        self.assertIn("CKEDITOR.replace", body)

    def test_repeated_widgets_use_the_same_stable_version(self):
        widget = widgets.CKEditorWidget(config_name="transcription_ckeditor")
        a = widget.render("a", "", {"id": "a"})
        b = widget.render("b", "", {"id": "b"})
        self.assertEqual(re.findall(r"plugin.js\?v=[a-f0-9]+", a), re.findall(r"plugin.js\?v=[a-f0-9]+", b))
