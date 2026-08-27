# PETi Customer SLOs

All measurements are aggregate, payload-free, and scoped by environment/service.
The error budget is consumed by failed requests, not by disabled optional AI.

| SLO | Target | Window | Exclusions |
|---|---:|---:|---|
| Authenticated API availability | 99.5% | 30 days | approved maintenance |
| Authenticated API p95 latency | < 800 ms | 30 days | media upload bytes |
| Media finalize success | 99.0% | 30 days | invalid client media |
| Existing-result read availability | 99.9% | 30 days | none |
| Analysis completion | 99.0% within 15 min | 30 days | provider outage after kill-switch |
| Notification delivery enqueue | 99.0% | 30 days | OS permission denied |
| Weekly report generation | 99.0% within 10 min | 30 days | no source activity |
| Export readiness | 99.0% within 15 min | 30 days | invalid request |
| Deletion completion | 99.9% with zero residuals | 30 days | failed verification remains NO-GO |

Canonical history, safety guidance, export, and deletion remain available when
optional AI or provider services are degraded.
