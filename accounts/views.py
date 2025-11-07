# accounts/views.py
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .models import Profile
from .forms import (
    UserRegistrationForm,
    UserUpdateForm,
    ProfileForm,
    UserCreateForm,
    UserEditForm,
    ProfileEditForm,
    PasswordSetForm,
)

def register_view(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            raw_password = form.cleaned_data["password1"]
            user = authenticate(username=user.username, password=raw_password)
            if user is not None:
                login(request, user)
                messages.success(request, "Ви успішно зареєструвалися!")
                return redirect("home")
            messages.info(request, "Обліковий запис створено. Увійдіть, будь ласка.")
            return redirect("accounts:login")
    else:
        form = UserRegistrationForm()
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Вітаємо! Ви увійшли в систему.")
            return redirect("home")
    else:
        form = AuthenticationForm(request)
    return render(request, "accounts/login.html", {"form": form})


def _require_manager(request):
    profile = getattr(request.user, "profile", None)
    if not profile or profile.role != Profile.Role.MANAGER:
        raise PermissionDenied


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    avatar_field_name = next(
        (n for n in ("avatar", "photo", "image", "picture") if hasattr(profile, n)),
        None,
    )
    avatar_url = None
    if avatar_field_name:
        try:
            val = getattr(profile, avatar_field_name)
            if val:
                avatar_url = val.url
        except Exception:
            avatar_url = None

    return render(
        request,
        "accounts/profile.html",
        {"profile": profile, "avatar_url": avatar_url},
    )


@login_required
@transaction.atomic
def profile_edit_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        uform = UserUpdateForm(request.POST, instance=request.user)
        pform = ProfileForm(request.POST, request.FILES, instance=profile)

        if uform.is_valid() and pform.is_valid():
            user = uform.save()
            prof = pform.save(commit=False)
            prof.email = user.email or ""
            prof.save()
            messages.success(request, "Профіль оновлено.")
            return redirect("accounts:profile")
    else:
        uform = UserUpdateForm(instance=request.user)
        pform = ProfileForm(instance=profile)

    avatar_url = None
    return render(
        request,
        "accounts/profile_edit.html",
        {
            "uform": uform,
            "pform": pform,
            "avatar_url": avatar_url,
            "profile": profile,
            "target_user": request.user,
        },
    )


@login_required
def people(request):
    kind = request.GET.get("kind", "clients").strip().lower()
    role_map = {
        "clients": Profile.Role.CLIENT,
        "trainers": Profile.Role.TRAINER,
        "managers": Profile.Role.MANAGER,
    }
    role = role_map.get(kind, Profile.Role.CLIENT)

    qs = (
        Profile.objects
        .select_related("user")
        .filter(role=role)
    )

    q = (request.GET.get("q") or "").strip()
    if q:
        qs = qs.filter(
            Q(user__username__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(phone__icontains=q) |
            Q(email__icontains=q)
        )

    sort = request.GET.get("sort", "name")
    dir_ = request.GET.get("dir", "asc").lower()
    asc = (dir_ == "asc")

    if sort == "created":
        order_fields = ["user__date_joined" if asc else "-user__date_joined"]
    elif sort == "name":
        base = ["user__last_name", "user__first_name", "user__username"]
        order_fields = base if asc else [f"-{f}" for f in base]
    else:
        order_fields = ["user__username" if asc else "-user__username"]

    profiles = qs.order_by(*order_fields)

    can_manage = (
        request.user.is_authenticated and
        hasattr(request.user, "profile") and
        request.user.profile.role == Profile.Role.MANAGER
    )

    return render(
        request,
        "accounts/people_list.html",
        {
            "profiles": profiles,
            "kind": kind,
            "q": q,
            "sort": sort,
            "dir": "asc" if asc else "desc",
            "can_manage": can_manage,
        },
    )


@login_required
@transaction.atomic
def user_create(request):
    _require_manager(request)

    if request.method == "POST":
        form = UserCreateForm(request.POST)
        pform = ProfileEditForm(request.POST)
        if form.is_valid() and pform.is_valid():
            user = form.save(commit=False)
            user.is_active = form.cleaned_data["is_active"]
            user.set_password(form.cleaned_data["password"])
            user.save()

            profile_defaults = {
                "role": pform.cleaned_data["role"],
                "birth_date": pform.cleaned_data.get("birth_date"),
                "phone": pform.cleaned_data.get("phone", ""),
                "email": pform.cleaned_data.get("email", user.email or ""),
                "gender": pform.cleaned_data.get("gender", ""),
                "status": pform.cleaned_data.get("status"),
                "specialization": pform.cleaned_data.get("specialization", ""),
                "work_time": pform.cleaned_data.get("work_time"),
            }
            Profile.objects.update_or_create(user=user, defaults=profile_defaults)

            messages.success(request, f"Користувача '{user.username}' створено.")
            return redirect("accounts:people")
    else:
        form = UserCreateForm()
        pform = ProfileEditForm()

    return render(
        request,
        "accounts/user_form.html",
        {"form": form, "pform": pform, "title": "Створити користувача"},
    )


@login_required
@transaction.atomic
def user_edit(request, pk):
    _require_manager(request)
    target_user = get_object_or_404(User, pk=pk)
    profile = getattr(target_user, "profile", None)
    if not profile:
        profile = Profile.objects.create(user=target_user, role=Profile.Role.CLIENT)

    if request.method == "POST":
        uform = UserEditForm(request.POST, instance=target_user)
        pform = ProfileEditForm(request.POST, request.FILES, instance=profile)

        if uform.is_valid() and pform.is_valid():
            user = uform.save()
            prof = pform.save(commit=False)
            prof.email = user.email or ""
            prof.save()

            messages.success(request, "Дані користувача оновлено.")
            return redirect("accounts:people")
    else:
        uform = UserEditForm(instance=target_user)
        pform = ProfileEditForm(instance=profile)

    return render(
        request,
        "accounts/people_edit.html",
        {
            "target_user": target_user,
            "profile": profile,
            "uform": uform,
            "pform": pform,
        },
    )


@login_required
def user_password_reset(request, pk):
    _require_manager(request)
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        form = PasswordSetForm(request.POST)
        if form.is_valid():
            user.set_password(form.cleaned_data["new_password"])
            user.save()
            messages.success(request, "Пароль оновлено.")
            return redirect("accounts:people")
    else:
        form = PasswordSetForm()
    return render(request, "accounts/password_set.html", {"form": form, "user_obj": user})


@login_required
@transaction.atomic
def user_delete(request, pk):
    _require_manager(request)
    user = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        username = user.username
        user.delete()
        messages.success(request, f"Користувача '{username}' видалено.")
        return redirect("accounts:people")
    return render(request, "accounts/confirm_delete.html", {"user_obj": user})
