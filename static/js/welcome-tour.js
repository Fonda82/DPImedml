/**
 * DPIMedML Welcome Tour System
 * Role-based guided tours for onboarding new users
 */

class WelcomeTour {
    constructor() {
        this.currentStep = 0;
        this.isActive = false;
        this.userRole = null;
        this.tourSteps = {};
        this.overlay = null;
        this.tooltip = null;
        
        // Initialize tour steps for each role
        this.initializeTourSteps();
        
        // Bind methods
        this.nextStep = this.nextStep.bind(this);
        this.previousStep = this.previousStep.bind(this);
        this.skipTour = this.skipTour.bind(this);
        this.endTour = this.endTour.bind(this);
    }
    
    initializeTourSteps() {
        // Superadmin Tour Steps
        this.tourSteps.superadmin = [
            {
                element: '.story-card:first-child',
                title: 'Bienvenue Super Admin!',
                content: 'Voici vos statistiques système principales. Surveillez le nombre total de patients dans le système.',
                position: 'bottom',
                highlight: true
            },
            {
                element: '.story-card:nth-child(2)',
                title: 'Établissements',
                content: 'Suivez le nombre d\'établissements actifs dans votre réseau de soins.',
                position: 'bottom',
                highlight: true
            },
            {
                element: '.widget:has(table)',
                title: 'Gestion des Établissements',
                content: 'Ici vous pouvez voir tous les établissements avec leurs statuts et statistiques de patients.',
                position: 'top',
                highlight: true
            },
            {
                element: '#patientStatsChart',
                title: 'Analyses Avancées',
                content: 'Ces graphiques vous montrent les tendances d\'enregistrement des patients sur 12 mois.',
                position: 'left',
                highlight: true
            },
            {
                element: '.card:has(.icon-circle)',
                title: 'Actions Administratives',
                content: 'Utilisez ces raccourcis pour créer rapidement de nouveaux établissements et gérer le personnel.',
                position: 'top',
                highlight: true
            }
        ];
        
        // Facility Admin Tour Steps
        this.tourSteps.facility_admin = [
            {
                element: '.story-card:first-child',
                title: 'Bienvenue Admin Structure!',
                content: 'Voici le nombre total de patients dans votre établissement.',
                position: 'bottom',
                highlight: true
            },
            {
                element: '.story-card:nth-child(2)',
                title: 'Rendez-vous du Jour',
                content: 'Surveillez le nombre de rendez-vous programmés pour aujourd\'hui.',
                position: 'bottom',
                highlight: true
            },
            {
                element: '.widget:has(table)',
                title: 'Rendez-vous en Temps Réel',
                content: 'Consultez tous les rendez-vous du jour avec les détails des patients et médecins.',
                position: 'top',
                highlight: true
            },
            {
                element: '.card:has(.icon-circle)',
                title: 'Actions Rapides',
                content: 'Créez rapidement de nouveaux patients, ajoutez du personnel ou planifiez des rendez-vous.',
                position: 'top',
                highlight: true
            },
            {
                element: '.sidebar-menu-link:contains("Patients")',
                title: 'Navigation',
                content: 'Utilisez le menu latéral pour accéder aux différentes sections de gestion.',
                position: 'right',
                highlight: true
            }
        ];
        
        // Doctor Tour Steps
        this.tourSteps.doctor = [
            {
                element: '.story-card:first-child',
                title: 'Bienvenue Docteur!',
                content: 'Voici vos patients assignés. Vous pouvez voir votre charge de travail actuelle.',
                position: 'bottom',
                highlight: true
            },
            {
                element: '.story-card:nth-child(2)',
                title: 'Rendez-vous',
                content: 'Suivez vos rendez-vous d\'aujourd\'hui et planifiez votre journée.',
                position: 'bottom',
                highlight: true
            },
            {
                element: '.sidebar-menu-link:contains("Patients")',
                title: 'Mes Patients',
                content: 'Accédez à la liste de vos patients pour consulter leurs dossiers médicaux.',
                position: 'right',
                highlight: true
            },
            {
                element: '.sidebar-menu-link:contains("Bons")',
                title: 'Gestion des Bons',
                content: 'Émettez et gérez les bons de soins pour vos patients.',
                position: 'right',
                highlight: true
            },
            {
                element: '.sidebar-menu-link:contains("Réhabilitation")',
                title: 'Plans de Réhabilitation',
                content: 'Créez et suivez les plans de réhabilitation personnalisés pour vos patients.',
                position: 'right',
                highlight: true
            }
        ];
        
        // Patient Tour Steps
        this.tourSteps.patient = [
            {
                element: '.story-card:first-child',
                title: 'Bienvenue!',
                content: 'Voici un aperçu de vos rendez-vous. Vous pouvez voir vos prochains RDV et votre historique.',
                position: 'bottom',
                highlight: true
            },
            {
                element: '.widget:has(.avatar-lg)',
                title: 'Votre Profil',
                content: 'Ici vous retrouvez toutes vos informations personnelles et coordonnées.',
                position: 'top',
                highlight: true
            },
            {
                element: '.sidebar-menu-link:contains("Dossier")',
                title: 'Dossier Médical',
                content: 'Consultez votre dossier médical complet, résultats d\'examens et prescriptions.',
                position: 'right',
                highlight: true
            },
            {
                element: '.sidebar-menu-link:contains("Rendez-vous")',
                title: 'Mes Rendez-vous',
                content: 'Gérez vos rendez-vous: consultez l\'historique et les prochains RDV.',
                position: 'right',
                highlight: true
            },
            {
                element: '.sidebar-menu-link:contains("Bons")',
                title: 'Mes Bons',
                content: 'Suivez vos bons de soins émis par votre médecin.',
                position: 'right',
                highlight: true
            }
        ];
    }
    
