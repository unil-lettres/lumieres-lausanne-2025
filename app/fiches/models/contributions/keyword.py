# fiches/models/keyword.py

from django.db import models
from django.utils.translation import gettext_lazy as _

class PrimaryKeyword(models.Model):
    """Primary keyword model for categorizing content."""
    
    word = models.CharField(_("Mot"), max_length=100, unique=True)

    def __str__(self):
        """Return string representation of the primary keyword."""
        return self.word

    class Meta:
        """Meta configuration for PrimaryKeyword model."""
        
        verbose_name = _("Mot clé principal")
        verbose_name_plural = _("Mots clés principaux")
        ordering = ("word",)


class SecondaryKeyword(models.Model):
    """Secondary keyword model that belongs to a primary keyword."""
    
    word = models.CharField(_("Mot"), max_length=100, unique=True)
    primary_keyword = models.ForeignKey(
        PrimaryKeyword,
        on_delete=models.CASCADE,
        db_column='parent_id',
        related_name='secondary_keywords',
        verbose_name=_("Mot clé principal")
    )

    def __str__(self):
        """Return string representation of the secondary keyword."""
        return f"{self.word} ({self.primary_keyword})"

    class Meta:
        """Meta configuration for SecondaryKeyword model."""
        
        verbose_name = _("Mot clé secondaire")
        verbose_name_plural = _("Mots clés secondaires")
        managed = False
        db_table = "fiches_secondarykeyword"
        ordering = ("primary_keyword__word", "word")
