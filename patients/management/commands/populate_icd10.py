from django.core.management.base import BaseCommand
from patients.models import ICD10Code


class Command(BaseCommand):
    help = 'Populate ICD-10 database with pediatric disability codes and common conditions in Mali'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting ICD-10 database population...'))
        
        # ICD-10 codes focused on pediatric disabilities and common conditions in Mali
        icd10_codes = [
            # F00-F99: Mental and Behavioral Disorders (Pediatric Focus)
            {
                'code': 'F70.9',
                'title': 'Déficience intellectuelle légère, sans précision',
                'description': 'Déficience intellectuelle légère (QI 50-69) sans précision supplémentaire.',
                'category': 'F00-F99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },
            {
                'code': 'F71.9',
                'title': 'Déficience intellectuelle modérée, sans précision',
                'description': 'Déficience intellectuelle modérée (QI 35-49) sans précision supplémentaire.',
                'category': 'F00-F99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },
            {
                'code': 'F72.9',
                'title': 'Déficience intellectuelle grave, sans précision',
                'description': 'Déficience intellectuelle grave (QI 20-34) sans précision supplémentaire.',
                'category': 'F00-F99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },
            {
                'code': 'F84.0',
                'title': 'Autisme infantile',
                'description': 'Trouble autistique présent avant l\'âge de 3 ans avec altérations de la communication et interactions sociales.',
                'category': 'F00-F99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': False
            },
            {
                'code': 'F84.9',
                'title': 'Trouble envahissant du développement, sans précision',
                'description': 'Trouble du spectre autistique sans spécification supplémentaire.',
                'category': 'F00-F99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': False
            },
            {
                'code': 'F90.0',
                'title': 'Trouble de l\'activité et de l\'attention',
                'description': 'TDAH avec déficit de l\'attention et hyperactivité.',
                'category': 'F00-F99',
                'is_pediatric_relevant': True,
                'is_disability_related': False,
                'is_common_in_mali': False
            },
            {
                'code': 'F98.5',
                'title': 'Bégaiement [Balbuties]',
                'description': 'Trouble de la fluence verbale caractérisé par des répétitions et prolongations involontaires.',
                'category': 'F00-F99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },

            # G00-G99: Diseases of the Nervous System (Pediatric Focus)
            {
                'code': 'G80.0',
                'title': 'Paralysie cérébrale spastique quadriplégique',
                'description': 'Paralysie cérébrale affectant les quatre membres avec spasticité.',
                'category': 'G00-G99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },
            {
                'code': 'G80.1',
                'title': 'Paralysie cérébrale spastique diplégique',
                'description': 'Paralysie cérébrale affectant principalement les membres inférieurs.',
                'category': 'G00-G99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },
            {
                'code': 'G80.2',
                'title': 'Paralysie cérébrale spastique hémiplégique',
                'description': 'Paralysie cérébrale affectant un côté du corps.',
                'category': 'G00-G99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },
            {
                'code': 'G80.3',
                'title': 'Paralysie cérébrale dyskinétique',
                'description': 'Paralysie cérébrale caractérisée par des mouvements involontaires.',
                'category': 'G00-G99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': False
            },
            {
                'code': 'G80.4',
                'title': 'Paralysie cérébrale ataxique',
                'description': 'Paralysie cérébrale avec troubles de la coordination et de l\'équilibre.',
                'category': 'G00-G99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': False
            },
            {
                'code': 'G80.9',
                'title': 'Paralysie cérébrale, sans précision',
                'description': 'Paralysie cérébrale non spécifiée.',
                'category': 'G00-G99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },
            {
                'code': 'G93.1',
                'title': 'Lésion cérébrale anoxique, non classée ailleurs',
                'description': 'Lésion cérébrale due à un manque d\'oxygène.',
                'category': 'G00-G99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },
            {
                'code': 'G40.9',
                'title': 'Épilepsie, sans précision',
                'description': 'Épilepsie non spécifiée.',
                'category': 'G00-G99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },

            # H00-H59: Diseases of the Eye and Adnexa
            {
                'code': 'H54.0',
                'title': 'Cécité, binoculaire',
                'description': 'Cécité affectant les deux yeux.',
                'category': 'H00-H59',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },
            {
                'code': 'H54.1',
                'title': 'Cécité d\'un œil, malvoyance de l\'autre',
                'description': 'Cécité unilatérale avec malvoyance controlatérale.',
                'category': 'H00-H59',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },
            {
                'code': 'H54.2',
                'title': 'Malvoyance binoculaire',
                'description': 'Déficience visuelle affectant les deux yeux.',
                'category': 'H00-H59',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },
            {
                'code': 'H25.9',
                'title': 'Cataracte sénile, sans précision',
                'description': 'Cataracte liée à l\'âge, peut être congénitale chez l\'enfant.',
                'category': 'H00-H59',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },

            # H60-H95: Diseases of the Ear and Mastoid Process
            {
                'code': 'H90.3',
                'title': 'Surdité neurosensorielle, bilatérale',
                'description': 'Surdité de perception affectant les deux oreilles.',
                'category': 'H60-H95',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },
            {
                'code': 'H90.4',
                'title': 'Surdité neurosensorielle, unilatérale avec audition normale controlatérale',
                'description': 'Surdité de perception d\'un côté avec audition normale de l\'autre côté.',
                'category': 'H60-H95',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },
            {
                'code': 'H91.9',
                'title': 'Déficience auditive, sans précision',
                'description': 'Perte auditive non spécifiée.',
                'category': 'H60-H95',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },

            # Q00-Q99: Congenital Malformations
            {
                'code': 'Q05.9',
                'title': 'Spina bifida, sans précision',
                'description': 'Malformation congénitale de la colonne vertébrale.',
                'category': 'Q00-Q99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },
            {
                'code': 'Q66.9',
                'title': 'Déformation congénitale du pied, sans précision',
                'description': 'Malformation congénitale du pied non spécifiée.',
                'category': 'Q00-Q99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },
            {
                'code': 'Q72.9',
                'title': 'Anomalie de réduction du membre inférieur, sans précision',
                'description': 'Malformation congénitale du membre inférieur.',
                'category': 'Q00-Q99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': False
            },
            {
                'code': 'Q71.9',
                'title': 'Anomalie de réduction du membre supérieur, sans précision',
                'description': 'Malformation congénitale du membre supérieur.',
                'category': 'Q00-Q99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': False
            },
            {
                'code': 'Q90.9',
                'title': 'Syndrome de Down, sans précision',
                'description': 'Trisomie 21 non spécifiée.',
                'category': 'Q00-Q99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': False
            },

            # Common Pediatric Conditions in Mali
            {
                'code': 'E43',
                'title': 'Malnutrition protéino-énergétique grave, sans précision',
                'description': 'Malnutrition sévère chez l\'enfant.',
                'category': 'OTHER',
                'is_pediatric_relevant': True,
                'is_disability_related': False,
                'is_common_in_mali': True
            },
            {
                'code': 'E46',
                'title': 'Malnutrition protéino-énergétique, sans précision',
                'description': 'Malnutrition non spécifiée.',
                'category': 'OTHER',
                'is_pediatric_relevant': True,
                'is_disability_related': False,
                'is_common_in_mali': True
            },
            {
                'code': 'A15.9',
                'title': 'Tuberculose respiratoire, sans précision',
                'description': 'Tuberculose pulmonaire non spécifiée.',
                'category': 'OTHER',
                'is_pediatric_relevant': True,
                'is_disability_related': False,
                'is_common_in_mali': True
            },
            {
                'code': 'B50.9',
                'title': 'Paludisme à Plasmodium falciparum, sans précision',
                'description': 'Paludisme grave non spécifié.',
                'category': 'OTHER',
                'is_pediatric_relevant': True,
                'is_disability_related': False,
                'is_common_in_mali': True
            },
            {
                'code': 'K59.0',
                'title': 'Constipation',
                'description': 'Constipation chronique.',
                'category': 'OTHER',
                'is_pediatric_relevant': True,
                'is_disability_related': False,
                'is_common_in_mali': True
            },

            # Z codes for follow-up and rehabilitation
            {
                'code': 'Z50.9',
                'title': 'Soins de réadaptation, sans précision',
                'description': 'Réadaptation non spécifiée.',
                'category': 'Z00-Z99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },
            {
                'code': 'Z51.8',
                'title': 'Autres soins médicaux précisés',
                'description': 'Autres soins médicaux spécifiés.',
                'category': 'Z00-Z99',
                'is_pediatric_relevant': True,
                'is_disability_related': False,
                'is_common_in_mali': True
            },
            {
                'code': 'Z00.1',
                'title': 'Examen de routine de l\'enfant',
                'description': 'Examen médical de routine chez l\'enfant.',
                'category': 'Z00-Z99',
                'is_pediatric_relevant': True,
                'is_disability_related': False,
                'is_common_in_mali': True
            },

            # Additional developmental and learning disorders
            {
                'code': 'F81.9',
                'title': 'Trouble du développement des acquisitions scolaires, sans précision',
                'description': 'Troubles d\'apprentissage non spécifiés.',
                'category': 'F00-F99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': True
            },
            {
                'code': 'F88',
                'title': 'Autres troubles du développement psychologique',
                'description': 'Autres troubles développementaux spécifiés.',
                'category': 'F00-F99',
                'is_pediatric_relevant': True,
                'is_disability_related': True,
                'is_common_in_mali': False
            },
        ]

        # Create ICD-10 codes
        created_count = 0
        updated_count = 0
        
        for code_data in icd10_codes:
            icd10_code, created = ICD10Code.objects.get_or_create(
                code=code_data['code'],
                defaults=code_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f"✅ Created: {icd10_code.code} - {icd10_code.title}")
            else:
                # Update existing code
                for field, value in code_data.items():
                    setattr(icd10_code, field, value)
                icd10_code.save()
                updated_count += 1
                self.stdout.write(f"🔄 Updated: {icd10_code.code} - {icd10_code.title}")

        self.stdout.write(
            self.style.SUCCESS(
                f'\n🎉 ICD-10 database population completed!\n'
                f'📊 Created: {created_count} new codes\n'
                f'🔄 Updated: {updated_count} existing codes\n'
                f'📈 Total: {created_count + updated_count} codes in database\n'
                f'\n🏥 Focus areas:\n'
                f'   • Pediatric disabilities (0-14 years)\n'
                f'   • Common conditions in Mali\n'
                f'   • Professional ICD-10 coding standards\n'
                f'   • Rehabilitation and follow-up codes'
            )
        ) 