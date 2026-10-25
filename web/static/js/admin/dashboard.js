// Admin Dashboard JavaScript

// Revenue Chart (Bar Chart)
const revenueCtx = document.getElementById('revenueChart');
if (revenueCtx) {
    new Chart(revenueCtx, {
        type: 'bar',
        data: {
            labels: ['10.12', '10.14', '10.15', '10.16', '10.18', '10.20', '10.22', '10.23', '10.24'],
            datasets: [{
                label: 'Tushum',
                data: [280000, 350000, 180000, 150000, 320000, 380000, 420000, 290000, 450000],
                backgroundColor: '#4a9eff',
                borderRadius: 8,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1a1f3a',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    padding: 12,
                    borderColor: '#2d3354',
                    borderWidth: 1,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return new Intl.NumberFormat('uz-UZ').format(context.parsed.y) + ' so\'m';
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: '#2d3354',
                        drawBorder: false
                    },
                    ticks: {
                        color: '#94a3b8',
                        callback: function(value) {
                            return (value / 1000) + 'k';
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                }
            }
        }
    });
}

// Order Status Chart (Donut Chart)
const statusCtx = document.getElementById('orderStatusChart');
if (statusCtx) {
    new Chart(statusCtx, {
        type: 'doughnut',
        data: {
            labels: ['Tasdiqlandi', 'Kutilmoqda', 'Bekor qilindi'],
            datasets: [{
                data: [43, 11, 6],
                backgroundColor: [
                    '#10b981',
                    '#f59e0b',
                    '#ef4444'
                ],
                borderWidth: 0,
                cutout: '70%'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: '#1a1f3a',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    padding: 12,
                    borderColor: '#2d3354',
                    borderWidth: 1,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            return context.label + ': ' + context.parsed + ' ta';
                        }
                    }
                }
            }
        },
        plugins: [{
            id: 'centerText',
            beforeDraw: function(chart) {
                const width = chart.width;
                const height = chart.height;
                const ctx = chart.ctx;
                ctx.restore();

                const fontSize = (height / 80).toFixed(2);
                ctx.font = fontSize + "em sans-serif";
                ctx.textBaseline = "middle";
                ctx.fillStyle = "#fff";

                const total = chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                const text = total;
                const textX = Math.round((width - ctx.measureText(text).width) / 2);
                const textY = height / 2;

                ctx.fillText(text, textX, textY);
                ctx.save();

                // Label
                ctx.font = (fontSize * 0.4) + "em sans-serif";
                ctx.fillStyle = "#94a3b8";
                const label = "buyurtma";
                const labelX = Math.round((width - ctx.measureText(label).width) / 2);
                const labelY = height / 2 + 25;
                ctx.fillText(label, labelX, labelY);
                ctx.save();
            }
        }]
    });
}

// Chart tabs functionality
document.querySelectorAll('.chart-tab').forEach(tab => {
    tab.addEventListener('click', function() {
        document.querySelectorAll('.chart-tab').forEach(t => t.classList.remove('active'));
        this.classList.add('active');
    });
});

// Real-time updates simulation (optional)
function updateStats() {
    // This would fetch real data from API
    console.log('Updating stats...');
}

// Update every 30 seconds
setInterval(updateStats, 30000);

// Initial load
console.log('Admin Dashboard loaded');
