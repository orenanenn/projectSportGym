# core/views.py
from datetime import timedelta, datetime, time
from collections import defaultdict

from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Q

from accounts.models import Profile
from .models import (
    GymHall,
    GroupClass,
    GroupEnrollment,
    IndividualSlot,
    IndividualBooking,
    SiteInfo,
    Tariff,
)
from .forms import GymHallForm, GroupClassForm, IndividualSlotForm, SiteInfoForm, TariffForm


def home(request):
    """Головна сторінка (landing)."""
    return render(request, "index.html")


@login_required
def halls_list(request):
    halls = GymHall.objects.all()
    return render(request, "halls/list.html", {"halls": halls})


@login_required
def hall_create(request):
    role = request.user.profile.role
    if role != Profile.Role.MANAGER:
        messages.error(request, "Недостатньо прав")
        return redirect("halls_list")

    form = GymHallForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Зал створено")
        return redirect("halls_list")
    return render(request, "halls/form.html", {"form": form, "title": "Новий зал"})


@login_required
def hall_edit(request, pk):
    role = request.user.profile.role
    if role != Profile.Role.MANAGER:
        messages.error(request, "Недостатньо прав")
        return redirect("halls_list")

    hall = get_object_or_404(GymHall, pk=pk)
    form = GymHallForm(request.POST or None, instance=hall)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Зал оновлено")
        return redirect("halls_list")
    return render(request, "halls/form.html", {"form": form, "title": f"Редагувати: {hall.name}"})


@login_required
def hall_delete(request, pk):
    if request.user.profile.role != Profile.Role.MANAGER:
        messages.error(request, "Недостатньо прав")
        return redirect("halls_list")

    hall = get_object_or_404(GymHall, pk=pk)
    if request.method == "POST":
        hall_name = hall.name
        hall.delete()
        messages.success(request, f"Зал «{hall_name}» видалено")
        return redirect("halls_list")

    return render(request, "halls/confirm_delete.html", {"hall": hall})


@login_required
def group_create(request):
    """Створення групового заняття (менеджер)."""
    if request.user.profile.role != Profile.Role.MANAGER:
        messages.error(request, "Недостатньо прав")
        return redirect("schedule_overview")

    form = GroupClassForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Заняття створено")
        return redirect("schedule_overview")
    return render(request, "group/form.html", {"form": form, "title": "Нове групове заняття"})


@login_required
def group_edit(request, pk):
    """Редагування групового заняття (менеджер)."""
    if request.user.profile.role != Profile.Role.MANAGER:
        messages.error(request, "Недостатньо прав")
        return redirect("schedule_overview")

    gc = get_object_or_404(GroupClass, pk=pk)
    form = GroupClassForm(request.POST or None, instance=gc)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Заняття оновлено")
        return redirect("schedule_overview")
    return render(request, "group/form.html", {"form": form, "title": f"Редагувати: {gc.title}"})


@login_required
def group_delete(request, pk):
    """Видалення групового заняття (менеджер)."""
    if request.user.profile.role != Profile.Role.MANAGER:
        messages.error(request, "Недостатньо прав")
        return redirect("schedule_overview")

    gc = get_object_or_404(GroupClass, pk=pk)
    if request.method == "POST":
        title = gc.title
        gc.delete()
        messages.warning(request, f"Заняття «{title}» видалено.")
        return redirect("schedule_overview")
    return render(request, "group/confirm_delete.html", {"obj": gc})


@login_required
def group_enroll(request, pk):
    """Запис клієнта на групове заняття з перевіркою місткості."""
    gc = get_object_or_404(GroupClass, pk=pk)

    if request.user.profile.role != Profile.Role.CLIENT:
        messages.error(request, "Лише клієнти можуть записуватись")
        return redirect("schedule_overview")

    capacity = getattr(gc, "max_slots", None)
    enrolled = gc.enrollments.count()
    if capacity is not None and enrolled >= capacity:
        messages.error(request, "Немає вільних місць")
        return redirect("schedule_overview")

    GroupEnrollment.objects.get_or_create(group_class=gc, client=request.user.profile)
    messages.success(request, "Запис виконано")
    return redirect("schedule_overview")


@login_required
def group_unenroll(request, pk):
    """Скасування запису клієнта на групове заняття."""
    gc = get_object_or_404(GroupClass, pk=pk)

    if request.user.profile.role != Profile.Role.CLIENT:
        messages.error(request, "Лише клієнти можуть скасовувати запис.")
        return redirect("schedule_overview")

    enrollment = GroupEnrollment.objects.filter(
        group_class=gc, client=request.user.profile
    ).first()

    if enrollment:
        enrollment.delete()
        messages.success(request, "Запис скасовано.")
    else:
        messages.info(request, "Ви не були записані на це заняття.")

    return redirect("schedule_overview")


