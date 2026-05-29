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

from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from fiches.views.transcription import (
    get_patrinum_tile_sources,
    patrinum_image_url_to_info_json,
)


class PatrinumFacsimileSourcesTest(SimpleTestCase):
    def tearDown(self):
        get_patrinum_tile_sources.cache_clear()

    def test_patrinum_image_url_maps_to_iiif_info_json(self):
        info_url = patrinum_image_url_to_info_json(
            "https://patrinum.ch/record/255692/files/BCUL-PREVIEW-296578_0001.jpg",
            "255692",
        )

        self.assertEqual(
            info_url,
            "https://patrinum.ch/nanna/api/multimedia/image/v2/recid:255692-BCUL-PREVIEW-296578_0001.jpg/info.json",
        )

    @patch("fiches.views.transcription.requests.get")
    def test_patrinum_manifest_fallback_reads_record_page_images(self, get_mock):
        response = Mock()
        response.text = """
            <meta property="og:image"
                  content="https://patrinum.ch/record/255692/files/BCUL-PREVIEW-296578_0001.jpg" />
            <meta property="og:image"
                  content="https://patrinum.ch/record/255692/files/BCUL-PREVIEW-296578_0002.jpg" />
            <meta property="og:image"
                  content="https://patrinum.ch/record/255692/files/BCUL-PREVIEW-296578_0001.jpg" />
        """
        response.raise_for_status.return_value = None
        get_mock.return_value = response

        tile_sources = get_patrinum_tile_sources("https://patrinum.ch/record/255692/export/iiif_manifest")

        self.assertEqual(
            tile_sources,
            [
                "https://patrinum.ch/nanna/api/multimedia/image/v2/"
                "recid:255692-BCUL-PREVIEW-296578_0001.jpg/info.json",
                "https://patrinum.ch/nanna/api/multimedia/image/v2/"
                "recid:255692-BCUL-PREVIEW-296578_0002.jpg/info.json",
            ],
        )
