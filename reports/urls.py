from django.urls import path, include
from . import views

urlpatterns = [
    path('',views.home_reports, name='home_reports'),
    path('api/echarts/by-analyst/', views.api_echarts_tickets_by_analyst, name='api_echarts_by_analyst'),


]


