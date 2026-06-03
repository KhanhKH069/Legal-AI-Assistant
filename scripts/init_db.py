import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlmodel import Session, select
from api.database import engine
from api.models import User, Employee, LeaveRequest, Appraisal, PayrollRecord, Ticket
from api.auth import get_password_hash

def load_json(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def init_db():
    print('Creating tables using Alembic migrations...')
    import subprocess
    import sys
    subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], check=True)
    print('Migrating data...')
    with Session(engine) as session:
        emp_data = load_json('data/employees_data.json')
        if emp_data and 'employees' in emp_data:
            for emp in emp_data['employees']:
                if not session.exec(select(Employee).where(Employee.employee_id == emp['employee_id'])).first():
                    new_emp = Employee(employee_id=emp['employee_id'], name=emp.get('name', ''), gender=emp.get('gender', 'N/A'), department=emp.get('department', ''), position=emp.get('position', ''), level=emp.get('level', 'Junior'), email=emp.get('email', ''), phone=emp.get('phone', ''), hire_date=emp.get('hire_date', ''), status=emp.get('status', 'Active'), manager_id=emp.get('manager_id'), salary_vnd=emp.get('salary_vnd', 0.0), leave_balance=emp.get('leave_balance', 0.0), performance_rating=emp.get('performance_rating', 3.0), address=emp.get('address', ''), education=emp.get('education', ''), skills_json=json.dumps(emp.get('skills', [])), contract_json=json.dumps(emp.get('contract', {})))
                    session.add(new_emp)
                if not session.exec(select(User).where(User.username == emp['employee_id'])).first():
                    role = 'employee'
                    if emp.get('department') in ['HR', 'IT']:
                        role = 'admin'
                    elif 'Lead' in emp.get('position', '') or 'Manager' in emp.get('position', '') or 'Director' in emp.get('position', ''):
                        role = 'manager'
                    new_user = User(username=emp['employee_id'], hashed_password=get_password_hash('password123'), role=role, employee_id=emp['employee_id'])
                    session.add(new_user)
            if not session.exec(select(User).where(User.username == 'admin')).first():
                admin_user = User(username='admin', hashed_password=get_password_hash('password123'), role='admin', employee_id=None)
                session.add(admin_user)
            session.commit()
            print(f"✅ Migrated {len(emp_data['employees'])} employees and created users.")
        att_data = load_json('data/attendance_data.json')
        if att_data and 'leave_requests' in att_data:
            for req in att_data['leave_requests']:
                if not session.exec(select(LeaveRequest).where(LeaveRequest.request_id == req['request_id'])).first():
                    new_req = LeaveRequest(request_id=req['request_id'], employee_id=req['employee_id'], type=req.get('type', 'Annual'), start_date=req.get('start_date', ''), end_date=req.get('end_date', ''), days=req.get('days', 0), reason=req.get('reason', ''), status=req.get('status', 'Pending'), approved_by=req.get('approved_by'), submitted_at=req.get('submitted_at', ''))
                    session.add(new_req)
            session.commit()
            print('✅ Migrated leave requests.')
        appr_data = load_json('data/appraisal_data.json')
        if appr_data and 'appraisals' in appr_data:
            for app in appr_data['appraisals']:
                if not session.exec(select(Appraisal).where(Appraisal.appraisal_id == app['appraisal_id'])).first():
                    new_app = Appraisal(appraisal_id=app['appraisal_id'], employee_id=app['employee_id'], period=app.get('period', ''), type=app.get('type', ''), status=app.get('status', 'Pending'), self_evaluation_json=json.dumps(app.get('self_evaluation', {})), manager_feedback_json=json.dumps(app.get('manager_feedback', {})), final_score=app.get('final_score'), rating_label=app.get('rating_label'), created_at=app.get('created_at', ''))
                    session.add(new_app)
            session.commit()
            print('✅ Migrated appraisals.')
        payroll_data = load_json('data/payroll_data.json')
        if payroll_data and 'payroll_records' in payroll_data:
            count = 0
            for emp_id, data in payroll_data['payroll_records'].items():
                if 'salary_history' in data:
                    for rec in data['salary_history']:
                        exist = session.exec(select(PayrollRecord).where(PayrollRecord.employee_id == emp_id, PayrollRecord.month == rec['month'])).first()
                        if not exist:
                            new_rec = PayrollRecord(employee_id=emp_id, month=rec['month'], month_label=rec.get('month_label', ''), working_days=rec.get('working_days', 22), days_worked=rec.get('days_worked', 22), leave_days=rec.get('leave_days', 0), absent_days=rec.get('absent_days', 0), base_salary=rec.get('base_salary', 0), ot_hours=rec.get('ot_hours', 0), ot_rate=rec.get('ot_rate', 0), ot_pay=rec.get('ot_pay', 0), kpi_bonus=rec.get('kpi_bonus', 0), other_bonus=rec.get('other_bonus', 0), gross_salary=rec.get('gross_salary', 0), social_insurance=rec.get('social_insurance', 0), health_insurance=rec.get('health_insurance', 0), unemployment_insurance=rec.get('unemployment_insurance', 0), income_tax=rec.get('income_tax', 0), total_deductions=rec.get('total_deductions', 0), net_salary=rec.get('net_salary', 0), status=rec.get('status', 'Pending'), payment_date=rec.get('payment_date'))
                            session.add(new_rec)
                            count += 1
            session.commit()
            print(f'✅ Migrated {count} payroll records.')
        ticket_data = load_json('data/helpdesk_data.json')
        if ticket_data and 'tickets' in ticket_data:
            for t in ticket_data['tickets']:
                if not session.exec(select(Ticket).where(Ticket.ticket_id == t['ticket_id'])).first():
                    new_t = Ticket(ticket_id=t['ticket_id'], employee_id=t['employee_id'], category=t.get('category', ''), subject=t.get('subject', ''), description=t.get('description', ''), priority=t.get('priority', 'Low'), status=t.get('status', 'Open'), created_at=t.get('created_at', ''), resolved_at=t.get('resolved_at'), comments_json=json.dumps(t.get('comments', [])))
                    session.add(new_t)
            session.commit()
            print('✅ Migrated tickets.')
if __name__ == '__main__':
    init_db()
    print('Migration hoan tat!')