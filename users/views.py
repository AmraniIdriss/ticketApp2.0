# users/views.py - VERSION ULTIMATE COMPLETE
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


# ============================
# REGISTER VIEW
# ============================
def register_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username já existe!")
        else:
            User.objects.create_user(username=username, email=email, password=password)
            messages.success(request, "Conta criada com sucesso!")
            return redirect('login')

    return render(request, 'users/register.html')


# ============================
# LOGIN VIEW
# ============================
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, "Username ou password inválido!")

    return render(request, 'users/login.html')


# ============================
# LOGOUT VIEW
# ============================
def logout_view(request):
    logout(request)
    return redirect('login')


# ============================
# HOME PAGE VIEW - INITIAL LOAD
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
    
    # Base context
    context = {
        "activity_types": TicketsActivitytype.objects.all(),
        "reported_by": TicketsReportedby.objects.all(),
        "current_state": TicketsCurrentstate.objects.all(),
        "activity_importance": TicketsActivityimportance.objects.all(),
        "related_tickets": TicketsActivityticket.objects.all(),
        # For multi-select filters
        "analysts": TicketsAnalystconsultant.objects.all(),
        "states": TicketsCurrentstate.objects.all(),
    }
    
    # Loop through each state and get tickets
    for state in states_config:
        tickets = TicketsActivityticket.objects.filter(
            current_state__name=state["name"]
        )
        
        context[f"{state['prefix']}_count"] = tickets.count()
        
        context[f"tickets_by_analyst_consultant_{state['prefix']}"] = tickets.values(
            "analyst_consultant__name",
            "activity_importance",
            "ticket_id",
            "sysdate",
            "time_spent",
            "related_ticket__ticket_id",
        ).annotate(total=Count("ticket_id")).order_by("analyst_consultant__name")
    
    # =============================
    # CHARTS DATA - INITIAL
    # =============================
    all_tickets = TicketsActivityticket.objects.all()
    
    # Chart 1: Tickets by State
    tickets_by_state = all_tickets.values('current_state__name').annotate(
        count=Count('ticket_id')
    ).order_by('-count')
    
    # Chart 2: Top 10 Analysts
    tickets_by_analyst = all_tickets.values('analyst_consultant__name').annotate(
        count=Count('ticket_id')
    ).order_by('-count')[:10]
    
    # Chart 3: Average Time per Analyst
    avg_time_by_analyst = all_tickets.values('analyst_consultant__name').annotate(
        avg_time=Avg('time_spent')
    ).order_by('-avg_time')[:10]
    
    # Chart 4: Tickets by Activity Type
    tickets_by_activity = all_tickets.values('activity_type__name').annotate(
        count=Count('ticket_id')
    ).order_by('-count')[:8]
    
    # Chart 5: Top 10 Customers
    tickets_by_customer = all_tickets.values('customer__name').annotate(
        count=Count('ticket_id')
    ).order_by('-count')[:10]
    
    # Chart 6: Total Time per Analyst
    total_time_by_analyst = all_tickets.values('analyst_consultant__name').annotate(
        total_time=Sum('time_spent')
    ).order_by('-total_time')[:10]
    
    # KPIs
    context['total_tickets'] = all_tickets.count()
    context['avg_resolution_time'] = round(all_tickets.aggregate(avg=Avg('time_spent'))['avg'] or 0, 2)
    context['total_time_spent'] = round(all_tickets.aggregate(total=Sum('time_spent'))['total'] or 0, 2)
    context['open_tickets_kpi'] = all_tickets.filter(current_state__name="✎ Open").count()
    
    # Serialize chart data
    context['chart1_labels'] = json.dumps([item['current_state__name'] or 'Unknown' for item in tickets_by_state])
    context['chart1_data'] = json.dumps([item['count'] for item in tickets_by_state])
    
    context['chart2_labels'] = json.dumps([item['analyst_consultant__name'] or 'Unknown' for item in tickets_by_analyst])
    context['chart2_data'] = json.dumps([item['count'] for item in tickets_by_analyst])
    
    context['chart3_labels'] = json.dumps([item['analyst_consultant__name'] or 'Unknown' for item in avg_time_by_analyst])
    context['chart3_data'] = json.dumps([float(item['avg_time'] or 0) for item in avg_time_by_analyst])
    
    context['chart4_labels'] = json.dumps([item['activity_type__name'] or 'Unknown' for item in tickets_by_activity])
    context['chart4_data'] = json.dumps([item['count'] for item in tickets_by_activity])
    
    context['chart5_labels'] = json.dumps([item['customer__name'] or 'Unknown' for item in tickets_by_customer])
    context['chart5_data'] = json.dumps([item['count'] for item in tickets_by_customer])
    
    context['chart6_labels'] = json.dumps([item['analyst_consultant__name'] or 'Unknown' for item in total_time_by_analyst])
    context['chart6_data'] = json.dumps([float(item['total_time'] or 0) for item in total_time_by_analyst])
    
    return render(request, "users/home.html", context)


