# Review Simulation Agent

Simulates how a **user persona** would rate and review healthcare products and services.

## Hackathon Task A

Produces realistic:
- **Star ratings** (1–5)
- **Review text** in the persona's voice
- **Behavioural reasoning** explaining the rating

## Inputs

| Field | Required | Description |
|-------|----------|-------------|
| `persona_name` | Optional* | Persona to simulate |
| `persona_reasoning` | Optional | Inline persona context |
| `product_description` | Optional** | Product being reviewed |
| `service_description` | Optional** | Service being reviewed |
| `target_type` | Yes (default: healthcare_apps) | Category of offering |

\*Uses latest stored persona if omitted.  
\*\*At least one of product or service description required.

## Target Types

| Type | Examples |
|------|----------|
| `healthcare_apps` | Sleep trackers, symptom diaries |
| `wellness_products` | Supplements, wearables |
| `telemedicine_services` | Video consult platforms |
| `pharmacies` | Online/offline pharmacy services |
| `fitness_programs` | Workout apps, gym programs |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/simulation/review` | Run simulation |
| GET | `/api/v1/simulation/history` | History (`?target_type=`) |
| GET | `/api/v1/simulation/current` | Latest simulation |

## Response

```json
{
  "rating": 4,
  "review": "This sleep app helped me notice my late-night habits...",
  "reasoning": "As a Sleep-Deprived Student, practical tools score well...",
  "persona_name": "Sleep-Deprived Student",
  "target_type": "healthcare_apps",
  "reasoning_trace": {
    "steps": [
      "Loaded user persona context",
      "Identified target type: healthcare_apps",
      "Analyzed product description",
      "Applied behavioural reasoning for rating expectations",
      "Simulated realistic review language",
      "Generated rating, review, and behavioural reasoning"
    ]
  }
}
```

## Examples

**Healthcare app**

```bash
curl -X POST http://localhost:8000/api/v1/simulation/review \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "persona_name": "Sleep Deprived Student",
    "product_description": "Sleep tracking app with smart alarms",
    "target_type": "healthcare_apps"
  }'
```

**Telemedicine service**

```bash
curl -X POST http://localhost:8000/api/v1/simulation/review \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "persona_name": "Busy Professional",
    "service_description": "24/7 video doctor consultations",
    "target_type": "telemedicine_services"
  }'
```

## Migration

```bash
alembic upgrade head  # revision 006
```
