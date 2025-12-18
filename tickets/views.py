# tickets/views.py - Ticket Management Views with Timer and Email Integration
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.http import JsonResponse
import json
from django.contrib.auth.decorators import login_required

from .models import (
    TicketsActivityticket, TicketsCustomer, TicketsReportedby,
    TicketsActivitytype, TicketsActivitytype2, TicketsAnalystconsultant,
    TicketsCurrentstate, TicketsActivityimportance, TicketsNextstate
)


# ==============================================================================
# TICKET CREATION VIEW
# ==============================================================================
def create_ticket(request):
    """
    Handle ticket creation form submission and display.
    POST: Create new ticket and redirect to email form
    GET: Display empty ticket creation form
    """
    
    if request.method == "POST":
        # Extract form data from POST request
        reported_user = request.POST.get("reported_user")  # User who reported the issue
        activity_title = request.POST.get("activity_title")  # Title of the activity/ticket
        activity_resolution_description = request.POST.get("activity_resolution_description")  # Resolution notes

        # Get related objects from database using foreign key relationships
        # get_object_or_404 will return 404 error if object doesn't exist
        customer = get_object_or_404(TicketsCustomer, name=request.POST.get("customer"))  # Customer company
        reported_by = get_object_or_404(TicketsReportedby, name=request.POST.get("reported_by"))  # Person who reported
        activity_type = get_object_or_404(TicketsActivitytype, name=request.POST.get("activity_type"))  # Main activity type
        
        # Activity Type 2 is optional, so check if it exists before fetching
        activity_type_2 = get_object_or_404(TicketsActivitytype2, name=request.POST.get("activity_type_2")) if request.POST.get("activity_type_2") else None
        
        activity_importance = get_object_or_404(TicketsActivityimportance, name=request.POST.get("activity_importance"))  # Priority level
        analyst_consultant = get_object_or_404(TicketsAnalystconsultant, name=request.POST.get("analyst_consultant"))  # Assigned analyst
        
        # Get the selected state (must be either "Open" or "In Progress")
        current_state_name = request.POST.get("current_state")
        current_state = get_object_or_404(
            TicketsCurrentstate,
            name__in=["✎ Open", "⇶ Inprogress | OnGoing"],  # Only allow these two initial states
            name=current_state_name
        )

        # Create new ticket in database
        ticket = TicketsActivityticket.objects.create(
            sysdate=now(),  # Set creation timestamp to current time
            customer=customer,
            reported_user=reported_user,
            reported_by=reported_by,
            activity_type=activity_type,
            activity_type_2=activity_type_2,
            activity_importance=activity_importance.name,  # Store as string
            analyst_consultant=analyst_consultant,
            current_state=current_state,
            activity_title=activity_title,
            activity_resolution_description=activity_resolution_description,
        )

        # Set the ticket as its own related ticket (root of the chain)
        ticket.related_ticket = ticket
        ticket.save()

        # AUTO-START TIMER: If state is "In Progress", automatically start the timer
        if current_state_name.strip() == "⇶ Inprogress | OnGoing":
            ticket.activity_start = now()  # Set start time to now
            ticket.activity_end = None  # Ensure end time is cleared
            ticket.save(update_fields=["activity_start", "activity_end"])  # Only update these fields

        # Redirect to email form so user can send notification about the new ticket
        return redirect("ticket_email_form", ticket_id=ticket.ticket_id)

    # GET REQUEST: Display empty form with all dropdown options
    context = {
        "customers": TicketsCustomer.objects.all(),  # All available customers
        "reported_by": TicketsReportedby.objects.all(),  # All available reporters
        "activity_types": TicketsActivitytype.objects.all(),  # All activity types
        "activity_types2": TicketsActivitytype2.objects.all(),  # All secondary activity types
        "activity_importance": TicketsActivityimportance.objects.all(),  # All priority levels
        "analyst_consultant": TicketsAnalystconsultant.objects.all(),  # All analysts
        "available_states": TicketsCurrentstate.objects.filter(name__in=["✎ Open", "⇶ Inprogress | OnGoing"]),  # Only initial states
    }
    return render(request, "tickets/create_ticket.html", context)


# ==============================================================================
# TICKET LIST VIEW
# ==============================================================================
def view_tickets(request):
    """
    Display all tickets in a table with timer controls.
    Ordered by ticket_id ascending (oldest first).
    """
    # Fetch all tickets from database, ordered by ID
    tickets = TicketsActivityticket.objects.all().order_by('ticket_id')
    
    # Render the tickets table template
    return render(request, "tickets/view_tickets.html", {"tickets": tickets})


