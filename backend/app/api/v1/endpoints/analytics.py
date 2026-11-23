from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.complaint import Complaint, ComplaintStatus
from app.models.user import User, UserRole
from app.services.intelligence import complaint_sla

router = APIRouter(prefix="/analytics", tags=["Civic Analytics"])
MIN_DEPARTMENT_SAMPLE = 5


def _scope(user: User):
    if user.role == UserRole.AUTHORITY:
        return (Complaint.assigned_to_id == user.id) | (Complaint.assigned_to_id.is_(None))
    return True


@router.get("/overview")
def overview(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AUTHORITY, UserRole.ADMIN)),
):
    scope = _scope(user)
    total = db.scalar(select(func.count(Complaint.id)).where(scope)) or 0
    status_rows = db.execute(
        select(Complaint.status, func.count(Complaint.id)).where(scope).group_by(Complaint.status)
    ).all()
    category_rows = db.execute(
        select(Complaint.category, func.count(Complaint.id)).where(scope).group_by(Complaint.category)
    ).all()
    resolved = db.scalar(
        select(func.count(Complaint.id)).where(scope, Complaint.status == ComplaintStatus.RESOLVED)
    ) or 0
    rejected = db.scalar(
        select(func.count(Complaint.id)).where(scope, Complaint.status == ComplaintStatus.REJECTED)
    ) or 0
    return {
        "total_complaints": total,
        "resolved_complaints": resolved,
        "open_complaints": total - resolved - rejected,
        "resolution_rate_percent": round((resolved / total) * 100, 2) if total else 0,
        "by_status": {status.value: count for status, count in status_rows},
        "by_category": {category.value: count for category, count in category_rows},
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/departments")
def department_performance(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AUTHORITY, UserRole.ADMIN)),
):
    query = (
        select(Complaint, User.department)
        .outerjoin(User, Complaint.assigned_to_id == User.id)
        .where(Complaint.status != ComplaintStatus.REJECTED, _scope(user))
    )
    grouped = defaultdict(lambda: {"complaints": [], "authorities": set()})
    for complaint, department in db.execute(query):
        key = department or ("Unassigned" if complaint.assigned_to_id is None else "Department not set")
        grouped[key]["complaints"].append(complaint)
        if complaint.assigned_to_id:
            grouped[key]["authorities"].add(complaint.assigned_to_id)

    departments = []
    for name, group in sorted(grouped.items()):
        complaints = group["complaints"]
        resolved = [item for item in complaints if item.status == ComplaintStatus.RESOLVED]
        pending = [item for item in complaints if item.status not in {ComplaintStatus.RESOLVED, ComplaintStatus.REJECTED}]
        durations = []
        for item in resolved:
            if item.resolved_at is None:
                continue
            start = item.created_at
            end = item.resolved_at
            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)
            durations.append(max(0.0, (end - start).total_seconds() / 3600))
        overdue = sum(complaint_sla(item)["risk_level"] == "overdue" for item in pending)
        total = len(complaints)
        sufficient_sample = total >= MIN_DEPARTMENT_SAMPLE
        departments.append({
            "department": name,
            "authority_count": len(group["authorities"]),
            "total_complaints": total,
            "resolved_complaints": len(resolved),
            "resolution_rate_percent": round(len(resolved) / total * 100, 2) if total else 0,
            "average_resolution_hours": round(sum(durations) / len(durations), 1) if durations else None,
            "pending_workload": len(pending),
            "overdue_complaints": overdue,
            "sample_sufficient": sufficient_sample,
            "sample_note": None if sufficient_sample else f"Small sample ({total} complaints); descriptive only.",
        })
    return {"minimum_sample_size": MIN_DEPARTMENT_SAMPLE, "departments": departments}


@router.get("/sla")
def sla_risk(
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AUTHORITY, UserRole.ADMIN)),
):
    query = (
        select(Complaint, User.department)
        .outerjoin(User, Complaint.assigned_to_id == User.id)
        .where(Complaint.status != ComplaintStatus.REJECTED, _scope(user))
        .order_by(Complaint.created_at)
        .limit(5000)
    )
    rows = list(db.execute(query))
    active = []
    risk_counts = {"overdue": 0, "at_risk": 0, "on_track": 0}
    resolution_counts = {"resolved_on_time": 0, "resolved_late": 0, "resolution_time_unavailable": 0}
    resolved_durations = []
    for complaint, department in rows:
        sla = complaint_sla(complaint)
        if complaint.status == ComplaintStatus.RESOLVED:
            if sla["risk_level"] in resolution_counts:
                resolution_counts[sla["risk_level"]] += 1
            if sla["risk_level"] in {"resolved_on_time", "resolved_late"}:
                resolved_durations.append(sla["elapsed_hours"])
            continue
        risk_counts[sla["risk_level"]] += 1
        active.append({
            "complaint_id": str(complaint.id),
            "tracking_code": complaint.tracking_code,
            "title": complaint.title,
            "category": complaint.category.value,
            "priority": complaint.priority.value,
            "status": complaint.status.value,
            "department": department or ("Unassigned" if complaint.assigned_to_id is None else "Department not set"),
            **sla,
        })
    risk_order = {"overdue": 0, "at_risk": 1, "on_track": 2}
    active.sort(key=lambda item: (risk_order[item["risk_level"]], -item["elapsed_hours"]))
    return {
        "active_count": len(active),
        "risk_counts": risk_counts,
        "resolution_counts": resolution_counts,
        "average_resolution_hours": (
            round(sum(resolved_durations) / len(resolved_durations), 1)
            if resolved_durations else None
        ),
        "items": active,
        "truncated": len(rows) == 5000,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
