from django.urls import path
from .views import (home,

    halls_list, hall_create, hall_edit, hall_delete,
    group_create, group_edit, group_delete, group_enroll, group_unenroll,
    trainer_slots, slot_book, slot_edit, slot_delete, slot_unbook, schedule_overview,

    about_view, siteinfo_edit,

    price_view, price_add, price_edit, price_delete,
)

urlpatterns = [
    path("", home, name="home"),

    path("schedule/", schedule_overview, name="schedule_overview"),

    path("halls/", halls_list, name="halls_list"),
    path("halls/new/", hall_create, name="hall_create"),
    path("halls/<int:pk>/edit/", hall_edit, name="hall_edit"),
    path("halls/<int:pk>/delete/", hall_delete, name="hall_delete"),

    path("schedule/groups/new/", group_create, name="group_create"),
    path("schedule/groups/<int:pk>/edit/", group_edit, name="group_edit"),
    path("schedule/groups/<int:pk>/delete/", group_delete, name="group_delete"),
    path("schedule/groups/<int:pk>/enroll/", group_enroll, name="group_enroll"),
    path("schedule/groups/<int:pk>/unenroll/", group_unenroll, name="group_unenroll"),

    path("trainer/slots/", trainer_slots, name="trainer_slots"),
    path("slots/<int:pk>/book/", slot_book, name="slot_book"),
    path("slots/<int:pk>/unbook/", slot_unbook, name="slot_unbook"),
    path("slots/<int:pk>/edit/", slot_edit, name="slot_edit"),
    path("slots/<int:pk>/delete/", slot_delete, name="slot_delete"),

    path("about/", about_view, name="about"),
    path("about/edit/", siteinfo_edit, name="siteinfo_edit"),

    path("price/", price_view, name="price"),
    path("price/<str:category_code>/new/", price_add, name="price_add"),
    path("price/<int:pk>/edit/", price_edit, name="price_edit"),
    path("price/<int:pk>/delete/", price_delete, name="price_delete"),
]
