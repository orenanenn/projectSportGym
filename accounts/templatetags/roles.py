from django import template
register = template.Library()

@register.filter
def is_role(user, role_name: str):
    try:
        return getattr(user, "profile", None) and user.profile.role == role_name
    except Exception:
        return False