@login_required
def trainer_slots(request):
    role = request.user.profile.role

    if role not in [Profile.Role.TRAINER, Profile.Role.MANAGER]:
        messages.error(request, "Недостатньо прав")
        return redirect("home")

    qs = (
        IndividualSlot.objects
        .select_related("hall", "trainer", "trainer__user")
        .order_by("start_time")
    )
    if role == Profile.Role.TRAINER:
        qs = qs.filter(trainer=request.user.profile)

    form = IndividualSlotForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        slot = form.save(commit=False)

        if role == Profile.Role.TRAINER:
            slot.trainer = request.user.profile
        elif role == Profile.Role.MANAGER:
            selected_trainer_id = request.POST.get("trainer")
            if selected_trainer_id:
                slot.trainer = get_object_or_404(
                    Profile, pk=selected_trainer_id, role=Profile.Role.TRAINER
                )
            else:
                messages.error(request, "Виберіть тренера для цього слоту.")
                return redirect("trainer_slots")

        slot.save()
        messages.success(request, "Слот додано.")
        return redirect("trainer_slots")

    trainers = None
    if role == Profile.Role.MANAGER:
        trainers = (
            Profile.objects
            .filter(role=Profile.Role.TRAINER)
            .select_related("user")
            .order_by("user__last_name", "user__first_name", "user__username")
        )

    return render(
        request,
        "trainer/slots.html",
        {"slots": qs, "form": form, "trainers": trainers, "is_manager": role == Profile.Role.MANAGER},
    )


@login_required
def slot_book(request, pk):
    """Бронювання слоту (клієнт)."""
    if request.user.profile.role != Profile.Role.CLIENT:
        messages.error(request, "Лише клієнти можуть бронювати")
        return redirect("schedule_overview")

    slot = get_object_or_404(IndividualSlot, pk=pk)
    if slot.is_booked:
        messages.error(request, "Слот уже заброньовано")
        return redirect("schedule_overview")

    IndividualBooking.objects.create(slot=slot, client=request.user.profile)
    slot.is_booked = True
    slot.save()
    messages.success(request, "Слот заброньовано")
    return redirect("schedule_overview")


@login_required
def slot_edit(request, pk):
    """Редагування слоту (менеджер або власник- тренер)."""
    slot = get_object_or_404(IndividualSlot, pk=pk)
    role = request.user.profile.role

    if not (role == Profile.Role.MANAGER or (role == Profile.Role.TRAINER and slot.trainer_id == request.user.profile.id)):
        messages.error(request, "Недостатньо прав.")
        return redirect("schedule_overview")

    if request.method == "POST":
        form = IndividualSlotForm(request.POST, instance=slot, user=request.user)
        if form.is_valid():
            slot = form.save(commit=False)
            if role == Profile.Role.MANAGER:
                selected_trainer_id = request.POST.get("trainer")
                if selected_trainer_id:
                    slot.trainer = get_object_or_404(
                        Profile, pk=selected_trainer_id, role=Profile.Role.TRAINER
                    )
            slot.save()
            messages.success(request, "Слот оновлено.")
            return redirect("schedule_overview")
    else:
        form = IndividualSlotForm(instance=slot, user=request.user)

    trainers = None
    if role == Profile.Role.MANAGER:
        trainers = (
            Profile.objects
            .filter(role=Profile.Role.TRAINER)
            .select_related("user")
            .order_by("user__last_name", "user__first_name", "user__username")
        )

    return render(
        request,
        "trainer/slot_form.html",
        {"form": form, "slot": slot, "trainers": trainers, "is_manager": role == Profile.Role.MANAGER},
    )


@login_required
def slot_delete(request, pk):
    """Видалення слоту (менеджер або власник-тренер)."""
    slot = get_object_or_404(IndividualSlot, pk=pk)
    role = request.user.profile.role

    if not (role == Profile.Role.MANAGER or (role == Profile.Role.TRAINER and slot.trainer_id == request.user.profile.id)):
        messages.error(request, "Недостатньо прав.")
        return redirect("schedule_overview")

    if request.method == "POST":
        slot.delete()
        messages.success(request, "Слот видалено.")
        return redirect("schedule_overview")

    return render(request, "trainer/slot_confirm_delete.html", {"slot": slot})


