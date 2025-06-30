# fiches/admin.py

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.urls import reverse as reverse_url, path
from django.forms import ModelForm, TextInput, CharField
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib import messages
import os

from django.contrib.contenttypes.admin import GenericStackedInline

from fiches.models.content.free_content import FreeContent
from fiches.models.content.news import News
from fiches.models.content.image import Image
from fiches.models.misc.project import Project
from fiches.models.content.publication import Publication
from fiches.models.content.finding import Finding

from fiches.models import (
    ContributionType,
    UserProfile,
    Person,
    PrimaryKeyword,
    SecondaryKeyword,
    Society,
    Biography,
    Biblio,
    Manuscript,
    Transcription,
    DocumentType,
    DocumentLanguage,
    DocumentFile,
    ObjectCollection,
    PlaceView,
    JournaltitleView,
    UserGroup,
    Nationality,
    RelationType,
    Religion,
    ManuscriptType,
    ActivityLog,
    Document,
    Relation,
    Depot,
)
from fiches.forms import ObjectCollectionForm, BiblioForm

from ckeditor.widgets import CKEditorWidget  # Ensure CKEditor is up-to-date

# -----------------------------------------------------------------------------
# Custom Admin Site
# -----------------------------------------------------------------------------


class FichesAdminSite(AdminSite):
    """
    Custom admin site for Lumières.Lausanne application.
    
    Provides a branded administration interface with University of Lausanne styling.
    """
    site_header = "Administration Lumières.Lausanne"
    site_title = "Lumières.Lausanne Admin"
    index_title = "Administration du site"
    site_url = "/"
    
    def each_context(self, request):
        """
        Return a dictionary of variables to put in the template context for
        every page in the admin site.
        """
        context = super().each_context(request)
        context.update({
            'site_header': self.site_header,
            'site_title': self.site_title,
            'index_title': self.index_title,
            'site_url': self.site_url,
            'has_permission': request.user.is_active and request.user.is_staff,
        })
        return context


fiches_admin = FichesAdminSite(name="fiches_admin")

# -----------------------------------------------------------------------------
# Inline Admin Classes
# -----------------------------------------------------------------------------


class ImageInlineForm(ModelForm):
    legend = CharField(label="Légende", widget=TextInput(attrs={"size": 150}))

    class Meta:
        model = Image
        fields = "__all__"


class ImageInline(GenericStackedInline):
    model = Image
    form = ImageInlineForm
    extra = 0


class DocumentInline(GenericStackedInline):
    model = Document
    extra = 0


# Add Biography inline for Person admin
class BiographyInline(admin.StackedInline):
    """Inline admin for Biography model."""
    
    model = Biography
    extra = 0
    fields = ('public_functions', 'birth_place', 'birth_date', 'death_place', 'death_date', 'valid')
    classes = ('collapse',)


# -----------------------------------------------------------------------------
# ModelAdmin Classes
# -----------------------------------------------------------------------------


class ContributionTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "name", "code")
    search_fields = ("type", "name", "code")
    list_filter = ("type",)


