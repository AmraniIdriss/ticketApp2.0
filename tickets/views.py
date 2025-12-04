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



# -----------------------
# Ticket creation
# -----------------------
def create_ticket(request):
    if request.method == "POST":
        reported_user = request.POST.get("reported_user")
        activity_title = request.POST.get("activity_title")
        activity_resolution_description = request.POST.get("activity_resolution_description")

        customer = get_object_or_404(TicketsCustomer, name=request.POST.get("customer"))
        reported_by = get_object_or_404(TicketsReportedby, name=request.POST.get("reported_by"))
        activity_type = get_object_or_404(TicketsActivitytype, name=request.POST.get("activity_type"))
        activity_type_2 = get_object_or_404(TicketsActivitytype2, name=request.POST.get("activity_type_2")) if request.POST.get("activity_type_2") else None
        activity_importance = get_object_or_404(TicketsActivityimportance, name=request.POST.get("activity_importance"))
        analyst_consultant = get_object_or_404(TicketsAnalystconsultant, name=request.POST.get("analyst_consultant"))
        

        current_state_name = request.POST.get("current_state")
        current_state = get_object_or_404(
            TicketsCurrentstate,
            name__in=["✎ Open", "⇶ Inprogress | OnGoing"],
            name=current_state_name
        )

        ticket = TicketsActivityticket.objects.create(
            sysdate=now(),
            customer=customer,
            reported_user=reported_user,
            reported_by=reported_by,
            activity_type=activity_type,
            activity_type_2=activity_type_2,
            activity_importance=activity_importance.name,
            analyst_consultant=analyst_consultant,
            current_state=current_state,
            activity_title=activity_title,
            activity_resolution_description=activity_resolution_description,
        )

        ticket.related_ticket = ticket
        ticket.save()

        # 🔹 Redireciona para a página de envio de email com o ticket_id
        # 🚀 Démarre le timer automatiquement si l'état est "⇶ Inprogress | OnGoing"
        if current_state_name.strip() == "⇶ Inprogress | OnGoing":
          ticket.activity_start = now()
          ticket.activity_end = None
          ticket.save(update_fields=["activity_start", "activity_end"])

        return redirect("ticket_email_form", ticket_id=ticket.ticket_id)

    # Se for GET, apenas renderiza a página de criação
    context = {
        "customers": TicketsCustomer.objects.all(),
        "reported_by": TicketsReportedby.objects.all(),
        "activity_types": TicketsActivitytype.objects.all(),
        "activity_types2": TicketsActivitytype2.objects.all(),
        "activity_importance": TicketsActivityimportance.objects.all(),
        "analyst_consultant": TicketsAnalystconsultant.objects.all(),
        "available_states": TicketsCurrentstate.objects.filter(name__in=["✎ Open", "⇶ Inprogress | OnGoing"]),
    }
    return render(request, "tickets/create_ticket.html", context)


# -----------------------
# Ticket list
# -----------------------
def view_tickets(request):
    tickets = TicketsActivityticket.objects.all().order_by('ticket_id')
    return render(request, "tickets/view_tickets.html", {"tickets": tickets})


# -----------------------
# Ticket detail (history chain)
# -----------------------
def ticket_detail(request, ticket_id):
    """
    Display ticket history chain using the same structure as view_tickets.
    Reuses the exact same template and JavaScript.
    """
    ticket = get_object_or_404(TicketsActivityticket, ticket_id=ticket_id)
    
    # Build history chain by following related_ticket backwards
    history_chain = []
    current = ticket
    visited_ids = set()
    
    # Walk backwards to find root
    while current and current.ticket_id not in visited_ids:
        visited_ids.add(current.ticket_id)
        history_chain.append(current)
        
        if current.related_ticket and current.related_ticket.ticket_id != current.ticket_id:
            current = current.related_ticket
        else:
            break
    
    # Reverse to show oldest first (chronological order)
    history_chain.reverse()
    
    # Reuse view_tickets template with filtered tickets
    return render(request, "tickets/view_tickets.html", {
        "tickets": history_chain,
        "viewing_history": True,
        "main_ticket": ticket,
    })


# -----------------------
# States & triggers
# -----------------------
STATE_MAPPING = {
    "✉ Reported to Customer": "⌚ Pending Customer",
    "✉ Reported to 3rd PartyID": "⌛ Pending 3rd Party",
    "☼ Pending analysis": "⇶ Inprogress | OnGoing",
    "Incomplete (Pending)": "⇶ Inprogress | OnGoing",
    "📅 Scheduled": "📅 Scheduled",
    "⇶ Inprogress | OnGoing": ["✉ Reported to Customer","✉ Reported to 3rd PartyID", "☼ Pending analysis" ]
}

