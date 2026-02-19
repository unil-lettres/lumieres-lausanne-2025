from django import forms
from django.contrib.auth.models import User
from .models.person import Person

# class PersonField(forms.Field):
#     """
#     A stub for PersonField. Extend this as needed.
#     """
#     pass

# class PersonWidget(forms.Widget):
#     """
#     A stub for PersonWidget. Extend this as needed.
#     """
#     def render(self, name, value, attrs=None, renderer=None):
#         return super().render(name, value, attrs, renderer)

# from django import forms
# #from .models import Person  # Assuming Person is the model you want to reference


class MultiplePersonField(forms.ModelMultipleChoiceField):
    """
    A custom field for handling multiple person-related data.
    """

    def __init__(self, *args, **kwargs):
        # Ensure you pass the queryset here, assuming you want to use the Person model
        if "queryset" not in kwargs:
            kwargs["queryset"] = Person.objects.all()
        kwargs.setdefault("widget", forms.CheckboxSelectMultiple)
        super().__init__(*args, **kwargs)

    def clean(self, value):
        """
        Accept legacy DynamicList payload entries like ``\"123|Doe, John\"``.
        The widget stores this format in hidden inputs, while ModelMultipleChoiceField
        expects plain primary-key values.
        """
        if not value:
            return super().clean(value)

        normalized = []
        for item in value:
            if isinstance(item, Person):
                normalized.append(str(item.pk))
                continue

            text = str(item).strip()
            if not text:
                continue
            if "|" in text:
                text = text.split("|", 1)[0].strip()
            normalized.append(text)

        return super().clean(normalized)


class MultipleUserField(forms.ModelMultipleChoiceField):
    """
    Accept regular user PKs and legacy DynamicList payload entries (\"id|label\").
    """

    def __init__(self, *args, **kwargs):
        if "queryset" not in kwargs:
            kwargs["queryset"] = User.objects.all()
        kwargs.setdefault("widget", forms.SelectMultiple)
        super().__init__(*args, **kwargs)

    def clean(self, value):
        if not value:
            return super().clean(value)

        normalized = []
        for item in value:
            if isinstance(item, User):
                normalized.append(str(item.pk))
                continue

            text = str(item).strip()
            if not text:
                continue
            if "|" in text:
                text = text.split("|", 1)[0].strip()
            normalized.append(text)

        return super().clean(normalized)
