from django.utils.text import slugify


def unique_slug(instance, value, slug_field="slug"):
    """Generate a unique slug for a model instance."""
    base = slugify(value) or "item"
    slug = base
    model = instance.__class__
    counter = 2
    queryset = model.objects.all()
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    while queryset.filter(**{slug_field: slug}).exists():
        slug = f"{base}-{counter}"
        counter += 1
    return slug
