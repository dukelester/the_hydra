from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "TheHydra administration"
admin.site.site_title = "TheHydra admin"
admin.site.index_title = "Evidence, projects, and reports"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("config.api_urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("projects/", include("apps.projects.urls")),
    path("institutions/", include("apps.projects.institution_urls")),
    path("sources/", include("apps.sources.urls")),
    path("investigations/", include("apps.investigations.urls")),
    path("reports/", include("apps.reports.urls")),
    path("policies/", include("apps.policies.urls")),
    path("", include("apps.core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
