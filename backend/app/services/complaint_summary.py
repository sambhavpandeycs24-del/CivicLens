import re
from typing import Any

from app.models.complaint import ComplaintCategory
from app.services.ai_assistant import priority_suggestion


RECOMMENDED_ACTIONS = {
    ComplaintCategory.POTHOLE: "Inspect the road surface and schedule a safe repair.",
    ComplaintCategory.GARBAGE: "Arrange collection and inspect the site for repeat dumping.",
    ComplaintCategory.STREETLIGHT: "Inspect the lighting equipment and restore safe illumination.",
    ComplaintCategory.WATER_LEAKAGE: "Dispatch a maintenance team to inspect and stop the leak.",
    ComplaintCategory.DRAINAGE: "Inspect the drain and clear any blockage or overflow.",
    ComplaintCategory.OTHER: "Review the report and route it to the appropriate civic team.",
}


def summarize_complaint(
    title: str, description: str, address: str, category: ComplaintCategory, priority: str
) -> dict[str, Any]:
    sentences = [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", description) if sentence.strip()]
    details = " ".join(sentences[:2])
    if len(details) > 240:
        details = details[:237].rsplit(" ", 1)[0] + "..."
    issue = title.strip()
    summary = f"{issue}: {details}" if details else issue
    inferred_priority, _, _ = priority_suggestion(title, description)
    urgency = f"{priority.capitalize()} priority supplied by the complaint workflow."
    if inferred_priority in {"high", "urgent"} and inferred_priority != priority:
        urgency += f" Text indicators also suggest {inferred_priority} priority; authority review is recommended."
    return {
        "summary": summary,
        "issue": issue,
        "location": address.strip(),
        "urgency": urgency,
        "recommended_action": RECOMMENDED_ACTIONS[category],
        "generated_by": "extractive_rules",
    }
