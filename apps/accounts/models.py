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


class User(AbstractUser):
    display_name = models.CharField(max_length=150, blank=True)

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"

    def __str__(self):
        return self.public_name()

    def public_name(self):
        return (self.display_name or self.get_username()).strip()

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
