let chart;

function generateReport() {
  const type = document.getElementById('report-type').value;
  const value = document.getElementById('report-value').value;
  fetch(`http://localhost:3000/api/officer/reports/${type}/${value}`, {
    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
  }).then(res => res.json()).then(data => {
    const ctx = document.getElementById('report-chart').getContext('2d');
    if (chart) chart.destroy();
    const labels = data.map(item => item[type === 'company' ? 'company' : type === 'branch' ? 'branch' : 'year']);
    const totals = data.map(item => item.total_applications);
    const selecteds = data.map(item => item.selected);
    chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Total Applications',
          data: totals,
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 1
        }, {
          label: 'Selected',
          data: selecteds,
          backgroundColor: 'rgba(153, 102, 255, 0.2)',
          borderColor: 'rgba(153, 102, 255, 1)',
          borderWidth: 1
        }]
      },
      options: {
        scales: {
          y: { beginAtZero: true }
        }
      }
    });
  });
}
