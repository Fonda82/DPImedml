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
        // SuperAdmin Tour - Focus on patient oversight and system-wide patient management
        this.tourSteps.superadmin = [
            {
                element: '.kpi-card:first-child',
                title: 'Enfants Pris en Charge - Mali',
                content: 'Voici le cœur du système : le nombre total d\'enfants de 0-14 ans pris en charge dans tout le réseau malien. Objectif TDR : 95% de taux de prise en charge.',
                position: 'bottom'
            },
            {
                element: '.analytics-widget:first-child',
                title: 'Distribution Géographique des Patients',
                content: 'Visualisez où vivent vos jeunes patients à Bamako. Essentiel pour planifier l\'accessibilité des soins et optimiser les ressources par commune.',
                position: 'top'
            },
            {
                element: '.sidebar-menu-link[href*="patients"]',
                title: 'Base de Données Patients Réseau',
                content: 'Accédez à la base centralisée de tous les enfants du réseau. Surveillez les nouvelles admissions et le suivi inter-établissements.',
                position: 'right'
            },
            {
                element: '.quick-actions-bar',
                title: 'Actions Rapides Patient-Centrées',
                content: 'Créez rapidement de nouveaux établissements pour rapprocher les soins des familles, ajoutez du personnel médical, et générez des rapports TDR patient-centrés.',
                position: 'bottom'
            },
            {
                element: '.sidebar-menu-link[href*="hospitalizations"]',
                title: 'Hospitalisations Pédiatriques',
                content: 'Supervisez toutes les hospitalisations d\'enfants dans le réseau. Indicateur TDR clé pour la qualité des soins pédiatriques.',
                position: 'right'
            },
            {
                element: '.sidebar-menu-link[href*="referrals"]',
                title: 'Références Inter-Établissements',
                content: 'Coordonnez le transfert des enfants vers les centres spécialisés. Essentiel pour assurer la continuité des soins pédiatriques.',
                position: 'right'
            }
        ];
        
        // Facility Admin Tour - Focus on patient management at facility level
        this.tourSteps.facility_admin = [
            {
                element: '.kpi-card:first-child',
                title: 'Patients de Votre Établissement',
                content: 'Nombre d\'enfants actuellement pris en charge dans votre structure. Surveillez l\'évolution et les nouvelles admissions quotidiennes.',
                position: 'bottom'
            },
            {
                element: '.kpi-card:nth-child(2)',
                title: 'Rendez-vous Patients du Jour',
                content: 'Consultations programmées aujourd\'hui. Veillez à ce qu\'aucun enfant ne manque son RDV - chaque consultation compte pour leur développement.',
                position: 'bottom'
            },
            {
                element: '.sidebar-menu-link[href*="patients"]',
                title: 'Gestion des Patients',
                content: 'Registre complet de vos jeunes patients : admissions, suivis, dossiers médicaux et plans de réhabilitation personnalisés.',
                position: 'right'
            },
            {
                element: '.sidebar-menu-link[href*="appointments"]',
                title: 'Planning des Consultations',
                content: 'Organisez les rendez-vous pour optimiser le temps de consultation. Réduisez les temps d\'attente pour les familles (objectif : <15min).',
                position: 'right'
            },
            {
                element: '.sidebar-menu-link[href*="vouchers"]',
                title: 'Bons de Soins pour Familles',
                content: 'Supervisez l\'émission des bons électroniques. Facilitez l\'accès aux soins pour les familles à faibles revenus.',
                position: 'right'
            },
            {
                element: '.sidebar-menu-link[href*="hospitalizations"]',
                title: 'Hospitalisations de votre Centre',
                content: 'Gérez les admissions d\'enfants nécessitant une hospitalisation. Suivez la durée de séjour et la qualité des soins.',
                position: 'right'
            }
        ];
        
        // Doctor Tour - Focus on direct patient care and rehabilitation
        this.tourSteps.doctor = [
            {
                element: '.kpi-card:first-child',
                title: 'Vos Jeunes Patients',
                content: 'Enfants sous votre responsabilité médicale. Chaque patient a un parcours unique de réhabilitation adapté à ses besoins spécifiques.',
                position: 'bottom'
            },
            {
                element: '.sidebar-menu-link[href*="patients"]',
                title: 'Mes Patients Assignés',
                content: 'Accédez aux dossiers complets de vos patients : historique médical, évaluations, et progrès de réhabilitation.',
                position: 'right'
            },
            {
                element: '.sidebar-menu-link[href*="rehabilitation"]',
                title: 'Plans de Réhabilitation Pédiatrique',
                content: 'Créez et ajustez les programmes personnalisés : kinésithérapie, orthophonie, soutien psychologique adaptés à chaque enfant.',
                position: 'right'
            },
            {
                element: '.sidebar-menu-link[href*="appointments"]',
                title: 'Consultations et Suivis',
                content: 'Planifiez les consultations régulières. Suivez l\'évolution de chaque enfant et ajustez les traitements selon les progrès.',
                position: 'right'
            },
            {
                element: '.sidebar-menu-link[href*="vouchers"]',
                title: 'Émission de Bons Médicaux',
                content: 'Émettez des bons pour rendre les soins accessibles aux familles. Incluez médicaments, thérapies et équipements spécialisés.',
                position: 'right'
            },
            {
                element: '.sidebar-menu-link[href*="prescriptions"]',
                title: 'Prescriptions Électroniques',
                content: 'Rédigez les ordonnances adaptées aux besoins pédiatriques : dosages appropriés et recommandations pour les parents.',
                position: 'right'
            }
        ];
        
        // Patient Tour - Focus on personal healthcare journey
        this.tourSteps.patient = [
            {
                element: '.kpi-card:first-child',
                title: 'Mon Parcours de Soins',
                content: 'Bienvenue sur votre espace personnel ! Ici vous retrouvez tous vos rendez-vous et le suivi de votre progression.',
                position: 'bottom'
            },
            {
                element: '.sidebar-menu-link[href*="medical_profile"]',
                title: 'Mon Dossier Médical Personnel',
                content: 'Votre dossier complet : diagnostics, traitements, examens et évolution. Partagé en sécurité avec votre équipe médicale.',
                position: 'right'
            },
            {
                element: '.sidebar-menu-link[href*="appointments"]',
                title: 'Mes Rendez-vous Médicaux',
                content: 'Consultez vos prochains RDV et l\'historique. N\'oubliez jamais une consultation importante pour votre santé.',
                position: 'right'
            },
            {
                element: '.sidebar-menu-link[href*="patient_exercises"]',
                title: 'Mon Programme de Réhabilitation',
                content: 'Exercices personnalisés prescrits par votre médecin. Suivez vos progrès et marquez les exercices accomplis.',
                position: 'right'
            },
            {
                element: '.sidebar-menu-link[href*="vouchers"]',
                title: 'Mes Bons de Soins',
                content: 'Bons émis par votre médecin pour faciliter l\'accès aux soins. Vérifiez leur validité et utilisation.',
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
        
        const welcomeMessages = {
            'superadmin': 'Découvrez comment superviser la prise en charge des enfants dans tout le réseau malien et optimiser la qualité des soins pédiatriques.',
            'facility_admin': 'Apprenez à gérer efficacement les patients de votre établissement et coordonner leurs parcours de soins.',
            'doctor': 'Explorez les outils pour créer des plans de réhabilitation personnalisés et suivre l\'évolution de vos jeunes patients.',
            'patient': 'Familiarisez-vous avec votre espace personnel pour suivre votre parcours de soins et votre progression.'
        };
        
        const modal = document.createElement('div');
        modal.className = 'modern-tour-welcome';
        modal.innerHTML = `
            <div class="modern-tour-welcome-content">
                <div class="modern-tour-welcome-header">
                    <h2 class="modern-tour-welcome-title">Bienvenue dans DPIMedML</h2>
                    <p class="modern-tour-welcome-subtitle">${roleNames[userRole]} - Système de Réhabilitation Pédiatrique</p>
                </div>
                <div class="modern-tour-welcome-body">
                    <p class="modern-tour-welcome-text">
                        ${welcomeMessages[userRole]} Souhaitez-vous une visite guidée interactive ?
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