# ==============================================================================
# TICKET HISTORY DETAIL VIEW
# ==============================================================================
def ticket_detail(request, ticket_id):
    """
    Display the complete history chain for a single ticket.
    Follows the related_ticket chain backwards to show all related tickets.
    Reuses the same template as view_tickets for consistency.
    """
    # Get the main ticket or return 404 if not found
    ticket = get_object_or_404(TicketsActivityticket, ticket_id=ticket_id)
    
    # Build history chain by following related_ticket backwards
    history_chain = []  # Will store all tickets in the chain
    current = ticket  # Start with the requested ticket
    visited_ids = set()  # Track visited IDs to prevent infinite loops
    
    # Walk backwards through the chain to find the root ticket
    while current and current.ticket_id not in visited_ids:
        visited_ids.add(current.ticket_id)  # Mark this ticket as visited
        history_chain.append(current)  # Add to chain
        
        # Check if there's a related ticket that's different from current
        if current.related_ticket and current.related_ticket.ticket_id != current.ticket_id:
            current = current.related_ticket  # Move to the related ticket
        else:
            break  # No more related tickets, stop
    
    # Reverse the chain to show chronological order (oldest first)
    history_chain.reverse()
    
    # Reuse the view_tickets template with the filtered history chain
    return render(request, "tickets/view_tickets.html", {
        "tickets": history_chain,  # Pass the history chain instead of all tickets
        "viewing_history": True,  # Flag to indicate we're viewing history
        "main_ticket": ticket,  # Pass the main ticket for reference
    })


# ==============================================================================
# STATE TRANSITION MAPPINGS
# ==============================================================================

# STATE_MAPPING: Defines automatic state transitions when a ticket is updated
# Key: Current state name
# Value: Next state to create a new ticket with
STATE_MAPPING = {
    "✉ Reported to Customer": "⌚ Pending Customer",  # When reported to customer, create pending ticket
    "✉ Reported to 3rd PartyID": "⌛ Pending 3rd Party",  # When reported to 3rd party, create pending ticket
    "☼ Pending analysis": "⇶ Inprogress | OnGoing",  # When analysis pending, move to in progress
    "Incomplete (Pending)": "⇶ Inprogress | OnGoing",  # When incomplete, move to in progress
    "📅 Scheduled": "📅 Scheduled",  # Scheduled stays scheduled
    "⇶ Inprogress | OnGoing": ["✉ Reported to Customer","✉ Reported to 3rd PartyID", "☼ Pending analysis"]  # Multiple possible next states
}

# NON_EDITABLE_STATES: Tickets in these states cannot be edited (final or external states)
NON_EDITABLE_STATES = [
    "✉ Reported to Customer",  # Waiting for customer response
    "🆗 Delivered Recommendation",  # Recommendation delivered
    "✉ Reported to 3rd PartyID",  # Waiting for 3rd party response
    "✂ Cancelled",  # Ticket cancelled
    "🆗 Solved",  # Ticket solved (final state)
]

# EMAIL_TRIGGER_STATES: Transitioning to these states should trigger email notification
EMAIL_TRIGGER_STATES = [
    "✉ Reported to Customer",  # Send email to customer
    "✉ Reported to 3rd PartyID",  # Send email to 3rd party
    "☼ Pending analysis",  # Notify about pending analysis
    "Incomplete (Pending)",  # Notify about incomplete ticket
    "📅 Scheduled",  # Notify about scheduled work
    "🆗 Delivered Recommendation",  # Send recommendation email
    "🆗 Solved",  # Send resolution email
]


