"""Report generation and export routes."""
from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Department, SoftwareCatalog, Category, Priority, Status, User, Complaint
from app.services.report import ReportService
from app.permissions.decorators import can_export_reports
from app.services.audit import AuditService
from datetime import datetime
from io import BytesIO

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/')
@login_required
@can_export_reports
def index():
    """Reports dashboard."""
    return render_template('reports/index.html')


@reports_bp.route('/dashboard')
@login_required
@can_export_reports
def dashboard():
    """Dashboard with charts and statistics."""
    stats = ReportService.get_dashboard_stats(current_user)
    by_status = ReportService.get_complaints_by_status(current_user)
    by_priority = ReportService.get_complaints_by_priority(current_user)
    by_department = ReportService.get_complaints_by_department(current_user)
    by_software = ReportService.get_complaints_by_software(current_user)
    by_assignee = ReportService.get_complaints_by_assignee(current_user)
    by_resolver = ReportService.get_complaints_by_resolver(current_user)
    daily_trends = ReportService.get_daily_trends(current_user, 30)
    weekly_trends = ReportService.get_weekly_trends(current_user, 12)
    monthly_trends = ReportService.get_monthly_trends(current_user, 12)
    sla_trends = ReportService.get_sla_compliance_trends(current_user, 30)
    
    return render_template('reports/dashboard.html',
                           stats=stats,
                           by_status=by_status,
                           by_priority=by_priority,
                           by_department=by_department,
                           by_software=by_software,
                           by_assignee=by_assignee,
                           by_resolver=by_resolver,
                           daily_trends=daily_trends,
                           weekly_trends=weekly_trends,
                           monthly_trends=monthly_trends,
                           sla_trends=sla_trends)


