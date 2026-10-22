import json
from html import escape

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from svglib.svglib import svg2rlg

from .models import CurriculumItem, Program


STEP_TITLES = {
    1: "Datos de la cátedra",
    2: "Programa",
    3: "Fechas de evaluación",
    4: "Horarios de consulta",
    5: "Revisión y descarga",
}


def _program_for_user(program_id, user):
    program = get_object_or_404(Program.objects.select_related("subject", "owner"), pk=program_id)
    if not program.can_edit(user) and program.status != "enviado":
        raise Http404
    return program


@login_required
def dashboard(request):
    programs = Program.objects.select_related("subject", "owner")
    if not request.user.is_staff:
        programs = programs.filter(owner=request.user) | Program.objects.filter(status="enviado")
    query = request.GET.get("q", "").strip()
    if query:
        programs = programs.filter(subject__name__icontains=query)
    status = request.GET.get("estado", "")
    if status in {"borrador", "enviado"}:
        programs = programs.filter(status=status)
    return render(request, "programas/dashboard.html", {"programs": programs.distinct(), "query": query, "status": status})


@login_required
def new_program(request):
    program = Program.objects.create(owner=request.user, academic_year=timezone.localdate().year)
    program.payload = {"career": "Abogacía", "plan": "2017", "academic_year": program.academic_year, "team": [], "assessments": [], "consultations": []}
    program.save(update_fields=["payload"])
    return redirect("wizard", program_id=program.pk)


@login_required
def wizard(request, program_id):
    program = _program_for_user(program_id, request.user)
    if not program.can_edit(request.user) and program.status != "enviado":
        return redirect("dashboard")
    try:
        step = int(request.GET.get("paso", program.current_step))
    except ValueError:
        step = 1
    step = max(1, min(5, step))
    catalog = list(CurriculumItem.objects.all().values("id", "name", "year", "group", "hours", "shift_suggestion", "weekly_hours", "credits", "prerequisites_to_take", "prerequisites_to_exam", "source_verified"))
    return render(request, "programas/wizard.html", {"program": program, "step": step, "titles": STEP_TITLES, "catalog": catalog, "payload": program.payload, "read_only": not program.can_edit(request.user)})


@login_required
@require_POST
def save_step(request, program_id, step):
    program = _program_for_user(program_id, request.user)
    if not program.can_edit(request.user) or step not in range(1, 5):
        return JsonResponse({"error": "No tenés permiso para modificar esta carga."}, status=403)
    try:
        body = json.loads(request.body.decode("utf-8"))
        if not isinstance(body, dict):
            raise ValueError
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return JsonResponse({"error": "No se pudo leer la información enviada."}, status=400)

    payload = program.payload or {}
    allowed = {
        1: {"career", "plan", "academic_year", "subject_id", "subject_name", "course_year", "shift", "format", "term", "character", "evaluation_type", "hours", "weekly_hours", "credits", "prerequisites_to_take", "prerequisites_to_exam", "team", "team_confirmed"},
        2: {"framing", "objectives_general", "objectives_specific", "expectations", "methodology", "units", "evaluation_text", "bibliography"},
        3: {"assessments"},
        4: {"consultations_confirmed"},
    }[step]
    old_subject_id = str(payload.get("subject_id", ""))
    payload.update({key: value for key, value in body.items() if key in allowed})
    if step == 1:
        try:
            year = int(payload.get("academic_year", timezone.localdate().year))
            subject = CurriculumItem.objects.get(pk=int(payload.get("subject_id")))
        except (ValueError, TypeError, CurriculumItem.DoesNotExist):
            return JsonResponse({"error": "Seleccioná una asignatura del catálogo."}, status=400)
        if not 2020 <= year <= 2100:
            return JsonResponse({"error": "Ingresá un año académico válido."}, status=400)
        program.academic_year = year
        program.subject = subject
        payload["academic_year"] = year
        payload["subject_name"] = subject.name
        payload["career"] = "Abogacía"
        payload["plan"] = subject.plan
        changed_subject = old_subject_id != str(subject.pk)
        payload["subject_id"] = str(subject.pk)
        if changed_subject:
            previous = Program.objects.filter(subject=subject, status="enviado").exclude(pk=program.pk).order_by("-submitted_at").first()
            if previous:
                previous_payload = previous.payload or {}
                for key in ("format", "term", "character", "evaluation_type", "weekly_hours", "credits", "team", "consultations"):
                    if not payload.get(key) and previous_payload.get(key):
                        payload[key] = previous_payload[key]
        if changed_subject or not payload.get("course_year"):
            payload["course_year"] = subject.year or subject.group
        if changed_subject or "hours" not in payload:
            payload["hours"] = subject.hours
        if changed_subject or not payload.get("shift"):
            payload["shift"] = subject.shift_suggestion
        if changed_subject or "weekly_hours" not in payload:
            payload["weekly_hours"] = str(subject.weekly_hours) if subject.weekly_hours is not None else ""
        if changed_subject or "credits" not in payload:
            payload["credits"] = str(subject.credits) if subject.credits is not None else ""
        if changed_subject or not payload.get("prerequisites_to_take"):
            payload["prerequisites_to_take"] = subject.prerequisites_to_take
        if changed_subject or not payload.get("prerequisites_to_exam"):
            payload["prerequisites_to_exam"] = subject.prerequisites_to_exam
    program.payload = payload
    program.current_step = max(program.current_step, step + (0 if body.get("__advance") is False else 1))
    program.save()
    return JsonResponse({"ok": True, "next": min(step + 1, 5), "status": program.get_status_display()})


