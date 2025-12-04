import plotly.express as px
from django.shortcuts import render
from tickets.models import TicketsActivityticket
from django.db.models.functions import TruncDate
from django.db.models import Count, Avg, Sum
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils.dateparse import parse_date
from django.db.models import Value
from django.db.models.functions import Coalesce
from datetime import datetime, timedelta


@require_GET
def api_echarts_tickets_by_analyst(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    state_filter = request.GET.get('current_state')
    
    qs = TicketsActivityticket.objects.all()
    if start_date:
        qs = qs.filter(sysdate__date__gte=parse_date(start_date))
    if end_date:
        qs = qs.filter(sysdate__date__lte=parse_date(end_date))
    if state_filter:
        qs = qs.filter(current_state__name=state_filter)
    
    rows = (
        qs.values(name=Coalesce('analyst_consultant__name', Value('Unknown')))
          .annotate(value=Count('ticket_id'))
          .order_by('-value')
    )
    
    data = list(rows)
    return JsonResponse({"data": data})


def home_reports(request):
    """
    Enhanced reports view with multiple charts and KPIs
    """
    # Get filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    state_filter = request.GET.get('current_state')
    analyst_filter = request.GET.get('analyst_consultant')
    
    # Base queryset
    tickets = TicketsActivityticket.objects.all()
    
    # Apply filters
    if start_date:
        tickets = tickets.filter(sysdate__date__gte=start_date)
    if end_date:
        tickets = tickets.filter(sysdate__date__lte=end_date)
    if state_filter:
        tickets = tickets.filter(current_state__name=state_filter)
    if analyst_filter:
        tickets = tickets.filter(analyst_consultant__name=analyst_filter)
    
    # KPIs
    total_tickets = tickets.count()
    avg_time = tickets.aggregate(avg=Avg('time_spent'))['avg'] or 0
    total_time = tickets.aggregate(total=Sum('time_spent'))['total'] or 0
    
    # Chart 1: Tickets per day (existing - keep Plotly)
    daily_counts = tickets.annotate(day=TruncDate('sysdate')) \
                          .values('day') \
                          .annotate(count=Count('ticket_id')) \
                          .order_by('day')
    
    if daily_counts:
        x_labels = [entry['day'].strftime('%Y-%m-%d') for entry in daily_counts]
        y_counts = [entry['count'] for entry in daily_counts]
        
        fig = px.bar(
            x=x_labels,
            y=y_counts,
            text=y_counts,
            labels={'x': 'Sysdate', 'y': 'Number of Tickets'},
            title='Tickets per Day'
        )
        fig.update_traces(textposition='outside')
        fig.update_yaxes(dtick=1)
        fig.update_traces(hovertemplate='Day: %{x}<br>Tickets: %{y}<extra></extra>')
        chart_daily = fig.to_html(include_plotlyjs=True, full_html=False, div_id="chart_daily")
    else:
        chart_daily = "<p class='text-center text-muted'>No tickets found for this filter.</p>"
    
    # Chart 2: Average time per analyst
    avg_time_by_analyst = tickets.values('analyst_consultant__name').annotate(
        avg_time=Avg('time_spent'),
        ticket_count=Count('ticket_id')
    ).order_by('-avg_time')[:10]
    
    # Chart 3: Tickets by state
    tickets_by_state = tickets.values('current_state__name').annotate(
        count=Count('ticket_id')
    ).order_by('-count')
    
    # Chart 4: Top customers
    tickets_by_customer = tickets.values('customer__name').annotate(
        count=Count('ticket_id')
    ).order_by('-count')[:10]
    
    # Chart 5: Total time per analyst
    total_time_by_analyst = tickets.values('analyst_consultant__name').annotate(
        total_time=Sum('time_spent')
    ).order_by('-total_time')[:10]
    
    # Chart 6: Tickets by activity type
    tickets_by_type = tickets.values('activity_type__name').annotate(
        count=Count('ticket_id')
    ).order_by('-count')[:8]
    
    context = {
        # Filters data
        'analysts': TicketsActivityticket.objects.values_list('analyst_consultant__name', flat=True).distinct(),
        'states': TicketsActivityticket.objects.values_list('current_state__name', flat=True).distinct(),
        
        # Current filter values
        'current_start_date': start_date,
        'current_end_date': end_date,
        'current_state': state_filter,
        'current_analyst': analyst_filter,
        
        # KPIs
        'total_tickets': total_tickets,
        'avg_time': round(avg_time, 2),
        'total_time': round(total_time, 2),
        
        # Original Plotly chart
        'chart_daily': chart_daily,
        
        # Chart.js data
        'chart2_labels': [item['analyst_consultant__name'] or 'Unknown' for item in avg_time_by_analyst],
        'chart2_data': [float(item['avg_time'] or 0) for item in avg_time_by_analyst],
        
        'chart3_labels': [item['current_state__name'] or 'Unknown' for item in tickets_by_state],
        'chart3_data': [item['count'] for item in tickets_by_state],
        
        'chart4_labels': [item['customer__name'] or 'Unknown' for item in tickets_by_customer],
        'chart4_data': [item['count'] for item in tickets_by_customer],
        
        'chart5_labels': [item['analyst_consultant__name'] or 'Unknown' for item in total_time_by_analyst],
        'chart5_data': [float(item['total_time'] or 0) for item in total_time_by_analyst],
        
        'chart6_labels': [item['activity_type__name'] or 'Unknown' for item in tickets_by_type],
        'chart6_data': [item['count'] for item in tickets_by_type],
    }
    
    return render(request, 'reports/home_reports.html', context)