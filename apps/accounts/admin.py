from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import AreaWatch, User


class AreaWatchInline(admin.TabularInline):
    model = AreaWatch
    extra = 0
    max_num = AreaWatch.MAX_PER_USER


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "display_name", "is_staff", "is_active", "date_joined")
    search_fields = (
        "username",
        "email",
        "display_name",
        "first_name",
        "last_name",
        "affiliation",
        "county",
        "constituency",
        "ward",
    )
    list_filter = ("is_staff", "is_superuser", "is_active")
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "Profile",
            {
                "fields": (
                    "display_name",
                    "affiliation",
                    "role",
                    "county",
                    "constituency",
                    "ward",
                    "location",
                    "track_area",
                    "website",
                    "bio",
                )
            },
        ),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (("Profile", {"fields": ("display_name",)}),)
    inlines = [AreaWatchInline]


@admin.register(AreaWatch)
class AreaWatchAdmin(admin.ModelAdmin):
    list_display = ("user", "county", "constituency", "ward", "created_at")
    search_fields = ("user__username", "county", "constituency", "ward")
    list_filter = ("county",)
