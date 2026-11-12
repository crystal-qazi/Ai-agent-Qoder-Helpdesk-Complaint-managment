"""SLA calculation and management service."""
from datetime import datetime, timedelta, time
from app.extensions import db
from app.models import SLAPolicy, SLAHistory, Holiday, WorkingSchedule, Complaint, Status


class SLAService:
    """Service for SLA calculations and management."""
    
    @staticmethod
    def get_applicable_policy(complaint):
        """Get the most specific applicable SLA policy for a complaint."""
        # Priority + Department + Category (most specific)
        policy = SLAPolicy.query.filter(
            SLAPolicy.priority_id == complaint.priority_id,
            SLAPolicy.department_id == complaint.department_id,
            SLAPolicy.category_id == complaint.category_id,
            SLAPolicy.is_active == True,
        ).first()
        
        if policy:
            return policy
        
        # Priority + Department
        policy = SLAPolicy.query.filter(
            SLAPolicy.priority_id == complaint.priority_id,
            SLAPolicy.department_id == complaint.department_id,
            SLAPolicy.category_id == None,
            SLAPolicy.is_active == True,
        ).first()
        
        if policy:
            return policy
        
        # Priority + Category
        policy = SLAPolicy.query.filter(
            SLAPolicy.priority_id == complaint.priority_id,
            SLAPolicy.department_id == None,
            SLAPolicy.category_id == complaint.category_id,
            SLAPolicy.is_active == True,
        ).first()
        
        if policy:
            return policy
        
        # Priority only
        policy = SLAPolicy.query.filter(
            SLAPolicy.priority_id == complaint.priority_id,
            SLAPolicy.department_id == None,
            SLAPolicy.category_id == None,
            SLAPolicy.is_active == True,
        ).first()
        
        if policy:
            return policy
        
        # Department only
        policy = SLAPolicy.query.filter(
            SLAPolicy.priority_id == None,
            SLAPolicy.department_id == complaint.department_id,
            SLAPolicy.category_id == None,
            SLAPolicy.is_active == True,
        ).first()
        
        if policy:
            return policy
        
        # Category only
        policy = SLAPolicy.query.filter(
            SLAPolicy.priority_id == None,
            SLAPolicy.department_id == None,
            SLAPolicy.category_id == complaint.category_id,
            SLAPolicy.is_active == True,
        ).first()
        
        if policy:
            return policy
        
        # Default policy
        return SLAPolicy.query.filter_by(is_default=True, is_active=True).first()
    
    MAX_DEADLINE_ITERATIONS = 10000  # Safety cap: ~14 days at 1-minute resolution

    @staticmethod
    def calculate_deadline(start_time, target_minutes, working_schedule=None, use_business_hours=True):
        """Calculate SLA deadline based on business hours or calendar hours."""
        if not use_business_hours or not working_schedule:
            # Calendar hours - simple addition
            return start_time + timedelta(minutes=target_minutes)

        # Business hours calculation
        remaining_minutes = target_minutes
        current_time = start_time
        iterations = 0

        while remaining_minutes > 0 and iterations < SLAService.MAX_DEADLINE_ITERATIONS:
            # Check if current time is within working hours
            if SLAService._is_working_time(current_time, working_schedule):
                # Calculate minutes until end of working day
                day_end = SLAService._get_day_end(current_time, working_schedule)
                if day_end:
                    minutes_today = (day_end - current_time).total_seconds() / 60
                    if minutes_today >= remaining_minutes:
                        return current_time + timedelta(minutes=remaining_minutes)
                    else:
                        remaining_minutes -= minutes_today
                        current_time = day_end
                else:
                    # No working hours today, move to next day
                    current_time = SLAService._next_working_day_start(current_time, working_schedule)
            else:
                # Outside working hours, move to next working period
                current_time = SLAService._next_working_period(current_time, working_schedule)
            iterations += 1

        return current_time
    
    @staticmethod
    def _is_working_time(dt, schedule):
        """Check if datetime is within working hours."""
        if not schedule.is_working_day(dt):
            return False
        
        day_schedule = schedule.get_working_hours_for_date(dt)
        if not day_schedule:
            return False
        
        current_time = dt.time()
        start_time = time.fromisoformat(day_schedule['start'])
        end_time = time.fromisoformat(day_schedule['end'])
        
        return start_time <= current_time < end_time
    
    @staticmethod
    def _get_day_end(dt, schedule):
        """Get end of working day for a datetime."""
        day_schedule = schedule.get_working_hours_for_date(dt)
        if not day_schedule:
            return None
        
        end_time = time.fromisoformat(day_schedule['end'])
        return datetime.combine(dt.date(), end_time)
    
    @staticmethod
    def _next_working_day_start(dt, schedule):
        """Get start of next working day."""
        next_day = dt + timedelta(days=1)
        next_day = datetime.combine(next_day.date(), time.min)
        
        # Find next working day
        for _ in range(14):  # Max 2 weeks lookahead
            if schedule.is_working_day(next_day):
                day_schedule = schedule.get_working_hours_for_date(next_day)
                if day_schedule:
                    start_time = time.fromisoformat(day_schedule['start'])
                    return datetime.combine(next_day.date(), start_time)
            next_day += timedelta(days=1)
        
        return next_day
    
    @staticmethod
    def _next_working_period(dt, schedule):
        """Get next working period start."""
        day_schedule = schedule.get_working_hours_for_date(dt)
        if day_schedule:
            start_time = time.fromisoformat(day_schedule['start'])
            if dt.time() < start_time:
                return datetime.combine(dt.date(), start_time)
        
        # Move to next day
        return SLAService._next_working_day_start(dt, schedule)
    
    @classmethod
    def calculate_complaint_sla(cls, complaint, user_id=None):
        """Calculate and set SLA deadlines for a complaint."""
        policy = cls.get_applicable_policy(complaint)
        
        if not policy:
            # No policy found, clear deadlines
            complaint.sla_response_deadline = None
            complaint.sla_resolution_deadline = None
            return None
        
        start_time = complaint.created_at
        working_schedule = policy.working_schedule
        use_business_hours = policy.use_business_hours
        
        # Calculate response deadline
        response_deadline = cls.calculate_deadline(
            start_time, 
            policy.response_target_minutes,
            working_schedule,
            use_business_hours
        )
        
        # Calculate resolution deadline
        resolution_deadline = cls.calculate_deadline(
            start_time,
            policy.resolution_target_minutes,
            working_schedule,
            use_business_hours
        )
        
        # Update complaint
        old_response = complaint.sla_response_deadline
        old_resolution = complaint.sla_resolution_deadline
        
        complaint.sla_response_deadline = response_deadline
        complaint.sla_resolution_deadline = resolution_deadline
        
        # Create SLA history record
        history = SLAHistory(
            complaint_id=complaint.id,
            sla_policy_id=policy.id,
            response_deadline=response_deadline,
            resolution_deadline=resolution_deadline,
            calculation_method='business_hours' if use_business_hours else 'calendar_hours',
            business_hours_used=use_business_hours,
            working_schedule_id=working_schedule.id if working_schedule else None,
            calculated_by_user_id=user_id,
            notes=f'Initial SLA calculation using policy: {policy.name}',
        )
        
        db.session.add(history)
        db.session.add(complaint)
        
        return {
            'policy': policy,
            'response_deadline': response_deadline,
            'resolution_deadline': resolution_deadline,
            'history': history,
        }
    
    @classmethod
    def recalculate_sla_on_status_change(cls, complaint, new_status, user_id=None):
        """Recalculate SLA when complaint status changes."""
        policy = cls.get_applicable_policy(complaint)
        
        if not policy:
            return None
        
        # Check if SLA should be paused
        pause_status_ids = policy.pause_on_status_ids or []
        
        # Get statuses that pause SLA based on policy settings
        if policy.pause_on_pending_info:
            pending_status = Status.query.filter_by(code='pending_info', is_active=True).first()
            if pending_status:
                pause_status_ids.append(pending_status.id)
        
        if policy.pause_on_hold:
            hold_status = Status.query.filter_by(code='on_hold', is_active=True).first()
            if hold_status:
                pause_status_ids.append(hold_status.id)
        
        if policy.pause_on_reopen:
            reopened_status = Status.query.filter_by(code='reopened', is_active=True).first()
            if reopened_status:
                pause_status_ids.append(reopened_status.id)
        
        is_paused = new_status.id in pause_status_ids
        
        # Get latest SLA history
        latest_history = SLAHistory.query.filter_by(complaint_id=complaint.id).order_by(SLAHistory.calculated_at.desc()).first()
        
        if is_paused and not (latest_history and latest_history.is_paused):
            # Pause SLA
            paused_at = datetime.utcnow()
            history = SLAHistory(
                complaint_id=complaint.id,
                sla_policy_id=policy.id,
                response_deadline=complaint.sla_response_deadline,
                resolution_deadline=complaint.sla_resolution_deadline,
                is_paused=True,
                paused_at=paused_at,
                paused_by_status_id=new_status.id,
                pause_reason=f'SLA paused due to status change to {new_status.name}',
                calculated_by_user_id=user_id,
            )
            db.session.add(history)
            
        elif not is_paused and latest_history and latest_history.is_paused:
            # Resume SLA - recalculate deadlines with paused time excluded
            resumed_at = datetime.utcnow()
            paused_duration = (resumed_at - latest_history.paused_at).total_seconds() / 60
            
            # Extend deadlines by paused duration
            new_response_deadline = complaint.sla_response_deadline + timedelta(minutes=paused_duration)
            new_resolution_deadline = complaint.sla_resolution_deadline + timedelta(minutes=paused_duration)
            
            complaint.sla_response_deadline = new_response_deadline
            complaint.sla_resolution_deadline = new_resolution_deadline
            
            # Update history
            latest_history.is_paused = False
            latest_history.resumed_at = resumed_at
            latest_history.resume_reason=f'SLA resumed due to status change to {new_status.name}'
            latest_history.total_paused_minutes += int(paused_duration)
            
            # Create new history record
            history = SLAHistory(
                complaint_id=complaint.id,
                sla_policy_id=policy.id,
                response_deadline=new_response_deadline,
                resolution_deadline=new_resolution_deadline,
                calculation_method='business_hours' if policy.use_business_hours else 'calendar_hours',
                business_hours_used=policy.use_business_hours,
                working_schedule_id=policy.working_schedule_id,
                is_paused=False,
                calculated_by_user_id=user_id,
                notes=f'SLA recalculated after pause. Paused duration: {paused_duration:.0f} minutes.',
            )
            db.session.add(history)
            db.session.add(complaint)
        
        return {
            'is_paused': is_paused,
            'policy': policy,
        }
    
    @classmethod
    def check_sla_breaches(cls):
        """Check all active complaints for SLA breaches."""
        from app.models import Notification
        
        breached = []
        now = datetime.utcnow()
        
        # Check response breaches
        response_breaches = Complaint.query.filter(
            Complaint.sla_response_deadline != None,
            Complaint.sla_response_deadline < now,
            Complaint.first_response_at == None,
            Complaint.status.has(Status.is_terminal == False),
        ).all()
        
        for complaint in response_breaches:
            # Check if already recorded as breached
            latest_history = SLAHistory.query.filter_by(complaint_id=complaint.id).order_by(SLAHistory.calculated_at.desc()).first()
            if not latest_history or not latest_history.response_breached:
                # Mark as breached
                if latest_history:
                    latest_history.response_breached = True
                    latest_history.response_breached_at = now
                
                # Create notification for assignee
                if complaint.assigned_to_user_id:
                    Notification.create_notification(
                        user_id=complaint.assigned_to_user_id,
                        title='SLA Response Breach',
                        message=f'Complaint {complaint.complaint_number} has breached its response SLA deadline.',
                        notification_type='sla_breach',
                        complaint_id=complaint.id,
                        priority='high',
                        action_url=f'/complaints/{complaint.id}',
                        action_label='View Complaint',
                    )
                
                # Notify supervisors/escalation
                breached.append({
                    'complaint': complaint,
                    'type': 'response',
                    'deadline': complaint.sla_response_deadline,
                })
        
        # Check resolution breaches
        resolution_breaches = Complaint.query.filter(
            Complaint.sla_resolution_deadline != None,
            Complaint.sla_resolution_deadline < now,
            Complaint.resolved_at == None,
            Complaint.status.has(Status.is_terminal == False),
        ).all()
        
        for complaint in resolution_breaches:
            latest_history = SLAHistory.query.filter_by(complaint_id=complaint.id).order_by(SLAHistory.calculated_at.desc()).first()
            if not latest_history or not latest_history.resolution_breached:
                if latest_history:
                    latest_history.resolution_breached = True
                    latest_history.resolution_breached_at = now
                
                if complaint.assigned_to_user_id:
                    Notification.create_notification(
                        user_id=complaint.assigned_to_user_id,
                        title='SLA Resolution Breach',
                        message=f'Complaint {complaint.complaint_number} has breached its resolution SLA deadline.',
                        notification_type='sla_breach',
                        complaint_id=complaint.id,
                        priority='urgent',
                        action_url=f'/complaints/{complaint.id}',
                        action_label='View Complaint',
                    )
                
                breached.append({
                    'complaint': complaint,
                    'type': 'resolution',
                    'deadline': complaint.sla_resolution_deadline,
                })
        
        return breached
    
    @classmethod
    def get_sla_status(cls, complaint):
        """Get current SLA status for a complaint."""
        if not complaint.sla_response_deadline and not complaint.sla_resolution_deadline:
            return {'response': 'no_policy', 'resolution': 'no_policy'}
        
        now = datetime.utcnow()
        response_status = 'ok'
        resolution_status = 'ok'
        
        if complaint.sla_response_deadline and not complaint.first_response_at:
            if now > complaint.sla_response_deadline:
                response_status = 'breached'
            else:
                total = (complaint.sla_response_deadline - complaint.created_at).total_seconds()
                remaining = (complaint.sla_response_deadline - now).total_seconds()
                if remaining / total < 0.25:
                    response_status = 'warning'
        
        if complaint.sla_resolution_deadline and not complaint.resolved_at:
            if now > complaint.sla_resolution_deadline:
                resolution_status = 'breached'
            else:
                total = (complaint.sla_resolution_deadline - complaint.created_at).total_seconds()
                remaining = (complaint.sla_resolution_deadline - now).total_seconds()
                if remaining / total < 0.25:
                    resolution_status = 'warning'
        
        return {
            'response': response_status,
            'resolution': resolution_status,
            'response_deadline': complaint.sla_response_deadline,
            'resolution_deadline': complaint.sla_resolution_deadline,
            'response_remaining': (complaint.sla_response_deadline - now).total_seconds() if complaint.sla_response_deadline and not complaint.first_response_at else None,
            'resolution_remaining': (complaint.sla_resolution_deadline - now).total_seconds() if complaint.sla_resolution_deadline and not complaint.resolved_at else None,
        }