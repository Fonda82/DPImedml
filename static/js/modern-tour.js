/**
 * DPIMedML Modern Tour System
 * Lightweight and responsive guided tour for Mali healthcare system
 */

class ModernTour {
    constructor() {
        this.currentStep = 0;
        this.isActive = false;
        this.userRole = null;
        this.tourSteps = [];
        this.elements = {};
        
        // Bind methods
        this.nextStep = this.nextStep.bind(this);
        this.previousStep = this.previousStep.bind(this);
        this.closeTour = this.closeTour.bind(this);
        this.skipTour = this.skipTour.bind(this);
        
        // Initialize tour steps for each role
        this.initializeTourSteps();
    }
    
    initializeTourSteps() {
        // SuperAdmin Tour - Focus on key management features
        this.tourSteps.superadmin = [
            {
                element: '.quick-actions-bar',
                title: 'Bienvenue Super Admin!',
                content: 'Utilisez cette barre d\'actions rapides pour accéder aux fonctions principales : créer des établissements, ajouter du personnel et voir les rapports.',
                position: 'bottom'
            },
            {
                element: '.kpi-card:first-child',
                title: 'Indicateurs TDR',
                content: 'Surveillez les indicateurs clés de performance conformes aux exigences du TDR : taux de prise en charge, temps d\'attente et fidélisation.',
                position: 'bottom'
            },
            {
                element: '.analytics-widget:first-child',
                title: 'Analytics Géographiques',
                content: 'Visualisez la distribution géographique des patients par commune de Bamako pour optimiser les ressources.',
                position: 'top'
            },
            {
                element: '.sidebar-menu-link[href*="facilities"]',
                title: 'Gestion Multi-Établissements',
                content: 'Gérez tous les établissements du réseau depuis cette interface centralisée.',
                position: 'right'
            },
            {
                element: '.sidebar-menu-link[href*="security"]',
                title: 'Sécurité & Conformité',
                content: 'Accédez aux tableaux de bord de sécurité et de conformité RGPD pour superviser la protection des données.',
                position: 'right'
            }
        ];
        
        // Facility Admin Tour - Focus on facility management
        this.tourSteps.facility_admin = [
            {
                element: '.quick-actions-bar',
                title: 'Bienvenue Admin Structure!',
                content: 'Gérez votre établissement efficacement avec ces actions rapides pour les patients, le personnel et les rapports.',
                position: 'bottom'
            },
            {
                element: '.kpi-card:first-child',
                title: 'Performances de votre Établissement',
                content: 'Suivez les métriques de votre établissement : patients pris en charge, temps d\'attente et taux de fidélisation.',
                position: 'bottom'
            },
            {
                element: '.sidebar-menu-link[href*="staff"]',
                title: 'Gestion du Personnel',
                content: 'Administrez votre équipe médicale et non-médicale depuis cette section.',
                position: 'right'
            },
            {
                element: '.sidebar-menu-link[href*="appointments"]',
                title: 'Planning des Rendez-vous',
                content: 'Coordonnez tous les rendez-vous de votre établissement en temps réel.',
                position: 'right'
            }
        ];
        
        // Doctor Tour - Focus on patient care
        this.tourSteps.doctor = [
            {
                element: '.kpi-card:first-child',
                title: 'Bienvenue Docteur!',
                content: 'Voici un aperçu de votre charge de travail et des patients sous votre responsabilité.',
                position: 'bottom'
            },
            {
                element: '.sidebar-menu-link[href*="patients"]',
                title: 'Mes Patients',
                content: 'Accédez rapidement à vos patients assignés et leurs dossiers médicaux complets.',
                position: 'right'
            },
            {
                element: '.sidebar-menu-link[href*="rehabilitation"]',
                title: 'Plans de Réhabilitation',
                content: 'Créez et suivez les plans de réhabilitation personnalisés pour vos jeunes patients.',
                position: 'right'
            },
            {
                element: '.sidebar-menu-link[href*="vouchers"]',
                title: 'Émission de Bons',
                content: 'Émettez des bons de soins électroniques pour faciliter l\'accès aux services pour vos patients.',
                position: 'right'
            }
        ];
        
        // Patient Tour - Focus on personal healthcare
        this.tourSteps.patient = [
            {
                element: '.kpi-card:first-child',
                title: 'Bienvenue!',
                content: 'Voici votre tableau de bord personnel avec vos prochains rendez-vous et informations de santé.',
                position: 'bottom'
            },
            {
                element: '.sidebar-menu-link[href*="medical_profile"]',
                title: 'Mon Dossier Médical',
                content: 'Consultez votre dossier médical complet, prescriptions et résultats d\'examens.',
                position: 'right'
            },
            {
                element: '.sidebar-menu-link[href*="appointments"]',
                title: 'Mes Rendez-vous',
                content: 'Gérez vos rendez-vous : consultez l\'historique et les prochains RDV.',
                position: 'right'
            },
            {
                element: '.sidebar-menu-link[href*="vouchers"]',
                title: 'Mes Bons de Santé',
                content: 'Suivez vos bons de soins émis par votre médecin et leur statut d\'utilisation.',
                position: 'right'
            }
        ];
    }
    
