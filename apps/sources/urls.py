from django.urls import path

from . import views

app_name = "sources"

urlpatterns = [
    path("", views.SourceDocumentListView.as_view(), name="list"),
    path("<int:pk>/", views.SourceDocumentDetailView.as_view(), name="detail"),
    path("<int:pk>/file/", views.source_file, name="file"),
    path("<int:pk>/download/", views.source_download, name="download"),
]
