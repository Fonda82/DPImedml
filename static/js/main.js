// Main JavaScript file for DPImedml

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Initialize dropdown menus
    var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'))
    var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
        return new bootstrap.Dropdown(dropdownToggleEl)
    });

    // Setup sidebar toggle
    setupSidebar();

    // Render charts if the chart containers exist
    renderCharts();

    // Initialize enhanced content area
    initializeEnhancedContentArea();
});

function setupSidebar() {
    // Modern sidebar elements
    const appContainer = document.getElementById('appContainer');
    const sidebar = document.getElementById('appSidebar');
    const backdrop = document.getElementById('sidebarBackdrop');
    const mobileToggle = document.querySelector('.mobile-toggle');
    // Mobile sidebar toggle
    if (mobileToggle) {
        mobileToggle.addEventListener('click', function() {
            toggleMobileSidebar();
        });
    }

    // Close sidebar when clicking on backdrop
    if (backdrop) {
        backdrop.addEventListener('click', function() {
            closeMobileSidebar();
        });
    }

    // Handle window resize
    window.addEventListener('resize', function() {
        handleResponsiveSidebar();
    });

    // Initialize responsive behavior
    handleResponsiveSidebar();
    
    // Initialize mobile bottom navigation
    initializeMobileBottomNav();

    function toggleMobileSidebar() {
        if (window.innerWidth <= 991) {
            sidebar.classList.toggle('mobile-open');
            backdrop.classList.toggle('active');
            document.body.style.overflow = sidebar.classList.contains('mobile-open') ? 'hidden' : '';
        }
    }

    function closeMobileSidebar() {
        sidebar.classList.remove('mobile-open');
        backdrop.classList.remove('active');
        document.body.style.overflow = '';
    }



    function handleResponsiveSidebar() {
        if (window.innerWidth <= 991) {
            // Mobile mode: close mobile sidebar
            closeMobileSidebar();
        } else {
            // Desktop mode: close mobile sidebar
            closeMobileSidebar();
        }
    }
    
    function initializeMobileBottomNav() {
        // Set active state for mobile bottom navigation
        const currentPath = window.location.pathname;
        const mobileNavItems = document.querySelectorAll('.mobile-bottom-nav-item');
        
        mobileNavItems.forEach(function(item) {
            const href = item.getAttribute('href');
            if (href === currentPath || (currentPath.startsWith(href) && href !== '/')) {
                item.classList.add('active');
            }
        });
        
        // Handle orientation change for mobile devices
        window.addEventListener('orientationchange', function() {
            setTimeout(function() {
                // Force layout recalculation on orientation change
                document.body.style.height = window.innerHeight + 'px';
                setTimeout(function() {
                    document.body.style.height = '';
                }, 500);
            }, 100);
        });
        
        // Handle viewport height on mobile browsers (address bar hiding)
        function setMobileViewHeight() {
            if (window.innerWidth <= 768) {
                const vh = window.innerHeight * 0.01;
                document.documentElement.style.setProperty('--vh', `${vh}px`);
            }
        }
        
        setMobileViewHeight();
        window.addEventListener('resize', setMobileViewHeight);
    }
    
    function enhanceSidebarAnimations() {
        // Add staggered animation to sidebar menu items
    const menuItems = document.querySelectorAll('.sidebar-menu-item');
        menuItems.forEach(function(item, index) {
            item.style.animationDelay = (index * 0.05) + 's';
        });
        
        // Add loading animation class initially
        const sidebar = document.getElementById('appSidebar');
        if (sidebar) {
            sidebar.classList.add('sidebar-loading');
            
            // Remove loading state after animations complete
            setTimeout(function() {
                sidebar.classList.remove('sidebar-loading');
            }, 1000);
        }
        
        // Enhanced tooltip system for collapsed sidebar
        function createTooltip(text, targetElement) {
            const tooltip = document.createElement('div');
            tooltip.className = 'sidebar-tooltip';
            tooltip.textContent = text;
            
            document.body.appendChild(tooltip);
            
            const targetRect = targetElement.getBoundingClientRect();
            tooltip.style.top = targetRect.top + (targetRect.height / 2) - (tooltip.offsetHeight / 2) + 'px';
            tooltip.style.left = targetRect.right + 15 + 'px';
            
            // Add show class for animation
            setTimeout(() => tooltip.classList.add('show'), 10);
            
            return tooltip;
        }
        
        function removeTooltip() {
            const tooltip = document.querySelector('.sidebar-tooltip');
            if (tooltip) {
                tooltip.classList.remove('show');
                setTimeout(() => tooltip.remove(), 150);
            }
        }
        
        // Enhanced menu item interactions
        menuItems.forEach(function(item) {
            const link = item.querySelector('.sidebar-menu-link');
            const text = item.querySelector('.sidebar-menu-text');
            
            if (link && text) {
                link.addEventListener('mouseenter', function() {
                    // Only show tooltip in collapsed desktop mode
                    if (appContainer.classList.contains('sidebar-collapsed') && window.innerWidth > 991) {
                        createTooltip(text.textContent.trim(), link);
                    }
                    
                    // Add hover sound effect (visual feedback)
                    link.style.transform = 'translateX(6px)';
                });
                
                link.addEventListener('mouseleave', function() {
                    removeTooltip();
                    
                    // Reset transform
                    if (!link.classList.contains('active')) {
                        link.style.transform = '';
                    }
                });
                
                // Enhanced click feedback
                link.addEventListener('click', function() {
                    // Add click animation
                    link.style.transform = 'translateX(2px) scale(0.98)';
                    setTimeout(() => {
                        link.style.transform = '';
                    }, 150);
                });
        }
    });
}

    // Initialize enhanced sidebar animations
    enhanceSidebarAnimations();
    
    // FIXED: Initialize sticky sidebar scroll detection
    initializeStickysidebar();
    
    function initializeStickysidebar() {
    const sidebarMenu = document.querySelector('.sidebar-menu');
        if (!sidebarMenu) return;
        
        // Check if sidebar content is scrollable
        function checkScrollable() {
            const isScrollable = sidebarMenu.scrollHeight > sidebarMenu.clientHeight;
            
            if (isScrollable) {
                sidebarMenu.classList.add('has-scroll');
                addScrollShadows();
            } else {
                sidebarMenu.classList.remove('has-scroll');
            }
        }
        
        // Add scroll shadow management
        function addScrollShadows() {
            sidebarMenu.addEventListener('scroll', function() {
                const scrollTop = this.scrollTop;
                const scrollHeight = this.scrollHeight;
                const clientHeight = this.clientHeight;
                const maxScroll = scrollHeight - clientHeight;
                
                // Update shadow visibility based on scroll position
                const shadowBefore = sidebarMenu.querySelector('::before');
                const shadowAfter = sidebarMenu.querySelector('::after');
                
                // Top shadow visibility
                if (scrollTop > 10) {
                    sidebarMenu.style.setProperty('--top-shadow-opacity', '1');
                } else {
                    sidebarMenu.style.setProperty('--top-shadow-opacity', '0');
                }
                
                // Bottom shadow visibility
                if (scrollTop < maxScroll - 10) {
                    sidebarMenu.style.setProperty('--bottom-shadow-opacity', '1');
                } else {
                    sidebarMenu.style.setProperty('--bottom-shadow-opacity', '0');
                }
            });
        }
        
        // Initialize scroll state
        checkScrollable();
        
        // Re-check on window resize
        window.addEventListener('resize', function() {
            setTimeout(checkScrollable, 100);
        });
        
        // Re-check when content changes (for dynamic content)
        const observer = new MutationObserver(function(mutations) {
            let shouldRecheck = false;
            mutations.forEach(function(mutation) {
                if (mutation.type === 'childList' || mutation.type === 'subtree') {
                    shouldRecheck = true;
                }
            });
            
            if (shouldRecheck) {
                setTimeout(checkScrollable, 100);
            }
        });
        
        observer.observe(sidebarMenu, {
            childList: true,
            subtree: true,
            attributes: false,
            characterData: false
        });
        
        // Smooth scrolling for programmatic navigation
        function smoothScrollToMenuItem(targetElement) {
            if (!targetElement) return;
            
            const menuRect = sidebarMenu.getBoundingClientRect();
            const targetRect = targetElement.getBoundingClientRect();
            const currentScroll = sidebarMenu.scrollTop;
            
            // Calculate target scroll position
            const targetScroll = currentScroll + targetRect.top - menuRect.top - (menuRect.height / 2) + (targetRect.height / 2);
            
            // Smooth scroll animation
            const startScroll = currentScroll;
            const scrollDiff = targetScroll - startScroll;
            const duration = 300;
            let startTime = null;
            
            function animateScroll(currentTime) {
                if (!startTime) startTime = currentTime;
                
                const progress = Math.min((currentTime - startTime) / duration, 1);
                const easeProgress = 1 - Math.pow(1 - progress, 3); // easeOutCubic
                
                sidebarMenu.scrollTop = startScroll + (scrollDiff * easeProgress);
                
                if (progress < 1) {
                    requestAnimationFrame(animateScroll);
                }
            }
            
            requestAnimationFrame(animateScroll);
        }
        
        // Add smooth scroll to active menu items
        const activeMenuItem = document.querySelector('.sidebar-menu-link.active');
        if (activeMenuItem) {
            setTimeout(() => {
                smoothScrollToMenuItem(activeMenuItem);
            }, 500);
        }
        
        // Enhanced keyboard navigation
        sidebarMenu.addEventListener('keydown', function(e) {
            const menuItems = Array.from(document.querySelectorAll('.sidebar-menu-link'));
            const currentIndex = menuItems.findIndex(item => item === document.activeElement);
            
            switch(e.key) {
                case 'ArrowUp':
                    e.preventDefault();
                    const prevIndex = currentIndex > 0 ? currentIndex - 1 : menuItems.length - 1;
                    menuItems[prevIndex].focus();
                    smoothScrollToMenuItem(menuItems[prevIndex]);
                    break;
                    
                case 'ArrowDown':
                    e.preventDefault();
                    const nextIndex = currentIndex < menuItems.length - 1 ? currentIndex + 1 : 0;
                    menuItems[nextIndex].focus();
                    smoothScrollToMenuItem(menuItems[nextIndex]);
                    break;
                    
                case 'Home':
                    e.preventDefault();
                    menuItems[0].focus();
                    smoothScrollToMenuItem(menuItems[0]);
                    break;
                    
                case 'End':
                    e.preventDefault();
                    menuItems[menuItems.length - 1].focus();
                    smoothScrollToMenuItem(menuItems[menuItems.length - 1]);
                    break;
            }
        });
    }
    
    // Initialize enhanced header functionality
    initializeEnhancedHeader();
    
    function initializeEnhancedHeader() {
        const header = document.getElementById('appHeader');
        const userProfile = document.getElementById('headerUserProfile');
        const userDropdown = document.getElementById('headerUserDropdown');
        const searchInput = document.getElementById('headerSearchInput');
        const searchSuggestions = document.getElementById('headerSearchSuggestions');
        
        // Header scroll effect
        let lastScrollTop = 0;
        window.addEventListener('scroll', function() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            if (scrollTop > 50) {
                header.classList.add('scrolled');
                        } else {
                header.classList.remove('scrolled');
            }
            
            lastScrollTop = scrollTop;
        });
        
        // User dropdown functionality
        if (userProfile && userDropdown) {
            userProfile.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                userDropdown.classList.toggle('show');
            });
            
            // Close dropdown when clicking outside
            document.addEventListener('click', function(e) {
                if (!userProfile.contains(e.target) && !userDropdown.contains(e.target)) {
                    userDropdown.classList.remove('show');
                }
            });
            
            // Close dropdown when pressing Escape
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    userDropdown.classList.remove('show');
            }
        });
    }
        
        // Enhanced search functionality
        if (searchInput && searchSuggestions) {
            let searchTimeout;
            
            searchInput.addEventListener('input', function() {
                const query = this.value.trim();
                
                clearTimeout(searchTimeout);
                searchTimeout = setTimeout(() => {
                    if (query.length >= 2) {
                        showSearchSuggestions(query);
                    } else {
                        hideSearchSuggestions();
                    }
                }, 300);
            });
            
            searchInput.addEventListener('focus', function() {
                if (this.value.trim().length >= 2) {
                    showSearchSuggestions(this.value.trim());
                }
            });
            
            searchInput.addEventListener('blur', function() {
                // Delay hiding to allow clicking on suggestions
                setTimeout(() => {
                    hideSearchSuggestions();
                }, 200);
            });
            
            function showSearchSuggestions(query) {
                // Sample suggestions - in a real app, this would be an AJAX call
                const suggestions = [
                    { type: 'patient', icon: 'fa-user', text: `Patient: ${query}...` },
                    { type: 'appointment', icon: 'fa-calendar', text: `Rendez-vous: ${query}...` },
                    { type: 'voucher', icon: 'fa-ticket', text: `Bon: ${query}...` }
                ];
                
                let html = '';
                suggestions.forEach(suggestion => {
                    html += `
                        <a href="#" class="header-search-suggestion">
                            <i class="fa-solid ${suggestion.icon} header-search-suggestion-icon"></i>
                            ${suggestion.text}
                        </a>
                    `;
                });
                
                searchSuggestions.innerHTML = html;
                searchSuggestions.classList.add('show');
            }
            
            function hideSearchSuggestions() {
                searchSuggestions.classList.remove('show');
            }
        }
        
        // Notification interactions
        const notificationItems = document.querySelectorAll('.header-notification-item');
        notificationItems.forEach(item => {
            item.addEventListener('click', function() {
                // Add click animation
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
                
                // In a real app, this would show notification dropdown
                console.log('Notification clicked');
        });
    });
        
        // Quick action button functionality
        const quickActionBtns = document.querySelectorAll('.header-quick-action-btn');
        quickActionBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                // Add click animation
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    this.style.transform = '';
                }, 150);
                
                // In a real app, this would trigger the respective action
                console.log('Quick action clicked:', this.textContent.trim());
            });
        });
    }

    // Add active class to current page menu item
    const currentPath = window.location.pathname;
    const menuLinks = document.querySelectorAll('.sidebar-menu-link');
    
    menuLinks.forEach(function(link) {
        const href = link.getAttribute('href');
        if (href === currentPath || (currentPath.startsWith(href) && href !== '/')) {
            link.classList.add('active');
        }
    });
}

