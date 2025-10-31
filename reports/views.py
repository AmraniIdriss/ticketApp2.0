import plotly.express as px

from django.shortcuts import render
from tickets.models import TicketsActivityticket
from django.db.models.functions import TruncDate
from django.db.models import Count


from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.utils.dateparse import parse_date
from django.db.models import Count, Value
from django.db.models.functions import TruncDate, Coalesce
from django.db.models import  Value
from tickets.models import TicketsActivityticket


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
    # ECharts pie attend [{name, value}, ...]
    data = list(rows)
    return JsonResponse({"data": data})

def home_reports(request):
    
    start_date = request.GET.get('start_date')  
    end_date = request.GET.get('end_date')
    state_filter = request.GET.get('current_state')
    analyst_filter = request.GET.get('analyst_consultant')

    tickets = TicketsActivityticket.objects.all()

    if start_date:
        tickets = tickets.filter(sysdate__date__gte=start_date)
    if end_date:
        tickets = tickets.filter(sysdate__date__lte=end_date)
    if state_filter:
        tickets = tickets.filter(current_state__name=state_filter) 
    if analyst_filter:
        tickets = tickets.filter(analyst_consultant__name=analyst_filter)

    daily_counts = tickets.annotate(day=TruncDate('sysdate')) \
                          .values('day') \
                          .annotate(count=Count('ticket_id')) \
                          .order_by('day')


    if not daily_counts:
        chart_html = "<p>No tickets found for this filter.</p>"
        return render(request, 'reports/home_reports.html', {'charts': [chart_html]})

    
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

    
    chart_html = fig.to_html(include_plotlyjs=True, full_html=False, div_id="chart_daily")
    return render(request, 'reports/home_reports.html', {'charts': [chart_html]})