# ==============================================================================
# TICKET EDITING VIEW
# ==============================================================================
def edit_ticket(request, ticket_id):
    """
    Handle ticket editing with dynamic fields based on activity type.
    Supports state transitions and automatic creation of related tickets.
    """
    # Get the ticket to edit or return 404
    ticket = get_object_or_404(TicketsActivityticket, pk=ticket_id)

    # Check if the ticket is in a non-editable state
    if ticket.current_state:
        current_state_name = ticket.current_state.name.strip()
        if current_state_name in NON_EDITABLE_STATES:
            # Show warning message and redirect back to ticket list
            messages.warning(
                request,
                f"Ticket #{ticket_id} current state '{current_state_name}' cannot be edited."
            )
            return redirect("view_tickets")

    # TEMPLATE_FIELDS: Define which fields to show based on activity type
    # Each activity type has specific fields relevant to that type of work
    template_fields = {
        "♣ Development": ["observations", "development_details", "details_evidences"],
        "♦ Release Deployment": ["observations", "development_details", "details_evidences"],
        "Project": ["observations", "development_details", "details_evidences"],
        "Maintenance Activity": ["observations", "analysis_resolution_details", "recommendations", "details_evidences"],
        "☛ Solicitation": ["observations", "resolution_details", "recommendations", "details_evidences"],
        "⚠️ Incident": ["observations", "analysis", "root_cause", "resolution_details", "recommendations", "details_evidences"],
        "☠ Trouble Ticket": ["error_description", "resolution_investigation_details", "recommendations", "details_evidences"],
    }

    # Get the activity type name and determine which fields to show
    activity_type_name = ticket.activity_type.name if ticket.activity_type else ""
    fields_to_show = template_fields.get(activity_type_name, [])  # Get fields or empty list if not found

    if request.method == "POST":
        # STEP 1: Validate and get the new analyst
        analyst_id = request.POST.get("analyst_consultant")
        if not analyst_id:
            messages.error(request, "Analyst Consultant is mandatory.")
            return redirect("edit_ticket", ticket_id=ticket_id)

        try:
            new_ticket_analyst = TicketsAnalystconsultant.objects.get(pk=analyst_id)
        except TicketsAnalystconsultant.DoesNotExist:
            messages.error(request, "Analyst Consultant not found.")
            return redirect("edit_ticket", ticket_id=ticket_id)

        # STEP 2: Get and validate the new state
        new_state_name = request.POST.get("new_state")
        new_state_obj = None
        if new_state_name:
            new_state_name = new_state_name.strip()
            try:
                new_state_obj = TicketsCurrentstate.objects.get(name=new_state_name)
            except TicketsCurrentstate.DoesNotExist:
                messages.error(request, f"State '{new_state_name}' not found")
                return redirect("edit_ticket", ticket_id=ticket_id)

        # STEP 3: Update dynamic fields based on activity type
        resolution_parts = []  # Will build the complete resolution description
        for field in fields_to_show:
            value = request.POST.get(field, "")  # Get field value from form
            setattr(ticket, field, value)  # Set the field on the ticket object
            if value.strip():  # Only include non-empty fields
                # Format: "Field Name: value"
                resolution_parts.append(f"{field.replace('_', ' ').title()}: {value}")

        # Combine all resolution parts into a single description
        ticket.activity_resolution_description = "\n\n".join(resolution_parts)

        # STEP 4: Update analyst and state on the ticket
        ticket.analyst_consultant = new_ticket_analyst
        if new_state_obj:
            ticket.current_state = new_state_obj

        ticket.save()  # Save all changes to database

        # STEP 5: Create a new related ticket if state is in STATE_MAPPING
        if new_state_name and new_state_name in STATE_MAPPING:
            next_state_name = STATE_MAPPING[new_state_name].strip()
            try:
                next_state_obj = TicketsCurrentstate.objects.get(name=next_state_name)
                # Create a new ticket with the next state, linked to current ticket
                new_ticket = TicketsActivityticket.objects.create(
                    sysdate=now(),  # Current timestamp
                    customer=ticket.customer,  # Same customer
                    reported_user=ticket.reported_user,  # Same reported user
                    reported_by=ticket.reported_by,  # Same reporter
                    activity_type=ticket.activity_type,  # Same activity type
                    activity_type_2=getattr(ticket, 'activity_type_2', None),  # Same secondary type if exists
                    activity_importance=ticket.activity_importance,  # Same priority
                    analyst_consultant=new_ticket_analyst,  # New analyst
                    current_state=next_state_obj,  # New state
                    activity_title=ticket.activity_title,  # Same title
                    activity_resolution_description=ticket.activity_resolution_description,  # Copy resolution
                    related_ticket=ticket  # Link to current ticket
                )
                messages.success(
                    request,
                    f"Ticket #{ticket_id} updated and new ticket #{new_ticket.ticket_id} created with state '{next_state_name}'"
                )
            except TicketsCurrentstate.DoesNotExist:
                messages.warning(request, f"Next ticket state '{next_state_name}' not found. New ticket not created.")

        # STEP 6: Redirect to email form if state requires email notification
        if ticket.current_state and ticket.current_state.name in EMAIL_TRIGGER_STATES:
            messages.info(request, f"Ticket #{ticket_id} updated — please confirm and send the email.")
            return redirect('ticket_email_form', ticket_id=ticket_id)

        # STEP 7: Default success message and redirect to ticket list
        messages.success(request, f"Ticket #{ticket_id} updated successfully.")
        return redirect("view_tickets")

    # GET REQUEST: Display edit form
    analysts = TicketsAnalystconsultant.objects.all()  # Get all available analysts
    return render(request, "tickets/edit_ticket.html", {
        "ticket": ticket,  # Current ticket data
        "fields_to_show": fields_to_show,  # Dynamic fields based on activity type
        "new_states": TicketsNextstate.objects.all(),  # Available next states
        "analysts": analysts,  # All analysts for dropdown
    })


