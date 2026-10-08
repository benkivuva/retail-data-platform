# Data Quality Log

## 2026-10-08 — On-time delivery rate was always 1.0

**Symptom.** `metrics_daily.on_time_delivery_rate` returned 1.0 for every day.

**Cause.** The deliveries CTE filtered `where delivery_status = 'delivered'`,
which excluded `delivered_late` rows from the denominator. The rate was
computed as on-time / on-time, always 1.0.

**Fix.** Broadened the filter to `delivery_status in ('delivered', 'delivered_late')`
so completed-but-late deliveries count in the denominator. Added a custom test
(`assert_metrics_daily_within_bounds`) that flags days where
`deliveries_on_time > deliveries_delivered`.

**Impact.** Corrected a metric that would have misled operations. Reinforces
the value of automated tests over spot checks.

**Owner.** Analytics Engineering.