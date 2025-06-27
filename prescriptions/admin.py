from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    MedicationCategory, Medication, Prescription, PrescriptionMedication,
    PrescriptionTemplate, TemplateMedication
)

@admin.register(MedicationCategory)
class MedicationCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'color_code', 'icon']
    list_filter = ['name']
    search_fields = ['name', 'description']
    prepopulated_fields = {'name': ()}

@admin.register(Medication)
class MedicationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'generic_name', 'category', 'form', 'strength',
        'is_pediatric_approved', 'available_in_mali', 'essential_drug_list'
    ]
    list_filter = [
        'category', 'form', 'is_pediatric_approved', 'available_in_mali',
        'essential_drug_list', 'weight_based_dosing', 'requires_special_storage'
    ]
    search_fields = ['name', 'generic_name', 'manufacturer']
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'generic_name', 'category', 'manufacturer')
        }),
        ('Formulation', {
            'fields': ('form', 'strength', 'unit')
        }),
        ('Usage pédiatrique', {
            'fields': (
                'is_pediatric_approved', 'min_age_months', 'max_age_years',
                'weight_based_dosing'
            ),
            'classes': ['collapse']
        }),
        ('Posologie', {
            'fields': (
                'default_dose_per_kg', 'max_dose_per_day', 'frequency_per_day'
            ),
            'classes': ['collapse']
        }),
        ('Informations de sécurité', {
            'fields': (
                'contraindications', 'side_effects', 'drug_interactions',
                'pregnancy_category'
            ),
            'classes': ['collapse']
        }),
        ('Contexte Mali', {
            'fields': (
                'available_in_mali', 'essential_drug_list', 'requires_special_storage'
            )
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')

class PrescriptionMedicationInline(admin.TabularInline):
    model = PrescriptionMedication
    extra = 1
    fields = [
        'medication', 'dose', 'dose_unit', 'frequency', 'route',
        'duration_days', 'total_quantity', 'instructions', 'substitution_allowed'
    ]
    autocomplete_fields = ['medication']

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = [
        'prescription_id', 'patient_name', 'prescribing_doctor_name',
        'status', 'priority', 'prescribed_date', 'is_expired_display',
        'medication_count'
    ]
    list_filter = [
        'status', 'priority', 'prescribed_date', 'requires_authorization',
        'covered_by_insurance', 'voucher_required'
    ]
    search_fields = [
        'prescription_id', 'patient__first_name', 'patient__last_name',
        'patient__patient_id', 'diagnosis'
    ]
    readonly_fields = ['prescription_id', 'created_at', 'updated_at']
    inlines = [PrescriptionMedicationInline]
    
    fieldsets = (
        ('Identification', {
            'fields': ('prescription_id', 'patient', 'medical_record')
        }),
        ('Personnel de santé', {
            'fields': (
                'prescribing_doctor', 'validating_pharmacist', 'dispensing_pharmacist'
            )
        }),
        ('Établissements', {
            'fields': ('prescribing_facility', 'dispensing_facility')
        }),
        ('Détails de prescription', {
            'fields': ('diagnosis', 'clinical_notes', 'instructions')
        }),
        ('Statut et priorité', {
            'fields': ('status', 'priority')
        }),
        ('Dates', {
            'fields': (
                'prescribed_date', 'validated_date', 'dispensed_date', 'expiry_date'
            )
        }),
        ('Workflow Mali', {
            'fields': (
                'requires_authorization', 'covered_by_insurance', 'voucher_required'
            )
        }),
        ('Administration', {
            'fields': ('created_at', 'updated_at'),
            'classes': ['collapse']
        }),
    )
    
    # autocomplete_fields = ['patient', 'medical_record']  # Removed for now
    
    def patient_name(self, obj):
        return f"{obj.patient.first_name} {obj.patient.last_name}"
    patient_name.short_description = 'Patient'
    patient_name.admin_order_field = 'patient__last_name'
    
    def prescribing_doctor_name(self, obj):
        if obj.prescribing_doctor:
            return f"Dr. {obj.prescribing_doctor.user.last_name}"
        return '-'
    prescribing_doctor_name.short_description = 'Médecin'
    prescribing_doctor_name.admin_order_field = 'prescribing_doctor__user__last_name'
    
    def is_expired_display(self, obj):
        if obj.is_expired():
            return format_html('<span style="color: red;">Expiré</span>')
        elif obj.expiry_date:
            days_left = (obj.expiry_date.date() - timezone.now().date()).days
            if days_left <= 7:
                return format_html(f'<span style="color: orange;">{days_left} jours</span>')
            return format_html(f'<span style="color: green;">{days_left} jours</span>')
        return '-'
    is_expired_display.short_description = 'Expiration'
    
    def medication_count(self, obj):
        return obj.get_total_medications()
    medication_count.short_description = 'Nb médicaments'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'patient', 'prescribing_doctor__user', 'prescribing_facility'
        ).prefetch_related('prescriptionmedication_set')

@admin.register(PrescriptionMedication)
class PrescriptionMedicationAdmin(admin.ModelAdmin):
    list_display = [
        'prescription_id', 'medication_name', 'dose_display',
        'frequency', 'duration_days', 'route', 'is_dispensed'
    ]
    list_filter = [
        'route', 'is_dispensed', 'substitution_allowed',
        'medication__category', 'prescription__status'
    ]
    search_fields = [
        'prescription__prescription_id', 'medication__name',
        'medication__generic_name'
    ]
    
    fieldsets = (
        ('Prescription', {
            'fields': ('prescription', 'medication')
        }),
        ('Posologie', {
            'fields': ('dose', 'dose_unit', 'frequency', 'route', 'duration_days')
        }),
        ('Quantité', {
            'fields': ('total_quantity', 'dispensed_quantity')
        }),
        ('Instructions', {
            'fields': ('instructions', 'special_notes', 'substitution_allowed')
        }),
        ('Dispensation', {
            'fields': ('is_dispensed', 'dispensed_date')
        }),
    )
    
    autocomplete_fields = ['prescription', 'medication']
    
    def prescription_id(self, obj):
        return obj.prescription.prescription_id
    prescription_id.short_description = 'ID Prescription'
    prescription_id.admin_order_field = 'prescription__prescription_id'
    
    def medication_name(self, obj):
        return obj.medication.name
    medication_name.short_description = 'Médicament'
    medication_name.admin_order_field = 'medication__name'
    
    def dose_display(self, obj):
        return f"{obj.dose} {obj.dose_unit}"
    dose_display.short_description = 'Dose'

class TemplateMedicationInline(admin.TabularInline):
    model = TemplateMedication
    extra = 1
    fields = [
        'medication', 'standard_dose_per_kg', 'standard_frequency',
        'standard_duration', 'order', 'is_optional'
    ]
    autocomplete_fields = ['medication']

@admin.register(PrescriptionTemplate)
class PrescriptionTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'age_range_display', 'is_who_approved',
        'is_mali_standard', 'created_by_name', 'created_at'
    ]
    list_filter = [
        'category', 'is_who_approved', 'is_mali_standard', 'created_at'
    ]
    search_fields = ['name', 'description', 'conditions']
    inlines = [TemplateMedicationInline]
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('name', 'description', 'category')
        }),
        ('Applicabilité', {
            'fields': ('min_age_months', 'max_age_months', 'conditions')
        }),
        ('Instructions', {
            'fields': ('standard_instructions',)
        }),
        ('Contexte Mali', {
            'fields': ('is_who_approved', 'is_mali_standard')
        }),
        ('Administration', {
            'fields': ('created_by', 'created_at'),
            'classes': ['collapse']
        }),
    )
    
    readonly_fields = ['created_at']
    
    def age_range_display(self, obj):
        if obj.min_age_months and obj.max_age_months:
            min_years = obj.min_age_months // 12
            min_months = obj.min_age_months % 12
            max_years = obj.max_age_months // 12
            max_months = obj.max_age_months % 12
            
            min_str = f"{min_years}a {min_months}m" if min_months else f"{min_years}a"
            max_str = f"{max_years}a {max_months}m" if max_months else f"{max_years}a"
            
            return f"{min_str} - {max_str}"
        elif obj.min_age_months:
            years = obj.min_age_months // 12
            months = obj.min_age_months % 12
            return f"≥ {years}a {months}m" if months else f"≥ {years}a"
        elif obj.max_age_months:
            years = obj.max_age_months // 12
            months = obj.max_age_months % 12
            return f"≤ {years}a {months}m" if months else f"≤ {years}a"
        return "Tous âges"
    age_range_display.short_description = 'Tranche d\'âge'
    
    def created_by_name(self, obj):
        if obj.created_by:
            return f"Dr. {obj.created_by.user.last_name}"
        return '-'
    created_by_name.short_description = 'Créé par'
    created_by_name.admin_order_field = 'created_by__user__last_name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'category', 'created_by__user'
        )

# Admin site customization
admin.site.site_header = "DPImedml - Système de Prescription"
admin.site.site_title = "Prescriptions Mali"
admin.site.index_title = "Administration des Prescriptions"
