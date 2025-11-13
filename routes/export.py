from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file
from functools import wraps
from models.models import User, TimeRecord, EmployeeStatus, Center, Category
from models.database import db
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta, date
import os
import tempfile
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from openpyxl.utils import get_column_letter
from collections import defaultdict

export_bp = Blueprint("export", __name__, template_folder="../templates")

STATUS_GROUPS = {
    "Trabajado": ["Trabajado"],
    "Baja": ["Baja"],
    "Ausente": ["Ausente", "Ausencia justificada", "Ausencia injustificada"],
    "Vacaciones": ["Vacaciones", "Permiso especial"]
}


def expand_status_filters(filters):
    """Expande filtros de estado generales a sus valores específicos."""
    expanded = []
    for status in filters:
        expanded.extend(STATUS_GROUPS.get(status, [status]))
    # Mantener orden y evitar duplicados
    seen = set()
    ordered_unique = []
    for status in expanded:
        if status not in seen:
            seen.add(status)
            ordered_unique.append(status)
    return ordered_unique

# Decorator to check if user is admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("is_admin"):
            flash("Acceso no autorizado. Se requieren permisos de administrador.", "danger")
            return redirect(url_for("auth.login"))
        user = User.query.get(session.get("user_id"))
        if not user or not user.role:
            session.clear()
            flash("Tu cuenta ya no tiene permisos de administrador.", "danger")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

# ========== FUNCIONES HELPER PARA EXPORTACIONES DIARIAS CON FILTROS ==========

