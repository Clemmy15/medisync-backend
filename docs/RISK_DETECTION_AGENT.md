# Risk Detection Agent

Detects health risks by analyzing user profile, persona, behavioural memory, imported context, and reported symptoms.

## Responsibilities

1. **Dangerous symptom patterns** — severity and combinations that may need urgent care
2. **Behavioural deterioration** — worsening sleep, stress, hydration, or habits over time
3. **Recurring health concerns** — repeated symptoms across memory and imports

## Risk levels

| Level | Value | When to use |
|-------|-------|-------------|
| Low | `low` | Stable or minor concerns; monitoring appropriate |
| Moderate | `moderate` | Persistent or worsening patterns; follow-up recommended |
| High | `high` | Potential emergency; urgent medical attention |

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/analysis/risk` | Run risk detection |
| GET | `/api/v1/analysis/risk/current` | Latest assessment |
| GET | `/api/v1/analysis/risk/history` | Assessment history |

## Request

```json
{
  "symptoms": ["persistent headache", "fatigue"],
  "context": "Symptoms worsening over two weeks"
}
```

Both fields are optional; the agent still analyzes stored profile, memory, and imports.

## Response

```json
{
  "risk_level": "moderate",
  "reasoning": "Dangerous symptom patterns: ... Behavioural deterioration: ... Recurring health concerns: ...",
  "recommended_action": "Schedule a primary care visit within 2 weeks; track symptoms daily.",
  "steps": [
    "Retrieved user profile",
    "Retrieved behavioural memory",
    "Retrieved imported AI context",
    "Identified dangerous symptom patterns",
    "Identified behavioural deterioration",
    "Identified recurring health concerns",
    "Assessed risk level and recommended action"
  ],
  "reasoning_trace": { "steps": ["..."] }
}
```

## Example

```bash
curl -X POST http://localhost:8000/api/v1/analysis/risk \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": ["chest tightness", "shortness of breath"],
    "context": "Started after exercise yesterday"
  }'
```

## Storage

Assessments are stored in `risk_assessments` (migration `007`). Reasoning traces use `trace_type=risk_detection`.

## Migration

```bash
alembic upgrade head  # revision 007
```
