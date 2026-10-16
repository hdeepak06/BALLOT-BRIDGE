/**
 * BallotBridge — Chart.js Initialization for Certified Election Results
 */

function initElectionCharts(labels, votes, colors) {
  if (typeof Chart === 'undefined') {
    console.error('Chart.js library is not loaded.');
    return;
  }

  // 1. Candidate Votes Bar Chart
  const barCanvas = document.getElementById('resultsBarChart');
  if (barCanvas) {
    const ctxBar = barCanvas.getContext('2d');
    new Chart(ctxBar, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Certified Votes',
          data: votes,
          backgroundColor: colors.map(c => c || '#0284c7'),
          borderColor: colors.map(c => c || '#0284c7'),
          borderWidth: 1,
          borderRadius: 6,
          maxBarThickness: 45,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            backgroundColor: '#0f172a',
            titleFont: { family: "'Plus Jakarta Sans', sans-serif", size: 13, weight: 'bold' },
            bodyFont: { family: "'Plus Jakarta Sans', sans-serif", size: 12 },
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: function(context) {
                const total = votes.reduce((a, b) => a + b, 0);
                const val = context.raw;
                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                return ` ${val} votes (${pct}%)`;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              precision: 0,
              font: { family: "'Plus Jakarta Sans', sans-serif" }
            },
            grid: {
              color: '#f1f5f9'
            }
          },
          x: {
            ticks: {
              font: { family: "'Plus Jakarta Sans', sans-serif", weight: '600' }
            },
            grid: {
              display: false
            }
          }
        }
      }
    });
  }

  // 2. Candidate Vote Share Doughnut Chart
  const doughnutCanvas = document.getElementById('resultsDoughnutChart');
  if (doughnutCanvas) {
    const ctxDoughnut = doughnutCanvas.getContext('2d');
    new Chart(ctxDoughnut, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: votes,
          backgroundColor: colors.map(c => c || '#0284c7'),
          borderWidth: 2,
          borderColor: '#ffffff',
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '68%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              boxWidth: 12,
              font: { family: "'Plus Jakarta Sans', sans-serif", size: 12, weight: '600' },
              padding: 15
            }
          },
          tooltip: {
            backgroundColor: '#0f172a',
            titleFont: { family: "'Plus Jakarta Sans', sans-serif", size: 13, weight: 'bold' },
            bodyFont: { family: "'Plus Jakarta Sans', sans-serif", size: 12 },
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: function(context) {
                const total = votes.reduce((a, b) => a + b, 0);
                const val = context.raw;
                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                return ` ${context.label}: ${val} votes (${pct}%)`;
              }
            }
          }
        }
      }
    });
  }
}
