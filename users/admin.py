from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from django.db.models import Count, Q
from django.utils import timezone

from .models import Client, States_editing
from django.shortcuts import redirect
from django.urls import reverse


# ----- Custom filter -----
class TicketsCountFilter(SimpleListFilter):
    # Title that will be shown in the Django admin filter sidebar
    title = "Tickets"
    # The parameter name used in the URL query string
    parameter_name = "tickets_period"

    # Override choices to display custom filter options in the admin
    def choices(self, changelist):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,  # mark selected option
                'query_string': changelist.get_query_string({self.parameter_name: lookup}),  # build query string
                'display': title,  # display name in the admin filter
            }

    # Define the available options for the filter
    def lookups(self, request, model_admin):
        return [
            ("this_month", "This month"),  # filter for tickets created this month
            ("this_year", "This year"),    # filter for tickets created this year
        ]

    # Apply the filtering logic based on the selected option
    def queryset(self, request, queryset):
        now = timezone.now()

        if self.value() == "this_month":
            # Annotate each object with a count of tickets created this month
            return queryset.annotate(
                tickets_count=Count(
                    'tickets_customers__activitytickets',
                    filter=Q(
                        tickets_customers__activitytickets__sysdate__year=now.year,
                        tickets_customers__activitytickets__sysdate__month=now.month
                    )
                )
            ).order_by('-tickets_count')  # order by descending count

        if self.value() == "this_year":
            # Annotate each object with a count of tickets created this year
            return queryset.annotate(
                tickets_count=Count(
                    'tickets_customers__activitytickets',
                    filter=Q(
                        tickets_customers__activitytickets__sysdate__year=now.year
                    )
                )
            ).order_by('-tickets_count')

        # If no filter is selected, return the original queryset
        return queryset



# ----- Client Admin -----
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    # Fields that will be shown in the list view of Django Admin
    list_display = (
        "company_name",
        "address",
        "email",
        "phone",
        "subscription_type",
        "tickets_this_month",   # number of tickets created this month
        "tickets_this_year",    # number of tickets created this year
        # Pedro also asked for 2 more fields:
        # 1. Total spent time for tickets solved remotely
        # 2. Total spent time for tickets solved on client’s side
    )

    # Searchable fields in the admin search bar
    search_fields = ("company_name", "email", "subscription_type")

    # Filters available in the right sidebar of Django Admin
    list_filter = (TicketsCountFilter,)

    # By default, the "This Month" filter is applied when opening the client list
    def changelist_view(self, request, extra_context=None):
        if "tickets_period" not in request.GET:
            return redirect(
                f"{reverse('admin:users_client_changelist')}?tickets_period=this_month"
            )
        return super().changelist_view(request, extra_context)

    # Method to display ticket count for the current month
    def tickets_this_month(self, obj):
        return getattr(obj, 'tickets_count', None) or 0
    tickets_this_month.short_description = "Tickets (this month)"

    # Method to display ticket count for the current year
    def tickets_this_year(self, obj):
        return getattr(obj, 'tickets_count', None) or 0
    tickets_this_year.short_description = "Tickets (this year)"


@admin.register(States_editing)
class StatesEditingAdmin(admin.ModelAdmin):
    # Fields to display in the list view of States_editing model
    list_display = (
        'get_ticket_id',        # related ticket ID
        'get_customer',         # related customer name
        'get_current_state',    # current state of the ticket
        'get_current_state2',   # secondary current state of the ticket
        'get_next_state',       # next state of the ticket
        'state_type',           # type of state being edited
        'state',                # actual state value
    )

    # Custom method to display ticket ID from related activity_ticket
    def get_ticket_id(self, obj):
        return obj.activity_ticket.ticket_id if obj.activity_ticket else None
    get_ticket_id.short_description = 'Ticket ID'

    # Custom method to display customer name from related activity_ticket
    def get_customer(self, obj):
        return obj.activity_ticket.customer.name if obj.activity_ticket else None
    get_customer.short_description = 'Customer'

    # Custom method to display current state
    def get_current_state(self, obj):
        return obj.activity_ticket.current_state if obj.activity_ticket else None
    get_current_state.short_description = 'Current State'

    # Custom method to display secondary current state
    def get_current_state2(self, obj):
        return obj.activity_ticket.current_state2 if obj.activity_ticket else None
    get_current_state2.short_description = 'Current State 2'

    # Custom method to display next state
    def get_next_state(self, obj):
        return obj.activity_ticket.next_state if obj.activity_ticket else None
    get_next_state.short_description = 'Next State'

    # 🔹 Override save_model to automatically update the linked ticket when saving a States_editing instance. IT DOESN'T WORK and I don't know why...
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if obj.activity_ticket:  # ensure the ticket exists before updating
            if obj.state_type == "Current_state":
                obj.activity_ticket.current_state = obj.state
            elif obj.state_type == "Current_state2":
                obj.activity_ticket.current_state2 = obj.state
            elif obj.state_type == "Next_state":
                obj.activity_ticket.next_state = obj.state

            obj.activity_ticket.save()  # persist changes to the related ticket
