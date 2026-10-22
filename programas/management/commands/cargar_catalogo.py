import csv
from pathlib import Path
from django.core.management.base import BaseCommand
from programas.models import CurriculumItem

class Command(BaseCommand):
    help = "Carga o actualiza el catálogo de Abogacía desde el CSV de referencia."

    SHIFT_SUGGESTIONS = {
        "Derecho Civil": "Ambos",
        "Derecho Político": "Ambos",
        "Historia de las Instituciones Argentinas y Latinoamericanas": "Ambos",
        "Inglés I": "Ambos",
        "Derecho Penal Parte General II": "Mañana",
        "Derecho de las Obligaciones II": "Mañana",
        "Derecho del Consumidor y Defensa de la Competencia": "Mañana",
        "Finanzas Públicas y Derecho Tributario": "Mañana",
        "Inglés III": "Mañana",
        "Práctica Profesional Supervisada II": "Mañana",
    }

    def handle(self, *args, **options):
        source = Path(__file__).resolve().parents[2] / "data" / "abogacia.csv"
        count = 0
        with source.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                year = int(row["year"]) if row["year"].strip() else None
                hours = int(row["hours"]) if row["hours"].strip() else None
                CurriculumItem.objects.update_or_create(
                    name=row["name"],
                    defaults={"plan": "2017", "year": year, "group": row["group"], "hours": hours,
                              "shift_suggestion": self.SHIFT_SUGGESTIONS.get(row["name"], ""), "source_verified": False},
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f"Catálogo SICAP: {count} espacios cargados/actualizados."))
