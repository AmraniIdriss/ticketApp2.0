from django.urls import path
from . import views
from emails.views import ticket_email_form

urlpatterns = [
    path("create-ticket/", views.create_ticket, name="create_ticket"),
    path('view_tickets/', views.view_tickets, name='view_tickets'),
    path('edit/<int:ticket_id>/', views.edit_ticket, name='edit_ticket'),
    # URLs pour le timer
    path("<int:ticket_id>/stop/", views.stop_timer, name="stop_timer"),
    path("<int:ticket_id>/start/", views.start_timer, name="start_timer"),
    path('create-ticket-email/<int:ticket_id>/', ticket_email_form, name='ticket_email_form'),
    
]
