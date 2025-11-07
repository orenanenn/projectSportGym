# core/models.py
from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import Profile


class SiteInfo(models.Model):
    title = models.CharField(max_length=150, default="Спортивний Зал")
    short_description = models.TextField(
        default=(
            "Сучасний фітнес-комплекс із індивідуальними та груповими тренуваннями. "
            "Професійні тренери, комфортні умови, онлайн-запис."
        )
    )

    address = models.CharField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    work_hours = models.CharField(
        max_length=200, blank=True, default="Пн–Пт: 07:00–22:00; Сб–Нд: 09:00–20:00"
    )

    map_embed = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)
    singleton_guard = models.BooleanField(default=True, unique=True, editable=False)

    class Meta:
        verbose_name = "Інформація про зал (один запис)"
        verbose_name_plural = "Інформація про зал (один запис)"

    def __str__(self):
        return "Інформація про зал"

    @classmethod
    def get_solo(cls):
        obj = cls.objects.first()
        if obj:
            return obj
        return cls.objects.create()


class Tariff(models.Model):
    class Category(models.TextChoices):
        INDIVIDUAL = "individual", "Індивідуальні тренування"
        DANCE      = "dance",      "Танці"
        YOGA       = "yoga",       "Йога"
        CROSSFIT   = "crossfit",   "Кросфіт"
        PILATES    = "pilates",    "Пілатес"
        STRETCHING = "stretching", "Стретчинг"
        MARTIAL    = "martial",    "Бойові мистецтва"
        FITNESS    = "fitness",    "Фітнес (групові)"
        GYM        = "gym",        "Бодібілдинг / Тренажерний зал"
        OTHER      = "other",      "Інше"

    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
        db_index=True,
    )
    name = models.CharField(max_length=120)
    duration_label = models.CharField(
        max_length=120,
        help_text="Напр.: 1 день / 30 днів / 90 днів / 365 днів",
    )
    price_uah = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Ціна в гривнях",
    )
    is_active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ("sort_order", "name")
        verbose_name = "Тариф"
        verbose_name_plural = "Тарифи"

    def __str__(self):
        return f"{self.name} — {self.duration_label} — {self.price_uah} грн"


class GymHall(models.Model):
    name = models.CharField(max_length=100, unique=True)
    capacity = models.PositiveIntegerField(default=10)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class GroupClass(models.Model):
    title = models.CharField(max_length=120)
    hall = models.ForeignKey(GymHall, on_delete=models.CASCADE, related_name="classes")
    trainer = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        limit_choices_to={"role": Profile.Role.TRAINER},
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    max_slots = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.title} — {self.start_time:%Y-%m-%d %H:%M}"


class GroupEnrollment(models.Model):
    group_class = models.ForeignKey(
        GroupClass, on_delete=models.CASCADE, related_name="enrollments"
    )
    client = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        limit_choices_to={"role": Profile.Role.CLIENT},
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("group_class", "client")


class IndividualSlot(models.Model):
    trainer = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        limit_choices_to={"role": Profile.Role.TRAINER},
    )
    hall = models.ForeignKey(GymHall, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        unique_together = ("trainer", "start_time", "end_time", "hall")


class IndividualBooking(models.Model):
    slot = models.OneToOneField(
        IndividualSlot, on_delete=models.CASCADE, related_name="booking"
    )
    client = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        limit_choices_to={"role": Profile.Role.CLIENT},
    )
    created_at = models.DateTimeField(auto_now_add=True)
