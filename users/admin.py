from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ResidentProfile, SpecialistProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Данные пользователя", {
            "fields": (
                "last_name",
                "first_name",
                "patronymic",
                "email",
                "phone",
                "role",
            ),
        }),
    )

    fieldsets = UserAdmin.fieldsets + (
        ("Дополнительные данные", {
            "fields": (
                "patronymic",
                "phone",
                "role",
            ),
        }),
    )

admin.site.register(SpecialistProfile)
admin.site.register(ResidentProfile)