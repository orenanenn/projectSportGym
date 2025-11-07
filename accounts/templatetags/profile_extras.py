from django import template

register = template.Library()


@register.filter(name="attr")
def attr(obj, name):
    return getattr(obj, name, "")


@register.filter
def add_class(field, css):
    try:
        from django.forms.boundfield import BoundField

        if isinstance(field, BoundField):
            attrs = field.field.widget.attrs.copy()
            if "class" in attrs:
                attrs["class"] = f'{attrs["class"]} {css}'
            else:
                attrs["class"] = css
            return field.as_widget(attrs=attrs)

    except Exception:
        pass

    return field
