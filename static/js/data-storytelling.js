/**
 * Data Storytelling JavaScript
 * Mali Healthcare System - DPImedml
 * Transforms static numbers into compelling visual stories
 */

class DataStorytelling {
    constructor() {
        this.animationDuration = 1500;
        this.easeOutQuint = (t) => 1 - (1 - t) ** 5;
    }

    /**
     * Initialize all data storytelling components
     */
    init() {
        this.createProgressRings();
        this.animateCounters();
        this.animateProgressBars();
        this.createMiniCharts();
        this.setupHoverEffects();
    }

    /**
     * Animate progress bars
     */
    animateProgressBars() {
        const progressBars = document.querySelectorAll('.story-progress-bar');
        
        progressBars.forEach(bar => {
            const percentage = parseInt(bar.dataset.percentage) || 0;
            
            // Start with 0 width
            bar.style.width = '0%';
            
            // Animate to target percentage after a delay
            setTimeout(() => {
                bar.style.width = percentage + '%';
            }, 500);
        });
    }

    /**
     * Create circular progress rings for completion rates
     */
    createProgressRings() {
        const rings = document.querySelectorAll('.progress-ring');
        
        rings.forEach(ring => {
            const percentage = parseInt(ring.dataset.percentage) || 0;
            const radius = 36;
            const circumference = 2 * Math.PI * radius;
            
            // Create SVG if it doesn't exist
            if (!ring.querySelector('svg')) {
                const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                svg.setAttribute('width', '80');
                svg.setAttribute('height', '80');
                
                // Background circle
                const bgCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                bgCircle.setAttribute('class', 'background');
                bgCircle.setAttribute('cx', '40');
                bgCircle.setAttribute('cy', '40');
                bgCircle.setAttribute('r', radius);
                
                // Progress circle
                const progressCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                progressCircle.setAttribute('class', 'progress');
                progressCircle.setAttribute('cx', '40');
                progressCircle.setAttribute('cy', '40');
                progressCircle.setAttribute('r', radius);
                progressCircle.style.strokeDasharray = circumference;
                progressCircle.style.strokeDashoffset = circumference;
                
                // Add color class based on percentage
                if (percentage < 50) {
                    progressCircle.classList.add('danger');
                } else if (percentage < 80) {
                    progressCircle.classList.add('warning');
                }
                
                svg.appendChild(bgCircle);
                svg.appendChild(progressCircle);
                ring.appendChild(svg);
                
                // Animate the progress
                setTimeout(() => {
                    const offset = circumference - (percentage / 100) * circumference;
                    progressCircle.style.strokeDashoffset = offset;
                }, 500);
            }
        });
    }

    /**
     * Animate number counters with storytelling context
     */
    animateCounters() {
        const counters = document.querySelectorAll('.story-value');
        
        counters.forEach(counter => {
            const target = parseInt(counter.dataset.target) || parseInt(counter.textContent);
            const suffix = counter.dataset.suffix || '';
            const prefix = counter.dataset.prefix || '';
            
            this.animateNumber(counter, 0, target, this.animationDuration, (value) => {
                counter.textContent = prefix + Math.round(value) + suffix;
            });
        });
    }

    /**
     * Create mini charts within stat cards
     */
    createMiniCharts() {
        const chartContainers = document.querySelectorAll('.mini-chart-container');
        
        chartContainers.forEach(container => {
            const canvas = container.querySelector('.mini-chart');
            if (!canvas) return;
            
            const ctx = canvas.getContext('2d');
            const data = JSON.parse(container.dataset.chartData || '[0,0,0,0,0]');
            const type = container.dataset.chartType || 'line';
            
            // Set canvas size
            canvas.width = container.offsetWidth;
            canvas.height = container.offsetHeight;
            
            if (type === 'line') {
                this.drawMiniLineChart(ctx, data, canvas.width, canvas.height);
            } else if (type === 'bar') {
                this.drawMiniBarChart(ctx, data, canvas.width, canvas.height);
            }
        });
    }

