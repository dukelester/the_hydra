from django.urls import path

from . import views

app_name = "sources"

urlpatterns = [
    path("<int:pk>/", views.SourceDocumentDetailView.as_view(), name="detail"),
]