class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model."""
    
    list_display = ("user",)
    search_fields = ("user__username",)
    list_filter = ("user__is_active", "user__is_staff")
    ordering = ("user__username",)
    readonly_fields = ("user",)


class PersonAdmin(admin.ModelAdmin):
    """Admin interface for Person model (reverted to basic version)."""
    list_display = ("name", "modern", "may_have_biography")
    list_display_links = ("name",)
    list_filter = ("modern", "may_have_biography")
    search_fields = ("name",)
    ordering = ("name",)


class PrimaryKeywordAdmin(admin.ModelAdmin):
    """Admin interface for PrimaryKeyword model."""
    
    list_display = ("word", "secondary_keywords_count")
    list_display_links = ("word",)
    search_fields = ("word",)
    ordering = ("word",)
    
    @admin.display(description="Mots clés secondaires")
    def secondary_keywords_count(self, obj):
        """Display count of related secondary keywords."""
        count = obj.secondary_keywords.count()
        if count > 0:
            return format_html(
                '<a href="{}?primary_keyword__id__exact={}">{} mot(s) clé(s)</a>',
                reverse_url("fiches_admin:fiches_secondarykeyword_changelist"),
                obj.id,
                count
            )
        return "Aucun"


class SecondaryKeywordAdmin(admin.ModelAdmin):
    """Admin interface for SecondaryKeyword model."""
    
    list_display = ("word", "primary_keyword")
    list_display_links = ("word",)
    search_fields = ("word", "primary_keyword__word")
    list_filter = ("primary_keyword",)
    ordering = ("primary_keyword__word", "word")


class SocietyAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class BiblioAdmin(admin.ModelAdmin):
    form = BiblioForm
    list_display = ("title", "document_type", "language")
    search_fields = ("title", "document_type__name", "language__name")
    list_filter = ("document_type", "language")


class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code")
    list_display_links = ("name",)
    ordering = ("id",)
    search_fields = ("name",)


class DocumentLanguageAdmin(admin.ModelAdmin):
    """Admin interface for DocumentLanguage model."""
    
    list_display = ("name", "code", "ordering")
    list_display_links = ("name",)
    list_editable = ("ordering",)
    ordering = ("ordering", "name")
    search_fields = ("name", "code")


class DepotAdmin(admin.ModelAdmin):
    """Admin interface for Depot (Repository Location) model."""
    
    list_display = ("name",)
    list_display_links = ("name",)
    ordering = ("name",)
    search_fields = ("name",)


class DocumentFileAdmin(admin.ModelAdmin):
    list_display = ("file", "file_link")
    search_fields = ("file__name",)

    @admin.display(description="File Link")
    def file_link(self, obj):
        """Generate a clickable link for the file."""
        if obj.file and obj.file.name:
            return format_html(
                '<a href="{}" target="_blank">{}</a>',
                obj.get_absolute_url(),
                os.path.basename(obj.file.name)
            )
        return "No file available"


class FindingAdmin(admin.ModelAdmin):
    list_display = ("description",)
    search_fields = ("description",)

    def save_model(self, request, obj, form, change):
        obj.save()


class FreeContentAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created_on", "modified_on")
    list_display_links = ("title",)
    search_fields = ("title", "author__username")
    list_filter = ("created_on", "modified_on", "author")
    ordering = ("id",)

    def has_add_permission(self, request):
        return False


class NewsAdmin(admin.ModelAdmin):
    list_display = ("title", "created_on", "modified_on", "published")
    search_fields = ("title", "content")


class ObjectCollectionAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(PlaceView)
class PlaceViewAdmin(admin.ModelAdmin):
    list_display = ("biblio", "place_name")
    search_fields = ("biblio__title", "place_name")
    list_filter = ("place_name",)
    ordering = ("place_name",)


@admin.register(JournaltitleView)
class JournaltitleViewAdmin(admin.ModelAdmin):
    list_display = ("journal_title",)
    search_fields = ("journal_title",)


class UserGroupAdmin(admin.ModelAdmin):
    """Admin interface for UserGroup model."""
    
    list_display = ("name", "sort")
    search_fields = ("name",)


class NationalityAdmin(admin.ModelAdmin):
    """Admin interface for Nationality model."""
    
    list_display = ("name",)
    list_display_links = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


class RelationTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "reverse_name", "sorting")


class ReligionAdmin(admin.ModelAdmin):
    list_display = ("name", "sorting")
    search_fields = ("name",)
    list_editable = ("sorting",)
    ordering = ("sorting", "id")


class ManuscriptTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sorting")
    search_fields = ("name",)
    list_editable = ("sorting",)
    ordering = ("sorting", "id")


class ManuscriptAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "creator")
    search_fields = ("title", "creator__username")
    list_filter = ("creator",)
    ordering = ("id",)


class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ("date", "user", "model_name")
    list_filter = (
        "model_name",
        "date",
    )
    search_fields = ("user__username", "user__first_name", "user__last_name")
    ordering = ("-date",)


class BiographyAdmin(admin.ModelAdmin):
    list_display = ("person",)
    search_fields = ("person__name", "bio")
    list_filter = ("person",)


class TranscriptionAdmin(admin.ModelAdmin):
    list_display = ("id",)
    list_filter = ("status",)


# -----------------------------------------------------------------------------
# Image Admin Class (If Needed)
# -----------------------------------------------------------------------------


class ImageAdmin(admin.ModelAdmin):
    list_display = ("id", "image", "legend")
    search_fields = ("legend", "image")
    ordering = ("id",)


# -----------------------------------------------------------------------------
# User and Group Admins
# -----------------------------------------------------------------------------


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Informations supplémentaires"
    fields = ("field_of_research", "shib_uniqueID")


class FichesUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (_("Groups"), {"fields": ("groups",)}),
    )
    list_filter = ("groups", "is_staff", "is_active", "is_superuser")
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "userActivities")
    list_per_page = 25

    @admin.display(description="Suivi de l'activité")
    def userActivities(self, obj):
        return format_html(
            '<a href="{}">[ suivi ]</a>',
            reverse_url("fiches_admin:fiches_activitylog_changelist") + f"?user__id__exact={obj.id}",
        )


class FichesGroupAdmin(GroupAdmin):
    pass


# -----------------------------------------------------------------------------
# Registering Models with Custom AdminSite
# -----------------------------------------------------------------------------


fiches_admin.register(ActivityLog, ActivityLogAdmin)
fiches_admin.register(News, NewsAdmin)
fiches_admin.register(FreeContent, FreeContentAdmin)
fiches_admin.register(DocumentFile, DocumentFileAdmin)
fiches_admin.register(UserGroup, UserGroupAdmin)
fiches_admin.register(UserProfile, UserProfileAdmin)
fiches_admin.register(DocumentLanguage, DocumentLanguageAdmin)
fiches_admin.register(Depot, DepotAdmin)
fiches_admin.register(PrimaryKeyword, PrimaryKeywordAdmin)
fiches_admin.register(SecondaryKeyword, SecondaryKeywordAdmin)
fiches_admin.register(Nationality, NationalityAdmin)
fiches_admin.register(Person, PersonAdmin)

# fiches_admin.register(ContributionType, ContributionTypeAdmin)
# fiches_admin.register(UserProfile, UserProfileAdmin)
# fiches_admin.register(Person, PersonAdmin)
# fiches_admin.register(PrimaryKeyword, PrimaryKeywordAdmin)
# fiches_admin.register(SecondaryKeyword, SecondaryKeywordAdmin)
# fiches_admin.register(Society, SocietyAdmin)
# fiches_admin.register(Biography, BiographyAdmin)
# fiches_admin.register(Biblio, BiblioAdmin)
# fiches_admin.register(ManuscriptType, ManuscriptTypeAdmin)  # Correctly registering ManuscriptType
# fiches_admin.register(Manuscript, ManuscriptAdmin)          # Correctly registering Manuscript
# fiches_admin.register(Transcription, TranscriptionAdmin)
# fiches_admin.register(DocumentType, DocumentTypeAdmin)
# fiches_admin.register(Finding, FindingAdmin)
# fiches_admin.register(Image, ImageAdmin)                    # Corrected registration
# fiches_admin.register(ObjectCollection, ObjectCollectionAdmin)
# fiches_admin.register(Project, ProjectAdmin)
# fiches_admin.register(PlaceView, PlaceViewAdmin)
# fiches_admin.register(JournaltitleView, JournaltitleViewAdmin)
# fiches_admin.register(UserGroup, UserGroupAdmin)
# fiches_admin.register(Nationality, NationalityAdmin)
# fiches_admin.register(RelationType, RelationTypeAdmin)
# fiches_admin.register(Religion, ReligionAdmin)
# fiches_admin.register(Group, FichesGroupAdmin)

# -----------------------------------------------------------------------------
# End of `fiches/admin.py`
# -----------------------------------------------------------------------------
