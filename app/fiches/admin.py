"""Admin configuration for the fiches app in Lumières.Lausanne."""

from django.utils.html import format_html
from django.urls import reverse as reverse_url
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.admin import GenericStackedInline
from django.contrib.sites.models import Site
from django.contrib.sites.admin import SiteAdmin
from django.forms import ModelForm, TextInput, CharField
from django.contrib import admin
from django.contrib import messages
from fiches.forms import ProjectForm

from fiches.models.content.free_content import FreeContent
from fiches.models.content.news import News
from fiches.models.content.image import Image
from fiches.models.misc.project import Project
from fiches.models.content.finding import Finding
from fiches.models import (
    UserProfile,
    Person,
    PrimaryKeyword,
    SecondaryKeyword,
    Society,
    Biography,
    DocumentType,
    DocumentLanguage,
    DocumentFile,
    PlaceView,
    JournaltitleView,
    UserGroup,
    Nationality,
    RelationType,
    Religion,
    ManuscriptType,
    ActivityLog,
    Document,
    Depot,
)
from fiches.forms import BiblioForm


class FichesAdminSite(AdminSite):
    """
    Custom admin site for Lumières.Lausanne application.

    Provides a branded administration interface with University of Lausanne styling.
    """

    site_header = "Administration Lumières.Lausanne"
    site_title = "Lumières.Lausanne Admin"
    index_title = "Administration du site"
    site_url = "/"


fiches_admin = FichesAdminSite(name="fiches_admin")


class ImageInlineForm(ModelForm):
    """Form for inline image editing in admin."""

    legend = CharField(label="Légende", widget=TextInput(attrs={"size": 150}))

    class Meta:
        """Meta options for ImageInlineForm."""

        model = Image
        fields = "__all__"


class ImageInline(GenericStackedInline):
    """Inline admin for Image model."""

    model = Image
    form = ImageInlineForm
    extra = 0


class DocumentInline(GenericStackedInline):
    """Inline admin for Document model."""

    model = Document
    extra = 0


class BiographyInline(admin.StackedInline):
    """Inline admin for Biography model."""

    model = Biography
    extra = 0
    fields = (
        "public_functions",
        "birth_place",
        "birth_date",
        "death_place",
        "death_date",
        "valid",
    )
    classes = ("collapse",)


class ContributionTypeAdmin(admin.ModelAdmin):
    """Admin interface for ContributionType model."""

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
    """Admin interface for Person model with custom columns and inline editing."""

    list_display = ("id", "name", "modern", "may_have_biography", "biography_link")
    list_display_links = ("name",)
    list_editable = ("modern", "may_have_biography")
    list_filter = ("modern", "may_have_biography")
    search_fields = ("name",)
    ordering = ("name",)
    inlines = [BiographyInline]
    actions = ["add_biography_action"]

    @admin.display(description=_("Biographie"))
    def biography_link(self, obj):
        """Display a link to the biography or a button to add one if missing."""
        bio = obj.biography_set.first()
        if bio:
            url = f"/fiches/bio/{obj.id}/"
            return format_html('<a href="{}" target="_blank">{}</a>', url, _(u"Afficher"))
        # Show button to add biography
        return format_html(
            '<button type="button" onclick="fiches_admin.add_person_biography({})">{}</button>',
            obj.id, _(u"Ajouter une biographie")
        )

    @admin.action(description=_("Ajouter une biographie"))
    def add_biography_action(self, request, queryset):
        """Admin action: create a Biography object for each selected person who does not have one."""
        created = 0
        for person in queryset:
            if not person.has_biography():
                Biography.objects.create(person=person)
                created += 1
        if created:
            self.message_user(
                request,
                _("%d biography(ies) created." % created),
                messages.SUCCESS
            )
        else:
            self.message_user(
                request,
                _("No biography was created. All selected persons already have a biography."),
                messages.INFO
            )


class PrimaryKeywordAdmin(admin.ModelAdmin):
    """Admin interface for PrimaryKeyword model."""

    list_display = ("word", "secondary_keywords_count")
    list_display_links = ("word",)
    search_fields = ("word",)
    ordering = ("word",)

    @admin.display(description="Mots clés secondaires")
    def secondary_keywords_count(self, obj):
        """Return the count of secondary keywords."""
        return obj.secondary_keywords.count()


class SecondaryKeywordAdmin(admin.ModelAdmin):
    """Admin interface for SecondaryKeyword model."""

    list_display = ("word", "primary_keyword")
    list_display_links = ("word",)
    search_fields = ("word", "primary_keyword__word")
    list_filter = ("primary_keyword",)
    ordering = ("primary_keyword__word", "word")


class SocietyAdmin(admin.ModelAdmin):
    """Admin interface for Society model."""

    list_display = ("name",)
    search_fields = ("name",)


class BiblioAdmin(admin.ModelAdmin):
    """Admin interface for Biblio model."""

    form = BiblioForm
    list_display = ("title", "document_type", "language")
    search_fields = ("title", "document_type__name", "language__name")
    list_filter = ("document_type", "language")


