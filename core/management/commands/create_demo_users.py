from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction
from accounts.models import Profile


class Command(BaseCommand):
    help = "Створює демо-користувачів з ролями (client, trainer, manager). Ідемпотентно."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Видалити існуючих демо-користувачів і створити заново",
        )
        parser.add_argument(
            "--force-passwords",
            action="store_true",
            help="Переписати паролі демо-користувачам, якщо вони вже існують",
        )

    def handle(self, *args, **options):
        users_data = [
            # username, password, role, full_name, first_name, last_name, gender
            ("client", "clientpass", Profile.Role.CLIENT, "Клієнт", "Іван", "Клієнт", "male"),
            ("trainer", "trainerpass", Profile.Role.TRAINER, "Тренер", "Олег", "Тренер", "male"),
            ("manager", "managerpass", Profile.Role.MANAGER, "Менеджер", "Марія", "Менеджер", "female"),

        ]
        usernames = [u[0] for u in users_data]

        if options["reset"]:
            deleted = User.objects.filter(username__in=usernames).delete()
            self.stdout.write(self.style.WARNING(f"️Видалено користувачів/профілів: {deleted}"))

        for username, password, role, full_name, first_name, last_name, gender in users_data:
            with transaction.atomic():
                user, u_created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        "first_name": first_name,
                        "last_name": last_name,
                        "email": f"{username}@example.com",
                        "is_active": True,
                    },
                )
                if u_created:
                    user.set_password(password)
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f"Створено користувача {username}"))
                else:
                    msg = f"Користувач {username} уже існує"
                    if options["force_passwords"]:
                        user.set_password(password)
                        msg += " (пароль оновлено)"
                    need_save = False
                    if user.first_name != first_name:
                        user.first_name = first_name
                        need_save = True
                    if user.last_name != last_name:
                        user.last_name = last_name
                        need_save = True
                    if not user.email:
                        user.email = f"{username}@example.com"
                        need_save = True
                    if need_save or options["force_passwords"]:
                        user.save()
                    self.stdout.write(msg)

                profile, p_created = Profile.objects.get_or_create(
                    user=user,
                    defaults={
                        "full_name": full_name,
                        "gender": gender,
                        "role": role,
                        "phone": "0990000000",
                    },
                )
                if p_created:
                    self.stdout.write(self.style.SUCCESS(f"   ↳ Профіль створено: {username} ({role})"))
                else:
                    changed = []
                    if profile.role != role:
                        profile.role = role
                        changed.append("role")
                    if not profile.full_name:
                        profile.full_name = full_name
                        changed.append("full_name")
                    if not profile.phone:
                        profile.phone = "0990000000"
                        changed.append("phone")
                    if not profile.gender:
                        profile.gender = gender
                        changed.append("gender")
                    if changed:
                        profile.save()
                        self.stdout.write(f"   ↳ Профіль оновлено ({', '.join(changed)})")
                    else:
                        self.stdout.write(f"   ↳ Профіль уже існує")

        self.stdout.write(self.style.SUCCESS("Усі демо-користувачі готові!"))
