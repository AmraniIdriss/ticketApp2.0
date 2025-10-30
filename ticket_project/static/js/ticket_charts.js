document.addEventListener("DOMContentLoaded", function () {
  const el = document.getElementById('echarts_pie_analyst');
  if (!el || typeof echarts === 'undefined') return;

  const chart = echarts.init(el, null, { renderer: 'canvas' });

  // Get Django URL and query string from template context if available
  let baseUrl = el.getAttribute('data-api-url');
  let qs = el.getAttribute('data-query-string');

  // Fallback: try to reconstruct from window.location if not set
  if (!baseUrl) {
    // Try to guess the endpoint (adjust if needed)
    baseUrl = "/api/tickets-by-analyst/";
  }
  if (typeof qs !== "string") {
    qs = window.location.search.replace(/^\?/, "");
  }

  const url = qs ? `${baseUrl}?${qs}` : baseUrl;

  fetch(url)
    .then(r => r.json())
    .then(({ data }) => {
      if (!data || data.length === 0) {
        chart.clear();
        el.innerHTML = '<div class="text-muted">No tickets found for this filter.</div>';
        return;
      }
      chart.setOption({
        title: { text: 'Tickets by Analyst', left: 'center' },
        tooltip: { trigger: 'item', formatter: '{b}<br/>{c} tickets ({d}%)' },
        legend: { orient: 'vertical', left: 0 },
        toolbox: { feature: { saveAsImage: {}, restore: {} } },
        series: [{
          name: 'Analysts',
          type: 'pie',
          radius: ['40%', '70%'],
          center: ['55%', '55%'],
          avoidLabelOverlap: true,
          label: { formatter: '{b}: {c} ({d}%)' },
          data: data
        }]
      });
    })
    .catch(e => {
      console.error(e);
      el.innerHTML = '<div class="text-danger">Error loading chart.</div>';
    });

  window.addEventListener('resize', () => chart.resize());
});