    /**
     * Draw mini line chart
     */
    drawMiniLineChart(ctx, data, width, height) {
        const padding = 4;
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding * 2;
        
        const max = Math.max(...data);
        const min = Math.min(...data);
        const range = max - min || 1;
        
        ctx.strokeStyle = '#0C7C59';
        ctx.lineWidth = 2;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        
        ctx.beginPath();
        
        data.forEach((value, index) => {
            const x = padding + (index / (data.length - 1)) * chartWidth;
            const y = padding + chartHeight - ((value - min) / range) * chartHeight;
            
            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        
        ctx.stroke();
        
        // Add gradient fill
        ctx.lineTo(padding + chartWidth, padding + chartHeight);
        ctx.lineTo(padding, padding + chartHeight);
        ctx.closePath();
        
        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        gradient.addColorStop(0, 'rgba(12, 124, 89, 0.3)');
        gradient.addColorStop(1, 'rgba(12, 124, 89, 0.05)');
        
        ctx.fillStyle = gradient;
        ctx.fill();
    }

    /**
     * Draw mini bar chart
     */
    drawMiniBarChart(ctx, data, width, height) {
        const padding = 2;
        const chartWidth = width - padding * 2;
        const chartHeight = height - padding * 2;
        
        const max = Math.max(...data);
        const barWidth = chartWidth / data.length;
        
        ctx.fillStyle = '#0C7C59';
        
        data.forEach((value, index) => {
            const barHeight = (value / max) * chartHeight;
            const x = padding + index * barWidth;
            const y = padding + chartHeight - barHeight;
            
            ctx.fillRect(x + 1, y, barWidth - 2, barHeight);
        });
    }

    /**
     * Setup hover effects for story cards
     */
    setupHoverEffects() {
        const storyCards = document.querySelectorAll('.story-card');
        
        storyCards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-4px) scale(1.02)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0) scale(1)';
            });
        });
    }

    /**
     * Animate number with easing
     */
    animateNumber(element, start, end, duration, callback) {
        const startTime = performance.now();
        
        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easedProgress = this.easeOutQuint(progress);
            
            const current = start + (end - start) * easedProgress;
            callback(current);
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    /**
     * Create progress bar animations
     */
    animateProgressBars() {
        const progressBars = document.querySelectorAll('.story-progress-bar');
        
        progressBars.forEach(bar => {
            const percentage = parseInt(bar.dataset.percentage) || 0;
            
            setTimeout(() => {
                bar.style.width = percentage + '%';
            }, 300);
        });
    }

    /**
     * Create storytelling dashboard cards
     */
    createStoryCard(data) {
        const {
            icon,
            title,
            value,
            target,
            context,
            trend,
            breakdown,
            color = 'primary'
        } = data;
        
        const percentage = target ? Math.round((value / target) * 100) : 0;
        const progressClass = percentage < 50 ? 'danger' : percentage < 80 ? 'warning' : 'success';
        
        return `
            <div class="story-card animate-in" data-percentage="${percentage}">
                <div class="story-header">
                    <div class="story-icon">
                        <i class="${icon}"></i>
                    </div>
                    <h6 class="story-title">${title}</h6>
                </div>
                
                <div class="story-value" data-target="${value}">${value}</div>
                
                <div class="story-context">${context}</div>
                
                ${target ? `
                    <div class="story-progress">
                        <div class="story-progress-bar ${progressClass}" 
                             data-percentage="${percentage}"></div>
                    </div>
                    
                    <div class="target-achievement">
                        <span class="target-text">Objectif: ${target}</span>
                        <span class="target-badge">${percentage}%</span>
                    </div>
                ` : ''}
                
                ${breakdown ? `
                    <div class="status-grid">
                        ${breakdown.map(item => `
                            <div class="status-item ${item.status}">
                                <span class="status-number">${item.value}</span>
                                <span class="status-label">${item.label}</span>
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
                
                ${trend ? `
                    <div class="mini-chart-container" 
                         data-chart-data='${JSON.stringify(trend.data)}'
                         data-chart-type="${trend.type}">
                        <canvas class="mini-chart"></canvas>
                    </div>
                ` : ''}
            </div>
        `;
    }

    /**
     * Transform existing stats to story format
     */
    transformDashboard() {
        // Example transformation for healthcare contexts
        const transformations = {
            // SuperAdmin transformations
            'total_patients': {
                icon: 'fa-solid fa-user-injured',
                title: 'Enfants pris en charge',
                context: 'enfants handicapés de 0-14 ans',
                target: 150, // Annual target
                breakdown: [
                    { value: 45, label: 'Actifs', status: 'success' },
                    { value: 12, label: 'Suivi', status: 'warning' },
                    { value: 3, label: 'Critiques', status: 'danger' }
                ]
            },
            
            // Doctor transformations  
            'patients_count': {
                icon: 'fa-solid fa-stethoscope',
                title: 'Mes patients',
                context: 'patients sous ma supervision',
                target: 50,
                breakdown: [
                    { value: 32, label: 'Progrès', status: 'success' },
                    { value: 8, label: 'Stable', status: 'warning' },
                    { value: 2, label: 'Attention', status: 'danger' }
                ]
            },
            
            // Facility Admin transformations
            'facility_patients': {
                icon: 'fa-solid fa-hospital',
                title: 'Capacité utilisée',
                context: 'de la capacité totale de l\'établissement',
                target: 100,
                breakdown: [
                    { value: 68, label: 'Consultations', status: 'success' },
                    { value: 24, label: 'Thérapie', status: 'warning' },
                    { value: 8, label: 'Urgences', status: 'danger' }
                ]
            }
        };
        
        return transformations;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const storytelling = new DataStorytelling();
    storytelling.init();
    
    // Make available globally for dynamic updates
    window.DataStorytelling = storytelling;
});

// Healthcare-specific story templates
const HealthcareStories = {
    // Patient recovery progress
    patientRecovery: (current, target) => ({
        title: 'Taux de récupération',
        value: current,
        target: target,
        context: `${current} enfants en voie de guérison sur ${target} traités`,
        icon: 'fa-solid fa-heart-pulse'
    }),
    
    // Appointment efficiency  
    appointmentEfficiency: (scheduled, completed) => ({
        title: 'Efficacité des RDV',
        value: completed,
        target: scheduled,
        context: `${completed} consultations réalisées sur ${scheduled} programmées`,
        icon: 'fa-solid fa-calendar-check'
    })
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DataStorytelling, HealthcareStories };
} 