# ==============================================================================
# TIMER START ENDPOINT (API)
# ==============================================================================
@require_POST  # Only accept POST requests
@csrf_protect  # CSRF protection enabled
def start_timer(request, ticket_id):
    """
    API endpoint to start the activity timer for a ticket.
    Sets activity_start to current time.
    Returns JSON response with status and timestamp.
    """
    try:
        # Get the ticket from database
        ticket = TicketsActivityticket.objects.get(pk=ticket_id)

        # VALIDATION 1: Check if timer already finished (has end time)
        if ticket.activity_end is not None:
            return JsonResponse({
                "error": "Impossible to restart a timer already finished. The cycle is complete."
            }, status=400)

        # VALIDATION 2: Check if timer is already running (has start but no end)
        if ticket.activity_start is not None:
            return JsonResponse({
                "error": "The timer is already running."
            }, status=400)

        # VALIDATION 3: Check if ticket is in a final state (cannot start timer)
        if ticket.current_state and ticket.current_state.name in ["🆗 Solved", "🆗 Delivered Recommendation", "✂ Cancelled"]:
            return JsonResponse({
                "error": "Impossible to start the timer. The ticket is in a final state."
            }, status=400)

        # All validations passed - START THE TIMER
        ticket.activity_start = now()  # Set start time to current datetime
        ticket.activity_end = None  # Make sure end time is cleared
        ticket.save(update_fields=["activity_start", "activity_end"])  # Save only these fields

        # Return success response with timestamp
        return JsonResponse({
            "status": "success",
            "activity_start": ticket.activity_start.strftime("%Y-%m-%d %H:%M:%S"),  # Format timestamp
            "message": f"Timer started for ticket {ticket_id}"
        })

    except TicketsActivityticket.DoesNotExist:
        # Ticket not found in database
        return JsonResponse({"error": "Ticket not found"}, status=404)
    except Exception as e:
        # Catch any other unexpected errors
        return JsonResponse({"error": str(e)}, status=500)


# ==============================================================================
# TIMER STOP ENDPOINT (API)
# ==============================================================================
@require_POST  # Only accept POST requests
@csrf_protect  # CSRF protection enabled
def stop_timer(request, ticket_id):
    """
    API endpoint to stop the activity timer for a ticket.
    Calculates elapsed time and updates time_spent.
    Optionally updates ticket state.
    Returns JSON response with status, timestamps, and total time.
    """
    try:
        # Get the ticket from database
        ticket = get_object_or_404(TicketsActivityticket, pk=ticket_id)

        # VALIDATION 1: Check that timer has been started
        if ticket.activity_start is None:
            return JsonResponse({
                "error": "The timer has not been started."
            }, status=400)

        # VALIDATION 2: Check that timer is not already stopped
        if ticket.activity_end is not None:
            return JsonResponse({
                "error": "The timer is already stopped."
            }, status=400)

        # Try to read optional new state from request body (JSON)
        try:
            data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            data = {}  # If JSON parsing fails, use empty dict

        # Update state if provided in request
        new_state_name = data.get("current_state")
        if new_state_name:
            try:
                ticket.current_state = TicketsCurrentstate.objects.get(name=new_state_name)
            except TicketsCurrentstate.DoesNotExist:
                pass  # Ignore if state not found, just don't update it

        # STOP THE TIMER
        ticket.activity_end = now()  # Set end time to current datetime

        # CALCULATE ELAPSED TIME
        if ticket.activity_start:
            # Calculate difference in hours
            delta_h = (ticket.activity_end - ticket.activity_start).total_seconds() / 3600
            # Add to existing time_spent (cumulative)
            prev = float(ticket.time_spent or 0)
            ticket.time_spent = round(prev + delta_h, 2)  # Round to 2 decimal places
        else:
            # If no start time (shouldn't happen), just keep existing time
            ticket.time_spent = float(ticket.time_spent or 0)

        # Save all changes to database
        ticket.save(update_fields=["activity_end", "activity_start", "current_state", "time_spent"])

        # Return success response with all data
        return JsonResponse({
            "status": "success",
            "activity_end": ticket.activity_end.strftime("%Y-%m-%d %H:%M:%S"),  # Format end timestamp
            "current_state": ticket.current_state.name if ticket.current_state else None,  # Current state name
            "time_spent": float(ticket.time_spent) if ticket.time_spent is not None else 0.0,  # Total time in hours
            "message": f"Timer stopped for ticket {ticket_id}"
        })

    except TicketsActivityticket.DoesNotExist:
        # Ticket not found in database
        return JsonResponse({"error": "Ticket not found"}, status=404)
    except Exception as e:
        # Catch any other unexpected errors
        print(f"ERROR in stop_timer: {e}")  # Log error to console
        return JsonResponse({"error": str(e)}, status=500)