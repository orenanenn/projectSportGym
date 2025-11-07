# core/forms.py
from django import forms
from django.core.validators import MinValueValidator
from accounts.models import Profile
from .models import (
    GymHall, GroupClass, IndividualSlot,
    SiteInfo, Tariff
)


def trainer_qs():
    return (
        Profile.objects
        .filter(role=Profile.Role.TRAINER)
        .select_related("user")
        .order_by("user__last_name", "user__first_name", "user__username")
    )


class SiteInfoForm(forms.ModelForm):
    class Meta:
        model = SiteInfo
        fields = [
            "title",
            "short_description",
            "address",
            "phone",
            "email",
            "work_hours",
            "map_embed",
        ]
        widgets = {
            "short_description": forms.Textarea(attrs={"rows": 4}),
            "map_embed": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": 'Вставте <iframe ...></iframe> або посилання на карту',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            css = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (css + " form-control bg-dark text-white border-secondary").strip()


class TariffForm(forms.ModelForm):
    price_uah = forms.DecimalField(
        min_value=0,
        decimal_places=2,
        max_digits=10,
        widget=forms.NumberInput(attrs={"step": "0.01", "placeholder": "0.00"}),
        label="Ціна, грн",
        validators=[MinValueValidator(0)],
    )

    class Meta:
        model = Tariff
        fields = ["category", "name", "duration_label", "price_uah", "is_active", "sort_order"]
        widgets = {
            "duration_label": forms.TextInput(attrs={"placeholder": "наприклад: 30 днів"}),
            "sort_order": forms.NumberInput(attrs={"min": 0, "step": 1}),
        }

    def __init__(self, *args, **kwargs):
        self.fixed_category = kwargs.pop("fixed_category", None)
        super().__init__(*args, **kwargs)

        if self.fixed_category:
            self.fields["category"].initial = self.fixed_category
            self.fields["category"].disabled = True

        for f in self.fields.values():
            css = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (css + " form-control bg-dark text-white border-secondary").strip()

    def clean_category(self):
        value = self.cleaned_data.get("category")
        return self.fixed_category or value


class GymHallForm(forms.ModelForm):
    class Meta:
        model = GymHall
        fields = ["name", "capacity", "description"]
        labels = {
            "name": "Назва залу",
            "capacity": "Місткість",
            "description": "Опис",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            css = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (css + " form-control bg-dark text-white border-secondary").strip()


class GroupClassForm(forms.ModelForm):
    class Meta:
        model = GroupClass
        fields = ["title", "hall", "trainer", "start_time", "end_time", "max_slots"]
        widgets = {
            "start_time": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "placeholder": "ДД.ММ.РРРР год:хв"
                }
            ),
            "end_time": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "placeholder": "ДД.ММ.РРРР год:хв"
                }
            ),
            "max_slots": forms.NumberInput(attrs={"min": 1, "step": 1}),
        }
        labels = {
            "title": "Назва",
            "hall": "Зал",
            "trainer": "Тренер",
            "start_time": "Початок",
            "end_time": "Кінець",
            "max_slots": "Макс. місць",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["trainer"].queryset = trainer_qs()
        self.fields["trainer"].empty_label = "— виберіть тренера —"

        def _label(p: Profile) -> str:
            full = (f"{p.user.last_name} {p.user.first_name}").strip()
            return full or p.user.username

        self.fields["trainer"].label_from_instance = _label

        self.fields["hall"].label = "Зал"
        self.fields["hall"].empty_label = "— виберіть зал —"

        for name, f in self.fields.items():
            css = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (css + " form-control bg-dark text-white border-secondary").strip()

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        if start and end and start >= end:
            raise forms.ValidationError("Час завершення має бути пізніше за час початку.")
        return cleaned


class IndividualSlotForm(forms.ModelForm):
    trainer = forms.ModelChoiceField(
        queryset=trainer_qs(),
        required=False,
        label="Тренер",
        empty_label="— виберіть тренера —",
    )

    class Meta:
        model = IndividualSlot
        fields = ["hall", "start_time", "end_time"]
        widgets = {
            "start_time": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "placeholder": "ДД.ММ.РРРР год:хв",
                }
            ),
            "end_time": forms.DateTimeInput(
                attrs={
                    "type": "datetime-local",
                    "placeholder": "ДД.ММ.РРРР год:хв",
                }
            ),
        }
        labels = {
            "hall": "Зал",
            "start_time": "Початок",
            "end_time": "Кінець",
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)


        self.fields["hall"].label = "Зал"
        if hasattr(self.fields["hall"].widget, "choices"):
            pass
        try:
            self.fields["hall"].empty_label = "— виберіть зал —"
        except Exception:
            pass

        if user and hasattr(user, "profile") and user.profile.role == Profile.Role.TRAINER:
            self.fields.pop("trainer", None)
        else:
            if "trainer" in self.fields:
                self.fields["trainer"].queryset = trainer_qs()
                self.fields["trainer"].empty_label = "— виберіть тренера —"

        for f in self.fields.values():
            css = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (css + " form-control bg-dark text-white border-secondary").strip()

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_time")
        end = cleaned.get("end_time")
        if start and end and start >= end:
            raise forms.ValidationError("Час завершення має бути пізніше за час початку.")
        return cleaned