def handle_daily_excel_export(req):
    """Maneja exportación Excel diaria con filtros de estado"""
    # Obtener fecha (hoy si no se especifica)
    start_date = req.form.get("start_date")
    end_date = req.form.get("end_date")

    if start_date:
        fecha = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        fecha = date.today()

    # Obtener filtros de estado
    status_filters = req.form.getlist('status')
    if not status_filters:
        status_filters = ['Trabajado']

    # Obtener registros de TimeRecord (si "Trabajado" está seleccionado)
    time_records = []
    if 'Trabajado' in status_filters:
        time_records = TimeRecord.query.filter(TimeRecord.date == fecha).order_by(TimeRecord.user_id).all()

    # Obtener registros de EmployeeStatus (Baja, Ausente, Vacaciones)
    employee_statuses = []
    selected_statuses = expand_status_filters([s for s in status_filters if s != 'Trabajado'])
    if selected_statuses:
        employee_statuses = EmployeeStatus.query.filter(
            EmployeeStatus.status.in_(selected_statuses),
            EmployeeStatus.date == fecha
        ).order_by(EmployeeStatus.user_id).all()

    if not time_records and not employee_statuses:
        flash("No hay registros para ese día con los filtros seleccionados.", "warning")
        return redirect(url_for("export.export_excel"))

    # Generar Excel con 3 pestañas
    wb = openpyxl.Workbook()

    # Pestaña 1: Registros de Fichaje
    if time_records:
        ws1 = wb.active
        ws1.title = "Registros de Fichaje"
        header1 = ["Usuario", "Nombre completo", "Categoría", "Centro", "Fecha", "Entrada", "Salida", "Horas Trabajadas", "Notas"]
        for col_num, header_text in enumerate(header1, 1):
            cell = ws1.cell(row=1, column=col_num)
            cell.value = header_text
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
            cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")

        row_num = 2
        for record in time_records:
            user = User.query.get(record.user_id)
            hours_worked = ""
            if record.check_in and record.check_out:
                time_diff = record.check_out - record.check_in
                hours = time_diff.total_seconds() / 3600
                hours_worked = f"{hours:.2f}"

            ws1.cell(row=row_num, column=1).value = user.username if user else f"ID: {record.user_id}"
            ws1.cell(row=row_num, column=2).value = user.full_name if user else "-"
            ws1.cell(row=row_num, column=3).value = user.categoria if user and user.categoria else "-"
            ws1.cell(row=row_num, column=4).value = user.centro if user and user.centro else "-"
            ws1.cell(row=row_num, column=5).value = record.date.strftime("%d/%m/%Y")
            ws1.cell(row=row_num, column=6).value = record.check_in.strftime("%H:%M:%S") if record.check_in else "-"
            ws1.cell(row=row_num, column=7).value = record.check_out.strftime("%H:%M:%S") if record.check_out else "-"
            ws1.cell(row=row_num, column=8).value = hours_worked
            ws1.cell(row=row_num, column=9).value = record.notes
            row_num += 1

        for col_num, _ in enumerate(header1, 1):
            col_letter = get_column_letter(col_num)
            ws1.column_dimensions[col_letter].width = 17
    else:
        wb.remove(wb.active)

    # Pestaña 2: Bajas y Ausencias
    if employee_statuses:
        ws2 = wb.create_sheet("Bajas y Ausencias")
        header2 = ["Usuario", "Nombre completo", "Categoría", "Centro", "Fecha", "Estado", "Notas"]
        for col_num, header_text in enumerate(header2, 1):
            cell = ws2.cell(row=1, column=col_num)
            cell.value = header_text
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
            cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")

        row_num = 2
        for status_record in employee_statuses:
            user = User.query.get(status_record.user_id)
            ws2.cell(row=row_num, column=1).value = user.username if user else f"ID: {status_record.user_id}"
            ws2.cell(row=row_num, column=2).value = user.full_name if user else "-"
            ws2.cell(row=row_num, column=3).value = user.categoria if user and user.categoria else "-"
            ws2.cell(row=row_num, column=4).value = user.centro if user and user.centro else "-"
            ws2.cell(row=row_num, column=5).value = status_record.date.strftime("%d/%m/%Y")
            ws2.cell(row=row_num, column=6).value = status_record.status
            ws2.cell(row=row_num, column=7).value = status_record.notes or "-"
            row_num += 1

        for col_num, _ in enumerate(header2, 1):
            col_letter = get_column_letter(col_num)
            ws2.column_dimensions[col_letter].width = 17

    # Pestaña 3: Resumen Consolidado
    ws3 = wb.create_sheet("Resumen Consolidado")
    header3 = ["Usuario", "Nombre completo", "Categoría", "Centro", "Fecha", "Estado", "Entrada", "Salida", "Horas", "Notas"]
    for col_num, header_text in enumerate(header3, 1):
        cell = ws3.cell(row=1, column=col_num)
        cell.value = header_text
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')
        cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")

    consolidated_records = []
    for record in time_records:
        user = User.query.get(record.user_id)
        hours_worked = ""
        if record.check_in and record.check_out:
            time_diff = record.check_out - record.check_in
            hours = time_diff.total_seconds() / 3600
            hours_worked = f"{hours:.2f}"
        consolidated_records.append({
            'user_id': record.user_id,
            'username': user.username if user else f"ID: {record.user_id}",
            'full_name': user.full_name if user else "-",
            'categoria': user.categoria if user and user.categoria else "-",
            'centro': user.centro if user and user.centro else "-",
            'date': record.date,
            'estado': "Trabajado",
            'entrada': record.check_in.strftime("%H:%M:%S") if record.check_in else "-",
            'salida': record.check_out.strftime("%H:%M:%S") if record.check_out else "-",
            'horas': hours_worked,
            'notas': record.notes or "-"
        })

    for status_record in employee_statuses:
        user = User.query.get(status_record.user_id)
        consolidated_records.append({
            'user_id': status_record.user_id,
            'username': user.username if user else f"ID: {status_record.user_id}",
            'full_name': user.full_name if user else "-",
            'categoria': user.categoria if user and user.categoria else "-",
            'centro': user.centro if user and user.centro else "-",
            'date': status_record.date,
            'estado': status_record.status,
            'entrada': "-",
            'salida': "-",
            'horas': "-",
            'notas': status_record.notes or "-"
        })

    consolidated_records.sort(key=lambda x: (x['user_id'], x['date']))

    row_num = 2
    for rec in consolidated_records:
        ws3.cell(row=row_num, column=1).value = rec['username']
        ws3.cell(row=row_num, column=2).value = rec['full_name']
        ws3.cell(row=row_num, column=3).value = rec['categoria']
        ws3.cell(row=row_num, column=4).value = rec['centro']
        ws3.cell(row=row_num, column=5).value = rec['date'].strftime("%d/%m/%Y")
        ws3.cell(row=row_num, column=6).value = rec['estado']
        ws3.cell(row=row_num, column=7).value = rec['entrada']
        ws3.cell(row=row_num, column=8).value = rec['salida']
        ws3.cell(row=row_num, column=9).value = rec['horas']
        ws3.cell(row=row_num, column=10).value = rec['notas']
        row_num += 1

    for col_num, _ in enumerate(header3, 1):
        col_letter = get_column_letter(col_num)
        ws3.column_dimensions[col_letter].width = 17

    fd, temp_path = tempfile.mkstemp(suffix='.xlsx')
    os.close(fd)
    wb.save(temp_path)

    filename = f"{fecha.strftime('%d_%m_%y')}_TimeT.xlsx"
    return send_file(
        temp_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

def handle_daily_pdf_export(req):
    """Maneja exportación PDF diaria con filtros de estado"""
    from fpdf import FPDF

    # Obtener fecha (hoy si no se especifica)
    start_date = req.form.get("start_date")
    end_date = req.form.get("end_date")

    if start_date:
        fecha = datetime.strptime(start_date, "%Y-%m-%d").date()
    else:
        fecha = date.today()

    # Obtener filtros de estado
    status_filters = req.form.getlist('status')
    if not status_filters:
        status_filters = ['Trabajado']

    # Obtener registros de TimeRecord (si "Trabajado" está seleccionado)
    time_records = []
    if 'Trabajado' in status_filters:
        time_records = TimeRecord.query.filter(TimeRecord.date == fecha).order_by(TimeRecord.user_id).all()

    # Obtener registros de EmployeeStatus (Baja, Ausente, Vacaciones)
    employee_statuses = []
    selected_statuses = expand_status_filters([s for s in status_filters if s != 'Trabajado'])
    if selected_statuses:
        employee_statuses = EmployeeStatus.query.filter(
            EmployeeStatus.status.in_(selected_statuses),
            EmployeeStatus.date == fecha
        ).order_by(EmployeeStatus.user_id).all()

    if not time_records and not employee_statuses:
        flash("No hay registros para ese día con los filtros seleccionados.", "warning")
        return redirect(url_for("export.export_excel"))

    # Crear PDF
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Registros del {fecha.strftime('%d/%m/%Y')}", ln=1, align="C")

    # Sección 1: Registros de Fichaje (si hay)
    if time_records:
        pdf.ln(5)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, "Registros de Fichaje", ln=1)

        pdf.set_font("Arial", "B", 9)
        header = ["Usuario", "Nombre", "Categoria", "Centro", "Entrada", "Salida", "Horas", "Notas"]
        col_widths = [28, 35, 22, 28, 20, 20, 18, 50]

        for i, col_name in enumerate(header):
            pdf.cell(col_widths[i], 7, col_name, border=1, align="C")
        pdf.ln()

        pdf.set_font("Arial", "", 8)
        for record in time_records:
            user = User.query.get(record.user_id)
            hours_worked = ""
            if record.check_in and record.check_out:
                time_diff = record.check_out - record.check_in
                hours = time_diff.total_seconds() / 3600
                hours_worked = f"{hours:.2f}"

            pdf.cell(col_widths[0], 6, user.username if user else f"ID:{record.user_id}", border=1)
            pdf.cell(col_widths[1], 6, (user.full_name if user else "-")[:20], border=1)
            pdf.cell(col_widths[2], 6, user.categoria if user and user.categoria else "-", border=1)
            pdf.cell(col_widths[3], 6, (user.centro if user and user.centro else "-")[:15], border=1)
            pdf.cell(col_widths[4], 6, record.check_in.strftime("%H:%M") if record.check_in else "-", border=1, align="C")
            pdf.cell(col_widths[5], 6, record.check_out.strftime("%H:%M") if record.check_out else "-", border=1, align="C")
            pdf.cell(col_widths[6], 6, hours_worked, border=1, align="C")
            pdf.cell(col_widths[7], 6, (record.notes or "")[:30], border=1)
            pdf.ln()

    # Sección 2: Bajas y Ausencias (si hay)
    if employee_statuses:
        pdf.ln(8)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(0, 8, "Bajas y Ausencias", ln=1)

        pdf.set_font("Arial", "B", 9)
        header2 = ["Usuario", "Nombre", "Categoria", "Centro", "Estado", "Notas"]
        col_widths2 = [35, 45, 28, 35, 35, 70]

        for i, col_name in enumerate(header2):
            pdf.cell(col_widths2[i], 7, col_name, border=1, align="C")
        pdf.ln()

        pdf.set_font("Arial", "", 8)
        for status_record in employee_statuses:
            user = User.query.get(status_record.user_id)

            pdf.cell(col_widths2[0], 6, user.username if user else f"ID:{status_record.user_id}", border=1)
            pdf.cell(col_widths2[1], 6, (user.full_name if user else "-")[:25], border=1)
            pdf.cell(col_widths2[2], 6, user.categoria if user and user.categoria else "-", border=1)
            pdf.cell(col_widths2[3], 6, (user.centro if user and user.centro else "-")[:20], border=1)
            pdf.cell(col_widths2[4], 6, status_record.status, border=1, align="C")
            pdf.cell(col_widths2[5], 6, (status_record.notes or "")[:40], border=1)
            pdf.ln()

    # Guardar PDF
    fd, temp_path = tempfile.mkstemp(suffix='.pdf')
    os.close(fd)
    pdf.output(temp_path)

    filename = f"{fecha.strftime('%d_%m_%y')}_TimeT.pdf"
    return send_file(
        temp_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )

