# Generated by Django 4.2.23 on 2025-06-19 10:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="SystemActivity",
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
                ("action", models.CharField(max_length=100)),
                ("description", models.TextField()),
                ("timestamp", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "action_type",
                    models.CharField(
                        choices=[
                            ("login", "Login"),
                            ("create", "Create"),
                            ("update", "Update"),
                            ("delete", "Delete"),
                            ("register", "Register"),
                            ("other", "Other"),
                        ],
                        default="other",
                        max_length=20,
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "System Activity",
                "verbose_name_plural": "System Activities",
                "ordering": ["-timestamp"],
            },
        ),
    ]
