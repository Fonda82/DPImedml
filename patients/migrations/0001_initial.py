# Generated by Django 4.2.23 on 2025-06-15 22:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("facilities", "0001_initial"),
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Patient",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "unique_id",
                    models.CharField(editable=False, max_length=20, unique=True),
                ),
                ("first_name", models.CharField(max_length=50)),
                ("last_name", models.CharField(max_length=50)),
                ("date_of_birth", models.DateField()),
                (
                    "gender",
                    models.CharField(
                        choices=[("M", "Masculin"), ("F", "Féminin"), ("O", "Autre")],
                        max_length=1,
                    ),
                ),
                (
                    "phone_number",
                    models.CharField(blank=True, max_length=15, null=True),
                ),
                ("address", models.TextField()),
                (
                    "guardian_name",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                (
                    "guardian_phone",
                    models.CharField(blank=True, max_length=15, null=True),
                ),
                ("registered_at", models.DateTimeField(auto_now_add=True)),
                ("last_updated", models.DateTimeField(auto_now=True)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "user",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="patient",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Patient",
                "verbose_name_plural": "Patients",
            },
        ),
        migrations.CreateModel(
            name="MedicalRecord",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("consultation_date", models.DateTimeField()),
                ("chief_complaint", models.TextField()),
                ("diagnosis", models.TextField()),
                ("treatment", models.TextField()),
                ("notes", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "doctor",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="medical_records",
                        to="accounts.userprofile",
                    ),
                ),
                (
                    "facility",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="facilities.facility",
                    ),
                ),
                (
                    "patient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="medical_records",
                        to="patients.patient",
                    ),
                ),
            ],
            options={
                "verbose_name": "Dossier médical",
                "verbose_name_plural": "Dossiers médicaux",
                "ordering": ["-consultation_date"],
            },
        ),
    ]
