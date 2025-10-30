from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError


# ----- Client model -----
class Client(models.Model):
    # Available subscription types
    SUBSCRIPTION_CHOICES = [
        ('monthly', 'Monthly'),
        ('6_month', '6 Month'),
        ('annually', 'Annually'),
        ('other', 'Other'),
    ]

    # Basic company / CEO info
    ceo_name = models.CharField(max_length=100, default='-')
    ceo_birthday = models.DateField(null=True, blank=True)
    ceo_email = models.EmailField(default='-')
    ceo_phone = models.CharField(max_length=100, default='-')
    company_name = models.CharField(max_length=100, default='-')
    employeas_number = models.IntegerField(blank=True, null=True)
    vat_nif = models.CharField(max_length=100, default='-')
    subscription_other = models.CharField(max_length=100, blank=True, null=True)

    # Contact details
    address = models.CharField(max_length=255, default='-')
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    # Subscription type (monthly / 6 months / annually / custom)
    subscription_type = models.CharField(
        max_length=20,
        choices=SUBSCRIPTION_CHOICES,
        default='monthly',
    )
    
    # Validation to ensure "other" subscriptions must have description
    def clean(self):
        if self.subscription_type == "other" and not self.subscription_other:
            raise ValidationError({"subscription_other": "Please specify the subscription type."})
        if self.subscription_type != "other":
            self.subscription_other = None

    class Meta:
        verbose_name = '"' + "Client" + '"'
        verbose_name_plural = "Clients-editing"

    def __str__(self):
        return self.company_name


# ----- Aggregated ticket summary per customer -----
class CustomerTicketSummary(models.Model):
    # Relation to client
    customer = models.ForeignKey(
        'users.Client',
        on_delete=models.SET_NULL,
        null=True,
        related_name='ticket_summaries'
    )
    # Total number of tickets
    ticket_count = models.IntegerField(default=0)


# ----- States editing model -----
class States_editing(models.Model):
    # Helper method to fetch related ticket states as dictionary
    def get_states(self):
        ticket = self.activity_ticket
        if not ticket:
            return {}

        return {
            "customer": str(ticket.customer),
            "current-state": str(ticket.current_state),
            "current-state2": str(ticket.current_state2),
            "next-state": str(ticket.next_state),
            "ticket-id": ticket.ticket_id,
            "activity-type": str(ticket.activity_type),
            "activity_type_2": str(ticket.activity_type_2),
        }
    
    # Choices for type of state
    STATES_CHOICES = [
        ('current_state', 'Current_state'),
        ('current_state2', 'Current_state2'),
        ('next_state', 'Next_state'),
    ]

    # Related ticket (main link to TicketsActivityticket)
    activity_ticket = models.ForeignKey(
        "tickets.TicketsActivityticket",
        on_delete=models.CASCADE, 
        related_name='state_editing',
        max_length=100,
        null=True,
        blank=True,
        default=None,
    )
    
    # New state value
    state = models.CharField(max_length=100, default=None)

    # What type of state we are updating (Current / Next / etc.)
    state_type = models.CharField(
        max_length=100,
        choices=STATES_CHOICES,
        default='',
    )

    class Meta:
        verbose_name = '"' + "State" + '"'
        verbose_name_plural = "States-editing"

    def __str__(self):
        return self.state
