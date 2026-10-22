from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("programas/nuevo/", views.new_program, name="new_program"),
    path("programas/<int:program_id>/", views.wizard, name="wizard"),
    path("programas/<int:program_id>/guardar/<int:step>/", views.save_step, name="save_step"),
    path("programas/<int:program_id>/enviar/", views.submit_program, name="submit_program"),
    path("programas/<int:program_id>/pdf/", views.download_pdf, name="download_pdf"),
]
