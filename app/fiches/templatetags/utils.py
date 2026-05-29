from django import get_version, template

register = template.Library()

@register.simple_tag
def django_version():
    """Returns the current Django version."""
    return get_version()
