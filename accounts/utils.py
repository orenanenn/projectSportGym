# accounts/utils.py
from functools import wraps
from django.http import HttpResponseForbidden

def role_required(*roles):
    def wrapper(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                from django.contrib.auth.views import redirect_to_login
                return redirect_to_login(request.get_full_path())
            try:
                role = getattr(user, "profile", None).role
            except Exception:
                role = None
            if role in roles:
                return view_func(request, *args, **kwargs)
            return HttpResponseForbidden("Доступ заборонено")
        return _wrapped
    return wrapper