NON_EDITABLE_STATES = [
    "✉ Reported to Customer",
    "🆗 Delivered Recommendation",
    "✉ Reported to 3rd PartyID",
    "✂ Cancelled",
    "🆗 Solved",
]

EMAIL_TRIGGER_STATES = [
    "✉ Reported to Customer",
    "✉ Reported to 3rd PartyID",
    "☼ Pending analysis",
    "Incomplete (Pending)",
    "📅 Scheduled",
    "🆗 Delivered Recommendation",
    "🆗 Solved",
]

# -----------------------
# Ticket editing
# -----------------------
def edit_ticket(request, ticket_id):
    ticket = get_object_or_404(TicketsActivityticket, pk=ticket_id)

    # Check if the ticket is in a non-editable state
    if ticket.current_state:
        current_state_name = ticket.current_state.name.strip()
        if current_state_name in NON_EDITABLE_STATES:
            messages.warning(
                request,
                f"Ticket #{ticket_id} current state '{current_state_name}' cannot be edited."
            )
            return redirect("view_tickets")

    # Dynamic fields by activity type
    template_fields = {
        "♣ Development": ["observations", "development_details", "details_evidences"],
        "♦ Release Deployment": ["observations", "development_details", "details_evidences"],
        "Project": ["observations", "development_details", "details_evidences"],
        "Maintenance Activity": ["observations", "analysis_resolution_details", "recommendations", "details_evidences"],
        "☛ Solicitation": ["observations", "resolution_details", "recommendations", "details_evidences"],
        "⚠️ Incident": ["observations", "analysis", "root_cause", "resolution_details", "recommendations", "details_evidences"],
        "☠ Trouble Ticket": ["error_description", "resolution_investigation_details", "recommendations", "details_evidences"],
    }

    activity_type_name = ticket.activity_type.name if ticket.activity_type else ""
    fields_to_show = template_fields.get(activity_type_name, [])

    if request.method == "POST":
        # 1️⃣ Validate new analyst
        analyst_id = request.POST.get("analyst_consultant")
        if not analyst_id:
            messages.error(request, "Analyst Consultant is mandatory.")
            return redirect("edit_ticket", ticket_id=ticket_id)

        try:
            new_ticket_analyst = TicketsAnalystconsultant.objects.get(pk=analyst_id)
        except TicketsAnalystconsultant.DoesNotExist:
            messages.error(request, "Analyst Consultant not found.")
            return redirect("edit_ticket", ticket_id=ticket_id)

        # 2️⃣ Get new state
        new_state_name = request.POST.get("new_state")
        new_state_obj = None
        if new_state_name:
            new_state_name = new_state_name.strip()
            try:
                new_state_obj = TicketsCurrentstate.objects.get(name=new_state_name)
            except TicketsCurrentstate.DoesNotExist:
                messages.error(request, f"State '{new_state_name}' not found")
                return redirect("edit_ticket", ticket_id=ticket_id)

        # 3️⃣ Update dynamic fields
        resolution_parts = []
        for field in fields_to_show:
            value = request.POST.get(field, "")
            setattr(ticket, field, value)
            if value.strip():
                resolution_parts.append(f"{field.replace('_', ' ').title()}: {value}")

        ticket.activity_resolution_description = "\n\n".join(resolution_parts)

        # 4️⃣ Update analyst and state
        ticket.analyst_consultant = new_ticket_analyst
        if new_state_obj:
            ticket.current_state = new_state_obj

        ticket.save()

        # 5️⃣ Create a new ticket if the state is in STATE_MAPPING
        if new_state_name and new_state_name in STATE_MAPPING:
            next_state_name = STATE_MAPPING[new_state_name].strip()
            try:
                next_state_obj = TicketsCurrentstate.objects.get(name=next_state_name)
                new_ticket = TicketsActivityticket.objects.create(
                    sysdate=now(),
                    customer=ticket.customer,
                    reported_user=ticket.reported_user,
                    reported_by=ticket.reported_by,
                    activity_type=ticket.activity_type,
                    activity_type_2=getattr(ticket, 'activity_type_2', None),
                    activity_importance=ticket.activity_importance,
                    analyst_consultant=new_ticket_analyst,
                    current_state=next_state_obj,
                    activity_title=ticket.activity_title,
                    activity_resolution_description=ticket.activity_resolution_description,
                    related_ticket=ticket
                )
                messages.success(
                    request,
                    f"Ticket #{ticket_id} updated and new ticket #{new_ticket.ticket_id} created with state '{next_state_name}'"
                )
            except TicketsCurrentstate.DoesNotExist:
                messages.warning(request, f"Next ticket state '{next_state_name}' not found. New ticket not created.")

        # 6️⃣ Redirect to email form if necessary
        if ticket.current_state and ticket.current_state.name in EMAIL_TRIGGER_STATES:
            messages.info(request, f"Ticket #{ticket_id} updated — please confirm and send the email.")
            return redirect('ticket_email_form', ticket_id=ticket_id)

        # 7️⃣ Default success message
        messages.success(request, f"Ticket #{ticket_id} updated successfully.")
        return redirect("view_tickets")

    # GET → render form
    analysts = TicketsAnalystconsultant.objects.all()
    return render(request, "tickets/edit_ticket.html", {
        "ticket": ticket,
        "fields_to_show": fields_to_show,
        "new_states": TicketsNextstate.objects.all(),
        "analysts": analysts,
    })