# ========== EXPORTACIÓN PRINCIPAL CON FILTROS ==========

@export_bp.route("/excel", methods=["GET", "POST"])
@admin_required
def export_excel():
    if request.method == "POST":
        # Detectar botones de Excel/PDF Diario
        if 'export_daily_excel' in request.form:
            return handle_daily_excel_export(request)
        if 'export_daily_pdf' in request.form:
            return handle_daily_pdf_export(request)

        # Detectar qué botón se ha pulsado realmente (el último en el array de botones recibidos)
        botones = [k for k in request.form.keys() if k.startswith('excel_')]
        boton_pulsado = botones[-1] if botones else None

        # LOG de depuración para ver los valores recibidos
        print('--- FILTROS RECIBIDOS ---')
        print('Botones recibidos:', botones)
        print('Botón realmente pulsado:', boton_pulsado)
        print('centro1:', request.form.get('centro1'))
        print('usuario1:', request.form.get('usuario1'))
        print('centro2:', request.form.get('centro2'))
        print('categoria2:', request.form.get('categoria2'))
        print('centro3:', request.form.get('centro3'))
        print('horas3:', request.form.get('horas3'))
        print('centro4:', request.form.get('centro4'))
        print('usuario4:', request.form.get('usuario4'))
        print('categoria4:', request.form.get('categoria4'))
        print('horas4:', request.form.get('horas4'))
        print('start_date:', request.form.get('start_date'))
        print('end_date:', request.form.get('end_date'))

        # Inicializar filtros
        centro = user_id = categoria = weekly_hours = None

        # Usar los campos correctos según el botón realmente pulsado
        if boton_pulsado == "excel_centro_usuario":
            centro = request.form.get("centro1")
            user_id = request.form.get("usuario1")
        elif boton_pulsado == "excel_centro_categoria":
            centro = request.form.get("centro2")
            categoria = request.form.get("categoria2")
        elif boton_pulsado == "excel_centro_horas":
            centro = request.form.get("centro3")
            weekly_hours = request.form.get("horas3")
        elif boton_pulsado == "excel_solo_centro":
            centro = request.form.get("centro4")
        elif boton_pulsado == "excel_solo_usuario":
            user_id = request.form.get("usuario4")
        elif boton_pulsado == "excel_solo_categoria":
            categoria = request.form.get("categoria4")
        elif boton_pulsado == "excel_solo_horas":
            weekly_hours = request.form.get("horas4")
        else:
            # Compatibilidad con los filtros antiguos
            centro = request.form.get("centro")
            user_id = request.form.get("user_id")
            categoria = request.form.get("categoria")
            weekly_hours = request.form.get("weekly_hours") or request.form.get("jornada")

        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        # Validación fechas
        try:
            if start_date:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            else:
                start_date = date.today()
            if end_date:
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            else:
                end_date = date.today()
            if end_date < start_date:
                flash("La fecha de fin no puede ser anterior a la fecha de inicio.", "danger")
                return redirect(url_for("export.export_excel"))
        except ValueError:
            flash("Formato de fecha inválido. Use YYYY-MM-DD.", "danger")
            return redirect(url_for("export.export_excel"))

        # Obtener filtros de estado
        status_filters = request.form.getlist('status')
        if not status_filters:
            status_filters = ['Trabajado']  # Default solo trabajado

        print('Valores usados para filtrar:')
        print('centro:', centro)
        print('user_id:', user_id)
        print('categoria:', categoria)
        print('weekly_hours:', weekly_hours)
        print('status_filters:', status_filters)
        print('--------------------------')

        # ========== OBTENER REGISTROS DE TIMERECORD (si "Trabajado" está seleccionado) ==========
        time_records = []
        if 'Trabajado' in status_filters:
            query = TimeRecord.query.join(User, TimeRecord.user_id == User.id).filter(
                TimeRecord.date >= start_date,
                TimeRecord.date <= end_date
            )

            # Aplicar filtros
            if centro:
                query = query.filter(User.centro == centro)
            if user_id:
                query = query.filter(TimeRecord.user_id == user_id)
            if categoria:
                query = query.filter(User.categoria == categoria)
            if weekly_hours:
                try:
                    wh = int(weekly_hours)
                    query = query.filter(User.weekly_hours.isnot(None))
                    query = query.filter(db.cast(User.weekly_hours, db.Integer) == wh)
                except ValueError:
                    flash("La jornada debe ser numérica.", "danger")
                    return redirect(url_for("export.export_excel"))

            time_records = query.order_by(TimeRecord.user_id, TimeRecord.date).all()

        # ========== OBTENER REGISTROS DE EMPLOYEESTATUS (Baja, Ausente, Vacaciones) ==========
        employee_statuses = []
        selected_statuses = expand_status_filters([s for s in status_filters if s != 'Trabajado'])
        if selected_statuses:
            status_query = EmployeeStatus.query.join(User, EmployeeStatus.user_id == User.id).filter(
                EmployeeStatus.status.in_(selected_statuses),
                EmployeeStatus.date >= start_date,
                EmployeeStatus.date <= end_date
            )

            # Aplicar los mismos filtros
            if centro:
                status_query = status_query.filter(User.centro == centro)
            if user_id:
                status_query = status_query.filter(EmployeeStatus.user_id == user_id)
            if categoria:
                status_query = status_query.filter(User.categoria == categoria)
            if weekly_hours:
                try:
                    wh = int(weekly_hours)
                    status_query = status_query.filter(User.weekly_hours.isnot(None))
                    status_query = status_query.filter(db.cast(User.weekly_hours, db.Integer) == wh)
                except ValueError:
                    pass  # Ya se validó arriba

            employee_statuses = status_query.order_by(EmployeeStatus.user_id, EmployeeStatus.date).all()

        # Verificar que hay al menos algún registro
        if not time_records and not employee_statuses:
            flash("No hay registros para el período y filtros seleccionados.", "warning")
            return redirect(url_for("export.export_excel"))

        # ========== GENERAR EXCEL CON 3 PESTAÑAS ==========

        wb = openpyxl.Workbook()

        # ========== PESTAÑA 1: REGISTROS DE FICHAJE ==========
        if time_records:
            ws1 = wb.active
            ws1.title = "Registros de Fichaje"

            header1 = ["Usuario", "Nombre completo", "Categoría", "Centro", "Fecha", "Entrada", "Salida", "Horas Trabajadas", "Notas", "Modificado Por", "Última Actualización"]
            for col_num, header_text in enumerate(header1, 1):
                cell = ws1.cell(row=1, column=col_num)
                cell.value = header_text
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
                cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")

            row_num = 2
            for record in time_records:
                user = User.query.get(record.user_id)
                modified_by = User.query.get(record.modified_by) if record.modified_by else None

                # Calcular horas
                hours_worked = ""
                if record.check_in and record.check_out:
                    time_diff = record.check_out - record.check_in
                    hours = time_diff.total_seconds() / 3600
                    hours_worked = f"{hours:.2f}"

                ws1.cell(row=row_num, column=1).value = user.username if user else f"ID: {record.user_id}"
                ws1.cell(row=row_num, column=2).value = user.full_name if user else "-"
                ws1.cell(row=row_num, column=3).value = user.categoria if user and user.categoria else "-"
                ws1.cell(row=row_num, column=4).value = user.centro if user and user.centro else "-"
                ws1.cell(row=row_num, column=5).value = record.date.strftime("%d/%m/%Y")
                ws1.cell(row=row_num, column=6).value = record.check_in.strftime("%H:%M:%S") if record.check_in else "-"
                ws1.cell(row=row_num, column=7).value = record.check_out.strftime("%H:%M:%S") if record.check_out else "-"
                ws1.cell(row=row_num, column=8).value = hours_worked
                ws1.cell(row=row_num, column=9).value = record.notes
                ws1.cell(row=row_num, column=10).value = modified_by.username if modified_by else "-"
                ws1.cell(row=row_num, column=11).value = record.updated_at.strftime("%d/%m/%Y %H:%M:%S")
                row_num += 1

            for col_num, _ in enumerate(header1, 1):
                col_letter = get_column_letter(col_num)
                ws1.column_dimensions[col_letter].width = 17
        else:
            # Si no hay registros de fichaje, eliminar la primera pestaña
            wb.remove(wb.active)

        # ========== PESTAÑA 2: BAJAS Y AUSENCIAS ==========
        if employee_statuses:
            ws2 = wb.create_sheet("Bajas y Ausencias")

            header2 = ["Usuario", "Nombre completo", "Categoría", "Centro", "Fecha", "Estado", "Notas"]
            for col_num, header_text in enumerate(header2, 1):
                cell = ws2.cell(row=1, column=col_num)
                cell.value = header_text
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
                cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")

            row_num = 2
            for status_record in employee_statuses:
                user = User.query.get(status_record.user_id)

                ws2.cell(row=row_num, column=1).value = user.username if user else f"ID: {status_record.user_id}"
                ws2.cell(row=row_num, column=2).value = user.full_name if user else "-"
                ws2.cell(row=row_num, column=3).value = user.categoria if user and user.categoria else "-"
                ws2.cell(row=row_num, column=4).value = user.centro if user and user.centro else "-"
                ws2.cell(row=row_num, column=5).value = status_record.date.strftime("%d/%m/%Y")
                ws2.cell(row=row_num, column=6).value = status_record.status
                ws2.cell(row=row_num, column=7).value = status_record.notes or "-"
                row_num += 1

            for col_num, _ in enumerate(header2, 1):
                col_letter = get_column_letter(col_num)
                ws2.column_dimensions[col_letter].width = 17

        # ========== PESTAÑA 3: RESUMEN CONSOLIDADO ==========
        ws3 = wb.create_sheet("Resumen Consolidado")

        header3 = ["Usuario", "Nombre completo", "Categoría", "Centro", "Fecha", "Estado", "Entrada", "Salida", "Horas", "Notas"]
        for col_num, header_text in enumerate(header3, 1):
            cell = ws3.cell(row=1, column=col_num)
            cell.value = header_text
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
            cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")

        # Combinar ambos tipos de registros en una lista unificada
        consolidated_records = []

        # Agregar TimeRecords
        for record in time_records:
            user = User.query.get(record.user_id)
            hours_worked = ""
            if record.check_in and record.check_out:
                time_diff = record.check_out - record.check_in
                hours = time_diff.total_seconds() / 3600
                hours_worked = f"{hours:.2f}"

            consolidated_records.append({
                'user_id': record.user_id,
                'username': user.username if user else f"ID: {record.user_id}",
                'full_name': user.full_name if user else "-",
                'categoria': user.categoria if user and user.categoria else "-",
                'centro': user.centro if user and user.centro else "-",
                'date': record.date,
                'estado': "Trabajado",
                'entrada': record.check_in.strftime("%H:%M:%S") if record.check_in else "-",
                'salida': record.check_out.strftime("%H:%M:%S") if record.check_out else "-",
                'horas': hours_worked,
                'notas': record.notes or "-"
            })

        # Agregar EmployeeStatus
        for status_record in employee_statuses:
            user = User.query.get(status_record.user_id)
            consolidated_records.append({
                'user_id': status_record.user_id,
                'username': user.username if user else f"ID: {status_record.user_id}",
                'full_name': user.full_name if user else "-",
                'categoria': user.categoria if user and user.categoria else "-",
                'centro': user.centro if user and user.centro else "-",
                'date': status_record.date,
                'estado': status_record.status,
                'entrada': "-",
                'salida': "-",
                'horas': "-",
                'notas': status_record.notes or "-"
            })

        # Ordenar por usuario y fecha
        consolidated_records.sort(key=lambda x: (x['user_id'], x['date']))

        # Escribir registros consolidados
        row_num = 2
        for rec in consolidated_records:
            ws3.cell(row=row_num, column=1).value = rec['username']
            ws3.cell(row=row_num, column=2).value = rec['full_name']
            ws3.cell(row=row_num, column=3).value = rec['categoria']
            ws3.cell(row=row_num, column=4).value = rec['centro']
            ws3.cell(row=row_num, column=5).value = rec['date'].strftime("%d/%m/%Y")
            ws3.cell(row=row_num, column=6).value = rec['estado']
            ws3.cell(row=row_num, column=7).value = rec['entrada']
            ws3.cell(row=row_num, column=8).value = rec['salida']
            ws3.cell(row=row_num, column=9).value = rec['horas']
            ws3.cell(row=row_num, column=10).value = rec['notas']
            row_num += 1

        for col_num, _ in enumerate(header3, 1):
            col_letter = get_column_letter(col_num)
            ws3.column_dimensions[col_letter].width = 17

        fd, temp_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd)
        wb.save(temp_path)

        # Generar nombre con formato dd_mm_yy_TimeT
        filename = f"{end_date.strftime('%d_%m_%y')}_TimeT.xlsx"
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    # GET
    from routes.admin import get_admin_centro, get_centros_dinamicos, get_categorias_disponibles
    centro_admin = get_admin_centro()
    q = User.query.filter_by(is_active=True)
    if centro_admin:
        q = q.filter(User.centro == centro_admin)
    users = q.order_by(User.username).all()

    # Calcular lista de horas únicas y ordenadas ascendentemente para el desplegable "horas4"
    horas_sorted = sorted({u.weekly_hours for u in users if u.weekly_hours is not None})

    # Obtener centros y categorías dinámicos
    centros = get_centros_dinamicos()
    categorias = get_categorias_disponibles()

    today = date.today().strftime('%Y-%m-%d')
    return render_template("export_excel.html", users=users, today=today, centro_admin=centro_admin, horas_sorted=horas_sorted, centros=centros, categorias=categorias)

