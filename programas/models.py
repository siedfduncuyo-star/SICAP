from django.conf import settings
from django.db import models


class CurriculumItem(models.Model):
    PLAN_CHOICES = [("2017", "Plan 2017")]
    TURN_CHOICES = [("", "Sin turno predeterminado"), ("Mañana", "Mañana"), ("Tarde", "Tarde"), ("Ambos", "Mañana y tarde")]

    plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default="2017")
    name = models.CharField(max_length=220, unique=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    group = models.CharField(max_length=100, blank=True, help_text="Ej.: Optativa de 3.º año")
    hours = models.PositiveSmallIntegerField(null=True, blank=True)
    shift_suggestion = models.CharField(max_length=20, choices=TURN_CHOICES, blank=True)
    weekly_hours = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    credits = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    prerequisites_to_take = models.TextField(blank=True)
    prerequisites_to_exam = models.TextField(blank=True)
    source_verified = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["year", "group", "name"]
        verbose_name = "espacio curricular"
        verbose_name_plural = "espacios curriculares"

    def __str__(self):
        prefix = f"{self.year}.º año · " if self.year else f"{self.group} · "
        return f"{prefix}{self.name}"


class Program(models.Model):
    STATUS_CHOICES = [("borrador", "Borrador"), ("enviado", "Enviado")]
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="programas")
    academic_year = models.PositiveSmallIntegerField()
    subject = models.ForeignKey(CurriculumItem, null=True, blank=True, on_delete=models.PROTECT)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="borrador")
    current_step = models.PositiveSmallIntegerField(default=1)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        subject = self.subject.name if self.subject_id else "Sin asignatura"
        return f"{self.academic_year} · {subject} · {self.get_status_display()}"

    def can_edit(self, user):
        return user.is_staff or (self.owner_id == user.id and self.status == "borrador")
