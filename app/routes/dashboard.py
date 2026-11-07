"""Dashboard routes."""
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from app.permissions.decorators import can_view_all_complaints
from app.services.report import ReportService


dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@dashboard_bp.route('/index')
@login_required
def index():
    """Main dashboard."""
    # Get dashboard statistics
    stats = ReportService.get_dashboard_stats(current_user)
    
    # Get chart data
    status_data = ReportService.get_complaints_by_status(current_user)
    priority_data = ReportService.get_complaints_by_priority(current_user)
    department_data = ReportService.get_complaints_by_department(current_user)
    software_data = ReportService.get_complaints_by_software(current_user)
    assignee_data = ReportService.get_complaints_by_assignee(current_user)
    resolver_data = ReportService.get_complaints_by_resolver(current_user)
    
    # Get trends
    daily_trends = ReportService.get_daily_trends(current_user, 30)
    weekly_trends = ReportService.get_weekly_trends(current_user, 12)
    monthly_trends = ReportService.get_monthly_trends(current_user, 12)
    sla_trends = ReportService.get_sla_compliance_trends(current_user, 30)
    
    # Get recent complaints
    from app.permissions.policy import PermissionPolicy
    from app.models import Complaint
    
    recent_complaints = PermissionPolicy.get_accessible_complaints_query(current_user).order_by(
        Complaint.created_at.desc()
    ).limit(10).all()
    
    # Get overdue complaints
    from app.services.sla import SLAService
    overdue_response = SLAService.check_sla_breaches()
    
    return render_template('dashboard/index.html',
                           stats=stats,
                           status_data=status_data,
                           priority_data=priority_data,
                           department_data=department_data,
                           software_data=software_data,
                           assignee_data=assignee_data,
                           resolver_data=resolver_data,
                           daily_trends=daily_trends,
                           weekly_trends=weekly_trends,
                           monthly_trends=monthly_trends,
                           sla_trends=sla_trends,
                           recent_complaints=recent_complaints,
                           overdue_count=len(overdue_response))


@dashboard_bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for dashboard statistics."""
    stats = ReportService.get_dashboard_stats(current_user)
    return jsonify(stats)


@dashboard_bp.route('/api/charts/status')
@login_required
def api_charts_status():
    """API endpoint for status chart data."""
    data = ReportService.get_complaints_by_status(current_user)
    return jsonify(data)


@dashboard_bp.route('/api/charts/priority')
@login_required
def api_charts_priority():
    """API endpoint for priority chart data."""
    data = ReportService.get_complaints_by_priority(current_user)
    return jsonify(data)


@dashboard_bp.route('/api/charts/department')
@login_required
def api_charts_department():
    """API endpoint for department chart data."""
    data = ReportService.get_complaints_by_department(current_user)
    return jsonify(data)


@dashboard_bp.route('/api/charts/software')
@login_required
def api_charts_software():
    """API endpoint for software chart data."""
    data = ReportService.get_complaints_by_software(current_user)
    return jsonify(data)


@dashboard_bp.route('/api/charts/trends/daily')
@login_required
def api_charts_trends_daily():
    """API endpoint for daily trends."""
    days = request.args.get('days', 30, type=int)
    data = ReportService.get_daily_trends(current_user, days)
    return jsonify(data)


@dashboard_bp.route('/api/charts/trends/weekly')
@login_required
def api_charts_trends_weekly():
    """API endpoint for weekly trends."""
    weeks = request.args.get('weeks', 12, type=int)
    data = ReportService.get_weekly_trends(current_user, weeks)
    return jsonify(data)


@dashboard_bp.route('/api/charts/trends/monthly')
@login_required
def api_charts_trends_monthly():
    """API endpoint for monthly trends."""
    months = request.args.get('months', 12, type=int)
    data = ReportService.get_monthly_trends(current_user, months)
    return jsonify(data)


@dashboard_bp.route('/api/charts/sla')
@login_required
def api_charts_sla():
    """API endpoint for SLA compliance trends."""
    days = request.args.get('days', 30, type=int)
    data = ReportService.get_sla_compliance_trends(current_user, days)
    return jsonify(data)


@dashboard_bp.route('/api/recent-complaints')
@login_required
def api_recent_complaints():
    """API endpoint for recent complaints."""
    from app.permissions.policy import PermissionPolicy
    from app.models import Complaint
    
    limit = request.args.get('limit', 10, type=int)
    complaints = PermissionPolicy.get_accessible_complaints_query(current_user).order_by(
        Complaint.created_at.desc()
    ).limit(limit).all()
    
    data = []
    for c in complaints:
        data.append({
            'id': c.id,
            'complaint_number': c.complaint_number,
            'title': c.title,
            'status': c.status.name if c.status else '',
            'status_color': c.status.color if c.status else '#6B7280',
            'priority': c.priority.name if c.priority else '',
            'priority_color': c.priority.color if c.priority else '#6B7280',
            'department': c.department.name if c.department else '',
            'created_at': c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else '',
            'sla_status': c.sla_resolution_status,
        })
    
    return jsonify(data)