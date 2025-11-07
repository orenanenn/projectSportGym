from django.contrib import admin
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user_username",
        "user_last_name",
        "user_first_name",
        "email",
        "phone",
        "gender",
        "role",
        "status",
        "specialization",
        "user_date_joined",
    )
    list_select_related = ("user",)
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "phone",
        "email",
    )
    list_filter = ("role", "gender", "status", "specialization")
    ordering = ("user__last_name", "user__first_name", "user__username")

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = "Логін"
    user_username.admin_order_field = "user__username"

    def user_first_name(self, obj):
        return obj.user.first_name
    user_first_name.short_description = "Ім’я"
    user_first_name.admin_order_field = "user__first_name"

    def user_last_name(self, obj):
        return obj.user.last_name
    user_last_name.short_description = "Прізвище"
    user_last_name.admin_order_field = "user__last_name"

    def user_date_joined(self, obj):
        return obj.user.date_joined
    user_date_joined.short_description = "Створено"
    user_date_joined.admin_order_field = "user__date_joined"
