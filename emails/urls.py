from django.urls import path
from . import views

urlpatterns = [
    
    path('create-ticket-email/<int:ticket_id>/', views.ticket_email_form, name='ticket_email_form'),
    
]