@login_required
def schedule_overview(request):
    """
    Огляд розкладу з фільтрами по залу, тренеру і діапазону дат.
    Для клієнта показуються його поточні/майбутні записи (групові та індивідуальні).
    """
    hall_id = request.GET.get("hall")
    trainer_id = request.GET.get("trainer")
    date_from_str = request.GET.get("from")
    date_to_str = request.GET.get("to")

    now = timezone.now()
    default_start = now.date()
    default_end = (now + timedelta(days=14)).date()

    dt_fmt = "%Y-%m-%d"
    start = default_start
    end = default_end
    try:
        if date_from_str:
            start = datetime.strptime(date_from_str, dt_fmt).date()
        if date_to_str:
            end = datetime.strptime(date_to_str, dt_fmt).date()
    except Exception:
        start, end = default_start, default_end
    if end < start:
        end = start

    tz = timezone.get_current_timezone()
    start_dt = timezone.make_aware(datetime.combine(start, time.min), tz)
    end_dt = timezone.make_aware(datetime.combine(end, time.max), tz)

    groups = (
        GroupClass.objects
        .select_related("hall", "trainer", "trainer__user")
        .filter(start_time__gte=start_dt, end_time__lte=end_dt)
    )
    slots = (
        IndividualSlot.objects
        .select_related("hall", "trainer", "trainer__user")
        .filter(start_time__gte=start_dt, end_time__lte=end_dt)
    )

    if hall_id and hall_id.isdigit():
        groups = groups.filter(hall_id=int(hall_id))
        slots = slots.filter(hall_id=int(hall_id))
    if trainer_id and trainer_id.isdigit():
        groups = groups.filter(trainer_id=int(trainer_id))
        slots = slots.filter(trainer_id=int(trainer_id))

    halls = GymHall.objects.all().order_by("name")
    trainers = (
        Profile.objects
        .filter(role=Profile.Role.TRAINER)
        .select_related("user")
        .order_by("user__last_name", "user__first_name", "user__username")
    )

    role = getattr(getattr(request.user, "profile", None), "role", None)
    is_client = role == Profile.Role.CLIENT
    is_trainer = role == Profile.Role.TRAINER
    is_manager = role == Profile.Role.MANAGER or (hasattr(Profile.Role, "HEAD_MANAGER") and role == Profile.Role.HEAD_MANAGER)

    enrolled_group_ids = set()
    my_booked_slot_ids = set()
    if is_client:
        enrolled_group_ids = set(
            GroupEnrollment.objects.filter(client=request.user.profile, group_class__in=groups)
            .values_list("group_class_id", flat=True)
        )
        my_booked_slot_ids = set(
            IndividualBooking.objects.filter(client=request.user.profile).values_list("slot_id", flat=True)
        )

    my_entries = []
    if is_client:
        my_group = (
            GroupEnrollment.objects
            .select_related("group_class", "group_class__hall", "group_class__trainer", "group_class__trainer__user")
            .filter(client=request.user.profile, group_class__end_time__gte=now)
        )
        for e in my_group:
            gc = e.group_class
            trainer_name = _profile_display_name(gc.trainer)
            my_entries.append({
                "kind": "group",
                "title": gc.title,
                "hall": gc.hall.name if gc.hall_id else "",
                "trainer": trainer_name,
                "start": gc.start_time,
                "end": gc.end_time,
                "group_id": gc.id,
            })

        my_slots = (
            IndividualBooking.objects
            .select_related("slot", "slot__hall", "slot__trainer", "slot__trainer__user")
            .filter(client=request.user.profile)
            .filter(Q(slot__start_time__gte=now) | Q(slot__end_time__gte=now))
            .order_by("slot__start_time")
        )
        for b in my_slots:
            s = b.slot
            trainer_name = _profile_display_name(s.trainer)
            my_entries.append({
                "kind": "slot",
                "title": "Індивідуальне тренування",
                "hall": s.hall.name if s.hall_id else "",
                "trainer": trainer_name,
                "start": s.start_time,
                "end": s.end_time,
                "slot_id": s.id,
            })
        my_entries.sort(key=lambda x: x["start"])

    is_empty = not groups.exists() and not slots.exists()
    had_filters = any([hall_id, trainer_id, date_from_str, date_to_str])
    if is_empty:
        if had_filters:
            empty_hint = "Немає занять за вибраними фільтрами. Спробуйте інший зал, тренера або змініть діапазон дат."
        else:
            empty_hint = "За замовчуванням показано найближчі 14 днів. Занять у цей період немає."
    else:
        empty_hint = ""

    context = {
        "halls": halls,
        "trainers": trainers,
        "groups": groups.order_by("start_time"),
        "slots": slots.order_by("start_time"),
        "hall_id": hall_id or "",
        "trainer_id": trainer_id or "",
        "from": start.strftime(dt_fmt),
        "to": end.strftime(dt_fmt),
        "is_client": is_client,
        "is_trainer": is_trainer,
        "is_manager": is_manager,
        "enrolled_group_ids": enrolled_group_ids,
        "booked_slot_ids": set(IndividualBooking.objects.filter(slot__in=slots).values_list("slot_id", flat=True)),
        "my_booked_slot_ids": my_booked_slot_ids,
        "my_entries": my_entries,
        "is_empty": is_empty,
        "had_filters": had_filters,
        "empty_hint": empty_hint,
    }
    return render(request, "schedule/overview.html", context)


