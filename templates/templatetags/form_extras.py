# templates/templatetags/form_extras.py
from django import template
register = template.Library()

@register.filter
def add_class(field, css):
    return field.as_widget(attrs={**field.field.widget.attrs, "class": css})