    createOverlay() {
        this.elements.overlay = document.createElement('div');
        this.elements.overlay.className = 'modern-tour-overlay';
        document.body.appendChild(this.elements.overlay);
    }
    
    createSpotlight(element) {
        if (this.elements.spotlight) {
            this.elements.spotlight.remove();
        }
        
        const rect = element.getBoundingClientRect();
        this.elements.spotlight = document.createElement('div');
        this.elements.spotlight.className = 'modern-tour-spotlight';
        this.elements.spotlight.style.cssText = `
            top: ${rect.top + window.scrollY - 10}px;
            left: ${rect.left + window.scrollX - 10}px;
            width: ${rect.width + 20}px;
            height: ${rect.height + 20}px;
        `;
        document.body.appendChild(this.elements.spotlight);
    }
    
    createTooltip() {
        this.elements.tooltip = document.createElement('div');
        this.elements.tooltip.className = 'modern-tour-tooltip';
        document.body.appendChild(this.elements.tooltip);
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
            this.currentStep++;
            this.showStep(this.currentStep);
            return;
        }
        
        // Create spotlight
        this.createSpotlight(element);
        
        // Update tooltip content
        this.elements.tooltip.innerHTML = `
            <div class="modern-tour-header">
                <h4 class="modern-tour-title">${step.title}</h4>
                <button class="modern-tour-close" onclick="modernTour.closeTour()">
                    <i class="fa-solid fa-times"></i>
                </button>
            </div>
            <div class="modern-tour-body">
                <p class="modern-tour-text">${step.content}</p>
            </div>
            <div class="modern-tour-footer">
                <div class="modern-tour-progress">
                    <span class="modern-tour-step-counter">${stepIndex + 1} / ${steps.length}</span>
                    <div class="modern-tour-progress-bar">
                        <div class="modern-tour-progress-fill" style="width: ${((stepIndex + 1) / steps.length) * 100}%"></div>
                    </div>
                </div>
                <div class="modern-tour-nav">
                    <button class="modern-tour-btn secondary" onclick="modernTour.previousStep()" 
                            ${stepIndex === 0 ? 'disabled' : ''}>
                        <i class="fa-solid fa-arrow-left"></i> Précédent
                    </button>
                    <button class="modern-tour-btn" onclick="modernTour.nextStep()">
                        ${stepIndex === steps.length - 1 ? 'Terminer' : 'Suivant'} 
                        <i class="fa-solid fa-arrow-right"></i>
                    </button>
                </div>
            </div>
        `;
        
        // Position tooltip
        this.positionTooltip(element, step.position);
        
        // Show tooltip with animation
        setTimeout(() => {
            this.elements.tooltip.classList.add('visible');
        }, 100);
        
