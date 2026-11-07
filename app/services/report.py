"""Report generation service."""
from datetime import datetime, timedelta, date
from io import BytesIO, StringIO
import csv
from app.extensions import db
from app.models import (
    Complaint, User, Department, SoftwareCatalog, Category, Priority, Status,
    ComplaintAssignment, ComplaintStatusHistory, SLAHistory
)
from app.permissions.policy import PermissionPolicy


class ReportService:
    """Service for generating reports."""
    
    @staticmethod
    def get_dashboard_stats(user):
        """Get dashboard statistics for a user."""
        from app.permissions.policy import PermissionPolicy
        
        query = PermissionPolicy.get_accessible_complaints_query(user)
        
        stats = {
            'total': query.count(),
            'new': query.filter(Complaint.status.has(Status.code == 'new')).count(),
            'assigned': query.filter(Complaint.status.has(Status.code == 'assigned')).count(),
            'in_progress': query.filter(Complaint.status.has(Status.code == 'in_progress')).count(),
            'pending_info': query.filter(Complaint.status.has(Status.code == 'pending_info')).count(),
            'on_hold': query.filter(Complaint.status.has(Status.code == 'on_hold')).count(),
            'resolved': query.filter(Complaint.status.has(Status.code == 'resolved')).count(),
            'closed': query.filter(Complaint.status.has(Status.code == 'closed')).count(),
            'reopened': query.filter(Complaint.status.has(Status.code == 'reopened')).count(),
            'rejected': query.filter(Complaint.status.has(Status.code == 'rejected')).count(),
        }
        
        # Overdue counts
        now = datetime.utcnow()
        stats['overdue_response'] = query.filter(
            Complaint.sla_response_deadline != None,
            Complaint.sla_response_deadline < now,
            Complaint.first_response_at == None,
            Complaint.status.has(Status.is_terminal == False),
        ).count()
        
        stats['overdue_resolution'] = query.filter(
            Complaint.sla_resolution_deadline != None,
            Complaint.sla_resolution_deadline < now,
            Complaint.resolved_at == None,
            Complaint.status.has(Status.is_terminal == False),
        ).count()
        
        stats['overdue_total'] = stats['overdue_response'] + stats['overdue_resolution']
        
        # SLA compliance
        total_with_sla = query.filter(
            Complaint.sla_resolution_deadline != None
        ).count()
        
        if total_with_sla > 0:
            met_sla = query.filter(
                Complaint.sla_resolution_deadline != None,
                db.or_(
                    Complaint.resolved_at != None,
                    Complaint.sla_resolution_deadline >= now
                )
            ).count()
            stats['sla_compliance'] = round((met_sla / total_with_sla) * 100, 1)
        else:
            stats['sla_compliance'] = 100.0
        
        return stats
    
    @staticmethod
    def get_complaints_by_status(user):
        """Get complaint counts grouped by status."""
        from app.permissions.policy import PermissionPolicy
        
        query = PermissionPolicy.get_accessible_complaints_query(user)
        
        results = db.session.query(
            Status.name,
            Status.code,
            Status.color,
            db.func.count(Complaint.id)
        ).join(Complaint, Complaint.status_id == Status.id).filter(
            Complaint.id.in_(query.with_entities(Complaint.id).subquery())
        ).group_by(Status.id, Status.name, Status.code, Status.color).all()
        
        return [
            {'status': r[0], 'code': r[1], 'color': r[2], 'count': r[3]}
            for r in results
        ]
    
    @staticmethod
    def get_complaints_by_priority(user):
        """Get complaint counts grouped by priority."""
        from app.permissions.policy import PermissionPolicy
        
        query = PermissionPolicy.get_accessible_complaints_query(user)
        
        results = db.session.query(
            Priority.name,
            Priority.code,
            Priority.color,
            Priority.level,
            db.func.count(Complaint.id)
        ).join(Complaint, Complaint.priority_id == Priority.id).filter(
            Complaint.id.in_(query.with_entities(Complaint.id).subquery())
        ).group_by(Priority.id, Priority.name, Priority.code, Priority.color, Priority.level).order_by(Priority.level).all()
        
        return [
            {'priority': r[0], 'code': r[1], 'color': r[2], 'level': r[3], 'count': r[4]}
            for r in results
        ]
    
    @staticmethod
    def get_complaints_by_department(user):
        """Get complaint counts grouped by department."""
        from app.permissions.policy import PermissionPolicy
        
        query = PermissionPolicy.get_accessible_complaints_query(user)
        
        results = db.session.query(
            Department.name,
            Department.code,
            db.func.count(Complaint.id)
        ).join(Complaint, Complaint.department_id == Department.id).filter(
            Complaint.id.in_(query.with_entities(Complaint.id).subquery())
        ).group_by(Department.id, Department.name, Department.code).order_by(db.func.count(Complaint.id).desc()).all()
        
        return [
            {'department': r[0], 'code': r[1], 'count': r[2]}
            for r in results
        ]
    
    @staticmethod
    def get_complaints_by_software(user):
        """Get complaint counts grouped by software."""
        from app.permissions.policy import PermissionPolicy
        
        query = PermissionPolicy.get_accessible_complaints_query(user)
        
        results = db.session.query(
            SoftwareCatalog.name,
            SoftwareCatalog.code,
            db.func.count(Complaint.id)
        ).join(Complaint, Complaint.software_id == SoftwareCatalog.id).filter(
            Complaint.id.in_(query.with_entities(Complaint.id).subquery())
        ).group_by(SoftwareCatalog.id, SoftwareCatalog.name, SoftwareCatalog.code).order_by(db.func.count(Complaint.id).desc()).all()
        
        return [
            {'software': r[0], 'code': r[1], 'count': r[2]}
            for r in results
        ]
    
    @staticmethod
    def get_complaints_by_assignee(user):
        """Get complaint counts grouped by assignee."""
        from app.permissions.policy import PermissionPolicy
        
        query = PermissionPolicy.get_accessible_complaints_query(user)
        
        results = db.session.query(
            User.first_name,
            User.last_name,
            User.username,
            db.func.count(Complaint.id)
        ).join(Complaint, Complaint.assigned_to_user_id == User.id).filter(
            Complaint.id.in_(query.with_entities(Complaint.id).subquery()),
            Complaint.assigned_to_user_id != None
        ).group_by(User.id, User.first_name, User.last_name, User.username).order_by(db.func.count(Complaint.id).desc()).limit(20).all()
        
        return [
            {'assignee': f'{r[0]} {r[1]}', 'username': r[2], 'count': r[3]}
            for r in results
        ]
    
    @staticmethod
    def get_complaints_by_resolver(user):
        """Get complaint counts grouped by resolver."""
        from app.permissions.policy import PermissionPolicy
        
        query = PermissionPolicy.get_accessible_complaints_query(user)
        
        results = db.session.query(
            User.first_name,
            User.last_name,
            User.username,
            db.func.count(Complaint.id)
        ).join(Complaint, Complaint.resolved_by_user_id == User.id).filter(
            Complaint.id.in_(query.with_entities(Complaint.id).subquery()),
            Complaint.resolved_by_user_id != None
        ).group_by(User.id, User.first_name, User.last_name, User.username).order_by(db.func.count(Complaint.id).desc()).limit(20).all()
        
        return [
            {'resolver': f'{r[0]} {r[1]}', 'username': r[2], 'count': r[3]}
            for r in results
        ]
    
    @staticmethod
    def get_daily_trends(user, days=30):
        """Get daily complaint trends."""
        from app.permissions.policy import PermissionPolicy
        from sqlalchemy import func
        
        query = PermissionPolicy.get_accessible_complaints_query(user)
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days-1)
        
        results = db.session.query(
            func.date(Complaint.created_at).label('date'),
            func.count(Complaint.id).label('count')
        ).filter(
            Complaint.id.in_(query.with_entities(Complaint.id).subquery()),
            func.date(Complaint.created_at) >= start_date,
            func.date(Complaint.created_at) <= end_date,
        ).group_by(func.date(Complaint.created_at)).order_by(func.date(Complaint.created_at)).all()
        
        # Fill in missing dates
        date_counts = {r.date: r.count for r in results}
        trends = []
        current = start_date
        while current <= end_date:
            trends.append({
                'date': current.isoformat(),
                'count': date_counts.get(current, 0)
            })
            current += timedelta(days=1)
        
        return trends
    
    @staticmethod
    def get_weekly_trends(user, weeks=12):
        """Get weekly complaint trends."""
        from app.permissions.policy import PermissionPolicy
        from sqlalchemy import func
        
        query = PermissionPolicy.get_accessible_complaints_query(user)
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(weeks=weeks)
        
        results = db.session.query(
            func.date(Complaint.created_at).label('day'),
            func.count(Complaint.id).label('count')
        ).filter(
            Complaint.id.in_(query.with_entities(Complaint.id).subquery()),
            func.date(Complaint.created_at) >= start_date,
            func.date(Complaint.created_at) <= end_date,
        ).group_by(func.date(Complaint.created_at)).order_by(func.date(Complaint.created_at)).all()

        buckets = {}
        for r in results:
            day = ReportService._to_date(r.day)
            week_start = day - timedelta(days=day.weekday())
            buckets[week_start] = buckets.get(week_start, 0) + r.count

        trends = []
        for week_start in sorted(buckets):
            trends.append({
                'week_start': week_start.isoformat(),
                'count': buckets[week_start]
            })

        return trends
    
    @staticmethod
    def get_monthly_trends(user, months=12):
        """Get monthly complaint trends."""
        from app.permissions.policy import PermissionPolicy
        from sqlalchemy import func
        
        query = PermissionPolicy.get_accessible_complaints_query(user)
        
        end_date = datetime.utcnow().date()
        start_date = date(end_date.year, end_date.month, 1) - timedelta(days=1)
        start_date = date(start_date.year - ((months - 1) // 12), (start_date.month - (months - 1)) % 12 + 1, 1)
        
        results = db.session.query(
            func.date(Complaint.created_at).label('day'),
            func.count(Complaint.id).label('count')
        ).filter(
            Complaint.id.in_(query.with_entities(Complaint.id).subquery()),
            func.date(Complaint.created_at) >= start_date,
            func.date(Complaint.created_at) <= end_date,
        ).group_by(func.date(Complaint.created_at)).order_by(func.date(Complaint.created_at)).all()

        buckets = {}
        for r in results:
            day = ReportService._to_date(r.day)
            month_start = date(day.year, day.month, 1)
            buckets[month_start] = buckets.get(month_start, 0) + r.count

        trends = []
        for month_start in sorted(buckets):
            trends.append({
                'month_start': month_start.isoformat(),
                'count': buckets[month_start]
            })

        return trends

    @staticmethod
    def _to_date(value):
        """Normalise a DB date/datetime/string value to a date."""
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return datetime.strptime(str(value)[:10], '%Y-%m-%d').date()
    
    @staticmethod
    def get_sla_compliance_trends(user, days=30):
        """Get SLA compliance trends."""
        from app.permissions.policy import PermissionPolicy
        from sqlalchemy import func
        
        query = PermissionPolicy.get_accessible_complaints_query(user)
        
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days-1)
        
        results = db.session.query(
            func.date(Complaint.created_at).label('date'),
            func.count(Complaint.id).label('total'),
            func.sum(db.case(
                (db.or_(
                    Complaint.resolved_at != None,
                    Complaint.sla_resolution_deadline >= datetime.utcnow()
                ), 1),
                else_=0
            )).label('met')
        ).filter(
            Complaint.id.in_(query.with_entities(Complaint.id).subquery()),
            Complaint.sla_resolution_deadline != None,
            func.date(Complaint.created_at) >= start_date,
            func.date(Complaint.created_at) <= end_date,
        ).group_by(func.date(Complaint.created_at)).order_by(func.date(Complaint.created_at)).all()
        
        date_compliance = {}
        for r in results:
            d = r.date
            total = r.total or 0
            met = r.met or 0
            date_compliance[d] = round((met / total * 100), 1) if total > 0 else 100.0
        
        trends = []
        current = start_date
        while current <= end_date:
            trends.append({
                'date': current.isoformat(),
                'compliance': date_compliance.get(current, 100.0)
            })
            current += timedelta(days=1)
        
        return trends
    
    @staticmethod
    def generate_report_data(user, report_type, filters=None):
        """Generate report data based on type and filters."""
        from app.permissions.policy import PermissionPolicy
        
        query = PermissionPolicy.get_accessible_complaints_query(user)
        
        # Apply filters
        if filters:
            if filters.get('date_from'):
                query = query.filter(Complaint.created_at >= filters['date_from'])
            if filters.get('date_to'):
                query = query.filter(Complaint.created_at <= filters['date_to'])
            if filters.get('department_id'):
                query = query.filter(Complaint.department_id == filters['department_id'])
            if filters.get('software_id'):
                query = query.filter(Complaint.software_id == filters['software_id'])
            if filters.get('priority_id'):
                query = query.filter(Complaint.priority_id == filters['priority_id'])
            if filters.get('status_id'):
                query = query.filter(Complaint.status_id == filters['status_id'])
            if filters.get('assigned_to_user_id'):
                query = query.filter(Complaint.assigned_to_user_id == filters['assigned_to_user_id'])
            if filters.get('reported_by_user_id'):
                query = query.filter(Complaint.reported_by_user_id == filters['reported_by_user_id'])
            if filters.get('category_id'):
                query = query.filter(Complaint.category_id == filters['category_id'])
        
        complaints = query.order_by(Complaint.created_at.desc()).all()
        
        # Build report data
        data = []
        for c in complaints:
            sla_status = c.sla_resolution_status if c.sla_resolution_deadline else 'no_policy'
            
            row = {
                'complaint_number': c.complaint_number,
                'title': c.title,
                'status': c.status.name if c.status else '',
                'priority': c.priority.name if c.priority else '',
                'severity': c.severity or '',
                'category': c.category.name if c.category else '',
                'department': c.department.name if c.department else '',
                'software': c.software.name if c.software else '',
                'reported_by': c.reported_by.full_name if c.reported_by else '',
                'reported_by_employee': c.reported_by.employee_number if c.reported_by else '',
                'assigned_to': c.assigned_to.full_name if c.assigned_to else '',
                'resolved_by': c.resolved_by.full_name if c.resolved_by else '',
                'created_at': c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else '',
                'incident_started_at': c.incident_started_at.strftime('%Y-%m-%d %H:%M') if c.incident_started_at else '',
                'assigned_at': c.assigned_at.strftime('%Y-%m-%d %H:%M') if c.assigned_at else '',
                'first_response_at': c.first_response_at.strftime('%Y-%m-%d %H:%M') if c.first_response_at else '',
                'resolved_at': c.resolved_at.strftime('%Y-%m-%d %H:%M') if c.resolved_at else '',
                'closed_at': c.closed_at.strftime('%Y-%m-%d %H:%M') if c.closed_at else '',
                'sla_response_deadline': c.sla_response_deadline.strftime('%Y-%m-%d %H:%M') if c.sla_response_deadline else '',
                'sla_resolution_deadline': c.sla_resolution_deadline.strftime('%Y-%m-%d %H:%M') if c.sla_resolution_deadline else '',
                'sla_status': sla_status,
                'resolution_summary': c.resolution_summary or '',
                'affected_users': c.affected_users_count,
            }
            data.append(row)
        
        return data
    
    @staticmethod
    def export_to_csv(data, filename=None):
        """Export report data to CSV."""
        if not data:
            return None

        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)

        return '\ufeff' + output.getvalue()
    
    @staticmethod
    def export_to_pdf(data, title, filters=None):
        """Export report data to PDF using ReportLab."""
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
        from reportlab.lib.enums import TA_CENTER, TA_LEFT
        
        buffer = BytesIO()
        
        # Use landscape for more columns
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(A4),
            rightMargin=10*mm,
            leftMargin=10*mm,
            topMargin=15*mm,
            bottomMargin=15*mm,
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=6,
            alignment=TA_CENTER,
        )
        elements.append(Paragraph(title, title_style))
        
        # Subtitle with date and filters
        subtitle_parts = [f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}']
        if filters:
            filter_strs = []
            if filters.get('date_from'):
                filter_strs.append(f"From: {filters['date_from']}")
            if filters.get('date_to'):
                filter_strs.append(f"To: {filters['date_to']}")
            if filters.get('department_id'):
                from app.models import Department
                dept = Department.query.get(filters['department_id'])
                if dept:
                    filter_strs.append(f"Department: {dept.name}")
            if filters.get('priority_id'):
                from app.models import Priority
                pri = Priority.query.get(filters['priority_id'])
                if pri:
                    filter_strs.append(f"Priority: {pri.name}")
            if filter_strs:
                subtitle_parts.append(' | '.join(filter_strs))
        
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=9,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=colors.grey,
        )
        elements.append(Paragraph(' | '.join(subtitle_parts), subtitle_style))
        
        # Table
        if data:
            # Select key columns for PDF (too many for landscape)
            pdf_columns = [
                'complaint_number', 'title', 'status', 'priority', 'severity',
                'category', 'department', 'software', 'reported_by', 'assigned_to',
                'created_at', 'resolved_at', 'sla_status', 'sla_resolution_deadline'
            ]
            
            # Prepare table data
            headers = [col.replace('_', ' ').title() for col in pdf_columns]
            table_data = [headers]
            
            for row in data:
                table_data.append([str(row.get(col, ''))[:50] for col in pdf_columns])
            
            # Create table
            col_widths = [70, 120, 50, 45, 40, 60, 60, 60, 60, 60, 65, 65, 40, 65]
            
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            
            # Style table
            table.setStyle(TableStyle([
                # Header
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f2937')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 7),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
                
                # Data rows
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                ('TOPPADDING', (0, 1), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
                
                # Alignment
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ]))
            
            elements.append(table)
        else:
            elements.append(Paragraph('No data found for the selected criteria.', styles['Normal']))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    
    @staticmethod
    def get_overdue_complaints(user):
        """Get overdue complaints report."""
        from app.permissions.policy import PermissionPolicy
        
        query = PermissionPolicy.get_accessible_complaints_query(user)
        now = datetime.utcnow()
        
        # Response overdue
        response_overdue = query.filter(
            Complaint.sla_response_deadline != None,
            Complaint.sla_response_deadline < now,
            Complaint.first_response_at == None,
            Complaint.status.has(Status.is_terminal == False),
        ).all()
        
        # Resolution overdue
        resolution_overdue = query.filter(
            Complaint.sla_resolution_deadline != None,
            Complaint.sla_resolution_deadline < now,
            Complaint.resolved_at == None,
            Complaint.status.has(Status.is_terminal == False),
        ).all()
        
        return {
            'response_overdue': response_overdue,
            'resolution_overdue': resolution_overdue,
        }
    
    @staticmethod
    def get_reopened_complaints(user, days=30):
        """Get reopened complaints report."""
        from app.permissions.policy import PermissionPolicy
        
        query = PermissionPolicy.get_accessible_complaints_query(user)
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        reopened = query.filter(
            Complaint.status.has(Status.code == 'reopened'),
            Complaint.updated_at >= start_date,
        ).all()
        
        return reopened