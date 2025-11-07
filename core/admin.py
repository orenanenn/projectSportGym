from django.contrib import admin
from .models import (
    GymHall, GroupClass, GroupEnrollment,
    IndividualSlot, IndividualBooking,
    SiteInfo, Tariff
)

@admin.register(SiteInfo)
class SiteInfoAdmin(admin.ModelAdmin):
    list_display = ("title", "address", "phone", "email", "updated_at")
    readonly_fields = ("updated_at",)
    fieldsets = (
        ("Основна інформація", {"fields": ("title", "short_description")}),
        ("Контакти", {"fields": ("address", "phone", "email", "work_hours")}),
        ("Карта", {"fields": ("map_embed",)}),
        ("Службова інформація", {"fields": ("updated_at",)}),
    )

    def has_add_permission(self, request):
        return not SiteInfo.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ("name", "duration_label", "price_uah", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    ordering = ("sort_order",)
    search_fields = ("name", "duration_label")


admin.site.register(GymHall)
admin.site.register(GroupClass)
admin.site.register(GroupEnrollment)
admin.site.register(IndividualSlot)
admin.site.register(IndividualBooking)
