(function() {
  const dataUrl = document.getElementById('statistics-data-url').value;
  fetch(dataUrl)
    .then(r => r.json())
    .then(renderCharts);

  function renderCharts(data) {
    const ctx1 = document.getElementById('viewsChart').getContext('2d');
    new Chart(ctx1, {
      type: 'bar',
      data: {
        labels: data.views_per_recipe.map(v => v.name),
        datasets: [{
          label: 'Views',
          data: data.views_per_recipe.map(v => v.total),
          backgroundColor: 'rgba(54,162,235,0.6)'
        }]
      },
      options: {responsive: true, maintainAspectRatio: false}
    });

    const ctx2 = document.getElementById('subsChart').getContext('2d');
    new Chart(ctx2, {
      type: 'pie',
      data: {
        labels: ['Standard', 'Healthy', 'Premium'],
        datasets: [{
          data: [
            data.subscription_breakdown.standard,
            data.subscription_breakdown.healthy,
            data.subscription_breakdown.premium
          ],
          backgroundColor: [
            'rgba(54,162,235,0.6)',
            'rgba(75,192,192,0.6)',
            'rgba(255,99,132,0.6)'
          ]
        }]
      },
      options: {responsive: true, maintainAspectRatio: false}
    });

    const ctx3 = document.getElementById('viewsDayChart').getContext('2d');
    new Chart(ctx3, {
      type: 'line',
      data: {
        labels: data.views_per_day.map(v => v.day),
        datasets: [{
          label: 'Views per day',
          data: data.views_per_day.map(v => v.total),
          borderColor: 'rgba(153,102,255,0.8)',
          fill: false
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {y: {beginAtZero: true}}
      }
    });

    document.getElementById('totalUsers').innerText =
      'Total users: ' + data.subscription_breakdown.total;
  }
})();