# ============================
# DASHBOARD API - DYNAMIC FILTERS
# ============================
@login_required(login_url='login')
def dashboard_api(request):
    """API endpoint for dynamic chart filtering"""
    
    # Get filter parameters (support multiple values)
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    analysts = request.GET.getlist('analysts')  # Multi-select
    states = request.GET.getlist('states')      # Multi-select
    
    # Start with all tickets
    tickets = TicketsActivityticket.objects.all()
    
    # Apply filters
    if start_date:
        tickets = tickets.filter(sysdate__date__gte=start_date)
    if end_date:
        tickets = tickets.filter(sysdate__date__lte=end_date)
    if analysts:
        tickets = tickets.filter(analyst_consultant__name__in=analysts)
    if states:
        tickets = tickets.filter(current_state__name__in=states)
    
    # Calculate KPIs
    total_tickets = tickets.count()
    avg_resolution_time = round(tickets.aggregate(avg=Avg('time_spent'))['avg'] or 0, 2)
    total_time_spent = round(tickets.aggregate(total=Sum('time_spent'))['total'] or 0, 2)
    open_tickets_kpi = tickets.filter(current_state__name="✎ Open").count()
    
    # Chart 1: Tickets by State
    tickets_by_state = tickets.values('current_state__name').annotate(
        count=Count('ticket_id')
    ).order_by('-count')
    
    chart1 = {
        'labels': [item['current_state__name'] or 'Unknown' for item in tickets_by_state],
        'data': [item['count'] for item in tickets_by_state]
    }
    
    # Chart 2: Top 10 Analysts
    tickets_by_analyst = tickets.values('analyst_consultant__name').annotate(
        count=Count('ticket_id')
    ).order_by('-count')[:10]
    
    chart2 = {
        'labels': [item['analyst_consultant__name'] or 'Unknown' for item in tickets_by_analyst],
        'data': [item['count'] for item in tickets_by_analyst]
    }
    
    # Chart 3: Average Time per Analyst
    avg_time_by_analyst = tickets.values('analyst_consultant__name').annotate(
        avg_time=Avg('time_spent')
    ).order_by('-avg_time')[:10]
    
    chart3 = {
        'labels': [item['analyst_consultant__name'] or 'Unknown' for item in avg_time_by_analyst],
        'data': [float(item['avg_time'] or 0) for item in avg_time_by_analyst]
    }
    
    # Chart 4: Tickets by Activity Type
    tickets_by_activity = tickets.values('activity_type__name').annotate(
        count=Count('ticket_id')
    ).order_by('-count')[:8]
    
    chart4 = {
        'labels': [item['activity_type__name'] or 'Unknown' for item in tickets_by_activity],
        'data': [item['count'] for item in tickets_by_activity]
    }
    
    # Chart 5: Top 10 Customers
    tickets_by_customer = tickets.values('customer__name').annotate(
        count=Count('ticket_id')
    ).order_by('-count')[:10]
    
    chart5 = {
        'labels': [item['customer__name'] or 'Unknown' for item in tickets_by_customer],
        'data': [item['count'] for item in tickets_by_customer]
    }
    
    # Chart 6: Total Time per Analyst
    total_time_by_analyst = tickets.values('analyst_consultant__name').annotate(
        total_time=Sum('time_spent')
    ).order_by('-total_time')[:10]
    
    chart6 = {
        'labels': [item['analyst_consultant__name'] or 'Unknown' for item in total_time_by_analyst],
        'data': [float(item['total_time'] or 0) for item in total_time_by_analyst]
    }
    
    # Return JSON response
    return JsonResponse({
        'kpis': {
            'total': total_tickets,
            'avg_time': avg_resolution_time,
            'total_time': total_time_spent,
            'open': open_tickets_kpi
        },
        'charts': {
            'chart1': chart1,
            'chart2': chart2,
            'chart3': chart3,
            'chart4': chart4,
            'chart5': chart5,
            'chart6': chart6
        }
    })