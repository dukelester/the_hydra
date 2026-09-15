from django.urls import path

from . import views

app_name = "sources"

urlpatterns = [
    path("", views.SourceDocumentListView.as_view(), name="list"),
    path("<uuid:pk>/", views.SourceDocumentDetailView.as_view(), name="detail"),
    path("<uuid:pk>/file/", views.source_file, name="file"),
    path("<uuid:pk>/download/", views.source_download, name="download"),
]