# ========== EXCEL MENSUAL CON SUMAS SEMANALES ==========

@export_bp.route("/excel_monthly", methods=["GET", "POST"])
@admin_required
def export_excel_monthly():
    if request.method == "POST":
        # Obtener filtros de estado
        status_filters = request.form.getlist('status')
        if not status_filters:
            status_filters = ['Trabajado']

        # Reutilizar la misma lógica de filtros que la función principal
        botones = [k for k in request.form.keys() if k.startswith('excel_')]
        boton_pulsado = botones[-1] if botones else None

        centro = user_id = categoria = weekly_hours = None
        if boton_pulsado == "excel_centro_usuario":
            centro = request.form.get("centro1")
            user_id = request.form.get("usuario1")
        elif boton_pulsado == "excel_centro_categoria":
            centro = request.form.get("centro2")
            categoria = request.form.get("categoria2")
        elif boton_pulsado == "excel_centro_horas":
            centro = request.form.get("centro3")
            weekly_hours = request.form.get("horas3")
        elif boton_pulsado == "excel_solo_centro":
            centro = request.form.get("centro4")
        elif boton_pulsado == "excel_solo_usuario":
            user_id = request.form.get("usuario4")
        elif boton_pulsado == "excel_solo_categoria":
            categoria = request.form.get("categoria4")
        elif boton_pulsado == "excel_solo_horas":
            weekly_hours = request.form.get("horas4")
        else:
            centro = request.form.get("centro")
            user_id = request.form.get("user_id")
            categoria = request.form.get("categoria")
            weekly_hours = request.form.get("weekly_hours") or request.form.get("jornada")

        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        # Validación fechas
        try:
            if start_date:
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            else:
                start_date = date.today()
            if end_date:
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            else:
                end_date = date.today()
            if end_date < start_date:
                flash("La fecha de fin no puede ser anterior a la fecha de inicio.", "danger")
                return redirect(url_for("export.export_excel_monthly"))
        except ValueError:
            flash("Formato de fecha inválido. Use YYYY-MM-DD.", "danger")
            return redirect(url_for("export.export_excel_monthly"))

        # Consultar TimeRecord si "Trabajado" está seleccionado
        records = []
        if 'Trabajado' in status_filters:
            query = TimeRecord.query.join(User, TimeRecord.user_id == User.id).filter(
                TimeRecord.date >= start_date,
                TimeRecord.date <= end_date
            )

            if centro:
                query = query.filter(User.centro == centro)
            if user_id:
                query = query.filter(TimeRecord.user_id == user_id)
            if categoria:
                query = query.filter(User.categoria == categoria)
            if weekly_hours:
                try:
                    wh = int(weekly_hours)
                    query = query.filter(User.weekly_hours.isnot(None))
                    query = query.filter(db.cast(User.weekly_hours, db.Integer) == wh)
                except ValueError:
                    flash("La jornada debe ser numérica.", "danger")
                    return redirect(url_for("export.export_excel_monthly"))

            records = query.order_by(TimeRecord.user_id, TimeRecord.date).all()

        # Consultar EmployeeStatus si otros estados están seleccionados
        employee_statuses = []
        selected_statuses = expand_status_filters([s for s in status_filters if s != 'Trabajado'])
        if selected_statuses:
            status_query = EmployeeStatus.query.join(User, EmployeeStatus.user_id == User.id).filter(
                EmployeeStatus.status.in_(selected_statuses),
                EmployeeStatus.date >= start_date,
                EmployeeStatus.date <= end_date
            )

            if centro:
                status_query = status_query.filter(User.centro == centro)
            if user_id:
                status_query = status_query.filter(EmployeeStatus.user_id == user_id)
            if categoria:
                status_query = status_query.filter(User.categoria == categoria)
            if weekly_hours:
                try:
                    wh = int(weekly_hours)
                    status_query = status_query.filter(User.weekly_hours.isnot(None))
                    status_query = status_query.filter(db.cast(User.weekly_hours, db.Integer) == wh)
                except ValueError:
                    pass

            employee_statuses = status_query.order_by(EmployeeStatus.user_id, EmployeeStatus.date).all()

        if not records and not employee_statuses:
            flash("No hay registros para el período y filtros seleccionados.", "warning")
            return redirect(url_for("export.export_excel_monthly"))

        # Generar Excel con 3 pestañas
        wb = openpyxl.Workbook()

        # ===== PESTAÑA 1: REGISTROS DE FICHAJE (con sumas semanales) =====
        if records:
            ws1 = wb.active
            ws1.title = "Registros de Fichaje"

            # Usar la misma lógica de sumas semanales
            def get_week_start(date_obj):
                return date_obj - timedelta(days=date_obj.weekday())

            weekly_data = defaultdict(lambda: defaultdict(list))
            weekly_totals = defaultdict(lambda: defaultdict(float))

            for record in records:
                week_start = get_week_start(record.date)
                weekly_data[record.user_id][week_start].append(record)

                if record.check_in and record.check_out:
                    time_diff = record.check_out - record.check_in
                    hours = time_diff.total_seconds() / 3600
                    weekly_totals[record.user_id][week_start] += hours

            header1 = ["Usuario", "Nombre completo", "Categoría", "Centro", "Horas Semanales", "Fecha", "Entrada", "Salida", "Horas Trabajadas", "Diferencia Horas", "Notas", "Modificado Por", "Última Actualización"]
            for col_num, header_text in enumerate(header1, 1):
                cell = ws1.cell(row=1, column=col_num)
                cell.value = header_text
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
                cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")

            row_num = 2

            for user_id in sorted(weekly_data.keys()):
                user = User.query.get(user_id)

                for week_start in sorted(weekly_data[user_id].keys()):
                    week_end = week_start + timedelta(days=6)
                    total_hours = weekly_totals[user_id][week_start]

                    # Fila de total semanal
                    cell = ws1.cell(row=row_num, column=1)
                    cell.value = f"TOTAL SEMANA ({week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m')})"
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal='center')
                    cell.fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")

                    cell = ws1.cell(row=row_num, column=2)
                    cell.value = user.full_name if user else "-"
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal='center')
                    cell.fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")

                    # Columnas 3 y 4: "-"
                    for col in range(3, 5):
                        cell = ws1.cell(row=row_num, column=col)
                        cell.value = "-"
                        cell.alignment = Alignment(horizontal='center')
                        cell.fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")

                    # Columna 5: Mostrar las horas semanales contractuales
                    cell = ws1.cell(row=row_num, column=5)
                    cell.value = user.weekly_hours if user and user.weekly_hours else "-"
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal='center')
                    cell.fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")

                    # Columnas 6, 7, 8: "-"
                    for col in range(6, 9):
                        cell = ws1.cell(row=row_num, column=col)
                        cell.value = "-"
                        cell.alignment = Alignment(horizontal='center')
                        cell.fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")

                    cell = ws1.cell(row=row_num, column=9)
                    cell.value = f"{total_hours:.2f}"
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal='center')
                    cell.fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")

                    # Calcular diferencia
                    weekly_hours_contract = user.weekly_hours if user and user.weekly_hours else 0
                    difference = weekly_hours_contract - total_hours
                    cell = ws1.cell(row=row_num, column=10)
                    cell.value = f"{difference:.2f}"
                    cell.font = Font(bold=True)
                    cell.alignment = Alignment(horizontal='center')
                    cell.fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")

                    for col in range(11, 14):
                        cell = ws1.cell(row=row_num, column=col)
                        cell.value = "-"
                        cell.alignment = Alignment(horizontal='center')
                        cell.fill = PatternFill(start_color="E6F3FF", end_color="E6F3FF", fill_type="solid")

                    row_num += 1

                    # Registros individuales
                    for record in weekly_data[user_id][week_start]:
                        modified_by = User.query.get(record.modified_by) if record.modified_by else None
                        hours_worked = ""
                        if record.check_in and record.check_out:
                            time_diff = record.check_out - record.check_in
                            hours = time_diff.total_seconds() / 3600
                            hours_worked = f"{hours:.2f}"

                        ws1.cell(row=row_num, column=1).value = user.username if user else f"ID: {record.user_id}"
                        ws1.cell(row=row_num, column=1).alignment = Alignment(horizontal='center')

                        ws1.cell(row=row_num, column=2).value = user.full_name if user else "-"
                        ws1.cell(row=row_num, column=2).alignment = Alignment(horizontal='center')

                        ws1.cell(row=row_num, column=3).value = user.categoria if user and user.categoria else "-"
                        ws1.cell(row=row_num, column=3).alignment = Alignment(horizontal='center')

                        ws1.cell(row=row_num, column=4).value = user.centro if user and user.centro else "-"
                        ws1.cell(row=row_num, column=4).alignment = Alignment(horizontal='center')

                        ws1.cell(row=row_num, column=5).value = user.weekly_hours if user and user.weekly_hours else "-"
                        ws1.cell(row=row_num, column=5).alignment = Alignment(horizontal='center')

                        ws1.cell(row=row_num, column=6).value = record.date.strftime("%d/%m/%Y")
                        ws1.cell(row=row_num, column=6).alignment = Alignment(horizontal='center')

                        ws1.cell(row=row_num, column=7).value = record.check_in.strftime("%H:%M:%S") if record.check_in else "-"
                        ws1.cell(row=row_num, column=7).alignment = Alignment(horizontal='center')

                        ws1.cell(row=row_num, column=8).value = record.check_out.strftime("%H:%M:%S") if record.check_out else "-"
                        ws1.cell(row=row_num, column=8).alignment = Alignment(horizontal='center')

                        ws1.cell(row=row_num, column=9).value = hours_worked
                        ws1.cell(row=row_num, column=9).alignment = Alignment(horizontal='center')

                        ws1.cell(row=row_num, column=10).value = "-"
                        ws1.cell(row=row_num, column=10).alignment = Alignment(horizontal='center')

                        ws1.cell(row=row_num, column=11).value = record.notes
                        ws1.cell(row=row_num, column=11).alignment = Alignment(horizontal='center')

                        ws1.cell(row=row_num, column=12).value = modified_by.username if modified_by else "-"
                        ws1.cell(row=row_num, column=12).alignment = Alignment(horizontal='center')

                        ws1.cell(row=row_num, column=13).value = record.updated_at.strftime("%d/%m/%Y %H:%M:%S")
                        ws1.cell(row=row_num, column=13).alignment = Alignment(horizontal='center')
                        row_num += 1

                    row_num += 1

            for col_num, _ in enumerate(header1, 1):
                col_letter = get_column_letter(col_num)
                ws1.column_dimensions[col_letter].width = 17
        else:
            wb.remove(wb.active)

        # ===== PESTAÑA 2: BAJAS Y AUSENCIAS =====
        if employee_statuses:
            ws2 = wb.create_sheet("Bajas y Ausencias")
            header2 = ["Usuario", "Nombre completo", "Categoría", "Centro", "Fecha", "Estado", "Notas"]
            for col_num, header_text in enumerate(header2, 1):
                cell = ws2.cell(row=1, column=col_num)
                cell.value = header_text
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal='center')
                cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")

            row_num = 2
            for status_record in employee_statuses:
                user = User.query.get(status_record.user_id)
                ws2.cell(row=row_num, column=1).value = user.username if user else f"ID: {status_record.user_id}"
                ws2.cell(row=row_num, column=2).value = user.full_name if user else "-"
                ws2.cell(row=row_num, column=3).value = user.categoria if user and user.categoria else "-"
                ws2.cell(row=row_num, column=4).value = user.centro if user and user.centro else "-"
                ws2.cell(row=row_num, column=5).value = status_record.date.strftime("%d/%m/%Y")
                ws2.cell(row=row_num, column=6).value = status_record.status
                ws2.cell(row=row_num, column=7).value = status_record.notes or "-"
                row_num += 1

            for col_num, _ in enumerate(header2, 1):
                col_letter = get_column_letter(col_num)
                ws2.column_dimensions[col_letter].width = 17

        # ===== PESTAÑA 3: RESUMEN CONSOLIDADO =====
        ws3 = wb.create_sheet("Resumen Consolidado")
        header3 = ["Usuario", "Nombre completo", "Categoría", "Centro", "Fecha", "Estado", "Entrada", "Salida", "Horas", "Notas"]
        for col_num, header_text in enumerate(header3, 1):
            cell = ws3.cell(row=1, column=col_num)
            cell.value = header_text
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal='center')
            cell.fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")

        consolidated_records = []
        for record in records:
            user = User.query.get(record.user_id)
            hours_worked = ""
            if record.check_in and record.check_out:
                time_diff = record.check_out - record.check_in
                hours = time_diff.total_seconds() / 3600
                hours_worked = f"{hours:.2f}"
            consolidated_records.append({
                'user_id': record.user_id,
                'username': user.username if user else f"ID: {record.user_id}",
                'full_name': user.full_name if user else "-",
                'categoria': user.categoria if user and user.categoria else "-",
                'centro': user.centro if user and user.centro else "-",
                'date': record.date,
                'estado': "Trabajado",
                'entrada': record.check_in.strftime("%H:%M:%S") if record.check_in else "-",
                'salida': record.check_out.strftime("%H:%M:%S") if record.check_out else "-",
                'horas': hours_worked,
                'notas': record.notes or "-"
            })

        for status_record in employee_statuses:
            user = User.query.get(status_record.user_id)
            consolidated_records.append({
                'user_id': status_record.user_id,
                'username': user.username if user else f"ID: {status_record.user_id}",
                'full_name': user.full_name if user else "-",
                'categoria': user.categoria if user and user.categoria else "-",
                'centro': user.centro if user and user.centro else "-",
                'date': status_record.date,
                'estado': status_record.status,
                'entrada': "-",
                'salida': "-",
                'horas': "-",
                'notas': status_record.notes or "-"
            })

        # Ordenar por usuario y fecha
        consolidated_records.sort(key=lambda x: (x['user_id'], x['date']))

        row_num = 2
        for rec in consolidated_records:
            ws3.cell(row=row_num, column=1).value = rec['username']
            ws3.cell(row=row_num, column=2).value = rec['full_name']
            ws3.cell(row=row_num, column=3).value = rec['categoria']
            ws3.cell(row=row_num, column=4).value = rec['centro']
            ws3.cell(row=row_num, column=5).value = rec['date'].strftime("%d/%m/%Y")
            ws3.cell(row=row_num, column=6).value = rec['estado']
            ws3.cell(row=row_num, column=7).value = rec['entrada']
            ws3.cell(row=row_num, column=8).value = rec['salida']
            ws3.cell(row=row_num, column=9).value = rec['horas']
            ws3.cell(row=row_num, column=10).value = rec['notas']
            row_num += 1

        for col_num, _ in enumerate(header3, 1):
            col_letter = get_column_letter(col_num)
            ws3.column_dimensions[col_letter].width = 17

        fd, temp_path = tempfile.mkstemp(suffix='.xlsx')
        os.close(fd)
        wb.save(temp_path)

        # Generar nombre con formato dd_mm_yy_TimeT
        from datetime import date as dt_date
        today = dt_date.today()
        filename = f"{today.strftime('%d_%m_%y')}_TimeT.xlsx"

        return send_file(
            temp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    # GET - usar el mismo template
    from routes.admin import get_admin_centro, get_centros_dinamicos, get_categorias_disponibles
    centro_admin = get_admin_centro()
    q = User.query.filter_by(is_active=True)
    if centro_admin:
        q = q.filter(User.centro == centro_admin)
    users = q.order_by(User.username).all()
    horas_sorted = sorted({u.weekly_hours for u in users if u.weekly_hours is not None})

    # Obtener centros y categorías dinámicos
    centros = get_centros_dinamicos()
    categorias = get_categorias_disponibles()

    today = date.today().strftime('%Y-%m-%d')
    return render_template("export_excel.html", users=users, today=today, centro_admin=centro_admin, horas_sorted=horas_sorted, centros=centros, categorias=categorias)

# ========== EXCEL DIARIO ==========

@export_bp.route("/excel_daily")
@admin_required
def export_excel_daily():
    fecha_str = request.args.get('fecha', date.today().strftime('%Y-%m-%d'))
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Formato de fecha inválido.", "danger")
        return redirect(url_for("export.export_excel"))

    records = TimeRecord.query.filter(TimeRecord.date == fecha).order_by(TimeRecord.user_id).all()
    if not records:
        flash("No hay registros para ese día.", "warning")
        return redirect(url_for("export.export_excel"))

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Registros diarios"
    header = ["Usuario", "Nombre completo", "Categoría", "Centro", "Fecha", "Entrada", "Salida", "Horas Trabajadas", "Notas"]
    for col_num, header_text in enumerate(header, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.value = header_text
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal='center')

    row_num = 2
    for record in records:
        user = User.query.get(record.user_id)
        hours_worked = ""
        if record.check_in and record.check_out:
            time_diff = record.check_out - record.check_in
            hours = time_diff.total_seconds() / 3600
            hours_worked = f"{hours:.2f}"

        ws.cell(row=row_num, column=1).value = user.username if user else f"ID: {record.user_id}"
        ws.cell(row=row_num, column=2).value = user.full_name if user else "-"
        ws.cell(row=row_num, column=3).value = user.categoria if user and user.categoria else "-"
        ws.cell(row=row_num, column=4).value = user.centro if user and user.centro else "-"
        ws.cell(row=row_num, column=5).value = record.date.strftime("%d/%m/%Y")
        ws.cell(row=row_num, column=6).value = record.check_in.strftime("%H:%M:%S") if record.check_in else "-"
        ws.cell(row=row_num, column=7).value = record.check_out.strftime("%H:%M:%S") if record.check_out else "-"
        ws.cell(row=row_num, column=8).value = hours_worked
        ws.cell(row=row_num, column=9).value = record.notes
        row_num += 1

    for col_num, _ in enumerate(header, 1):
        col_letter = get_column_letter(col_num)
        ws.column_dimensions[col_letter].width = 17

    fd, temp_path = tempfile.mkstemp(suffix='.xlsx')
    os.close(fd)
    wb.save(temp_path)

    filename = f"{fecha.strftime('%d_%m_%y')}_TimeT.xlsx"
    return send_file(
        temp_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# ========== PDF DIARIO ==========

from fpdf import FPDF

@export_bp.route("/pdf_daily")
@admin_required
def export_pdf_daily():
    fecha_str = request.args.get('fecha', date.today().strftime('%Y-%m-%d'))
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Formato de fecha inválido.", "danger")
        return redirect(url_for("export.export_excel"))

    records = TimeRecord.query.filter(TimeRecord.date == fecha).order_by(TimeRecord.user_id).all()
    if not records:
        flash("No hay registros para ese día.", "warning")
        return redirect(url_for("export.export_excel"))

    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Registros de fichaje del {fecha.strftime('%d/%m/%Y')}", ln=1, align="C")

    pdf.set_font("Arial", "B", 10)
    header = ["Usuario", "Nombre completo", "Categoría", "Centro", "Entrada", "Salida", "Horas", "Notas"]
    col_widths = [30, 40, 25, 30, 22, 22, 30, 55]

    for i, col_name in enumerate(header):
        pdf.cell(col_widths[i], 8, col_name, border=1, align="C")
    pdf.ln()

    pdf.set_font("Arial", "", 9)
    for record in records:
        user = User.query.get(record.user_id)
        hours_worked = ""
        if record.check_in and record.check_out:
            time_diff = record.check_out - record.check_in
            hours = time_diff.total_seconds() / 3600
            hours_worked = f"{hours:.2f}"

        row = [
            user.username if user else f"ID: {record.user_id}",
            user.full_name if user else "-",
            user.categoria if user and user.categoria else "-",
            user.centro if user and user.centro else "-",
            record.check_in.strftime("%H:%M:%S") if record.check_in else "-",
            record.check_out.strftime("%H:%M:%S") if record.check_out else "-",
            hours_worked,
            record.notes or ""
        ]
        for i, item in enumerate(row):
            pdf.cell(col_widths[i], 8, str(item), border=1, align="C")
        pdf.ln()

    fd, temp_path = tempfile.mkstemp(suffix='.pdf')
    os.close(fd)
    pdf.output(temp_path)

    filename = f"{fecha.strftime('%d_%m_%y')}_TimeT.pdf"
    return send_file(
        temp_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )
