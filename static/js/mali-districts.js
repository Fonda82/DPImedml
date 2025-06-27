// Mali Districts Geographic Map Interactions
// Fixes popup positioning and provides professional district analytics

function showDistrictDetails(district, patients, facilities) {
    // Remove any existing district details
    const existingDetails = document.querySelector('.district-details-popup');
    if (existingDetails) {
        existingDetails.remove();
    }
    
    // Remove any existing backdrop
    const existingBackdrop = document.querySelector('.district-backdrop');
    if (existingBackdrop) {
        existingBackdrop.remove();
    }
    
    // Create a centered modal-style popup instead of mispositioned toast
    const detailsHtml = `
        <div class="district-backdrop" style="
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 9998;
            backdrop-filter: blur(4px);
        " onclick="closeDistrictDetails()"></div>
        
        <div class="district-details-popup" style="
            position: fixed; 
            top: 50%; 
            left: 50%; 
            transform: translate(-50%, -50%);
            z-index: 9999;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            padding: 24px;
            min-width: 350px;
            max-width: 450px;
            border: 3px solid transparent;
            background-image: linear-gradient(white, white), linear-gradient(45deg, #0C7C59, #FCD116);
            background-origin: border-box;
            background-clip: content-box, border-box;
        ">
            <div class="district-header" style="
                display: flex; 
                align-items: center; 
                justify-content: space-between; 
                margin-bottom: 20px;
                padding-bottom: 16px;
                border-bottom: 2px solid #f1f3f4;
            ">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="
                        width: 48px; 
                        height: 48px; 
                        background: linear-gradient(45deg, #0C7C59, #FCD116);
                        border-radius: 50%;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-size: 20px;
                    ">🇲🇱</div>
                    <div>
                        <h5 style="margin: 0; color: #0C7C59; font-weight: 700;">${district}</h5>
                        <small style="color: #6c757d;">District de Bamako</small>
                    </div>
                </div>
                <button onclick="closeDistrictDetails()" style="
                    background: none;
                    border: none;
                    font-size: 24px;
                    color: #6c757d;
                    cursor: pointer;
                    padding: 4px;
                    border-radius: 4px;
                    transition: background-color 0.2s ease;
                " onmouseover="this.style.backgroundColor='#f1f3f4'" onmouseout="this.style.backgroundColor='transparent'">×</button>
            </div>
            
            <div class="district-stats-grid" style="
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
                margin-bottom: 20px;
            ">
                <div class="stat-card" style="
                    background: linear-gradient(135deg, #f1f8f5, #e8f5e9);
                    padding: 16px;
                    border-radius: 12px;
                    text-align: center;
                    border: 1px solid rgba(12, 124, 89, 0.1);
                ">
                    <div style="font-size: 28px; font-weight: 800; color: #0C7C59; margin-bottom: 4px;">${patients}</div>
                    <div style="font-size: 12px; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px;">Enfants Pris en Charge</div>
                </div>
                <div class="stat-card" style="
                    background: linear-gradient(135deg, #fff8e1, #fff3cd);
                    padding: 16px;
                    border-radius: 12px;
                    text-align: center;
                    border: 1px solid rgba(252, 209, 22, 0.1);
                ">
                    <div style="font-size: 28px; font-weight: 800; color: #f59e0b; margin-bottom: 4px;">${facilities}</div>
                    <div style="font-size: 12px; color: #6c757d; text-transform: uppercase; letter-spacing: 0.5px;">Centres Actifs</div>
                </div>
            </div>
            
            <div class="additional-stats" style="
                background: #f8f9fa;
                padding: 16px;
                border-radius: 12px;
                margin-bottom: 20px;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="color: #495057; font-weight: 500;">Taux de Couverture:</span>
                    <span style="font-weight: 700; color: #0C7C59;">${Math.round((patients/127)*100)}%</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="color: #495057; font-weight: 500;">Capacité par Centre:</span>
                    <span style="font-weight: 700; color: #6c757d;">${facilities > 0 ? Math.round(patients/facilities) : 0} enfants/centre</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #495057; font-weight: 500;">Statut de Couverture:</span>
                    <span class="badge ${patients > 20 ? 'bg-success' : patients > 10 ? 'bg-warning text-dark' : 'bg-danger'}" style="padding: 6px 12px; border-radius: 20px;">
                        ${patients > 20 ? '✅ Optimal' : patients > 10 ? '⚠️ Modéré' : '🚨 Insuffisant'}
                    </span>
                </div>
            </div>
            
            <div style="text-align: center;">
                <button onclick="closeDistrictDetails()" style="
                    background: linear-gradient(45deg, #0C7C59, #14A97C);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 25px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.3s ease;
                " onmouseover="this.style.transform='scale(1.05)'" onmouseout="this.style.transform='scale(1)'">
                    Fermer
                </button>
            </div>
        </div>
    `;
    
    // Insert the modal at the end of body
    document.body.insertAdjacentHTML('beforeend', detailsHtml);
    
    // Add entrance animation
    const popup = document.querySelector('.district-details-popup');
    popup.style.opacity = '0';
    popup.style.transform = 'translate(-50%, -50%) scale(0.7)';
    
    setTimeout(() => {
        popup.style.transition = 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)';
        popup.style.opacity = '1';
        popup.style.transform = 'translate(-50%, -50%) scale(1)';
    }, 10);
    
    // Remove auto-close - only close when user clicks close or backdrop
}

function closeDistrictDetails() {
    const popup = document.querySelector('.district-details-popup');
    const backdrop = document.querySelector('.district-backdrop');
    
    if (popup) {
        popup.style.transition = 'all 0.3s ease';
        popup.style.opacity = '0';
        popup.style.transform = 'translate(-50%, -50%) scale(0.7)';
        
        setTimeout(() => {
            if (popup.parentNode) popup.remove();
        }, 300);
    }
    
    if (backdrop) {
        backdrop.style.transition = 'opacity 0.3s ease';
        backdrop.style.opacity = '0';
        
        setTimeout(() => {
            if (backdrop.parentNode) backdrop.remove();
        }, 300);
    }
}

// Enhanced district zone interactions
function initializeMaliDistrictsMap() {
    const districtZones = document.querySelectorAll('.district-zone');
    
    districtZones.forEach((zone, index) => {
        // Enhanced hover effects
        zone.addEventListener('mouseenter', () => {
            zone.style.transform = 'translateY(-8px) scale(1.05)';
            zone.style.boxShadow = '0 15px 35px rgba(12, 124, 89, 0.2)';
            zone.style.borderColor = 'rgba(12, 124, 89, 0.4)';
        });
        
        zone.addEventListener('mouseleave', () => {
            zone.style.transform = 'translateY(0) scale(1)';
            zone.style.boxShadow = '0 6px 20px rgba(0, 0, 0, 0.08)';
            zone.style.borderColor = 'transparent';
        });
        
        // Click handler for district details
        zone.addEventListener('click', () => {
            const district = zone.getAttribute('data-district');
            const patients = zone.getAttribute('data-patients') || '0';
            const facilities = zone.getAttribute('data-facilities') || '0';
            
            // Show professional district details modal
            showDistrictDetails(district, patients, facilities);
        });
    });
}

// Initialize when DOM is ready - without auto-triggering
document.addEventListener('DOMContentLoaded', function() {
    // Small delay to ensure all elements are rendered
    setTimeout(initializeMaliDistrictsMap, 500);
    
    // Debug: Check if any district is being clicked automatically
    console.log('Mali districts map initialized - no auto-popup');
}); 