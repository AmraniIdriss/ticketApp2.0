# users/views.py - User Authentication and Dashboard Views
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, Sum, Q
from django.http import JsonResponse
import json

from tickets.models import (
    TicketsActivityticket,
    TicketsActivitytype,
    TicketsReportedby,
    TicketsCurrentstate,
    TicketsAnalystconsultant, 
    TicketsActivityimportance,
)


# ==============================================================================
# USER REGISTRATION VIEW
# ==============================================================================
def register_view(request):
    """
    Handle user registration form.
    POST: Create new user account and redirect to login
    GET: Display registration form
    """
    
    if request.method == 'POST':
        # Extract form data from POST request
        username = request.POST['username']  # Desired username
        email = request.POST['email']  # User's email address
        password = request.POST['password']  # Password (will be hashed)

        # Check if username already exists in database
        if User.objects.filter(username=username).exists():
            # Username is taken, show error message
            messages.error(request, "Username já existe!")
        else:
            # Username is available, create new user
            # create_user() automatically hashes the password
            User.objects.create_user(username=username, email=email, password=password)
            # Show success message
            messages.success(request, "Conta criada com sucesso!")
            # Redirect to login page
            return redirect('login')

    # GET request: render registration form
    return render(request, 'users/register.html')


# ==============================================================================
# USER LOGIN VIEW
# ==============================================================================
def login_view(request):
    """
    Handle user login form.
    POST: Authenticate user and create session
    GET: Display login form
    """
    
    if request.method == 'POST':
        # Extract credentials from POST request
        username = request.POST['username']  # Username entered
        password = request.POST['password']  # Password entered

        # Authenticate user (check if credentials are valid)
        # Returns User object if valid, None if invalid
        user = authenticate(request, username=username, password=password)
        
        if user:
            # Credentials are valid - log the user in
            # This creates a session and sets session cookie
            login(request, user)
            # Redirect to home page
            return redirect('/')
        else:
            # Invalid credentials - show error message
            messages.error(request, "Username ou password inválido!")

    # GET request: render login form
    return render(request, 'users/login.html')


# ==============================================================================
# USER LOGOUT VIEW
# ==============================================================================
def logout_view(request):
    """
    Log out the current user and destroy their session.
    Always redirects to login page.
    """
    # Destroy the user's session
    logout(request)
    # Redirect to login page
    return redirect('login')


