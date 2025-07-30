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

    const ctxVerify = document.getElementById('verifyChart').getContext('2d');
    new Chart(ctxVerify, {
      type: 'doughnut',
      data: {
        labels: ['Unverified', 'Verified'],
        datasets: [{
          data: [data.verification.unverified, data.verification.verified],
          backgroundColor: ['rgba(201, 203, 207, 0.6)', 'rgba(40,167,69,0.6)']
        }]
      },
      options: {responsive: true, maintainAspectRatio: false}
    });

    const ctxVerifySubs = document.getElementById('verifySubsChart').getContext('2d');
    new Chart(ctxVerifySubs, {
      type: 'bar',
      data: {
        labels: ['Standard', 'Healthy', 'Premium'],
        datasets: [{
          label: 'Verified users',
          data: [
            data.verification.verified_standard,
            data.verification.verified_healthy,
            data.verification.verified_premium
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

    const ctxNew = document.getElementById('newRecipeChart').getContext('2d');
    new Chart(ctxNew, {
      type: 'bar',
      data: {
        labels: data.new_recipes.map(v => v.day),
        datasets: [{
          label: 'New recipes',
          data: data.new_recipes.map(v => v.total),
          backgroundColor: 'rgba(255,159,64,0.6)'
        }]
      },
      options: {responsive: true, maintainAspectRatio: false}
    });

    const visitDayCtx = document.getElementById('visitDayChart').getContext('2d');
    new Chart(visitDayCtx, {
      type: 'bar',
      data: {
        labels: ['24h'],
        datasets: [{
          label: 'Visits',
          data: [data.site_visits.day],
          backgroundColor: 'rgba(54,162,235,0.6)'
        }]
      },
      options: {responsive: true, maintainAspectRatio: false, scales: {y: {beginAtZero: true}}}
    });

    const visitWeekCtx = document.getElementById('visitWeekChart').getContext('2d');
    new Chart(visitWeekCtx, {
      type: 'bar',
      data: {
        labels: ['7d'],
        datasets: [{
          label: 'Visits',
          data: [data.site_visits.week],
          backgroundColor: 'rgba(75,192,192,0.6)'
        }]
      },
      options: {responsive: true, maintainAspectRatio: false, scales: {y: {beginAtZero: true}}}
    });

    const visitMonthCtx = document.getElementById('visitMonthChart').getContext('2d');
    new Chart(visitMonthCtx, {
      type: 'bar',
      data: {
        labels: ['30d'],
        datasets: [{
          label: 'Visits',
          data: [data.site_visits.month],
          backgroundColor: 'rgba(255,99,132,0.6)'
        }]
      },
      options: {responsive: true, maintainAspectRatio: false, scales: {y: {beginAtZero: true}}}
    });

    document.getElementById('totalUsers').innerText =
      'Total users: ' + data.subscription_breakdown.total;
  }
})();
