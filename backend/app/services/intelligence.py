import json
import math
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.models.complaint import Complaint, ComplaintCategory, ComplaintPriority, ComplaintStatus


def sla_target_hours(category: ComplaintCategory, priority: ComplaintPriority) -> float:
    try:
        configured = json.loads(settings.sla_target_hours_json)
    except json.JSONDecodeError as exc:
        raise ValueError("SLA_TARGET_HOURS_JSON must be a JSON object") from exc
    if not isinstance(configured, dict):
        raise ValueError("SLA_TARGET_HOURS_JSON must be a JSON object")
    keys = (
        f"{category.value}:{priority.value}",
        f"category:{category.value}",
        f"priority:{priority.value}",
    )
    target = next((configured[key] for key in keys if key in configured), None)
    if not isinstance(target, (int, float)) or isinstance(target, bool) or not math.isfinite(target) or target <= 0:
        raise ValueError(f"No valid SLA target is configured for {category.value}/{priority.value}")
    return float(target)


def complaint_sla(complaint: Complaint, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    created_at = complaint.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    elapsed_hours = max(0.0, (now - created_at).total_seconds() / 3600)
    target = sla_target_hours(complaint.category, complaint.priority)
    if complaint.status == ComplaintStatus.RESOLVED:
        resolved_at = complaint.resolved_at
        if resolved_at and resolved_at.tzinfo is None:
            resolved_at = resolved_at.replace(tzinfo=timezone.utc)
        if resolved_at:
            resolution_hours = max(0.0, (resolved_at - created_at).total_seconds() / 3600)
            return {
                "risk_level": "resolved_on_time" if resolution_hours <= target else "resolved_late",
                "target_hours": target,
                "elapsed_hours": round(resolution_hours, 1),
                "explanation": f"Resolved in {resolution_hours:.1f} hours against a {target:g}-hour target.",
            }
        return {
            "risk_level": "resolution_time_unavailable",
            "target_hours": target,
            "elapsed_hours": None,
            "explanation": "No resolution timestamp was recorded; this historical record is excluded from SLA timing.",
        }
    if complaint.status == ComplaintStatus.REJECTED:
        return {
            "risk_level": "not_applicable",
            "target_hours": target,
            "elapsed_hours": round(elapsed_hours, 1),
            "explanation": "Rejected complaints are excluded from resolution SLA risk.",
        }
    if elapsed_hours >= target:
        level = "overdue"
        explanation = f"Past the {target:g}-hour resolution target."
    elif elapsed_hours >= target * 0.8:
        level = "at_risk"
        explanation = f"{elapsed_hours:.1f} of {target:g} target hours elapsed; less than 20% remains."
    else:
        level = "on_track"
        explanation = f"{elapsed_hours:.1f} of {target:g} target hours elapsed."
    return {
        "risk_level": level,
        "target_hours": target,
        "elapsed_hours": round(elapsed_hours, 1),
        "explanation": explanation,
    }