# ==============================================================================
# HOME DASHBOARD VIEW - INITIAL PAGE LOAD
# ==============================================================================
@login_required(login_url='login')  # Require user to be logged in
def home_view(request):
    """
    Main dashboard view that displays:
    1. KPI cards (total tickets, avg time, etc.)
    2. 6 interactive charts (Chart.js)
    3. 8 ticket tables filtered by state (with checkbox filters)
    
    Generates initial data server-side, passes to template.
    Charts can be dynamically updated via AJAX using dashboard_api().
    """
    
    # CONFIGURATION: Define all ticket states and their prefixes for context keys
    states_config = [
        {"name": "✎ Open", "prefix": "open"},  # Newly created tickets
        {"name": "⇶ Inprogress | OnGoing", "prefix": "inprogress_ongoing"},  # Currently being worked on
        {"name": "⌚ Pending Customer", "prefix": "pending_customer"},  # Waiting for customer response
        {"name": "⌛ Pending 3rd Party", "prefix": "pending_3rd_party"},  # Waiting for external party
        {"name": "🆗 Solved", "prefix": "solved"},  # Ticket resolved
        {"name": "☼ Pending analysis", "prefix": "pending_analysis"},  # Needs analysis
        {"name": "Incomplete (Pending)", "prefix": "incomplete_pending"},  # Missing information
        {"name": "🆗 Delivered Recommendation", "prefix": "delivery_recommendation"},  # Recommendation sent
        {"name": "📅 Scheduled", "prefix": "scheduled"},  # Scheduled for future work
        {"name": "↻ Re-Opened", "prefix": "re_opened"},  # Previously closed, reopened
    ]
    
    # Initialize context dictionary with base data
    context = {
        # All available options for dropdowns and filters
        "activity_types": TicketsActivitytype.objects.all(),  # All activity types
        "reported_by": TicketsReportedby.objects.all(),  # All reporters
        "current_state": TicketsCurrentstate.objects.all(),  # All states
        "activity_importance": TicketsActivityimportance.objects.all(),  # All priority levels
        "related_tickets": TicketsActivityticket.objects.all(),  # All tickets (for dropdowns)
        
        # For multi-select filters in dashboard
        "analysts": TicketsAnalystconsultant.objects.all(),  # All analysts for filter
        "states": TicketsCurrentstate.objects.all(),  # All states for filter
    }
    
    # LOOP: For each state, get tickets and generate table data
    for state in states_config:
        # Filter tickets by current state
        tickets = TicketsActivityticket.objects.filter(
            current_state__name=state["name"]
        )
        
        # COUNT: Store count of tickets in this state
        # Used for badge numbers next to checkboxes
        context[f"{state['prefix']}_count"] = tickets.count()
        
        # GROUPED DATA: Get tickets grouped by analyst with aggregated data
        # .values() creates a dict-like queryset
        # .annotate() adds computed fields
        context[f"tickets_by_analyst_consultant_{state['prefix']}"] = tickets.values(
            "analyst_consultant__name",  # Analyst name (joined from FK)
            "activity_importance",  # Priority level
            "ticket_id",  # Ticket ID
            "sysdate",  # Creation date
            "time_spent",  # Hours spent
            "related_ticket__ticket_id",  # Related ticket ID (joined from FK)
        ).annotate(
            total=Count("ticket_id")  # Count tickets per analyst
        ).order_by("analyst_consultant__name")  # Sort by analyst name
    
    # =============================
    # CHART DATA GENERATION
    # =============================
    # Get all tickets for aggregation
    all_tickets = TicketsActivityticket.objects.all()
    
    # CHART 1: Pie/Doughnut chart - Tickets by State
    # Groups tickets by state and counts each group
    tickets_by_state = all_tickets.values('current_state__name').annotate(
        count=Count('ticket_id')  # Count tickets per state
    ).order_by('-count')  # Sort by count descending
    
    # CHART 2: Bar chart - Top 10 Analysts by Ticket Count
    # Groups tickets by analyst and counts each group
    tickets_by_analyst = all_tickets.values('analyst_consultant__name').annotate(
        count=Count('ticket_id')  # Count tickets per analyst
    ).order_by('-count')[:10]  # Top 10 only
    
    # CHART 3: Bar chart - Average Resolution Time per Analyst
    # Groups tickets by analyst and calculates average time
    avg_time_by_analyst = all_tickets.values('analyst_consultant__name').annotate(
        avg_time=Avg('time_spent')  # Average time_spent per analyst
    ).order_by('-avg_time')[:10]  # Top 10 only
    
    # CHART 4: Bar chart - Tickets by Activity Type
    # Groups tickets by activity type and counts each group
    tickets_by_activity = all_tickets.values('activity_type__name').annotate(
        count=Count('ticket_id')  # Count tickets per type
    ).order_by('-count')[:8]  # Top 8 only
    
    # CHART 5: Horizontal bar chart - Top 10 Customers by Ticket Count
    # Groups tickets by customer and counts each group
    tickets_by_customer = all_tickets.values('customer__name').annotate(
        count=Count('ticket_id')  # Count tickets per customer
    ).order_by('-count')[:10]  # Top 10 only
    
    # CHART 6: Bar chart - Total Time Spent per Analyst
    # Groups tickets by analyst and sums total time
    total_time_by_analyst = all_tickets.values('analyst_consultant__name').annotate(
        total_time=Sum('time_spent')  # Sum of all time_spent per analyst
    ).order_by('-total_time')[:10]  # Top 10 only
    
    # =============================
    # KPI CALCULATIONS
    # =============================
    # Calculate key performance indicators
    context['total_tickets'] = all_tickets.count()  # Total number of tickets
    context['avg_resolution_time'] = round(
        all_tickets.aggregate(avg=Avg('time_spent'))['avg'] or 0,  # Calculate average, default to 0 if None
        2  # Round to 2 decimal places
    )
    context['total_time_spent'] = round(
        all_tickets.aggregate(total=Sum('time_spent'))['total'] or 0,  # Calculate sum, default to 0 if None
        2  # Round to 2 decimal places
    )
    context['open_tickets_kpi'] = all_tickets.filter(
        current_state__name="✎ Open"  # Count only "Open" tickets
    ).count()
    
    # =============================
    # SERIALIZE CHART DATA FOR JAVASCRIPT
    # =============================
    # Convert Python data to JSON strings for use in template
    # Template will inject these into JavaScript via {{ chart1_labels|safe }}
    
    # Chart 1 data
    context['chart1_labels'] = json.dumps([
        item['current_state__name'] or 'Unknown'  # State names, fallback to 'Unknown'
        for item in tickets_by_state
    ])
    context['chart1_data'] = json.dumps([
        item['count']  # Counts for each state
        for item in tickets_by_state
    ])
    
    # Chart 2 data
    context['chart2_labels'] = json.dumps([
        item['analyst_consultant__name'] or 'Unknown'  # Analyst names
        for item in tickets_by_analyst
    ])
    context['chart2_data'] = json.dumps([
        item['count']  # Counts for each analyst
        for item in tickets_by_analyst
    ])
    
    # Chart 3 data
    context['chart3_labels'] = json.dumps([
        item['analyst_consultant__name'] or 'Unknown'  # Analyst names
        for item in avg_time_by_analyst
    ])
    context['chart3_data'] = json.dumps([
        float(item['avg_time'] or 0)  # Average times, convert to float
        for item in avg_time_by_analyst
    ])
    
    # Chart 4 data
    context['chart4_labels'] = json.dumps([
        item['activity_type__name'] or 'Unknown'  # Activity type names
        for item in tickets_by_activity
    ])
    context['chart4_data'] = json.dumps([
        item['count']  # Counts for each activity type
        for item in tickets_by_activity
    ])
    
    # Chart 5 data
    context['chart5_labels'] = json.dumps([
        item['customer__name'] or 'Unknown'  # Customer names
        for item in tickets_by_customer
    ])
    context['chart5_data'] = json.dumps([
        item['count']  # Counts for each customer
        for item in tickets_by_customer
    ])
    
    # Chart 6 data
    context['chart6_labels'] = json.dumps([
        item['analyst_consultant__name'] or 'Unknown'  # Analyst names
        for item in total_time_by_analyst
    ])
    context['chart6_data'] = json.dumps([
        float(item['total_time'] or 0)  # Total times, convert to float
        for item in total_time_by_analyst
    ])
    
    # Render template with all context data
    return render(request, "users/home.html", context)