@login_required
def slot_unbook(request, pk):
    """Скасування власного бронювання (клієнт)."""
    if request.user.profile.role != Profile.Role.CLIENT:
        messages.error(request, "Лише клієнти можуть скасовувати бронювання.")
        return redirect("schedule_overview")

    slot = get_object_or_404(IndividualSlot, pk=pk)
    booking = IndividualBooking.objects.filter(slot=slot, client=request.user.profile).first()
    if not booking:
        messages.info(request, "Це бронювання не належить вам або вже скасовано.")
        return redirect("schedule_overview")

    if request.method == "POST":
        booking.delete()
        slot.is_booked = False
        slot.save(update_fields=["is_booked"])
        messages.success(request, "Бронювання слоту скасовано.")
    return redirect("schedule_overview")


def _profile_display_name(p: Profile) -> str:
    """
    Безпечно повертає ім'я тренера для відображення:
    спочатку повне ім'я користувача (User.get_full_name), інакше username.
    """
    if not p:
        return ""
    u = getattr(p, "user", None)
    if not u:
        return ""
    full = (u.get_full_name() or "").strip()
    return full or u.username


def _is_manager(user) -> bool:
    role = getattr(getattr(user, "profile", None), "role", None)
    is_head = hasattr(Profile.Role, "HEAD_MANAGER") and role == Profile.Role.HEAD_MANAGER
    return role == Profile.Role.MANAGER or is_head


def about_view(request):
    siteinfo = SiteInfo.get_solo()
    return render(request, "about/about.html", {
        "siteinfo": siteinfo,
        "is_manager": _is_manager(request.user),
    })


def price_view(request):
    """
    Сторінка «Прайс»:
    - Гості/клієнти/тренери бачать активні тарифи по категоріях.
    - Менеджер додатково має кнопки CRUD.
    """
    is_mgr = _is_manager(request.user)

    all_tariffs = list(Tariff.objects.filter(is_active__in=[True]).order_by("sort_order", "name"))

    grouped = defaultdict(list)
    for t in all_tariffs:
        grouped[t.category].append(t)

    categories = []
    for code, label in Tariff.Category.choices:
        categories.append({
            "code": code,
            "label": label,
            "items": grouped.get(code, []),
        })

    return render(request, "price/price.html", {
        "categories": categories,
        "is_manager": is_mgr,
    })


@login_required
def price_add(request, category_code: str):
    if not _is_manager(request.user):
        return HttpResponseForbidden("Доступ лише для менеджера.")

    valid_codes = {c for c, _ in Tariff.Category.choices}
    if category_code not in valid_codes:
        messages.error(request, "Невідома категорія.")
        return redirect("price")

    if request.method == "POST":
        form = TariffForm(request.POST, fixed_category=category_code)
        if form.is_valid():
            form.save()
            messages.success(request, "Тариф додано.")
            return redirect("price")
    else:
        form = TariffForm(initial={"is_active": True}, fixed_category=category_code)

    label = dict(Tariff.Category.choices).get(category_code, category_code)
    return render(request, "price/form.html", {"form": form, "title": f"Новий тариф — {label}"})


@login_required
def price_edit(request, pk: int):
    if not _is_manager(request.user):
        return HttpResponseForbidden("Доступ лише для менеджера.")

    obj = get_object_or_404(Tariff, pk=pk)
    if request.method == "POST":
        form = TariffForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Зміни збережено.")
            return redirect("price")
    else:
        form = TariffForm(instance=obj)

    return render(request, "price/form.html", {"form": form, "title": f"Редагувати: {obj.name}"})


@login_required
def price_delete(request, pk: int):
    if not _is_manager(request.user):
        return HttpResponseForbidden("Доступ лише для менеджера.")

    obj = get_object_or_404(Tariff, pk=pk)
    if request.method == "POST":
        name = obj.name
        obj.delete()
        messages.warning(request, f"Тариф «{name}» видалено.")
        return redirect("price")

    return render(request, "price/confirm_delete.html", {"obj": obj})


@login_required
def siteinfo_edit(request):
    if not _is_manager(request.user):
        messages.error(request, "Недостатньо прав.")
        return redirect("about")

    siteinfo = SiteInfo.get_solo()
    form = SiteInfoForm(request.POST or None, instance=siteinfo)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Інформацію збережено.")
        return redirect("about")

    return render(request, "about/siteinfo_form.html", {"form": form})