    createOverlay() {
        this.overlay = document.createElement('div');
        this.overlay.className = 'tour-overlay';
        this.overlay.innerHTML = `
            <div class="tour-backdrop"></div>
            <div class="tour-controls">
                <button class="tour-btn tour-skip" onclick="welcomeTour.skipTour()">
                    <i class="fas fa-times"></i> Ignorer le tour
                </button>
                <button class="tour-btn tour-replay" onclick="welcomeTour.replayTour()" style="display: none;">
                    <i class="fas fa-redo"></i> Revoir le tour
                </button>
            </div>
        `;
        document.body.appendChild(this.overlay);
    }
    
    createTooltip() {
        this.tooltip = document.createElement('div');
        this.tooltip.className = 'tour-tooltip';
        document.body.appendChild(this.tooltip);
    }
    
    showStep(stepIndex) {
        const steps = this.tourSteps[this.userRole];
        if (!steps || stepIndex >= steps.length) {
            this.endTour();
            return;
        }
        
        const step = steps[stepIndex];
        const element = document.querySelector(step.element);
        
        if (!element) {
            // Skip to next step if element not found
            this.nextStep();
            return;
        }
        
        // Update tooltip content
        this.tooltip.innerHTML = `
            <div class="tour-tooltip-header">
                <h4 class="tour-tooltip-title">${step.title}</h4>
                <button class="tour-close" onclick="welcomeTour.endTour()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="tour-tooltip-content">
                <p>${step.content}</p>
            </div>
            <div class="tour-tooltip-footer">
                <div class="tour-progress">
                    <span class="tour-step-counter">${stepIndex + 1} de ${steps.length}</span>
                    <div class="tour-progress-bar">
                        <div class="tour-progress-fill" style="width: ${((stepIndex + 1) / steps.length) * 100}%"></div>
                    </div>
                </div>
                <div class="tour-navigation">
                    <button class="tour-btn tour-prev" onclick="welcomeTour.previousStep()" 
                            ${stepIndex === 0 ? 'disabled' : ''}>
                        <i class="fas fa-arrow-left"></i> Précédent
                    </button>
                    <button class="tour-btn tour-next" onclick="welcomeTour.nextStep()">
                        ${stepIndex === steps.length - 1 ? 'Terminer' : 'Suivant'} 
                        <i class="fas fa-arrow-right"></i>
                    </button>
                </div>
            </div>
        `;
        
        // Position tooltip
        this.positionTooltip(element, step.position);
        
        // Highlight element
        if (step.highlight) {
            this.highlightElement(element);
        }
        
        // Show tooltip with animation
        this.tooltip.style.display = 'block';
        setTimeout(() => {
            this.tooltip.classList.add('tour-tooltip-visible');
        }, 50);
        
        // Scroll element into view
        element.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center' 
        });
    }
    
    positionTooltip(element, position) {
        const rect = element.getBoundingClientRect();
        const tooltip = this.tooltip;
        const tooltipRect = tooltip.getBoundingClientRect();
        
        // Reset classes
        tooltip.className = 'tour-tooltip tour-tooltip-visible';
        
        let top, left;
        
        switch (position) {
            case 'top':
                top = rect.top - tooltipRect.height - 15;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
                tooltip.classList.add('tour-tooltip-top');
                break;
            case 'bottom':
                top = rect.bottom + 15;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
                tooltip.classList.add('tour-tooltip-bottom');
                break;
            case 'left':
                top = rect.top + (rect.height - tooltipRect.height) / 2;
                left = rect.left - tooltipRect.width - 15;
                tooltip.classList.add('tour-tooltip-left');
                break;
            case 'right':
                top = rect.top + (rect.height - tooltipRect.height) / 2;
                left = rect.right + 15;
                tooltip.classList.add('tour-tooltip-right');
                break;
            default:
                top = rect.bottom + 15;
                left = rect.left + (rect.width - tooltipRect.width) / 2;
                tooltip.classList.add('tour-tooltip-bottom');
        }
        
        // Ensure tooltip stays within viewport
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        if (left < 10) left = 10;
        if (left + tooltipRect.width > viewportWidth - 10) {
            left = viewportWidth - tooltipRect.width - 10;
        }
        if (top < 10) top = 10;
        if (top + tooltipRect.height > viewportHeight - 10) {
            top = viewportHeight - tooltipRect.height - 10;
        }
        
        tooltip.style.top = `${top + window.scrollY}px`;
        tooltip.style.left = `${left}px`;
    }
    
    highlightElement(element) {
        // Remove previous highlights
        document.querySelectorAll('.tour-highlight').forEach(el => {
            el.classList.remove('tour-highlight');
        });
        
        // Add highlight to current element
        element.classList.add('tour-highlight');
        
        // Create spotlight effect
        const rect = element.getBoundingClientRect();
        const backdrop = document.querySelector('.tour-backdrop');
        if (backdrop) {
            backdrop.style.clipPath = `polygon(
                0% 0%, 
                0% 100%, 
                ${rect.left - 10}px 100%, 
                ${rect.left - 10}px ${rect.top - 10}px, 
                ${rect.right + 10}px ${rect.top - 10}px, 
                ${rect.right + 10}px ${rect.bottom + 10}px, 
                ${rect.left - 10}px ${rect.bottom + 10}px, 
                ${rect.left - 10}px 100%, 
                100% 100%, 
                100% 0%
            )`;
        }
    }
    
    nextStep() {
        this.currentStep++;
        this.showStep(this.currentStep);
    }
    
    previousStep() {
        if (this.currentStep > 0) {
            this.currentStep--;
            this.showStep(this.currentStep);
        }
    }
    
    skipTour() {
        this.endTour();
        this.markTourAsCompleted();
    }
    
    endTour() {
        this.isActive = false;
        
        // Remove highlights
        document.querySelectorAll('.tour-highlight').forEach(el => {
            el.classList.remove('tour-highlight');
        });
        
        // Remove tooltip
        if (this.tooltip) {
            this.tooltip.remove();
            this.tooltip = null;
        }
        
        // Remove overlay
        if (this.overlay) {
            this.overlay.remove();
            this.overlay = null;
        }
        
        // Mark as completed
        this.markTourAsCompleted();
        
        // Show replay button
        this.showReplayButton();
    }
    
    markTourAsCompleted() {
        if (this.userRole) {
            localStorage.setItem(`tour_completed_${this.userRole}`, 'true');
            localStorage.setItem(`tour_completed_date_${this.userRole}`, new Date().toISOString());
        }
    }
    
    isTourCompleted(role) {
        return localStorage.getItem(`tour_completed_${role}`) === 'true';
    }
    
    showReplayButton() {
        // Add replay button to top bar
        const topbar = document.querySelector('.topbar-nav');
        if (topbar && !document.querySelector('.tour-replay-btn')) {
            const replayBtn = document.createElement('div');
            replayBtn.className = 'topbar-nav-item tour-replay-btn';
            replayBtn.innerHTML = `
                <button class="btn btn-link text-primary" onclick="welcomeTour.replayTour()" 
                        data-bs-toggle="tooltip" title="Revoir le tour d'accueil">
                    <i class="fas fa-question-circle"></i>
                </button>
            `;
            topbar.insertBefore(replayBtn, topbar.firstChild);
        }
    }
    
    replayTour() {
        this.startTour(this.userRole);
    }
    
    startTour(userRole) {
        this.userRole = userRole;
        this.currentStep = 0;
        this.isActive = true;
        
        // Remove existing tour elements
        if (this.tooltip) this.tooltip.remove();
        if (this.overlay) this.overlay.remove();
        
        // Create tour elements
        this.createOverlay();
        this.createTooltip();
        
        // Start tour
        setTimeout(() => {
            this.showStep(0);
        }, 500);
    }
    
    autoStartTour() {
        // Detect user role from page
        const userRole = this.detectUserRole();
        
        if (userRole && !this.isTourCompleted(userRole)) {
            // Show welcome message first
            this.showWelcomeMessage(userRole);
        } else if (userRole) {
            // Show replay button for completed tours
            this.userRole = userRole;
            this.showReplayButton();
        }
    }
    
    detectUserRole() {
        // Detect role from URL or page content
        if (window.location.href.includes('/superadmin/')) return 'superadmin';
        if (window.location.href.includes('/facility-admin/')) return 'facility_admin';
        if (window.location.href.includes('/doctor/')) return 'doctor';
        if (window.location.href.includes('/patient/')) return 'patient';
        
        // Fallback: detect from user role text
        const roleText = document.querySelector('.topbar-user-role')?.textContent?.toLowerCase();
        if (roleText?.includes('super')) return 'superadmin';
        if (roleText?.includes('administrateur')) return 'facility_admin';
        if (roleText?.includes('médecin')) return 'doctor';
        if (roleText?.includes('patient')) return 'patient';
        
        return null;
    }
    
    showWelcomeMessage(userRole) {
        const roleNames = {
            'superadmin': 'Super Administrateur',
            'facility_admin': 'Administrateur de Structure',
            'doctor': 'Médecin',
            'patient': 'Patient'
        };
        
        const modal = document.createElement('div');
        modal.className = 'tour-welcome-modal';
        modal.innerHTML = `
            <div class="modal-backdrop show"></div>
            <div class="modal show d-block" tabindex="-1">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-header bg-primary text-white">
                            <h5 class="modal-title">
                                <i class="fas fa-hand-wave me-2"></i>
                                Bienvenue dans DPIMedML!
                            </h5>
                        </div>
                        <div class="modal-body text-center">
                            <div class="mb-4">
                                <i class="fas fa-user-circle text-primary" style="font-size: 4rem;"></i>
                            </div>
                            <h6 class="mb-3">Bienvenue ${roleNames[userRole]}!</h6>
                            <p class="mb-4">
                                Nous allons vous faire découvrir les principales fonctionnalités 
                                de votre tableau de bord en 30 secondes.
                            </p>
                            <div class="d-grid gap-2">
                                <button class="btn btn-primary" onclick="welcomeTour.startTourFromWelcome('${userRole}')">
                                    <i class="fas fa-play me-2"></i>Commencer le tour
                                </button>
                                <button class="btn btn-outline-secondary" onclick="welcomeTour.skipWelcome()">
                                    Ignorer pour cette fois
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        this.welcomeModal = modal;
    }
    
    startTourFromWelcome(userRole) {
        if (this.welcomeModal) {
            this.welcomeModal.remove();
            this.welcomeModal = null;
        }
        this.startTour(userRole);
    }
    
    skipWelcome() {
        if (this.welcomeModal) {
            this.welcomeModal.remove();
            this.welcomeModal = null;
        }
        this.userRole = this.detectUserRole();
        this.markTourAsCompleted();
        this.showReplayButton();
    }
}

// Initialize tour system
const welcomeTour = new WelcomeTour();

// Auto-start on page load
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        welcomeTour.autoStartTour();
    }, 1000);
});

// Handle window resize
window.addEventListener('resize', function() {
    if (welcomeTour.isActive && welcomeTour.tooltip) {
        // Reposition current tooltip
        const steps = welcomeTour.tourSteps[welcomeTour.userRole];
        if (steps && steps[welcomeTour.currentStep]) {
            const step = steps[welcomeTour.currentStep];
            const element = document.querySelector(step.element);
            if (element) {
                welcomeTour.positionTooltip(element, step.position);
                welcomeTour.highlightElement(element);
            }
        }
    }
}); 