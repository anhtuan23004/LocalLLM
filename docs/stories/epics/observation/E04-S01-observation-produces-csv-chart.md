# E04-S01 Observation produces CSV + chart

## Status

implemented

## Lane

normal

## Product Contract

Observation batch dashboard generates CSV summary and a latency chart.

## Relevant Product Docs

- `docs/product/overview.md`

## Acceptance Criteria

- `observation` compose profile `batch` runs successfully.
- Generates `metrics_summary.csv` and `latency_chart.png` in `observation/dashboards/`.

## Design Notes

- Commands: `docker compose --profile batch run --rm observation`

## Validation

| Layer | Expected proof |
| --- | --- |
| Unit | |
| Integration | container exits 0 and creates CSV and PNG |
| E2E | |
| Platform | |
| Release | |

## Harness Delta

N/A

## Evidence

Ran:
```
cd observation
docker compose --profile batch run --rm observation
```
Output:
```
Summary saved to /app/dashboards/metrics_summary.csv
Chart saved to /app/dashboards/latency_chart.png
```
CSV and PNG correctly written in `observation/dashboards/`.