function renderCharts() {
    renderRegistrationsChart();
    renderUserTypesChart();
    renderDailyAppointmentsChart();
    renderServiceBreakdownChart();
    renderWeeklyPatientsChart();
    renderDiagnosisBreakdownChart();
    renderRehabProgressChart();
}

function renderRegistrationsChart() {
    const chartElement = document.getElementById('registrationsChart');
    if (!chartElement) return;

    const data = chartElement.getAttribute('data-values');
    if (!data) return;

    const values = JSON.parse(data);
    
    const ctx = chartElement.getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jui', 'Jui', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc'],
            datasets: [{
                label: 'Nouveaux patients',
                data: values,
                borderColor: '#0066cc',
                backgroundColor: 'rgba(0, 102, 204, 0.1)',
                borderWidth: 2,
                tension: 0.3,
                fill: true,
                pointBackgroundColor: '#ffffff',
                pointBorderColor: '#0066cc',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: '#ffffff',
                    titleColor: '#343a40',
                    bodyColor: '#343a40',
                    borderColor: '#e9ecef',
                    borderWidth: 1,
                    titleFont: {
                        weight: 'bold'
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        drawBorder: false
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

function renderUserTypesChart() {
    const chartElement = document.getElementById('userTypesChart');
    if (!chartElement) return;

    const data = chartElement.getAttribute('data-values');
    if (!data) return;

    const values = JSON.parse(data);
    
    const ctx = chartElement.getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Médecins', 'Administrateurs', 'Patients', 'Autre personnel'],
            datasets: [{
                data: values,
                backgroundColor: [
                    '#0066cc',
                    '#17a2b8',
                    '#28a745',
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
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        boxWidth: 12
                    }
                }
            },
            cutout: '70%'
        }
    });
}

