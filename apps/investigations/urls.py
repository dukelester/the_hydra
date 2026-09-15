from django.urls import path

from . import views

app_name = "investigations"

urlpatterns = [
    path("", views.MyInvestigationsView.as_view(), name="list"),
    path("<uuid:pk>/", views.investigation_detail, name="detail"),
]
