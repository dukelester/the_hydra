from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("how-it-works/", views.HowItWorksView.as_view(), name="how-it-works"),
    path("what-hydra-means/", views.WhatHydraMeansView.as_view(), name="what-hydra-means"),
    path("terms/", views.TermsView.as_view(), name="terms"),
    path("search/", views.search_view, name="search"),
    path("search/suggest/", views.search_suggest, name="search-suggest"),
]