function renderDailyAppointmentsChart() {
    const chartElement = document.getElementById('dailyAppointmentsChart');
    if (!chartElement) return;

    const data = chartElement.getAttribute('data-values');
    if (!data) return;

    const values = JSON.parse(data);
    
    const ctx = chartElement.getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
            datasets: [{
                label: 'Rendez-vous',
                data: values,
                backgroundColor: '#28a745',
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
                        drawBorder: false
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

function renderServiceBreakdownChart() {
    const chartElement = document.getElementById('serviceBreakdownChart');
    if (!chartElement) return;

    const data = chartElement.getAttribute('data-values');
    if (!data) return;

    const values = JSON.parse(data);
    
    const ctx = chartElement.getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Consultations', 'Réadaptation', 'Vaccinations', 'Autre'],
            datasets: [{
                data: values,
                backgroundColor: [
                    '#0066cc',
                    '#28a745',
                    '#ffc107',
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
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        boxWidth: 12
                    }
                }
            }
        }
    });
}

function renderWeeklyPatientsChart() {
    const chartElement = document.getElementById('weeklyPatientsChart');
    if (!chartElement) return;

    const data = chartElement.getAttribute('data-values');
    if (!data) return;

    const values = JSON.parse(data);
    
    const ctx = chartElement.getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven'],
            datasets: [{
                label: 'Patients',
                data: values,
                backgroundColor: '#0066cc',
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
                        drawBorder: false
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

function renderDiagnosisBreakdownChart() {
    const chartElement = document.getElementById('diagnosisBreakdownChart');
    if (!chartElement) return;

    const data = chartElement.getAttribute('data-values');
    if (!data) return;

    const values = JSON.parse(data);
    
    const ctx = chartElement.getContext('2d');
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Paralysie cérébrale', 'Retard de développement', 'Malnutrition', 'Traumatisme', 'Autre'],
            datasets: [{
                data: values,
                backgroundColor: [
                    '#0066cc',
                    '#28a745',
                    '#ffc107',
                    '#dc3545',
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
                    position: 'bottom',
                    labels: {
                        padding: 20,
                        boxWidth: 12
                    }
                }
            }
        }
    });
}

function renderRehabProgressChart() {
    const chartElement = document.getElementById('rehabProgressChart');
    if (!chartElement) return;

    const data = chartElement.getAttribute('data-values');
    if (!data) return;

    const values = JSON.parse(data);
    
    const ctx = chartElement.getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Semaine 1', 'Semaine 2', 'Semaine 3', 'Semaine 4', 'Semaine 5', 'Semaine 6'],
            datasets: [{
                label: 'Progression',
                data: values,
                borderColor: '#28a745',
                backgroundColor: 'rgba(40, 167, 69, 0.1)',
                borderWidth: 2,
                tension: 0.3,
                fill: true,
                pointBackgroundColor: '#ffffff',
                pointBorderColor: '#28a745',
                pointBorderWidth: 2
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
                    max: 100,
                    grid: {
                        drawBorder: false
                    },
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
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

/* ========================================
   PHASE 2.2: ENHANCED CONTENT AREA INTERACTIONS
======================================== */

// Premium Card Interactions
function initializeEnhancedCards() {
    // Add premium interaction to all modern cards
    const cards = document.querySelectorAll('.card-modern, .card-mali, .card-medical, .card-premium');
    
    cards.forEach(card => {
        // Add interactive class
        card.classList.add('card-interactive');
        
        // Enhanced hover parallax effect
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            
            const centerX = rect.width / 2;
            const centerY = rect.height / 2;
            
            const rotateX = (y - centerY) / 10;
            const rotateY = (centerX - x) / 10;
            
            card.style.transform = `
                perspective(1000px) 
                rotateX(${rotateX}deg) 
                rotateY(${rotateY}deg) 
                translateZ(20px) 
                scale(1.02)
            `;
        });
        
        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
        });
        
        // Click ripple effect
        card.addEventListener('click', (e) => {
            if (!card.querySelector('.ripple')) {
                const ripple = document.createElement('span');
                ripple.classList.add('ripple');
                
                const rect = card.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                const x = e.clientX - rect.left - size / 2;
                const y = e.clientY - rect.top - size / 2;
                
                ripple.style.cssText = `
                    position: absolute;
                    width: ${size}px;
                    height: ${size}px;
                    left: ${x}px;
                    top: ${y}px;
                    background: radial-gradient(circle, rgba(12, 124, 89, 0.3) 0%, transparent 70%);
                    border-radius: 50%;
                    transform: scale(0);
                    animation: ripple 0.6s ease-out;
                    pointer-events: none;
                    z-index: 10;
                `;
                
                card.appendChild(ripple);
                
                setTimeout(() => {
                    ripple.remove();
                }, 600);
            }
        });
    });
}

