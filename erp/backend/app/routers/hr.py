from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional
from pydantic import BaseModel
from datetime import date
from app.database import get_db
from app.models.hr import Employee, Department, Position, Payroll, PayrollItem, LeaveRequest, LeaveStatus, EmploymentType
from app.routers.auth import get_current_user
from app.models.user import User
import uuid

router = APIRouter(prefix="/hr", tags=["hr"])


# ─── Departments ──────────────────────────────────────────────────────────────

@router.get("/departments")
def list_departments(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    depts = db.query(Department).filter(Department.is_active == True).all()
    return [{"id": str(d.id), "name": d.name, "code": d.code, "jurisdiction": d.jurisdiction} for d in depts]


@router.post("/departments")
def create_department(payload: dict, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    dept = Department(
        name=payload["name"],
        code=payload.get("code"),
        cost_center=payload.get("cost_center"),
        jurisdiction=payload.get("jurisdiction", "US"),
    )
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return {"id": str(dept.id), "name": dept.name}


# ─── Employees ────────────────────────────────────────────────────────────────

class EmployeeIn(BaseModel):
    first_name: str
    last_name: str
    email: str
    department_id: Optional[str] = None
    position_id: Optional[str] = None
    employment_type: str = "full_time"
    hire_date: date
    salary: Optional[float] = None
    salary_currency: str = "USD"
    jurisdiction: str = "US"
    phone: Optional[str] = None


@router.get("/employees")
def list_employees(
    department_id: Optional[str] = Query(None),
    jurisdiction: Optional[str] = Query(None),
    active_only: bool = Query(True),
    page: int = Query(1, ge=1),
    size: int = Query(20, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(Employee)
    if active_only:
        q = q.filter(Employee.is_active == True)
    if department_id:
        q = q.filter(Employee.department_id == department_id)
    if jurisdiction:
        q = q.filter(Employee.jurisdiction == jurisdiction)
    total = q.count()
    emps = q.order_by(Employee.last_name).offset((page - 1) * size).limit(size).all()
    return {
        "total": total,
        "items": [
            {
                "id": str(e.id),
                "employee_number": e.employee_number,
                "full_name": f"{e.first_name} {e.last_name}",
                "email": e.email,
                "department_id": str(e.department_id) if e.department_id else None,
                "employment_type": e.employment_type.value,
                "hire_date": e.hire_date.isoformat(),
                "salary": float(e.salary) if e.salary else None,
                "salary_currency": e.salary_currency,
                "jurisdiction": e.jurisdiction,
                "is_active": e.is_active,
            }
            for e in emps
        ],
    }


@router.post("/employees")
def create_employee(req: EmployeeIn, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    count = db.query(Employee).count()
    emp_num = f"EMP-{count + 1:05d}"
    emp = Employee(
        employee_number=emp_num,
        first_name=req.first_name,
        last_name=req.last_name,
        email=req.email,
        department_id=uuid.UUID(req.department_id) if req.department_id else None,
        position_id=uuid.UUID(req.position_id) if req.position_id else None,
        employment_type=EmploymentType(req.employment_type),
        hire_date=req.hire_date,
        salary=req.salary,
        salary_currency=req.salary_currency,
        jurisdiction=req.jurisdiction,
        phone=req.phone,
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return {"id": str(emp.id), "employee_number": emp.employee_number}


@router.get("/employees/{emp_id}")
def get_employee(emp_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    emp = db.query(Employee).filter(Employee.id == emp_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {
        "id": str(emp.id),
        "employee_number": emp.employee_number,
        "first_name": emp.first_name,
        "last_name": emp.last_name,
        "email": emp.email,
        "phone": emp.phone,
        "employment_type": emp.employment_type.value,
        "hire_date": emp.hire_date.isoformat(),
        "salary": float(emp.salary) if emp.salary else None,
        "salary_currency": emp.salary_currency,
        "jurisdiction": emp.jurisdiction,
        "is_active": emp.is_active,
    }


# ─── Leave Requests ───────────────────────────────────────────────────────────

@router.get("/leave-requests")
def list_leave_requests(
    employee_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(LeaveRequest)
    if employee_id:
        q = q.filter(LeaveRequest.employee_id == employee_id)
    if status:
        q = q.filter(LeaveRequest.status == status)
    items = q.order_by(desc(LeaveRequest.created_at)).limit(100).all()
    return [
        {
            "id": str(l.id),
            "employee_id": str(l.employee_id),
            "leave_type": l.leave_type,
            "start_date": l.start_date.isoformat(),
            "end_date": l.end_date.isoformat(),
            "days": float(l.days) if l.days else None,
            "status": l.status.value,
            "reason": l.reason,
        }
        for l in items
    ]


@router.post("/leave-requests")
def create_leave_request(payload: dict, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    start = date.fromisoformat(payload["start_date"])
    end = date.fromisoformat(payload["end_date"])
    days = (end - start).days + 1
    lr = LeaveRequest(
        employee_id=uuid.UUID(payload["employee_id"]),
        leave_type=payload["leave_type"],
        start_date=start,
        end_date=end,
        days=days,
        reason=payload.get("reason"),
    )
    db.add(lr)
    db.commit()
    return {"id": str(lr.id), "days": days}


@router.patch("/leave-requests/{lr_id}/approve")
def approve_leave(lr_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    lr = db.query(LeaveRequest).filter(LeaveRequest.id == lr_id).first()
    if not lr:
        raise HTTPException(status_code=404, detail="Leave request not found")
    lr.status = LeaveStatus.APPROVED
    lr.approved_by = current_user.id
    from datetime import datetime, timezone
    lr.approved_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Approved"}


# ─── Dashboard ────────────────────────────────────────────────────────────────

@router.get("/dashboard")
def hr_dashboard(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    total_employees = db.query(func.count(Employee.id)).filter(Employee.is_active == True).scalar()
    by_dept = db.query(
        Department.name, func.count(Employee.id)
    ).join(Employee, Employee.department_id == Department.id).filter(
        Employee.is_active == True
    ).group_by(Department.name).all()

    pending_leaves = db.query(func.count(LeaveRequest.id)).filter(
        LeaveRequest.status == LeaveStatus.PENDING
    ).scalar()

    by_jurisdiction = db.query(
        Employee.jurisdiction, func.count(Employee.id)
    ).filter(Employee.is_active == True).group_by(Employee.jurisdiction).all()

    return {
        "total_employees": total_employees,
        "pending_leave_requests": pending_leaves,
        "by_department": [{"name": n, "count": c} for n, c in by_dept],
        "by_jurisdiction": [{"jurisdiction": j, "count": c} for j, c in by_jurisdiction],
    }
