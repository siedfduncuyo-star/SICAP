from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="CurriculumItem", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("plan", models.CharField(choices=[("2017", "Plan 2017")], default="2017", max_length=20)),
            ("name", models.CharField(max_length=220, unique=True)),
            ("year", models.PositiveSmallIntegerField(blank=True, null=True)),
            ("group", models.CharField(blank=True, max_length=100, help_text="Ej.: Optativa de 3.º año")),
            ("hours", models.PositiveSmallIntegerField(blank=True, null=True)),
            ("shift_suggestion", models.CharField(blank=True, choices=[("", "Sin turno predeterminado"), ("Mañana", "Mañana"), ("Tarde", "Tarde"), ("Ambos", "Mañana y tarde")], max_length=20)),
            ("weekly_hours", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
            ("credits", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
            ("prerequisites_to_take", models.TextField(blank=True)),
            ("prerequisites_to_exam", models.TextField(blank=True)),
            ("source_verified", models.BooleanField(default=False)),
            ("updated_at", models.DateTimeField(auto_now=True)),
        ], options={"ordering": ["year", "group", "name"], "verbose_name": "espacio curricular", "verbose_name_plural": "espacios curriculares"}),
        migrations.CreateModel(name="Program", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("academic_year", models.PositiveSmallIntegerField()),
            ("status", models.CharField(choices=[("borrador", "Borrador"), ("enviado", "Enviado")], default="borrador", max_length=12)),
            ("current_step", models.PositiveSmallIntegerField(default=1)),
            ("payload", models.JSONField(blank=True, default=dict)),
            ("created_at", models.DateTimeField(auto_now_add=True)),
            ("updated_at", models.DateTimeField(auto_now=True)),
            ("submitted_at", models.DateTimeField(blank=True, null=True)),
            ("owner", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="programas", to=settings.AUTH_USER_MODEL)),
            ("subject", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to="programas.curriculumitem")),
        ], options={"ordering": ["-updated_at"]}),
    ]