// Enhanced List Interactions
function initializeEnhancedLists() {
    const listItems = document.querySelectorAll('.list-modern-item');
    
    listItems.forEach((item, index) => {
        // Staggered animation on scroll
        item.style.animationDelay = `${index * 0.1}s`;
        
        // Enhanced hover effect with magnetic attraction
        item.addEventListener('mouseenter', (e) => {
            const icon = item.querySelector('.list-modern-item-icon');
            if (icon) {
                icon.style.transform = 'scale(1.2) rotate(5deg)';
                icon.style.boxShadow = '0 8px 25px rgba(12, 124, 89, 0.4)';
            }
            
            // Magnetic effect for neighboring items
            const siblings = Array.from(item.parentNode.children);
            siblings.forEach((sibling, sibIndex) => {
                if (sibling !== item) {
                    const distance = Math.abs(sibIndex - index);
                    if (distance <= 2) {
                        const translateX = distance === 1 ? '4px' : '2px';
                        sibling.style.transform = `translateX(${translateX})`;
                        sibling.style.opacity = '0.7';
                    }
                }
            });
        });
        
        item.addEventListener('mouseleave', () => {
            const icon = item.querySelector('.list-modern-item-icon');
            if (icon) {
                icon.style.transform = '';
                icon.style.boxShadow = '';
            }
            
            // Reset neighboring items
            const siblings = Array.from(item.parentNode.children);
            siblings.forEach(sibling => {
                sibling.style.transform = '';
                sibling.style.opacity = '';
            });
        });
    });
}

// Enhanced Modal System
function initializeEnhancedModals() {
    // Auto-initialize modals
    document.addEventListener('click', (e) => {
        if (e.target.matches('[data-modal]')) {
            e.preventDefault();
            const modalId = e.target.getAttribute('data-modal');
            openModal(modalId);
        }
        
        if (e.target.matches('.overlay-modern') || e.target.matches('[data-modal-close]')) {
            closeModal();
        }
    });
    
    // ESC key to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

function openModal(modalId) {
    const overlay = document.getElementById(modalId);
    if (overlay) {
        overlay.classList.add('active');
        document.body.classList.add('modal-open');
        
        // Prevent background scroll
        document.body.style.overflow = 'hidden';
        
        // Focus trap
        const modal = overlay.querySelector('.modal-modern');
        if (modal) {
            const focusableElements = modal.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            if (focusableElements.length) {
                focusableElements[0].focus();
            }
        }
    }
}

function closeModal() {
    const activeModal = document.querySelector('.overlay-modern.active');
    if (activeModal) {
        activeModal.classList.remove('active');
        document.body.classList.remove('modal-open');
        document.body.style.overflow = '';
    }
}

// Enhanced Animation Observer
function initializeEnhancedAnimations() {
    const animatedElements = document.querySelectorAll(`
        .fade-in, .slide-in-left, .slide-in-right, .slide-in-up, .slide-in-down,
        .bounce-in, .scale-in, .rotate-in, .card-modern, .list-modern-item
    `);
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.animationPlayState = 'running';
                
                // Add staggered animation to child elements
                const children = entry.target.querySelectorAll('.stagger-1, .stagger-2, .stagger-3, .stagger-4, .stagger-custom');
                children.forEach((child, index) => {
                    child.style.animationDelay = `${index * 0.1}s`;
                    child.classList.add('fade-in');
                });
                
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '50px'
    });
    
    animatedElements.forEach(el => {
        el.style.animationPlayState = 'paused';
        observer.observe(el);
    });
}

// Enhanced Scroll Effects
function initializeEnhancedScrollEffects() {
    let ticking = false;
    
    function updateScrollEffects() {
        const scrolled = window.pageYOffset;
        const rate = scrolled * -0.5;
        
        // Parallax effect for floating elements
        const floatingElements = document.querySelectorAll('.float-animation');
        floatingElements.forEach(el => {
            el.style.transform = `translateY(${rate * 0.1}px)`;
        });
        
        // Enhanced header blur based on scroll
        const header = document.querySelector('.header-enhanced');
        if (header) {
            const blurAmount = Math.min(scrolled / 10, 20);
            header.style.backdropFilter = `blur(${20 + blurAmount}px)`;
            header.style.background = `rgba(255, 255, 255, ${0.95 + (scrolled / 1000) * 0.05})`;
        }
        
        ticking = false;
    }
    
    function requestScrollUpdate() {
        if (!ticking) {
            requestAnimationFrame(updateScrollEffects);
            ticking = true;
        }
    }
    
    window.addEventListener('scroll', requestScrollUpdate);
}

// Enhanced Performance Optimizations
function initializePerformanceOptimizations() {
    // Lazy load animations
    const lazyAnimations = document.querySelectorAll('[data-lazy-animation]');
    const animationObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const animationType = entry.target.getAttribute('data-lazy-animation');
                entry.target.classList.add(animationType);
                animationObserver.unobserve(entry.target);
            }
        });
    });
    
    lazyAnimations.forEach(el => animationObserver.observe(el));
    
    // Reduce motion for accessibility
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        document.documentElement.style.setProperty('--transition-base', '0ms');
        document.documentElement.style.setProperty('--transition-fast', '0ms');
        
        // Disable complex animations
        const complexAnimations = document.querySelectorAll('.float-animation, .pulse-gentle, .card-pulse');
        complexAnimations.forEach(el => {
            el.style.animation = 'none';
        });
    }
}

// Enhanced Content Interactions
function initializeContentInteractions() {
    // Enhanced button click feedback
    const buttons = document.querySelectorAll('.btn-mali-primary, .btn-mali-secondary, .btn-medical');
    buttons.forEach(button => {
        button.addEventListener('click', (e) => {
            // Haptic feedback simulation
            button.style.transform = 'scale(0.95)';
            setTimeout(() => {
                button.style.transform = '';
            }, 100);
            
            // Success particle effect
            createParticleEffect(e.target, 'success');
        });
    });
    
    // Enhanced form interactions
    const formControls = document.querySelectorAll('.form-control-modern');
    formControls.forEach(control => {
        control.addEventListener('focus', () => {
            control.parentNode.classList.add('focused');
        });
        
        control.addEventListener('blur', () => {
            control.parentNode.classList.remove('focused');
            if (control.value) {
                control.parentNode.classList.add('filled');
            } else {
                control.parentNode.classList.remove('filled');
            }
        });
    });
}

// Particle Effect System
function createParticleEffect(element, type = 'default') {
    const colors = {
        success: ['#0C7C59', '#FCD116', '#FFFFFF'],
        medical: ['#3498db', '#5dade2', '#FFFFFF'],
        warning: ['#FCD116', '#e6a500', '#FFFFFF'],
        default: ['#0C7C59', '#FCD116', '#CE1126']
    };
    
    const particleColors = colors[type] || colors.default;
    const rect = element.getBoundingClientRect();
    
    for (let i = 0; i < 6; i++) {
        const particle = document.createElement('div');
        particle.style.cssText = `
            position: fixed;
            width: 4px;
            height: 4px;
            background: ${particleColors[Math.floor(Math.random() * particleColors.length)]};
            border-radius: 50%;
            pointer-events: none;
            z-index: 9999;
            left: ${rect.left + rect.width / 2}px;
            top: ${rect.top + rect.height / 2}px;
        `;
        
        document.body.appendChild(particle);
        
        const angle = (Math.PI * 2 * i) / 6;
        const velocity = 50 + Math.random() * 50;
        
        particle.animate([
            {
                transform: 'translate(0, 0) scale(1)',
                opacity: 1
            },
            {
                transform: `translate(${Math.cos(angle) * velocity}px, ${Math.sin(angle) * velocity}px) scale(0)`,
                opacity: 0
            }
        ], {
            duration: 800,
            easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
        }).onfinish = () => particle.remove();
    }
}

// Initialize all enhanced content area features
function initializeEnhancedContentArea() {
    initializeEnhancedCards();
    initializeEnhancedLists();
    initializeEnhancedModals();
    initializeEnhancedAnimations();
    initializeEnhancedScrollEffects();
    initializePerformanceOptimizations();
    initializeContentInteractions();
    
    console.log('✨ Enhanced Content Area initialized - Phase 2.2 Complete');
}

// Add ripple animation keyframe
const rippleStyle = document.createElement('style');
rippleStyle.textContent = `
    @keyframes ripple {
        to {
            transform: scale(2);
            opacity: 0;
        }
    }
    
    .card-interactive {
        position: relative;
        overflow: hidden;
    }
    
    .form-group-modern.focused .form-label-modern {
        color: var(--mali-green);
        transform: translateY(-2px);
    }
    
    .form-group-modern.filled .form-label-modern {
        font-size: 0.8rem;
        color: var(--mali-green);
    }
`;
document.head.appendChild(rippleStyle); 