@reports_bp.route('/generate', methods=['GET', 'POST'])
@login_required
@can_export_reports
def generate_report():
    """Generate a custom report."""
    if request.method == 'POST':
        report_type = request.form.get('report_type')
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')
        department_id = request.form.get('department_id')
        software_id = request.form.get('software_id')
        priority_id = request.form.get('priority_id')
        status_id = request.form.get('status_id')
        assigned_to_user_id = request.form.get('assigned_to_user_id')
        reported_by_user_id = request.form.get('reported_by_user_id')
        category_id = request.form.get('category_id')
        export_format = request.form.get('export_format', 'html')
        
        filters = {}
        if date_from:
            filters['date_from'] = datetime.strptime(date_from, '%Y-%m-%d')
        if date_to:
            filters['date_to'] = datetime.strptime(date_to, '%Y-%m-%d')
        if department_id:
            filters['department_id'] = int(department_id)
        if software_id:
            filters['software_id'] = int(software_id)
        if priority_id:
            filters['priority_id'] = int(priority_id)
        if status_id:
            filters['status_id'] = int(status_id)
        if assigned_to_user_id:
            filters['assigned_to_user_id'] = int(assigned_to_user_id)
        if reported_by_user_id:
            filters['reported_by_user_id'] = int(reported_by_user_id)
        if category_id:
            filters['category_id'] = int(category_id)
        
        data = ReportService.generate_report_data(current_user, report_type, filters)
        
        if export_format == 'csv':
            if not current_user.has_permission('reports.export'):
                flash('You do not have permission to export reports.', 'danger')
                return redirect(url_for('reports.generate_report'))
            
            csv_data = ReportService.export_to_csv(data)
            if csv_data is None:
                flash('No data to export.', 'warning')
                return redirect(url_for('reports.generate_report'))
            
            filename = f'report_{report_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            AuditService.log_action(
                user_id=current_user.id,
                action='export_report',
                entity_type='report',
                entity_id=0,
                entity_repr=filename,
                new_values={'report_type': report_type, 'format': 'csv', 'filters': filters, 'row_count': len(data)},
                category='audit',
            )
            
            return send_file(
                BytesIO(csv_data.encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=filename
            )
        
        elif export_format == 'pdf':
            if not current_user.has_permission('reports.export'):
                flash('You do not have permission to export reports.', 'danger')
                return redirect(url_for('reports.generate_report'))
            
            pdf_data = ReportService.export_to_pdf(data, f'{report_type.title()} Report', filters)
            if pdf_data is None:
                flash('No data to export.', 'warning')
                return redirect(url_for('reports.generate_report'))
            
            filename = f'report_{report_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
            
            AuditService.log_action(
                user_id=current_user.id,
                action='export_report',
                entity_type='report',
                entity_id=0,
                entity_repr=filename,
                new_values={'report_type': report_type, 'format': 'pdf', 'filters': filters, 'row_count': len(data)},
                category='audit',
            )
            
            return send_file(
                BytesIO(pdf_data),
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
        
        return render_template('reports/results.html',
                               data=data,
                               filters=filters,
                               report_type=report_type)
    
    # GET request - show filter form
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    software_list = SoftwareCatalog.query.filter_by(is_active=True).order_by(SoftwareCatalog.name).all()
    categories = Category.query.filter_by(is_active=True).order_by(Category.name).all()
    priorities = Priority.query.filter_by(is_active=True).order_by(Priority.level).all()
    statuses = Status.query.filter_by(is_active=True).order_by(Status.sort_order).all()
    assignees = User.query.filter_by(is_active=True).order_by(User.first_name, User.last_name).all()
    reporters = User.query.filter_by(is_active=True).order_by(User.first_name, User.last_name).all()
    
    return render_template('reports/generate.html',
                           departments=departments,
                           software_list=software_list,
                           categories=categories,
                           priorities=priorities,
                           statuses=statuses,
                           assignees=assignees,
                           reporters=reporters)


@reports_bp.route('/preset/<report_type>')
@login_required
@can_export_reports
def preset_report(report_type):
    """Generate a preset report."""
    filters = {}
    
    if report_type == 'daily':
        from datetime import timedelta
        filters['date_from'] = datetime.utcnow() - timedelta(days=1)
    elif report_type == 'weekly':
        from datetime import timedelta
        filters['date_from'] = datetime.utcnow() - timedelta(days=7)
    elif report_type == 'monthly':
        from datetime import timedelta
        filters['date_from'] = datetime.utcnow() - timedelta(days=30)
    elif report_type == 'overdue':
        from datetime import timedelta
        filters['date_from'] = datetime.utcnow() - timedelta(days=365)
    elif report_type == 'sla_compliance':
        from datetime import timedelta
        filters['date_from'] = datetime.utcnow() - timedelta(days=30)
    elif report_type == 'reopened':
        from datetime import timedelta
        filters['date_from'] = datetime.utcnow() - timedelta(days=30)
    
    data = ReportService.generate_report_data(current_user, report_type, filters)
    
    return render_template('reports/results.html',
                           data=data,
                           filters=filters,
                           report_type=report_type)


@reports_bp.route('/overdue')
@login_required
@can_export_reports
def overdue_report():
    """Overdue complaints report."""
    overdue = ReportService.get_overdue_complaints(current_user)
    return render_template('reports/overdue.html', overdue=overdue, now=datetime.utcnow())


@reports_bp.route('/reopened')
@login_required
@can_export_reports
def reopened_report():
    """Reopened complaints report."""
    days = request.args.get('days', 30, type=int)
    reopened = ReportService.get_reopened_complaints(current_user, days)
    return render_template('reports/reopened.html', reopened=reopened, days=days)


@reports_bp.route('/sla-compliance')
@login_required
@can_export_reports
def sla_compliance_report():
    """SLA compliance report."""
    days = request.args.get('days', 30, type=int)
    trends = ReportService.get_sla_compliance_trends(current_user, days)
    return render_template('reports/sla_compliance.html', trends=trends, days=days)


@reports_bp.route('/api/dashboard-stats')
@login_required
@can_export_reports
def api_dashboard_stats():
    """API endpoint for dashboard stats."""
    stats = ReportService.get_dashboard_stats(current_user)
    return jsonify(stats)


@reports_bp.route('/api/chart-data/<chart_type>')
@login_required
@can_export_reports
def api_chart_data(chart_type):
    """API endpoint for chart data."""
    if chart_type == 'status':
        data = ReportService.get_complaints_by_status(current_user)
    elif chart_type == 'priority':
        data = ReportService.get_complaints_by_priority(current_user)
    elif chart_type == 'department':
        data = ReportService.get_complaints_by_department(current_user)
    elif chart_type == 'software':
        data = ReportService.get_complaints_by_software(current_user)
    elif chart_type == 'assignee':
        data = ReportService.get_complaints_by_assignee(current_user)
    elif chart_type == 'resolver':
        data = ReportService.get_complaints_by_resolver(current_user)
    elif chart_type == 'daily':
        days = request.args.get('days', 30, type=int)
        data = ReportService.get_daily_trends(current_user, days)
    elif chart_type == 'weekly':
        weeks = request.args.get('weeks', 12, type=int)
        data = ReportService.get_weekly_trends(current_user, weeks)
    elif chart_type == 'monthly':
        months = request.args.get('months', 12, type=int)
        data = ReportService.get_monthly_trends(current_user, months)
    elif chart_type == 'sla':
        days = request.args.get('days', 30, type=int)
        data = ReportService.get_sla_compliance_trends(current_user, days)
    else:
        return jsonify({'error': 'Invalid chart type'}), 400
    
    return jsonify(data)


# Import SoftwareCatalog at the end to avoid circular imports
from app.models import SoftwareCatalog

# ============================================================
# Export helpers and routes
# ============================================================

def _parse_filters(args):
    """Convert request args into ReportService filter values."""
    filters = {}

    for key in ('date_from', 'date_to'):
        raw = args.get(key)
        if not raw:
            continue
        for fmt in ('%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M'):
            try:
                filters[key] = datetime.strptime(raw, fmt)
                break
            except ValueError:
                continue
        else:
            try:
                filters[key] = datetime.fromisoformat(raw)
            except ValueError:
                pass

    for key in ('department_id', 'software_id', 'priority_id', 'status_id',
                'assigned_to_user_id', 'reported_by_user_id', 'category_id'):
        raw = args.get(key)
        if raw and str(raw).isdigit():
            filters[key] = int(raw)

    return filters


@reports_bp.route('/export')
@login_required
@can_export_reports
def export():
    """Entry point for exports; renders the report builder."""
    return redirect(url_for('reports.generate_report'))


@reports_bp.route('/export/csv')
@login_required
@can_export_reports
def export_csv():
    """Export the complaint report as CSV."""
    filters = _parse_filters(request.args)
    data = ReportService.generate_report_data(current_user, 'complaints', filters)

    csv_data = ReportService.export_to_csv(data)
    if csv_data is None:
        flash('No data to export.', 'warning')
        return redirect(url_for('reports.generate_report'))

    filename = f'complaints_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    AuditService.log_action(
        user_id=current_user.id,
        action='export_report',
        entity_type='report',
        entity_id=0,
        entity_repr=filename,
        new_values={'report_type': 'complaints', 'format': 'csv', 'row_count': len(data)},
        category='audit',
    )
    return send_file(
        BytesIO(csv_data.encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename,
    )


@reports_bp.route('/export/pdf')
@login_required
@can_export_reports
def export_pdf():
    """Export the complaint report as PDF."""
    filters = _parse_filters(request.args)
    data = ReportService.generate_report_data(current_user, 'complaints', filters)

    pdf_data = ReportService.export_to_pdf(data, 'Complaints Report', filters)
    if pdf_data is None:
        flash('No data to export.', 'warning')
        return redirect(url_for('reports.generate_report'))

    filename = f'complaints_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    AuditService.log_action(
        user_id=current_user.id,
        action='export_report',
        entity_type='report',
        entity_id=0,
        entity_repr=filename,
        new_values={'report_type': 'complaints', 'format': 'pdf', 'row_count': len(data)},
        category='audit',
    )
    return send_file(
        BytesIO(pdf_data),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename,
    )