@login_required
@require_POST
def submit_program(request, program_id):
    program = _program_for_user(program_id, request.user)
    if not program.can_edit(request.user):
        return JsonResponse({"error": "No tenés permiso para enviar esta carga."}, status=403)
    if not program.subject_id:
        return JsonResponse({"error": "Completá primero los datos de la cátedra."}, status=400)
    if not (program.payload or {}).get("consultations_confirmed"):
        return JsonResponse({"error": "Confirmá que revisaste los horarios de consulta en SICDo."}, status=400)
    program.status = "enviado"
    program.submitted_at = timezone.now()
    program.current_step = 5
    program.save(update_fields=["status", "submitted_at", "current_step", "updated_at"])
    return JsonResponse({"ok": True, "pdf_url": f"/programas/{program.pk}/pdf/"})


def _p(text, style):
    safe = escape(str(text or "")).replace("\n", "<br/>")
    return Paragraph(safe or "—", style)


@login_required
def download_pdf(request, program_id):
    program = _program_for_user(program_id, request.user)
    data = program.payload or {}
    response = HttpResponse(content_type="application/pdf")
    subject = (data.get("subject_name") or "programa").replace(" ", "-")
    response["Content-Disposition"] = f'attachment; filename="SICAP-{program.academic_year}-{subject}.pdf"'
    doc = SimpleDocTemplate(response, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=15*mm, bottomMargin=18*mm)
    navy = colors.HexColor("#102E49")
    gold = colors.HexColor("#C5AD68")
    styles = getSampleStyleSheet()
    title = ParagraphStyle("SicapTitle", parent=styles["Title"], textColor=navy, fontName="Helvetica-Bold", fontSize=15, leading=19, alignment=TA_LEFT, spaceAfter=4)
    section = ParagraphStyle("SicapSection", parent=styles["Heading2"], textColor=navy, fontSize=11, leading=14, spaceBefore=9, spaceAfter=4)
    body = ParagraphStyle("SicapBody", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.5, leading=13, spaceAfter=4)
    small = ParagraphStyle("SicapSmall", parent=body, fontSize=8, leading=10)
    story = []
    logo_path = str(__import__("pathlib").Path(__file__).resolve().parent.parent / "static" / "img" / "logo-fd.svg")
    try:
        logo = svg2rlg(logo_path)
        if logo and logo.width:
            scale = min(65*mm / logo.width, 18*mm / logo.height)
            logo.width *= scale; logo.height *= scale; logo.scale(scale, scale)
            story.extend([logo, Spacer(1, 4*mm)])
    except Exception:
        pass
    story.extend([_p("SICAP · Programa de estudio", title), _p(data.get("subject_name", ""), title), Spacer(1, 3*mm)])
    facts = [
        ["Año académico", str(program.academic_year), "Carrera", "Abogacía"],
        ["Plan", data.get("plan", "2017"), "Año de cursado", str(data.get("course_year", "—"))],
        ["Turno", data.get("shift", "—"), "Formato", data.get("format", "—")],
        ["Régimen", data.get("term", "—"), "Carácter", data.get("character", "—")],
        ["Evaluación", data.get("evaluation_type", "—"), "Carga total", f"{data.get('hours', '—')} hs."],
        ["Carga semanal", data.get("weekly_hours", "—"), "Créditos", data.get("credits", "—")],
    ]
    table = Table([[Paragraph(f"<b>{escape(str(x))}</b>", small) if i % 2 == 0 else _p(x, small) for i, x in enumerate(row)] for row in facts], colWidths=[27*mm, 45*mm, 27*mm, 45*mm])
    table.setStyle(TableStyle([("BACKGROUND", (0,0), (0,-1), colors.HexColor("#EDF2F6")), ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#EDF2F6")), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#CFD9E1")), ("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 5), ("RIGHTPADDING", (0,0), (-1,-1), 5), ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5)]))
    story.extend([table, Spacer(1, 3*mm)])
    team = data.get("team", [])
    if team:
        story.append(_p("Equipo docente", section))
        for member in team:
            title_value = " · ".join(filter(None, [member.get("prefix"), member.get("degrees", "").strip()]))
            story.append(_p(" · ".join(filter(None, [member.get("position"), member.get("name"), title_value])), body))
    sections = [("Encuadre teórico / fundamentación", "framing"), ("Objetivo general", "objectives_general"), ("Objetivos específicos", "objectives_specific"), ("Expectativas de logro", "expectations"), ("Metodología de enseñanza y aprendizaje", "methodology"), ("Programa: unidades y contenidos", "units"), ("Evaluación", "evaluation_text"), ("Bibliografía", "bibliography")]
    for heading, key in sections:
        if data.get(key): story.extend([_p(heading, section), _p(data[key], body)])
    if data.get("assessments"):
        story.append(_p("Fechas previstas de trabajos prácticos y parciales", section))
        rows = [["Instancia", "Fecha", "Descripción"]]
        for item in data["assessments"]:
            rows.append([item.get("type", ""), item.get("date", ""), item.get("details", "")])
        table = Table([[ _p(c, small) for c in row] for row in rows], colWidths=[40*mm, 32*mm, 72*mm], repeatRows=1)
        table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), navy), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#CFD9E1")), ("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 5), ("RIGHTPADDING", (0,0), (-1,-1), 5)]))
        story.extend([table, Spacer(1, 3*mm)])
    if data.get("consultations"):
        story.append(_p("Horarios de consulta", section))
        for item in data["consultations"]:
            detail = " · ".join(filter(None, [item.get("day"), f"{item.get('from','')} a {item.get('to','')}", item.get("modality"), item.get("place") or item.get("link")]))
            story.append(_p(detail, body))
    elif data.get("consultations_confirmed"):
        story.extend([_p("Horarios de consulta", section), _p("Revisados y gestionados en el Sistema de Información de Consultas Docentes (SICDo): https://consultas.derecho.uncu.edu.ar/horarios", body)])
    def draw_footer(canvas, _doc):
        canvas.saveState(); canvas.setStrokeColor(gold); canvas.setLineWidth(1); canvas.line(18*mm, 13*mm, 192*mm, 13*mm)
        canvas.setFont("Helvetica", 8); canvas.setFillColor(colors.HexColor("#526273")); canvas.drawString(18*mm, 8*mm, f"SICAP · Año académico {program.academic_year}")
        canvas.drawRightString(192*mm, 8*mm, f"Página {_doc.page}"); canvas.restoreState()
    doc.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    return response
