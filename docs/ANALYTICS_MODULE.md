# Analytics Module

Admin-only aggregated metrics and **chart-ready** responses for dashboards (Chart.js, Recharts, etc.).

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/analytics/overview` | Platform KPIs + activity & memory charts |
| GET | `/api/v1/analytics/personas` | Persona distribution + chart |
| GET | `/api/v1/analytics/recommendations` | Recommendation stats + charts |

All routes require an **admin** JWT (`is_admin=true`).

## Metrics tracked

| Metric | Source |
|--------|--------|
| Active users | Distinct users with events/activity in last 30 days |
| Contexts imported | `context_imports` table |
| Recommendations generated | `recommendations` table |
| Reviews simulated | `review_simulations` table |
| Persona distribution | `personas` table (grouped by name) |
| Memory growth | `memories` table (daily new + cumulative series) |

## Chart format

All charts use a shared shape compatible with most chart libraries:

```json
{
  "labels": ["2026-05-10", "2026-05-11"],
  "datasets": [
    { "label": "Recommendations", "data": [2, 5] }
  ]
}
```

## Overview example

```json
{
  "metrics": {
    "active_users": 12,
    "total_users": 45,
    "contexts_imported": 28,
    "recommendations_generated": 67,
    "reviews_simulated": 34,
    "personas_generated": 52,
    "total_memories": 210,
    "memories_added_7d": 18
  },
  "activity_chart": {
    "labels": ["..."],
    "datasets": [
      { "label": "Recommendations", "data": [] },
      { "label": "Reviews simulated", "data": [] },
      { "label": "Contexts imported", "data": [] }
    ]
  },
  "memory_growth_chart": {
    "labels": ["..."],
    "datasets": [
      { "label": "New memories", "data": [] },
      { "label": "Cumulative memories", "data": [] }
    ]
  }
}
```

## Personas example

```json
{
  "total_personas": 52,
  "unique_persona_types": 5,
  "distribution": [
    { "persona_name": "Sleep-Deprived Student", "count": 20, "percentage": 38.5 }
  ],
  "chart": {
    "labels": ["Sleep-Deprived Student"],
    "datasets": [{ "label": "Persona assignments", "data": [20] }]
  }
}
```

## Recommendations example

```json
{
  "total": 67,
  "average_confidence": 0.86,
  "recent_count_7d": 12,
  "by_category": [
    { "category": "sleep_improvement", "count": 25, "percentage": 37.3 }
  ],
  "category_chart": { "labels": [], "datasets": [] },
  "daily_chart": { "labels": [], "datasets": [] }
}
```

## Architecture

```
app/analytics/
├── engine.py        # SQL aggregations + chart assembly
└── time_series.py   # Date buckets and series helpers

app/services/analytics_service.py  # Event tracking + facade
```

## Event tracking

Agents record events via `AnalyticsService.track_event()`:

- `context_imported`
- `recommendation_generated`
- `review_simulated`
- `risk_assessed`

These support **active user** counts alongside direct table aggregates.