        // Scroll element into view
        element.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'center',
            inline: 'center'
        });
    }
    
    positionTooltip(element, position) {
        const rect = element.getBoundingClientRect();
        const tooltip = this.elements.tooltip;
        tooltip.className = `modern-tour-tooltip position-${position}`;
        
        let top, left;
        
        switch (position) {
            case 'top':
                top = rect.top + window.scrollY - tooltip.offsetHeight - 20;
                left = rect.left + window.scrollX + (rect.width / 2) - (tooltip.offsetWidth / 2);
                break;
            case 'bottom':
                top = rect.bottom + window.scrollY + 20;
                left = rect.left + window.scrollX + (rect.width / 2) - (tooltip.offsetWidth / 2);
                break;
            case 'left':
                top = rect.top + window.scrollY + (rect.height / 2) - (tooltip.offsetHeight / 2);
                left = rect.left + window.scrollX - tooltip.offsetWidth - 20;
                break;
            case 'right':
                top = rect.top + window.scrollY + (rect.height / 2) - (tooltip.offsetHeight / 2);
                left = rect.right + window.scrollX + 20;
                break;
        }
        
        // Keep tooltip within viewport
        top = Math.max(10, Math.min(top, window.innerHeight + window.scrollY - tooltip.offsetHeight - 10));
        left = Math.max(10, Math.min(left, window.innerWidth - tooltip.offsetWidth - 10));
        
        tooltip.style.top = `${top}px`;
        tooltip.style.left = `${left}px`;
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
    
    closeTour() {
        this.endTour();
    }
    
    skipTour() {
        this.endTour();
        this.markAsCompleted();
    }
    
    endTour() {
        this.isActive = false;
        
        // Remove all tour elements
        Object.values(this.elements).forEach(element => {
            if (element && element.remove) {
                element.remove();
            }
        });
        
        this.elements = {};
        this.showReplayButton();
    }
    
    startTour(userRole) {
        this.userRole = userRole;
        this.currentStep = 0;
        this.isActive = true;
        
        // Remove existing elements
        this.endTour();
        
        // Create tour elements
        this.createOverlay();
        this.createTooltip();
        
        // Show overlay
        setTimeout(() => {
            this.elements.overlay.classList.add('active');
            this.showStep(0);
        }, 100);
    }
    
    detectUserRole() {
        // Detect user role from page context
        const userRoleBadge = document.querySelector('.header-user-role-badge');
        if (userRoleBadge) {
            const text = userRoleBadge.textContent.trim();
            switch (text) {
                case 'SA': return 'superadmin';
                case 'FA': return 'facility_admin';
                case 'DR': return 'doctor';
                case 'PT': return 'patient';
            }
        }
        
        // Fallback: check sidebar menu items
        if (document.querySelector('[href*="facilities:list"]')) return 'superadmin';
        if (document.querySelector('[href*="staff_list"]')) return 'facility_admin';
        if (document.querySelector('[href*="rehabilitation"]')) return 'doctor';
        if (document.querySelector('[href*="medical_profile"]')) return 'patient';
        
        return 'doctor'; // Default fallback
    }
    
    showWelcomeModal() {
        const userRole = this.detectUserRole();
        if (!userRole || this.isCompleted(userRole)) {
            this.showReplayButton();
            return;
        }
        
        const roleNames = {
            'superadmin': 'Super Administrateur',
            'facility_admin': 'Administrateur de Structure',
            'doctor': 'Médecin',
            'patient': 'Patient'
        };
        
        const modal = document.createElement('div');
        modal.className = 'modern-tour-welcome';
        modal.innerHTML = `
            <div class="modern-tour-welcome-content">
                <div class="modern-tour-welcome-header">
                    <h2 class="modern-tour-welcome-title">Bienvenue dans DPIMedML</h2>
                    <p class="modern-tour-welcome-subtitle">${roleNames[userRole]}</p>
                </div>
                <div class="modern-tour-welcome-body">
                    <p class="modern-tour-welcome-text">
                        Souhaitez-vous découvrir les fonctionnalités principales du système 
                        à travers une visite guidée interactive ?
                    </p>
                    <div class="modern-tour-welcome-actions">
                        <button class="modern-tour-btn" onclick="modernTour.startWelcomeTour('${userRole}')">
                            <i class="fa-solid fa-play"></i> Commencer la visite
                        </button>
                        <button class="modern-tour-btn secondary" onclick="modernTour.skipWelcome()">
                            <i class="fa-solid fa-times"></i> Ignorer
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        setTimeout(() => {
            modal.classList.add('active');
        }, 100);
        
        this.elements.welcomeModal = modal;
    }
    
    startWelcomeTour(userRole) {
        if (this.elements.welcomeModal) {
            this.elements.welcomeModal.remove();
        }
        this.startTour(userRole);
    }
    
    skipWelcome() {
        if (this.elements.welcomeModal) {
            this.elements.welcomeModal.remove();
        }
        this.markAsCompleted();
        this.showReplayButton();
    }
    
    showReplayButton() {
        if (document.querySelector('.modern-tour-replay')) return;
        
        const replayBtn = document.createElement('button');
        replayBtn.className = 'modern-tour-replay';
        replayBtn.innerHTML = '<i class="fa-solid fa-play"></i>';
        replayBtn.title = 'Revoir la visite guidée';
        replayBtn.onclick = () => {
            replayBtn.remove();
            this.showWelcomeModal();
        };
        
        document.body.appendChild(replayBtn);
        
        setTimeout(() => {
            replayBtn.classList.add('visible');
        }, 500);
    }
    
    markAsCompleted() {
        const userRole = this.detectUserRole();
        if (userRole) {
            localStorage.setItem(`tour_completed_${userRole}`, 'true');
            localStorage.setItem(`tour_completed_date_${userRole}`, new Date().toISOString());
        }
    }
    
    isCompleted(userRole) {
        return localStorage.getItem(`tour_completed_${userRole}`) === 'true';
    }
    
    autoStart() {
        // Auto-start tour for first-time users
        setTimeout(() => {
            const userRole = this.detectUserRole();
            if (userRole && !this.isCompleted(userRole)) {
                this.showWelcomeModal();
            } else {
                this.showReplayButton();
            }
        }, 2000); // Delay to ensure page is fully loaded
    }
}

// Initialize modern tour
const modernTour = new ModernTour();

// Auto-start on page load
document.addEventListener('DOMContentLoaded', function() {
    modernTour.autoStart();
});

// Handle window resize
window.addEventListener('resize', function() {
    if (modernTour.isActive && modernTour.elements.tooltip) {
        const steps = modernTour.tourSteps[modernTour.userRole];
        if (steps && steps[modernTour.currentStep]) {
            const step = steps[modernTour.currentStep];
            const element = document.querySelector(step.element);
            if (element) {
                modernTour.createSpotlight(element);
                modernTour.positionTooltip(element, step.position);
            }
        }
    }
});
