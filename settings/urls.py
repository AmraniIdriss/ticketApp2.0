from django.urls import path
from .views import settings_page

# Namespace = "settings"
app_name = "settings"

urlpatterns = [
    path("", settings_page, name="index"),   # -> nom complet: "settings:index"
]
