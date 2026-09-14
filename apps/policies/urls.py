from django.urls import path

from . import views

app_name = "policies"

urlpatterns = [
    path("", views.PolicyListView.as_view(), name="list"),
    path("<slug:slug>/", views.PolicyDetailView.as_view(), name="detail"),
]
