from django.contrib import admin
from .models import CurriculumItem, Program

@admin.register(CurriculumItem)
class CurriculumItemAdmin(admin.ModelAdmin):
    list_display = ("name", "year", "group", "hours", "shift_suggestion", "source_verified")
    list_filter = ("year", "source_verified", "shift_suggestion")
    search_fields = ("name", "group")
    list_editable = ("hours", "shift_suggestion", "source_verified")

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("academic_year", "subject", "owner", "status", "updated_at")
    list_filter = ("academic_year", "status")
    search_fields = ("subject__name", "owner__username", "owner__email")
    readonly_fields = ("created_at", "updated_at", "submitted_at")
