// Dashboard functionality
document.addEventListener('DOMContentLoaded', function() {
    // Modern sidebar handled in main.js
    
    // Dropdown toggles
    const dropdownToggles = document.querySelectorAll('[data-bs-toggle="dropdown"]');
    dropdownToggles.forEach(function(dropdownToggle) {
        dropdownToggle.addEventListener('click', function(e) {
            e.preventDefault();
            const dropdown = this.nextElementSibling;
            dropdown.classList.toggle('show');
        });
    });
    
    // Close dropdowns when clicking outside
    document.addEventListener('click', function(e) {
        const dropdowns = document.querySelectorAll('.dropdown-menu.show');
        dropdowns.forEach(function(dropdown) {
            if (!dropdown.previousElementSibling.contains(e.target)) {
                dropdown.classList.remove('show');
            }
        });
    });
    
    // Active menu item
    const currentLocation = window.location.pathname;
    const menuItems = document.querySelectorAll('.sidebar-menu-link');
    menuItems.forEach(function(menuItem) {
        const menuItemPath = menuItem.getAttribute('href');
        if (menuItemPath && currentLocation.includes(menuItemPath) && menuItemPath !== '/') {
            menuItem.classList.add('active');
        } else if (menuItemPath === '/' && currentLocation === '/') {
            menuItem.classList.add('active');
        }
    });
    
    // Tooltip initialization if Bootstrap is available
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Charts initialization if Chart.js is available
    if (typeof Chart !== 'undefined') {
        initializeCharts();
    }
});

function initializeCharts() {
    // Patient Statistics Chart
    const patientStatsCtx = document.getElementById('patientStatsChart');
    if (patientStatsCtx) {
        new Chart(patientStatsCtx, {
            type: 'line',
            data: {
                labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                datasets: [{
                    label: 'Nouveaux Patients',
                    data: [15, 20, 25, 22, 30, 28, 35, 40, 45, 43, 50, 55],
                    borderColor: '#14A97C',
                    backgroundColor: 'rgba(20, 169, 124, 0.1)',
                    borderWidth: 2,
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }
    
    // Appointments Chart
    const appointmentsChartCtx = document.getElementById('appointmentsChart');
    if (appointmentsChartCtx) {
        new Chart(appointmentsChartCtx, {
            type: 'bar',
            data: {
                labels: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
                datasets: [{
                    label: 'Rendez-vous',
                    data: [18, 25, 20, 30, 22, 15, 5],
                    backgroundColor: '#FFDE4D',
                    borderColor: '#E9B700',
                    borderWidth: 1,
                    borderRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    }
    
    // Vouchers Distribution Chart
    const vouchersChartCtx = document.getElementById('vouchersChart');
    if (vouchersChartCtx) {
        new Chart(vouchersChartCtx, {
            type: 'doughnut',
            data: {
                labels: ['Transport', 'Nourriture', 'Hébergement', 'Médicaments'],
                datasets: [{
                    data: [35, 25, 20, 20],
                    backgroundColor: [
                        '#14A97C',
                        '#FFDE4D',
                        '#E3344D',
                        '#6c757d'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                cutout: '70%'
            }
        });
    }
    
    // Rehabilitation Progress Chart
    const rehabProgressChartCtx = document.getElementById('rehabProgressChart');
    if (rehabProgressChartCtx) {
        new Chart(rehabProgressChartCtx, {
            type: 'radar',
            data: {
                labels: ['Mobilité', 'Douleur', 'Force', 'Coordination', 'Équilibre'],
                datasets: [{
                    label: 'Début',
                    data: [2, 3, 2, 1, 2],
                    backgroundColor: 'rgba(227, 52, 77, 0.2)',
                    borderColor: '#E3344D',
                    borderWidth: 2,
                    pointBackgroundColor: '#E3344D'
                }, {
                    label: 'Actuel',
                    data: [4, 5, 4, 3, 4],
                    backgroundColor: 'rgba(20, 169, 124, 0.2)',
                    borderColor: '#14A97C',
                    borderWidth: 2,
                    pointBackgroundColor: '#14A97C'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        angleLines: {
                            color: 'rgba(0, 0, 0, 0.1)'
                        },
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        pointLabels: {
                            font: {
                                size: 12
                            }
                        },
                        suggestedMin: 0,
                        suggestedMax: 5
                    }
                }
            }
        });
    }
} 