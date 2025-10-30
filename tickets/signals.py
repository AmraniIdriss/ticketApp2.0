from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Count

from tickets.models import TicketsActivityticket
from users.models import CustomerTicketSummary

def update_ticket_summary():
    """Recalculate ticket counts for all clients."""
    # Clear old summaries
    CustomerTicketSummary.objects.all().delete()

    # Count tickets per client
    ticket_counts = (
        TicketsActivityticket.objects.values('customer_id')
        .annotate(ticket_count=Count('ticket_id'))
    )

    # Create new summary rows
    new_rows = [
        CustomerTicketSummary(customer_id=item['customer_id'], ticket_count=item['ticket_count'])
        for item in ticket_counts if item['customer_id'] is not None
    ]
    CustomerTicketSummary.objects.bulk_create(new_rows)

@receiver(post_save, sender=TicketsActivityticket)
@receiver(post_delete, sender=TicketsActivityticket)

def tickets_activity_change(sender, instance, **kwargs):
    update_ticket_summary()

