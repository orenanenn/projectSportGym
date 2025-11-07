# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Profile


class _BootstrapFormMixin:
    def _style_widget(self, field_name, field):
        w = field.widget
        base = w.__class__.__name__.lower()
        control_cls = "form-control bg-dark text-white border-secondary"
        select_cls = "form-select bg-dark text-white border-secondary"
        if "select" in base or isinstance(w, (forms.Select, forms.SelectMultiple)):
            w.attrs["class"] = select_cls
        else:
            w.attrs["class"] = control_cls
        w.attrs.setdefault("placeholder", str(field.label or field_name).strip())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            self._style_widget(name, field)


class UserRegistrationForm(_BootstrapFormMixin, UserCreationForm):
    email = forms.EmailField(label="Email", required=True)
    first_name = forms.CharField(label="Ім'я", required=False)
    last_name = forms.CharField(label="Прізвище", required=False)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Користувач з таким email вже існує.")
        return email


class UserUpdateForm(_BootstrapFormMixin, forms.ModelForm):
    username = forms.CharField(label="Логін", required=True)
    email = forms.EmailField(label="Email", required=True)

    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Такий логін вже зайнятий.")
        return username


class ProfileForm(_BootstrapFormMixin, forms.ModelForm):
    birth_date = forms.DateField(
        label="Дата народження", required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    specialization = forms.ChoiceField(
        label="Спеціалізація",
        choices=[("", "—")] + list(Profile.Specialization.choices),
        required=False,
        help_text="Оберіть напрям роботи",
    )
    work_time = forms.CharField(
        label="Час роботи", required=False,
        widget=forms.TextInput(attrs={"placeholder": "Напр.: Пн–Пт 10:00–18:00"}),
    )

    class Meta:
        model = Profile
        fields = ["birth_date", "phone", "email", "gender", "status", "specialization", "work_time"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "status" in self.fields:
            self.fields["status"].required = False

    def clean(self):
        cleaned = super().clean()
        role = getattr(self.instance, "role", None)
        status = cleaned.get("status")

        if role == Profile.Role.TRAINER:
            if not status:
                self.add_error("status", "Вкажіть статус тренера.")
        else:
            cleaned["status"] = None
            if "specialization" in cleaned:
                cleaned["specialization"] = ""
            if "work_time" in cleaned:
                cleaned["work_time"] = ""

        return cleaned


class UserCreateForm(_BootstrapFormMixin, forms.ModelForm):
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput, required=True)
    role = forms.ChoiceField(label="Роль", choices=Profile.Role.choices, required=True)
    is_active = forms.BooleanField(label="Активний", initial=True, required=False)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]

    def clean_password(self):
        pwd = self.cleaned_data["password"]
        validate_password(pwd)
        return pwd


class UserEditForm(_BootstrapFormMixin, forms.ModelForm):
    username = forms.CharField(label="Логін", required=True)
    email = forms.EmailField(label="Email", required=True)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email"]

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Такий логін вже зайнятий.")
        return username


class ProfileEditForm(_BootstrapFormMixin, forms.ModelForm):
    birth_date = forms.DateField(
        label="Дата народження", required=False,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    specialization = forms.ChoiceField(
        label="Спеціалізація",
        choices=[("", "—")] + list(Profile.Specialization.choices),
        required=False,
    )

    class Meta:
        model = Profile
        fields = [
            "birth_date", "phone", "email", "gender", "role",
            "status", "specialization", "work_time"
        ]
        widgets = {
            "work_time": forms.TextInput(attrs={"placeholder": "Напр.: Пн–Пт 10:00–18:00"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "status" in self.fields:
            self.fields["status"].required = False

    def clean(self):
        cleaned = super().clean()
        role = cleaned.get("role") or getattr(self.instance, "role", None)
        status = cleaned.get("status")

        if role == Profile.Role.TRAINER:
            if not status:
                self.add_error("status", "Вкажіть статус тренера.")
        else:
            cleaned["status"] = None
            if "specialization" in cleaned:
                cleaned["specialization"] = ""
            if "work_time" in cleaned:
                cleaned["work_time"] = ""

        return cleaned


class PasswordSetForm(_BootstrapFormMixin, forms.Form):
    new_password = forms.CharField(label="Новий пароль", widget=forms.PasswordInput)

    def clean_new_password(self):
        pwd = self.cleaned_data["new_password"]
        validate_password(pwd)
        return pwd