class DocumentTypeAdmin(admin.ModelAdmin):
    """Admin interface for DocumentType model."""

    list_display = ("id", "name", "exclusive_fields_display", "code")
    search_fields = ("name", "code")
    ordering = ("name",)

    @admin.display(description="Exclusive fields")
    def exclusive_fields_display(self, obj):
        """Return a display string for exclusive fields."""
        return getattr(obj, "exclusive_fields", "-")


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
    """Admin interface for DocumentFile model."""

    # Only include valid text fields for searching. Do not include FileField or ImageField.
    search_fields = ("title", "slug", "url")

    list_display = ("file", "file_link", "access_owner", "access_public", "access_groups_list")
    filter_horizontal = ("access_groups",)
    fields = ("file", "title", "slug", "url", "access_owner", "access_public", "access_groups")

    @admin.display(description="File Link")
    def file_link(self, obj):
        """Return a link to the file if available."""
        if obj.file:
            return format_html('<a href="{}">Download</a>', obj.file.url)
        return "-"

    @admin.display(description="Access Groups")
    def access_groups_list(self, obj):
        """Return a comma-separated list of access groups."""
        return ", ".join(str(g) for g in obj.access_groups.all())


class FindingAdmin(admin.ModelAdmin):
    """Admin interface for Finding model with vignette preview in change form only."""

    list_display = ("title", "created_on", "modified_on", "published")
    search_fields = ("title",)
    readonly_fields = ("vignette_preview",)
    ordering = ("-created_on",)
    inlines = [ImageInline, DocumentInline]

    @admin.display(description="Vignette")
    def vignette_preview(self, obj):
        """Return a preview of the vignette image if available."""
        if hasattr(obj, "vignette") and obj.vignette:
            return format_html('<img src="{}" style="max-width: 200px;" />', obj.vignette.url)
        return "-"

    @admin.display(boolean=True, description="Publié")
    def published(self, obj):
        """Return True if the finding is published."""
        return getattr(obj, "published", False)


class FreeContentAdmin(admin.ModelAdmin):
    """Admin interface for FreeContent model with image and document inlines."""

    list_display = ("id", "title", "created_on", "modified_on")
    list_display_links = ("title",)
    search_fields = ("title", "author__username")
    list_filter = ("created_on", "modified_on", "author")
    ordering = ("id",)
    inlines = [ImageInline, DocumentInline]

    def has_add_permission(self, request):
        """Disable add permission for FreeContent."""
        return False


class NewsAdmin(admin.ModelAdmin):
    """Admin interface for News model with image and document inlines."""

    list_display = ("title", "created_on", "modified_on", "published")
    search_fields = ("title", "content")
    inlines = [ImageInline, DocumentInline]


class ObjectCollectionAdmin(admin.ModelAdmin):
    """Admin interface for ObjectCollection model."""

    list_display = ("id", "name")
    search_fields = ("name",)


class ProjectAdmin(admin.ModelAdmin):
    """Admin interface for Project model with URL column and clickable link."""

    list_display = (
        "name",
        "project_url_link",
        "publish",
        "members_list",
        "groups_list",
    )
    search_fields = ("name",)
    ordering = ("name",)
    form = ProjectForm
    readonly_fields = ("vignette_preview",)
    fields = (
        "name",
        "url",
        "image",
        "vignette_preview",
        "publish",
        "owner",
        "members",
        "access_groups",
        "description",
        "short_desc",
    )
    inlines = [ImageInline, DocumentInline]

    @admin.display(description="Vignette Prévisualisation")
    def vignette_preview(self, obj):
        """Return a preview of the vignette image if available."""
        if hasattr(obj, "image") and obj.image:
            return format_html('<img src="{}" style="max-width: 200px;" />', obj.image.url)
        return "-"

    @admin.display(description="Members")
    def members_list(self, obj):
        """Return a comma-separated list of member full names."""
        return ", ".join(f"{m.first_name} {m.last_name}".strip() for m in obj.members.all())

    @admin.display(description="Groups")
    def groups_list(self, obj):
        """Return a comma-separated list of groups."""
        return ", ".join(str(g) for g in obj.access_groups.all())

    @admin.display(description="Project URL")
    def project_url_link(self, obj):
        """Return the project's URL path as a clickable link (without host)."""
        if hasattr(obj, "get_absolute_url"):
            url = obj.get_absolute_url()
        elif hasattr(obj, "url"):
            url = f"/projets/{obj.url}"
        else:
            return "-"
        return format_html('<a href="{}" target="_blank">{}</a>', url, url)


@admin.register(PlaceView)
class PlaceViewAdmin(admin.ModelAdmin):
    """Admin interface for PlaceView model."""

    pass


@admin.register(JournaltitleView)
class JournaltitleViewAdmin(admin.ModelAdmin):
    """Admin interface for JournaltitleView model."""

    pass


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
    """Admin interface for RelationType model."""

    list_display = ("name", "reverse_name", "sorting")
    search_fields = ("name", "reverse_name")
    ordering = ("sorting",)


class ReligionAdmin(admin.ModelAdmin):
    """Admin interface for Religion model."""

    list_display = ("name", "sorting")
    search_fields = ("name",)
    ordering = ("sorting", "name")


class ManuscriptTypeAdmin(admin.ModelAdmin):
    """Admin interface for ManuscriptType model."""

    list_display = ("name", "sorting")
    search_fields = ("name",)
    ordering = ("sorting",)


class ManuscriptAdmin(admin.ModelAdmin):
    """Admin interface for Manuscript model."""

    list_display = ("id", "title", "creator")
    search_fields = ("title", "creator__username")
    list_filter = ("creator",)
    ordering = ("id",)


class ActivityLogAdmin(admin.ModelAdmin):
    """Admin interface for ActivityLog model."""

    list_display = ("date", "user_link", "record_type", "record_title_link")
    list_display_links = ("record_title_link",)
    list_filter = ("model_name", "date")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    ordering = ("-date",)

    @admin.display(description="Utilisateur")
    def user_link(self, obj):
        """Return the user's full name (or username) as a clickable link to the user admin page."""
        if not obj.user:
            return "-"
        
        # Get user's full name or fallback to username
        full_name = obj.user.get_full_name()
        display_name = full_name if full_name.strip() else obj.user.username
        
        # Create link to user admin page
        try:
            url = reverse_url("admin:auth_user_change", args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, display_name)
        except (AttributeError, ValueError):
            return display_name

    @admin.display(description="Type de fiche")
    def record_type(self, obj):
        """Return the verbose name of the related model (type de fiche)."""
        info = obj.object_info
        if info and "model_name" in info:
            return info["model_name"]
        return obj.model_name

    @admin.display(description="Fiche")
    def record_title_link(self, obj):
        """Return the title as a clickable link to the associated record (public/detail view if possible)."""
        info = obj.object_info
        if info and "object" in info:
            record = info["object"]
            title = getattr(record, "title", None) or getattr(record, "name", None) or str(record)
            # Prefer get_absolute_url if available
            get_url = getattr(record, "get_absolute_url", None)
            if callable(get_url):
                try:
                    url = get_url()
                    return format_html('<a href="{}">{}</a>', url, title)
                except Exception:
                    pass
            # Fallback to admin change url
            app_label = record._meta.app_label
            model_name = record._meta.model_name
            try:
                url = reverse_url(f"admin:{app_label}_{model_name}_change", args=[record.pk])
            except Exception:
                try:
                    url = reverse_url(f"admin:{model_name}_change", args=[record.pk])
                except Exception:
                    return title
            return format_html('<a href="{}">{}</a>', url, title)
        return "-"


class BiographyAdmin(admin.ModelAdmin):
    """Admin interface for Biography model."""

    list_display = ("person",)
    search_fields = ("person__name", "bio")
    list_filter = ("person",)


class TranscriptionAdmin(admin.ModelAdmin):
    """Admin interface for Transcription model."""

    list_display = ("id", "sorting")
    list_filter = ("status",)


class ImageAdmin(admin.ModelAdmin):
    """Admin interface for Image model."""

    list_display = ("id", "image", "legend")
    search_fields = ("legend", "image")
    ordering = ("id",)


class UserProfileInline(admin.StackedInline):
    """Inline admin for UserProfile model."""

    model = UserProfile
    can_delete = False
    verbose_name_plural = "Informations supplémentaires"
    fields = ("field_of_research", "shib_uniqueID")


class FichesUserAdmin(UserAdmin):
    """Admin interface for User model."""

    inlines = (UserProfileInline,)


class CustomUserAdmin(UserAdmin):
    """Custom admin for User model with UserProfile inline."""

    inlines = (UserProfileInline,)


class FichesGroupAdmin(GroupAdmin):
    """Admin interface for Group model."""

    pass


fiches_admin.register(ActivityLog, ActivityLogAdmin)
fiches_admin.register(News, NewsAdmin)
fiches_admin.register(FreeContent, FreeContentAdmin)
fiches_admin.register(DocumentFile, DocumentFileAdmin)
fiches_admin.register(UserGroup, UserGroupAdmin)
fiches_admin.register(DocumentLanguage, DocumentLanguageAdmin)
fiches_admin.register(Depot, DepotAdmin)
fiches_admin.register(PrimaryKeyword, PrimaryKeywordAdmin)
fiches_admin.register(SecondaryKeyword, SecondaryKeywordAdmin)
fiches_admin.register(Nationality, NationalityAdmin)
fiches_admin.register(Person, PersonAdmin)
# fiches_admin.register(Biography, BiographyAdmin)
fiches_admin.register(Project, ProjectAdmin)
fiches_admin.register(Religion, ReligionAdmin)
fiches_admin.register(Society, SocietyAdmin)
fiches_admin.register(Finding, FindingAdmin)
fiches_admin.register(DocumentType, DocumentTypeAdmin)
fiches_admin.register(RelationType, RelationTypeAdmin)
fiches_admin.register(ManuscriptType, ManuscriptTypeAdmin)
fiches_admin.register(User, UserAdmin)
fiches_admin.register(Group, GroupAdmin)
fiches_admin.register(Site, SiteAdmin)

# Unregister and re-register User with the custom admin
fiches_admin.unregister(User)
fiches_admin.register(User, CustomUserAdmin)
