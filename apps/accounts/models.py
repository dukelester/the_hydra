from django.contrib.auth.models import AbstractUser
from django.db import models


AVATAR_PALETTES = (
    ("#163a45", "#f3efe4", "#c4a35a"),
    ("#102e37", "#c4a35a", "#d4b56c"),
    ("#1d5c68", "#f3efe4", "#c4a35a"),
    ("#1f6b52", "#f3efe4", "#c4a35a"),
    ("#8a6a2f", "#fff8e8", "#163a45"),
    ("#2f7d8c", "#f3efe4", "#c4a35a"),
)


class UserRole(models.TextChoices):
    CITIZEN = "citizen", "Resident / citizen"
    JOURNALIST = "journalist", "Journalist"
    RESEARCHER = "researcher", "Researcher"
    STUDENT = "student", "Student"
    OFFICIAL = "official", "Public official"
    CSO = "cso", "Civil society / oversight"
    OTHER = "other", "Other"


class User(AbstractUser):
    display_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="Public name shown on your dashboard and avatar.",
    )
    affiliation = models.CharField(
        max_length=255,
        blank=True,
        help_text="Newsroom, university, department, or organisation — if you want it recorded.",
    )
    role = models.CharField(
        max_length=40,
        blank=True,
        choices=UserRole.choices,
        help_text="How you usually use this record. Optional.",
    )
    county = models.CharField(max_length=120, blank=True)
    constituency = models.CharField(max_length=120, blank=True)
    ward = models.CharField(max_length=120, blank=True)
    location = models.CharField(
        max_length=255,
        blank=True,
        help_text="Town, ward, or area you follow.",
    )
    track_area = models.BooleanField(
        default=False,
        help_text="Show projects from this county on the dashboard.",
    )
    area_last_seen_at = models.DateTimeField(null=True, blank=True)
    website = models.URLField(blank=True)
    bio = models.TextField(blank=True)

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.public_name()

    def public_name(self):
        if (self.display_name or "").strip():
            return self.display_name.strip()
        full = f"{self.first_name} {self.last_name}".strip()
        if full:
            return full
        return self.get_username()

    def avatar_initials(self):
        name = self.public_name()
        parts = [part for part in name.replace(".", " ").replace("_", " ").split() if part]
        if len(parts) >= 2:
            return (parts[0][0] + parts[1][0]).upper()
        return name[:2].upper() or "?"

    def avatar_palette(self):
        index = sum(ord(char) for char in self.username) % len(AVATAR_PALETTES)
        background, foreground, accent = AVATAR_PALETTES[index]
        return {"bg": background, "fg": foreground, "accent": accent}

    def is_watching_area(self):
        return self.track_area and bool((self.county or "").strip())

    def area_label(self):
        parts = [part for part in (self.county, self.constituency, self.ward) if (part or "").strip()]
        return " · ".join(parts)
