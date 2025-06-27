from django.core.management.base import BaseCommand
from prescriptions.models import (
    MedicationCategory, Medication, PrescriptionTemplate, TemplateMedication
)
from accounts.models import UserProfile

class Command(BaseCommand):
    help = 'Populate database with pediatric medications for Mali healthcare context'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Populating medications for Mali pediatric healthcare...'))
        
        # Create medication categories
        self.create_medication_categories()
        
        # Create medications
        self.create_medications()
        
        # Create prescription templates
        self.create_prescription_templates()
        
        self.stdout.write(self.style.SUCCESS('Successfully populated medication database!'))

    def create_medication_categories(self):
        """Create medication categories for pediatric care"""
        categories = [
            {
                'name': 'Antibiotiques',
                'description': 'Médicaments pour traiter les infections bactériennes',
                'color_code': '#dc3545',
                'icon': 'fa-shield-virus'
            },
            {
                'name': 'Antipyrétiques/Analgésiques',
                'description': 'Médicaments pour la fièvre et la douleur',
                'color_code': '#fd7e14',
                'icon': 'fa-thermometer-half'
            },
            {
                'name': 'Antipaludiques',
                'description': 'Médicaments contre le paludisme',
                'color_code': '#198754',
                'icon': 'fa-bug'
            },
            {
                'name': 'Vitamines et Suppléments',
                'description': 'Vitamines et suppléments nutritionnels',
                'color_code': '#ffc107',
                'icon': 'fa-pills'
            },
            {
                'name': 'Antidiarrhéiques',
                'description': 'Médicaments contre la diarrhée',
                'color_code': '#0dcaf0',
                'icon': 'fa-tint'
            },
            {
                'name': 'Respiratoire',
                'description': 'Médicaments pour les problèmes respiratoires',
                'color_code': '#6f42c1',
                'icon': 'fa-lungs'
            },
            {
                'name': 'Antihistaminiques',
                'description': 'Médicaments contre les allergies',
                'color_code': '#20c997',
                'icon': 'fa-allergies'
            },
            {
                'name': 'Topiques',
                'description': 'Médicaments à usage externe',
                'color_code': '#6c757d',
                'icon': 'fa-hand-holding-medical'
            }
        ]
        
        for cat_data in categories:
            category, created = MedicationCategory.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

    def create_medications(self):
        """Create common pediatric medications for Mali"""
        
        # Get categories
        categories = {cat.name: cat for cat in MedicationCategory.objects.all()}
        
        medications = [
            # Antibiotics
            {
                'name': 'Amoxicilline',
                'generic_name': 'Amoxicillin',
                'category': categories['Antibiotiques'],
                'form': 'SYRUP',
                'strength': '125mg/5ml',
                'unit': 'mg',
                'is_pediatric_approved': True,
                'min_age_months': 1,
                'max_age_years': 14,
                'weight_based_dosing': True,
                'default_dose_per_kg': 20.0,
                'max_dose_per_day': 1000.0,
                'frequency_per_day': 3,
                'available_in_mali': True,
                'essential_drug_list': True,
                'manufacturer': 'Laboratoire Malien'
            },
            {
                'name': 'Ampicilline',
                'generic_name': 'Ampicillin',
                'category': categories['Antibiotiques'],
                'form': 'SUSPENSION',
                'strength': '250mg/5ml',
                'unit': 'mg',
                'is_pediatric_approved': True,
                'min_age_months': 1,
                'max_age_years': 14,
                'weight_based_dosing': True,
                'default_dose_per_kg': 25.0,
                'max_dose_per_day': 2000.0,
                'frequency_per_day': 4,
                'available_in_mali': True,
                'essential_drug_list': True,
                'manufacturer': 'USINE MALIENNE DE PRODUITS PHARMACEUTIQUES'
            },
            {
                'name': 'Azithromycine',
                'generic_name': 'Azithromycin',
                'category': categories['Antibiotiques'],
                'form': 'SYRUP',
                'strength': '200mg/5ml',
                'unit': 'mg',
                'is_pediatric_approved': True,
                'min_age_months': 6,
                'max_age_years': 14,
                'weight_based_dosing': True,
                'default_dose_per_kg': 10.0,
                'max_dose_per_day': 500.0,
                'frequency_per_day': 1,
                'available_in_mali': True,
                'essential_drug_list': True
            },
            
            # Antipyretics/Analgesics
            {
                'name': 'Paracétamol',
                'generic_name': 'Paracetamol',
                'category': categories['Antipyrétiques/Analgésiques'],
                'form': 'SYRUP',
                'strength': '120mg/5ml',
                'unit': 'mg',
                'is_pediatric_approved': True,
                'min_age_months': 1,
                'max_age_years': 14,
                'weight_based_dosing': True,
                'default_dose_per_kg': 15.0,
                'max_dose_per_day': 1000.0,
                'frequency_per_day': 4,
                'available_in_mali': True,
                'essential_drug_list': True,
                'manufacturer': 'COPHARMED'
            },
            {
                'name': 'Ibuprofène',
                'generic_name': 'Ibuprofen',
                'category': categories['Antipyrétiques/Analgésiques'],
                'form': 'SYRUP',
                'strength': '100mg/5ml',
                'unit': 'mg',
                'is_pediatric_approved': True,
                'min_age_months': 6,
                'max_age_years': 14,
                'weight_based_dosing': True,
                'default_dose_per_kg': 10.0,
                'max_dose_per_day': 600.0,
                'frequency_per_day': 3,
                'available_in_mali': True,
                'essential_drug_list': True
            },
            {
                'name': 'Aspirine',
                'generic_name': 'Acetylsalicylic acid',
                'category': categories['Antipyrétiques/Analgésiques'],
                'form': 'TABLET',
                'strength': '100mg',
                'unit': 'mg',
                'is_pediatric_approved': True,
                'min_age_months': 24,  # Caution with Reye's syndrome
                'max_age_years': 14,
                'weight_based_dosing': True,
                'default_dose_per_kg': 10.0,
                'max_dose_per_day': 500.0,
                'frequency_per_day': 4,
                'available_in_mali': True,
                'essential_drug_list': True,
                'contraindications': 'Syndrome de Reye, moins de 2 ans'
            },
            
            # Antimalarials
            {
                'name': 'Artémether-Luméfantrine',
                'generic_name': 'Artemether-Lumefantrine',
                'category': categories['Antipaludiques'],
                'form': 'TABLET',
                'strength': '20mg/120mg',
                'unit': 'mg',
                'is_pediatric_approved': True,
                'min_age_months': 6,
                'max_age_years': 14,
                'weight_based_dosing': True,
                'default_dose_per_kg': 1.0,  # Complex dosing, simplified
                'frequency_per_day': 2,
                'available_in_mali': True,
                'essential_drug_list': True,
                'manufacturer': 'Novartis - Programme Mali'
            },
            {
                'name': 'Sulfadoxine-Pyriméthamine',
                'generic_name': 'Sulfadoxine-Pyrimethamine',
                'category': categories['Antipaludiques'],
                'form': 'TABLET',
                'strength': '500mg/25mg',
                'unit': 'mg',
                'is_pediatric_approved': True,
                'min_age_months': 6,
                'max_age_years': 14,
                'weight_based_dosing': True,
                'default_dose_per_kg': 25.0,
                'frequency_per_day': 1,
                'available_in_mali': True,
                'essential_drug_list': True
            },
            
            # Vitamins and Supplements
            {
                'name': 'Vitamine A',
                'generic_name': 'Retinol',
                'category': categories['Vitamines et Suppléments'],
                'form': 'CAPSULE',
                'strength': '200000UI',
                'unit': 'UI',
                'is_pediatric_approved': True,
                'min_age_months': 6,
                'max_age_years': 14,
                'weight_based_dosing': False,
                'frequency_per_day': 1,
                'available_in_mali': True,
                'essential_drug_list': True,
                'manufacturer': 'UNICEF Mali'
            },
            {
                'name': 'Fer-Acide Folique',
                'generic_name': 'Iron-Folic Acid',
                'category': categories['Vitamines et Suppléments'],
                'form': 'SYRUP',
                'strength': '25mg/2.5mg per 5ml',
                'unit': 'mg',
                'is_pediatric_approved': True,
                'min_age_months': 6,
                'max_age_years': 14,
                'weight_based_dosing': True,
                'default_dose_per_kg': 2.0,
                'frequency_per_day': 1,
                'available_in_mali': True,
                'essential_drug_list': True
            },
            {
                'name': 'Zinc',
                'generic_name': 'Zinc Sulfate',
                'category': categories['Vitamines et Suppléments'],
                'form': 'TABLET',
                'strength': '20mg',
                'unit': 'mg',
                'is_pediatric_approved': True,
                'min_age_months': 6,
                'max_age_years': 14,
                'weight_based_dosing': False,
                'frequency_per_day': 1,
                'available_in_mali': True,
                'essential_drug_list': True,
                'manufacturer': 'Programme Nutrition Mali'
            },
            
            # Antidiarrheals
            {
                'name': 'Sels de Réhydratation Orale (SRO)',
                'generic_name': 'Oral Rehydration Salts',
                'category': categories['Antidiarrhéiques'],
                'form': 'POWDER',
                'strength': '20.5g/L',
                'unit': 'g',
                'is_pediatric_approved': True,
                'min_age_months': 0,
                'max_age_years': 14,
                'weight_based_dosing': False,
                'frequency_per_day': 4,
                'available_in_mali': True,
                'essential_drug_list': True,
                'manufacturer': 'OMS Mali'
            },
            {
                'name': 'Lopéramide',
                'generic_name': 'Loperamide',
                'category': categories['Antidiarrhéiques'],
                'form': 'SYRUP',
                'strength': '1mg/5ml',
                'unit': 'mg',
                'is_pediatric_approved': True,
                'min_age_months': 24,
                'max_age_years': 14,
                'weight_based_dosing': True,
                'default_dose_per_kg': 0.1,
                'max_dose_per_day': 2.0,
                'frequency_per_day': 2,
                'available_in_mali': True,
                'contraindications': 'Diarrhée sanglante, fièvre'
            },
            
            # Respiratory
            {
                'name': 'Salbutamol',
                'generic_name': 'Salbutamol',
                'category': categories['Respiratoire'],
                'form': 'SYRUP',
                'strength': '2mg/5ml',
                'unit': 'mg',
                'is_pediatric_approved': True,
                'min_age_months': 6,
                'max_age_years': 14,
                'weight_based_dosing': True,
                'default_dose_per_kg': 0.1,
                'max_dose_per_day': 8.0,
                'frequency_per_day': 3,
                'available_in_mali': True,
                'essential_drug_list': True
            },
            {
                'name': 'Prednisone',
                'generic_name': 'Prednisolone',
                'category': categories['Respiratoire'],
                'form': 'SYRUP',
                'strength': '5mg/5ml',
                'unit': 'mg',
                'is_pediatric_approved': True,
                'min_age_months': 6,
                'max_age_years': 14,
                'weight_based_dosing': True,
                'default_dose_per_kg': 1.0,
                'max_dose_per_day': 40.0,
                'frequency_per_day': 1,
                'available_in_mali': True,
                'contraindications': 'Infections virales, varicelle'
            },
            
            # Antihistamines
            {
                'name': 'Cétirizine',
                'generic_name': 'Cetirizine',
                'category': categories['Antihistaminiques'],
                'form': 'SYRUP',
                'strength': '5mg/5ml',
                'unit': 'mg',
                'is_pediatric_approved': True,
                'min_age_months': 6,
                'max_age_years': 14,
                'weight_based_dosing': True,
                'default_dose_per_kg': 0.25,
                'max_dose_per_day': 10.0,
                'frequency_per_day': 1,
                'available_in_mali': True
            },
            
            # Topical
            {
                'name': 'Pommade Antibiotique',
                'generic_name': 'Mupirocin',
                'category': categories['Topiques'],
                'form': 'OINTMENT',
                'strength': '2%',
                'unit': '%',
                'is_pediatric_approved': True,
                'min_age_months': 0,
                'max_age_years': 14,
                'weight_based_dosing': False,
                'frequency_per_day': 3,
                'available_in_mali': True,
                'essential_drug_list': True
            },
            {
                'name': 'Crème Antifongique',
                'generic_name': 'Clotrimazole',
                'category': categories['Topiques'],
                'form': 'CREAM',
                'strength': '1%',
                'unit': '%',
                'is_pediatric_approved': True,
                'min_age_months': 0,
                'max_age_years': 14,
                'weight_based_dosing': False,
                'frequency_per_day': 2,
                'available_in_mali': True,
                'essential_drug_list': True
            }
        ]
        
        created_count = 0
        for med_data in medications:
            medication, created = Medication.objects.get_or_create(
                name=med_data['name'],
                generic_name=med_data['generic_name'],
                defaults=med_data
            )
            if created:
                created_count += 1
                self.stdout.write(f'Created medication: {medication.name}')
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} new medications'))

    def create_prescription_templates(self):
        """Create common prescription templates for Mali pediatric care"""
        
        # Get first doctor for created_by
        try:
            doctor = UserProfile.objects.filter(user_type='doctor').first()
        except:
            doctor = None
        
        templates = [
            {
                'name': 'Traitement Paludisme Simple',
                'description': 'Protocole standard pour le traitement du paludisme non compliqué chez l\'enfant',
                'category': MedicationCategory.objects.get(name='Antipaludiques'),
                'min_age_months': 6,
                'max_age_months': 168,  # 14 years
                'conditions': 'Paludisme non compliqué, absence de signes de gravité',
                'standard_instructions': 'Administrer avec les repas. Surveiller la température. Retour si pas d\'amélioration en 48h.',
                'is_who_approved': True,
                'is_mali_standard': True,
                'created_by': doctor
            },
            {
                'name': 'Diarrhée Aiguë Enfant',
                'description': 'Protocole de traitement de la diarrhée aiguë chez l\'enfant avec déshydratation légère',
                'category': MedicationCategory.objects.get(name='Antidiarrhéiques'),
                'min_age_months': 6,
                'max_age_months': 168,
                'conditions': 'Diarrhée aiguë sans déshydratation sévère, absence de sang dans les selles',
                'standard_instructions': 'Poursuivre l\'allaitement. Donner SRO après chaque selle. Alimentation normale dès que possible.',
                'is_who_approved': True,
                'is_mali_standard': True,
                'created_by': doctor
            },
            {
                'name': 'Infection Respiratoire Haute',
                'description': 'Traitement des infections respiratoires hautes chez l\'enfant',
                'category': MedicationCategory.objects.get(name='Antibiotiques'),
                'min_age_months': 6,
                'max_age_months': 168,
                'conditions': 'Infection respiratoire haute bactérienne présumée',
                'standard_instructions': 'Compléter le traitement même si amélioration. Repos et hydratation.',
                'is_who_approved': False,
                'is_mali_standard': True,
                'created_by': doctor
            },
            {
                'name': 'Fièvre et Douleur Pédiatrique',
                'description': 'Traitement symptomatique de la fièvre et de la douleur chez l\'enfant',
                'category': MedicationCategory.objects.get(name='Antipyrétiques/Analgésiques'),
                'min_age_months': 3,
                'max_age_months': 168,
                'conditions': 'Fièvre > 38.5°C ou douleur modérée à sévère',
                'standard_instructions': 'Administrer toutes les 6 heures maximum. Surveiller la température. Boire beaucoup.',
                'is_who_approved': True,
                'is_mali_standard': True,
                'created_by': doctor
            }
        ]
        
        created_templates = 0
        for template_data in templates:
            template, created = PrescriptionTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            if created:
                created_templates += 1
                self.stdout.write(f'Created template: {template.name}')
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_templates} new prescription templates'))

        # Add medications to templates
        self.add_medications_to_templates()

    def add_medications_to_templates(self):
        """Add medications to prescription templates"""
        
        try:
            # Paludisme template
            malaria_template = PrescriptionTemplate.objects.get(name='Traitement Paludisme Simple')
            artemether = Medication.objects.get(name='Artémether-Luméfantrine')
            paracetamol = Medication.objects.get(name='Paracétamol')
            
            TemplateMedication.objects.get_or_create(
                template=malaria_template,
                medication=artemether,
                defaults={
                    'standard_dose_per_kg': 1.0,
                    'standard_frequency': '2 fois par jour',
                    'standard_duration': 3,
                    'standard_instructions': 'Administrer avec les repas',
                    'order': 1
                }
            )
            
            TemplateMedication.objects.get_or_create(
                template=malaria_template,
                medication=paracetamol,
                defaults={
                    'standard_dose_per_kg': 15.0,
                    'standard_frequency': '3 fois par jour',
                    'standard_duration': 3,
                    'standard_instructions': 'Si fièvre > 38.5°C',
                    'order': 2,
                    'is_optional': True
                }
            )
            
            # Diarrhée template
            diarrhea_template = PrescriptionTemplate.objects.get(name='Diarrhée Aiguë Enfant')
            sro = Medication.objects.get(name='Sels de Réhydratation Orale (SRO)')
            zinc = Medication.objects.get(name='Zinc')
            
            TemplateMedication.objects.get_or_create(
                template=diarrhea_template,
                medication=sro,
                defaults={
                    'standard_frequency': 'Après chaque selle',
                    'standard_duration': 7,
                    'standard_instructions': 'Reconstituer dans 1L d\'eau propre',
                    'order': 1
                }
            )
            
            TemplateMedication.objects.get_or_create(
                template=diarrhea_template,
                medication=zinc,
                defaults={
                    'standard_frequency': '1 fois par jour',
                    'standard_duration': 10,
                    'standard_instructions': 'Continuer 10 jours même après arrêt diarrhée',
                    'order': 2
                }
            )
            
            self.stdout.write(self.style.SUCCESS('Added medications to templates'))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'Could not add medications to templates: {e}')) 