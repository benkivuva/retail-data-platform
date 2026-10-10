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

## 2026-10-10 — Duplicate zone_id in ops zone master

**Symptom.** `unique_stg_ops_zone_master_zone_id` failed: 1 duplicate row.

**Cause.** The ops team's Google Sheet contains `Z028` twice with two different
spellings of the same zone name (`Kileleshwa` and `Kileleswa`). This is a
source-side data entry error, not a pipeline bug.

**Fix.** Added a deduplication step in `stg_ops_zone_master.sql` using
`row_number()` partitioned by `zone_id`, ordered by completeness of fields
and then alphabetically by name. The unique test remains in place and now
passes. The source-side duplicate was reported to the ops team owner for
correction at the point of entry.

**Impact.** Prevents downstream joins (`dim_delivery_zones`, fact joins) from
duplicating rows. Reinforces the pattern: tests catch the issue, staging
handles it defensively, and the source owner is notified.

**Owner.** Analytics Engineering.