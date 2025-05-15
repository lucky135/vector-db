from django.contrib import admin
from django.urls import path, include

import src.api.health_api as health_api

urlpatterns = [
    path("vector-api/v1/", include("src.api.urls")),
    path("health", health_api.health),
]