# -----------------------
# Timer : START
# -----------------------
@require_POST
@csrf_protect
def start_timer(request, ticket_id):
    try:
        ticket = TicketsActivityticket.objects.get(pk=ticket_id)

        # Check if the ticket already has an activity_end (cycle finished)
        if ticket.activity_end is not None:
            return JsonResponse({
                "error": "Impossible to restart a timer already finished. The cycle is complete."
            }, status=400)

        # Check if the timer is already running (start exists but no end)
        if ticket.activity_start is not None:
            return JsonResponse({
                "error": "The timer is already running."
            }, status=400)

        # Check the ticket state
        if ticket.current_state and ticket.current_state.name in ["🆗 Solved", "🆗 Delivered Recommendation", "✂ Cancelled"]:
            return JsonResponse({
                "error": "Impossible to start the timer. The ticket is in a final state."
            }, status=400)

        # Start the timer
        ticket.activity_start = now()
        ticket.activity_end = None  # Make sure there is no end
        ticket.save(update_fields=["activity_start", "activity_end"])

        return JsonResponse({
            "status": "success",
            "activity_start": ticket.activity_start.strftime("%Y-%m-%d %H:%M:%S"),
            "message": f"Timer started for ticket {ticket_id}"
        })

    except TicketsActivityticket.DoesNotExist:
        return JsonResponse({"error": "Ticket not found"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# -----------------------
# Timer : STOP
# -----------------------
@require_POST
@csrf_protect
def stop_timer(request, ticket_id):
    try:
        ticket = get_object_or_404(TicketsActivityticket, pk=ticket_id)

        # Check that the timer has been started
        if ticket.activity_start is None:
            return JsonResponse({
                "error": "The timer has not been started."
            }, status=400)

        # Check that the timer is not already stopped
        if ticket.activity_end is not None:
            return JsonResponse({
                "error": "The timer is already stopped."
            }, status=400)

        # Read a possible new state
        try:
            data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            data = {}

        new_state_name = data.get("current_state")
        if new_state_name:
            try:
                ticket.current_state = TicketsCurrentstate.objects.get(name=new_state_name)
            except TicketsCurrentstate.DoesNotExist:
                pass

        # Stop the timer
        ticket.activity_end = now()

        # Calculate elapsed time
        if ticket.activity_start:
            delta_h = (ticket.activity_end - ticket.activity_start).total_seconds() / 3600
            prev = float(ticket.time_spent or 0)
            ticket.time_spent = round(prev + delta_h, 2)
        else:
            ticket.time_spent = float(ticket.time_spent or 0)

        ticket.save(update_fields=["activity_end", "activity_start", "current_state", "time_spent"])

        return JsonResponse({
            "status": "success",
            "activity_end": ticket.activity_end.strftime("%Y-%m-%d %H:%M:%S"),
            "current_state": ticket.current_state.name if ticket.current_state else None,
            "time_spent": float(ticket.time_spent) if ticket.time_spent is not None else 0.0,
            "message": f"Timer stopped for ticket {ticket_id}"
        })

    except TicketsActivityticket.DoesNotExist:
        return JsonResponse({"error": "Ticket not found"}, status=404)
    except Exception as e:
        print(f"ERROR in stop_timer: {e}")
        return JsonResponse({"error": str(e)}, status=500)