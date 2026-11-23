from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, text
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


@router.get("/hotspots")
def complaint_hotspots(
    days: int = Query(default=30, ge=7, le=365),
    radius_meters: int = Query(default=500, ge=100, le=5000),
    min_complaints: int = Query(default=2, ge=2, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(UserRole.AUTHORITY, UserRole.ADMIN)),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    if db.bind.dialect.name == "postgresql":
        rows = db.execute(
            text("""
                WITH points AS (
                    SELECT category, created_at,
                        ST_Transform(
                            ST_SetSRID(ST_MakePoint(
                                longitude,
                                LEAST(GREATEST(latitude, -85.051128), 85.051128)
                            ), 4326),
                            3857
                        ) AS geom
                    FROM complaints
                    WHERE status <> 'rejected'
                      AND created_at >= :since
                      AND (:is_admin OR assigned_to_id = :user_id OR assigned_to_id IS NULL)
                ),
                clustered AS (
                    SELECT category, date_trunc('week', created_at) AS time_bucket, geom,
                        ST_ClusterDBSCAN(geom, :radius_meters, :min_complaints)
                            OVER (PARTITION BY category, date_trunc('week', created_at)) AS cluster_id
                    FROM points
                )
                SELECT category, time_bucket, COUNT(*) AS complaint_count,
                    ST_X(ST_Transform(ST_Centroid(ST_Collect(geom)), 4326)) AS longitude,
                    ST_Y(ST_Transform(ST_Centroid(ST_Collect(geom)), 4326)) AS latitude
                FROM clustered
                WHERE cluster_id IS NOT NULL
                GROUP BY category, time_bucket, cluster_id
                ORDER BY complaint_count DESC, time_bucket DESC
            """),
            {
                "since": since,
                "is_admin": user.role == UserRole.ADMIN,
                "user_id": user.id,
                "radius_meters": radius_meters,
                "min_complaints": min_complaints,
            },
        ).mappings().all()
        hotspots = [{
            "category": row["category"],
            "time_bucket": row["time_bucket"].date().isoformat(),
            "complaint_count": row["complaint_count"],
            "latitude": round(row["latitude"], 6),
            "longitude": round(row["longitude"], 6),
        } for row in rows]
        method = "postgis_clusterdbscan"
    else:
        query = select(Complaint).where(
            Complaint.status != ComplaintStatus.REJECTED,
            Complaint.created_at >= since,
        ).order_by(Complaint.created_at.desc()).limit(5000)
        if user.role == UserRole.AUTHORITY:
            query = query.where((Complaint.assigned_to_id == user.id) | (Complaint.assigned_to_id.is_(None)))
        grouped = {}
        for complaint in db.scalars(query):
            week_start = complaint.created_at.date() - timedelta(days=complaint.created_at.weekday())
            key = (
                complaint.category.value,
                week_start.isoformat(),
                round(complaint.latitude, 2),
                round(complaint.longitude, 2),
            )
            group = grouped.setdefault(key, {"count": 0, "latitude": 0.0, "longitude": 0.0})
            group["count"] += 1
            group["latitude"] += complaint.latitude
            group["longitude"] += complaint.longitude
        hotspots = [{
            "category": category,
            "time_bucket": time_bucket,
            "complaint_count": group["count"],
            "latitude": round(group["latitude"] / group["count"], 6),
            "longitude": round(group["longitude"] / group["count"], 6),
        } for (category, time_bucket, _, _), group in grouped.items()
            if group["count"] >= min_complaints]
        hotspots.sort(key=lambda item: (item["complaint_count"], item["time_bucket"]), reverse=True)
        method = "coordinate_grid_fallback"
    return {
        "days": days,
        "radius_meters": radius_meters,
        "minimum_complaints": min_complaints,
        "method": method,
        "count": len(hotspots),
        "hotspots": hotspots,
    }
