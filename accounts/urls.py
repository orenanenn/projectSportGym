from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views


app_name = "accounts"

urlpatterns = [
    path("people/", views.people, name="people"),
    path("people/create/", views.user_create, name="user_create"),
    path("people/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("people/<int:pk>/password/", views.user_password_reset, name="user_password_reset"),
    path("people/<int:pk>/delete/", views.user_delete, name="user_delete"),

    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),

    path("profile/", views.profile_view, name="profile"),
    path("profile/edit/", views.profile_edit_view, name="profile_edit"),
]
