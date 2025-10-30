from django.core.management.base import BaseCommand
from tickets.models import TicketsActivityticket, TicketsSummary

class Command(BaseCommand):
    help = "Copy first 3 tickets to TicketsSummary"

    def handle(self, *args, **kwargs):
        tickets = TicketsActivityticket.objects.all()[:3]
        new_rows = [
            TicketsSummary(ticket_id=ticket.ticket_id, customer=ticket.customer)
            for ticket in tickets
        ]
        TicketsSummary.objects.bulk_create(new_rows)
        self.stdout.write(self.style.SUCCESS('Successfully copied tickets.'))