# accounts/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Profile(models.Model):
    class Gender(models.TextChoices):
        MALE = "male", "Чоловіча"
        FEMALE = "female", "Жіноча"
        OTHER = "other", "Інша"

    class Role(models.TextChoices):
        CLIENT = "client", "Клієнт"
        TRAINER = "trainer", "Тренер"
        MANAGER = "manager", "Менеджер"

    class TrainerStatus(models.TextChoices):
        TRAINER = "trainer", "Тренер"
        SENIOR_TRAINER = "senior_trainer", "Старший тренер"
        HEAD_TRAINER = "head_trainer", "Головний тренер залу"

    class Specialization(models.TextChoices):
        PERSONAL = "personal", "Індивідуальні тренування"
        DANCE = "dance", "Танці"
        YOGA = "yoga", "Йога"
        CROSSFIT = "crossfit", "Кросфіт"
        PILATES = "pilates", "Пілатес"
        STRETCHING = "stretching", "Стретчинг"
        MARTIAL_ARTS = "martial_arts", "Бойові мистецтва"
        FITNESS = "fitness", "Фітнес"
        BODYBUILDING = "bodybuilding", "Бодібілдинг"
        OTHER = "other", "Інше"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")

    birth_date = models.DateField("Дата народження", null=True, blank=True)
    phone = models.CharField("Телефон", max_length=32)
    email = models.EmailField("Email")
    gender = models.CharField("Стать", max_length=16, choices=Gender.choices)
    role = models.CharField("Роль", max_length=32, choices=Role.choices)

    status = models.CharField(
        "Статус тренера",
        max_length=32,
        choices=TrainerStatus.choices,
        null=True,
        blank=True,
        help_text="Напр., Тренер / Старший тренер / Головний тренер залу",
    )
    specialization = models.CharField(
        "Спеціалізація",
        max_length=32,
        choices=Specialization.choices,
        null=True,
        blank=True,
    )
    work_time = models.CharField(
        "Час роботи",
        max_length=128,
        null=True,
        blank=True,
        help_text="Вільний текст: напр. Пн–Пт 09:00–18:00",
    )

    manager_status = models.CharField(
        "Статус менеджера",
        max_length=64,
        null=True,
        blank=True,
        help_text="Опціонально: напр., Менеджер зміни / Менеджер залу",
    )

    class Meta:
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["gender"]),
        ]

    def clean(self):
        if self.role == self.Role.TRAINER:
            if not self.status:
                raise ValidationError({"status": "Вкажіть статус тренера."})
            if not self.specialization:
                raise ValidationError({"specialization": "Вкажіть спеціалізацію тренера."})

    @property
    def display_name(self) -> str:
        """Ім’я для відображення: ім’я + прізвище з User, або логін."""
        full = f"{self.user.first_name} {self.user.last_name}".strip()
        return full or self.user.username

    def __str__(self):
        return f"{self.display_name} ({self.role})"
