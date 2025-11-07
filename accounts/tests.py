from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase

from accounts.models import Profile


def first_choice_value(model, field_name, default=None):
    """
    Повертає перше допустиме значення з choices для поля моделі.
    Якщо choices порожні/відсутні — повертає default.
    """
    try:
        choices = model._meta.get_field(field_name).choices or []
        return choices[0][0] if choices else default
    except Exception:
        return default


class ProfileSignalTests(TestCase):
    def test_profile_is_created_for_new_user_with_client_role(self):
        user = User.objects.create_user(username="alice", password="pass12345")
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.role, Profile.Role.CLIENT)

    def test_display_name_prefers_full_name_else_username(self):
        u1 = User.objects.create_user(username="bob", first_name="Bob", last_name="Marley")
        p1 = Profile.objects.get(user=u1)
        self.assertEqual(p1.display_name, "Bob Marley")

        u2 = User.objects.create_user(username="charlie")
        p2 = Profile.objects.get(user=u2)
        self.assertEqual(p2.display_name, "charlie")


class ProfileValidationTests(TestCase):
    def setUp(self):
        self.user_tr = User.objects.create_user(username="trainer1", password="x")

    def _fill_common_required_fields(self, profile: Profile):
        gender_val = first_choice_value(Profile, "gender", default=None)
        profile.gender = gender_val
        profile.phone = "+380000000000"
        if hasattr(profile, "email"):
            profile.email = "trainer1@example.com"

    def test_trainer_requires_status_and_specialization(self):
        profile = Profile.objects.get(user=self.user_tr)
        profile.role = Profile.Role.TRAINER
        self._fill_common_required_fields(profile)
        profile.status = None
        if hasattr(profile, "specialization"):
            profile.specialization = None

        with self.assertRaises(ValidationError) as ctx:
            profile.full_clean()

        msg = str(ctx.exception)
        self.assertTrue("status" in msg or "specialization" in msg)

    def test_trainer_with_status_and_specialization_is_valid(self):
        profile = Profile.objects.get(user=self.user_tr)
        profile.role = Profile.Role.TRAINER
        self._fill_common_required_fields(profile)

        status_val = first_choice_value(Profile, "status", default=None)
        spec_val = first_choice_value(Profile, "specialization", default=None)

        profile.status = status_val
        if hasattr(profile, "specialization"):
            profile.specialization = spec_val

        profile.full_clean()
        profile.save()
