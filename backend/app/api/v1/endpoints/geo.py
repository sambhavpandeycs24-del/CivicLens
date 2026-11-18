from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.api.deps import require_roles
from app.db.session import get_db
from app.models.complaint import Complaint, ComplaintStatus
from app.models.user import User, UserRole

router = APIRouter(prefix="/geo", tags=["Geospatial"])

@router.get("/complaints")
def complaint_points(
    min_lat: float = Query(ge=-90, le=90), max_lat: float = Query(ge=-90, le=90),
    min_lon: float = Query(ge=-180, le=180), max_lon: float = Query(ge=-180, le=180),
    db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.AUTHORITY, UserRole.ADMIN))
):
    if min_lat > max_lat or min_lon > max_lon:
        return {"items": [], "count": 0}
    query = select(Complaint).where(Complaint.latitude >= min_lat, Complaint.latitude <= max_lat,
                                   Complaint.longitude >= min_lon, Complaint.longitude <= max_lon,
                                   Complaint.status != ComplaintStatus.REJECTED).limit(1000)
    if user.role == UserRole.AUTHORITY:
        query = query.where((Complaint.assigned_to_id == user.id) | (Complaint.assigned_to_id.is_(None)))
    rows = list(db.scalars(query))
    return {"count": len(rows), "items": [{"id": str(c.id), "tracking_code": c.tracking_code,
            "title": c.title, "category": c.category.value, "status": c.status.value,
            "priority": c.priority.value, "latitude": c.latitude, "longitude": c.longitude} for c in rows]}

@router.get("/heatmap")
def complaint_heatmap(
    precision: int = Query(default=2, ge=1, le=4),
    db: Session = Depends(get_db), user: User = Depends(require_roles(UserRole.AUTHORITY, UserRole.ADMIN))
):
    query = select(Complaint).where(Complaint.status != ComplaintStatus.REJECTED)
    if user.role == UserRole.AUTHORITY:
        query = query.where((Complaint.assigned_to_id == user.id) | (Complaint.assigned_to_id.is_(None)))
    rows = list(db.scalars(query.limit(5000)))
    scale = 10 ** precision
    cells = {}
    for c in rows:
        key = (round(c.latitude * scale) / scale, round(c.longitude * scale) / scale)
        cells[key] = cells.get(key, 0) + 1
    return {"precision": precision, "count": len(rows), "cells": [
        {"latitude": lat, "longitude": lon, "complaint_count": count} for (lat, lon), count in cells.items()
    ]}
