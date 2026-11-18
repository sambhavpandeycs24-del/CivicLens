# Phase 3 — AI Intelligence Layer

## Goal
Add explainable AI-assisted suggestions to help organise civic complaints. The current implementation is a transparent rules-based baseline, not a trained machine-learning model.

## Features in this phase
- Text-keyword category suggestion for pothole, garbage, streetlight, water leakage and drainage.
- Explainable priority suggestion (low/medium/high/urgent) based on configured safety and impact terms.
- Similar-complaint candidate search using text similarity and (when coordinates are supplied) a 500-metre distance check.
- Human-review notice in every AI response.

## API
`POST /api/v1/ai/analyze` (authenticated)

Example body:
```json
{
  "title": "Garbage pile near school",
  "description": "Large garbage dump and bad smell near the school gate",
  "category": "garbage",
  "latitude": 27.4924,
  "longitude": 77.6737
}
```

The response includes suggested category, confidence, reason, suggested priority, score, reasons and duplicate candidates.

## Important limitations
- Rules and thresholds are an initial baseline, not a trained model and not validated against a labelled dataset.
- Keyword matches can be wrong, incomplete or biased by language and spelling.
- Similarity is a candidate signal, not proof that two reports are duplicates.
- Duplicate search examines at most 300 recent non-rejected complaints; without coordinates it relies on text similarity only.
- Priority is not a safety certification. Human authorities must review all suggestions.
- The AI endpoint does not automatically alter a complaint's saved category or priority.
- No external AI API or paid service is required.

## Tests
Run from `backend/`:
```bash
pytest -q
```
