"""Exercise image upload and thumbnail consumers against the Pillow security update."""

import io
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from sorl.thumbnail import get_thumbnail


@pytest.mark.django_db
@pytest.mark.parametrize(
    "image_format,mode", [("PNG", "RGBA"), ("JPEG", "RGB"), ("GIF", "P"), ("WEBP", "RGBA"), ("TIFF", "RGB")]
)
def test_routed_upload_and_sorl_thumbnail(client, django_user_model, tmp_path, image_format, mode):
    editor = django_user_model.objects.create_user("image-editor", is_staff=True)
    client.force_login(editor)
    data = io.BytesIO()
    Image.new(mode, (160, 80)).save(data, format=image_format)
    name = "benign." + image_format.lower()
    with override_settings(MEDIA_ROOT=str(tmp_path)):
        response = client.post(
            "/ckeditor/upload/?CKEditorFuncNum=1", {"upload": SimpleUploadedFile(name, data.getvalue())}
        )
        assert response.status_code == 200
        assert "/media/uploads/" in response.content.decode()
        stored = next((tmp_path / "uploads").rglob(name))
        with Image.open(stored) as decoded:
            decoded.load()
            assert decoded.size == (160, 80)
        result = get_thumbnail(str(stored), "64x64", crop="center")
        with Image.open(result.storage.open(result.name)) as decoded:
            decoded.load()
            assert decoded.size == (64, 64)


@pytest.mark.django_db
@pytest.mark.parametrize("logged_in", [False, True])
def test_image_upload_remains_staff_only(client, django_user_model, tmp_path, logged_in):
    if logged_in:
        client.force_login(django_user_model.objects.create_user("reader", is_staff=False))
    with override_settings(MEDIA_ROOT=str(tmp_path)):
        response = client.post(
            "/ckeditor/upload/?CKEditorFuncNum=1", {"upload": SimpleUploadedFile("not-written.png", b"not an image")}
        )
        assert response.status_code in (302, 403)
        assert list(Path(tmp_path).rglob("*")) == []


@pytest.mark.django_db
@pytest.mark.parametrize("image_format,mode", [("PNG", "RGBA"), ("JPEG", "RGB")])
def test_optional_pillow_backend_thumbnail(client, django_user_model, tmp_path, image_format, mode):
    client.force_login(django_user_model.objects.create_user("optional-editor", is_staff=True))
    data = io.BytesIO()
    Image.new(mode, (160, 80)).save(data, format=image_format)
    with override_settings(
        MEDIA_ROOT=str(tmp_path), CKEDITOR_IMAGE_BACKEND="ckeditor_uploader.backends.PillowBackend"
    ):
        response = client.post(
            "/ckeditor/upload/?CKEditorFuncNum=1",
            {"upload": SimpleUploadedFile("optional." + image_format.lower(), data.getvalue())},
        )
        assert response.status_code == 200
        thumbnail = next(tmp_path.rglob("optional_thumb.*"))
        with Image.open(thumbnail) as decoded:
            decoded.load()
            assert decoded.format == "JPEG"
            assert decoded.size == (75, 38)
