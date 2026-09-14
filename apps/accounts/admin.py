from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "display_name", "is_staff", "is_active", "date_joined")
    search_fields = ("username", "email", "display_name", "first_name", "last_name")
    list_filter = ("is_staff", "is_superuser", "is_active")
    fieldsets = DjangoUserAdmin.fieldsets + (("Profile", {"fields": ("display_name",)}),)
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (("Profile", {"fields": ("display_name",)}),)
