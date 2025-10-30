# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from tickets.models import TicketsActivityticket

from tickets.models import (
    TicketsActivityticket,
    TicketsActivitytype,
    TicketsReportedby,
    TicketsCurrentstate,
    TicketsAnalystconsultant, 
    TicketsActivityimportance,
    )

from django.db.models import Count



# ============================
# REGISTER VIEW
# ============================
def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        # Check if username already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username já existe!")
        else:
            # Create a new user
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, "Conta criada com sucesso!")
            return redirect('login')  # redirect to login page

    return render(request, 'users/register.html')


# ============================
# LOGIN VIEW
# ============================
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # Authenticate user
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('/')  # Home page after login
        else:
            messages.error(request, "Username ou password inválido!")

    return render(request, 'users/login.html')


# ============================
# LOGOUT VIEW
# ============================
def logout_view(request):
    # Log out the user
    logout(request)
    return redirect('login')


# ============================
# HOME PAGE VIEW
# ============================

@login_required(login_url='login')
def home_view(request):
    
    # Configuration of states with prefix keys for context
    states_config = [
        {"name": "✎ Open", "prefix": "open"},
        {"name": "⇶ Inprogress | OnGoing", "prefix": "inprogress_ongoing"},
        {"name": "⌚ Pending Customer", "prefix": "pending_customer"},
        {"name": "⌛ Pending 3rd Party", "prefix": "pending_3rd_party"},
        {"name": "🆗 Solved", "prefix": "solved"}, 
        {"name": "☼ Pending analysis", "prefix": "pending_analysis"},
        {"name": "Incomplete (Pending)", "prefix": "incomplete_pending"},  
        {"name": "🆗 Delivered Recommendation", "prefix": "delivery_recommendation"},
        {"name": "📅 Scheduled", "prefix": "scheduled"},
        {"name": "↻ Re-Opened", "prefix": "re_opened"},
    ]
    
    # Base context with all activity types, reported by, states, importance, and related tickets
    context = {
        "activity_types": TicketsActivitytype.objects.all(),
        "reported_by": TicketsReportedby.objects.all(),
        "current_state": TicketsCurrentstate.objects.all(),
        "activity_importance": TicketsActivityimportance.objects.all(),
        "related_tickets": TicketsActivityticket.objects.all(),
    }
    
    # Loop through each state and calculate ticket counts and group by analyst
    for state in states_config:
        tickets = TicketsActivityticket.objects.filter(
            current_state__name=state["name"]
        )
        
        # Count of tickets per state
        context[f"{state['prefix']}_count"] = tickets.count()
        
        # Tickets grouped by analyst consultant with annotation
        context[f"tickets_by_analyst_consultant_{state['prefix']}"] = tickets.values(
            "analyst_consultant__name",
            "activity_importance",
            "ticket_id",
            "sysdate",
            "time_spent",
            "related_tickets",
        ).annotate(total=Count("ticket_id")).order_by("analyst_consultant__name")
    
    # Render the home page template with the context
    return render(request, "users/home.html", context)