# ==============================================================================
# DASHBOARD API - DYNAMIC CHART FILTERING
# ==============================================================================
@login_required(login_url='login')  # Require authentication
def dashboard_api(request):
    """
    REST API endpoint for dynamic dashboard filtering.
    Returns JSON data for charts and KPIs based on filter parameters.
    
    Query Parameters:
    - start_date: Filter tickets created after this date (YYYY-MM-DD)
    - end_date: Filter tickets created before this date (YYYY-MM-DD)
    - analysts: Multi-select analyst names (can pass multiple times)
    - states: Multi-select state names (can pass multiple times)
    
    Response Format:
    {
        "kpis": {
            "total": 150,
            "avg_time": 2.5,
            "total_time": 375.0,
            "open": 45
        },
        "charts": {
            "chart1": {"labels": [...], "data": [...]},
            "chart2": {"labels": [...], "data": [...]},
            ...
        }
    }
    """
    
    # EXTRACT FILTER PARAMETERS from query string
    start_date = request.GET.get('start_date')  # Single value
    end_date = request.GET.get('end_date')  # Single value
    analysts = request.GET.getlist('analysts')  # Multi-select (list of values)
    states = request.GET.getlist('states')  # Multi-select (list of values)
    
    # Start with all tickets
    tickets = TicketsActivityticket.objects.all()
    
    # APPLY FILTERS progressively (chain filters)
    if start_date:
        # Filter tickets created on or after start_date
        tickets = tickets.filter(sysdate__date__gte=start_date)
    
    if end_date:
        # Filter tickets created on or before end_date
        tickets = tickets.filter(sysdate__date__lte=end_date)
    
    if analysts:
        # Filter tickets assigned to any of the selected analysts
        # __in does an OR operation (analyst1 OR analyst2 OR ...)
        tickets = tickets.filter(analyst_consultant__name__in=analysts)
    
    if states:
        # Filter tickets in any of the selected states
        # __in does an OR operation (state1 OR state2 OR ...)
        tickets = tickets.filter(current_state__name__in=states)
    
    # =============================
    # CALCULATE KPIs (filtered data)
    # =============================
    total_tickets = tickets.count()  # Total count
    avg_resolution_time = round(
        tickets.aggregate(avg=Avg('time_spent'))['avg'] or 0,  # Average time
        2
    )
    total_time_spent = round(
        tickets.aggregate(total=Sum('time_spent'))['total'] or 0,  # Sum of time
        2
    )
    open_tickets_kpi = tickets.filter(
        current_state__name="✎ Open"  # Count open tickets
    ).count()
    
    # =============================
    # GENERATE CHART DATA (filtered)
    # =============================
    
    # CHART 1: Tickets by State
    tickets_by_state = tickets.values('current_state__name').annotate(
        count=Count('ticket_id')
    ).order_by('-count')
    
    chart1 = {
        'labels': [item['current_state__name'] or 'Unknown' for item in tickets_by_state],
        'data': [item['count'] for item in tickets_by_state]
    }
    
    # CHART 2: Top 10 Analysts
    tickets_by_analyst = tickets.values('analyst_consultant__name').annotate(
        count=Count('ticket_id')
    ).order_by('-count')[:10]
    
    chart2 = {
        'labels': [item['analyst_consultant__name'] or 'Unknown' for item in tickets_by_analyst],
        'data': [item['count'] for item in tickets_by_analyst]
    }
    
    # CHART 3: Average Time per Analyst
    avg_time_by_analyst = tickets.values('analyst_consultant__name').annotate(
        avg_time=Avg('time_spent')
    ).order_by('-avg_time')[:10]
    
    chart3 = {
        'labels': [item['analyst_consultant__name'] or 'Unknown' for item in avg_time_by_analyst],
        'data': [float(item['avg_time'] or 0) for item in avg_time_by_analyst]
    }
    
    # CHART 4: Tickets by Activity Type
    tickets_by_activity = tickets.values('activity_type__name').annotate(
        count=Count('ticket_id')
    ).order_by('-count')[:8]
    
    chart4 = {
        'labels': [item['activity_type__name'] or 'Unknown' for item in tickets_by_activity],
        'data': [item['count'] for item in tickets_by_activity]
    }
    
    # CHART 5: Top 10 Customers
    tickets_by_customer = tickets.values('customer__name').annotate(
        count=Count('ticket_id')
    ).order_by('-count')[:10]
    
    chart5 = {
        'labels': [item['customer__name'] or 'Unknown' for item in tickets_by_customer],
        'data': [item['count'] for item in tickets_by_customer]
    }
    
    # CHART 6: Total Time per Analyst
    total_time_by_analyst = tickets.values('analyst_consultant__name').annotate(
        total_time=Sum('time_spent')
    ).order_by('-total_time')[:10]
    
    chart6 = {
        'labels': [item['analyst_consultant__name'] or 'Unknown' for item in total_time_by_analyst],
        'data': [float(item['total_time'] or 0) for item in total_time_by_analyst]
    }
    
    # =============================
    # RETURN JSON RESPONSE
    # =============================
    # JsonResponse automatically serializes Python dict to JSON
    return JsonResponse({
        'kpis': {
            'total': total_tickets,
            'avg_time': avg_resolution_time,
            'total_time': total_time_spent,
            'open': open_tickets_kpi
        },
        'charts': {
            'chart1': chart1,  # Doughnut chart data
            'chart2': chart2,  # Bar chart data
            'chart3': chart3,  # Bar chart data
            'chart4': chart4,  # Bar chart data
            'chart5': chart5,  # Horizontal bar chart data
            'chart6': chart6  # Bar chart data
        }
    })