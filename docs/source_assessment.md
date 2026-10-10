### Source: Ops Weekly Tracker (Google Sheet)

**Type:** Google Sheet, human-edited by the Operations team
**Owner:** Operations
**Update frequency:** Weekly (Monday mornings, informally)
**Volume:** ~250 rows across 3 tabs
**Retention at source:** Indefinite

**Tabs and grain:**

| Tab | Grain | Key |
|---|---|---|
| Zone Master | one row per delivery zone | Zone_ID |
| Driver Roster | one row per driver-day assignment | (Date, driver_name, Zone) |
| Vehicle Log | one row per service event | Vehicle_Reg + Last_Service |

**Known quality issues:**

- Mixed-case and inconsistent county spelling (`Nairobi`, `nairobi`, `NBO`)
- Boolean column (`Active?`) with 5 representations of "yes" plus blanks
- Dates in 3 formats within the same column
- Phone numbers in 3 formats plus an invalid prefix (`+2540`)
- Free-text vehicle descriptions that should be an enum
- Duplicate rows (both intentional and accidental)
- Blank rows used as section separators
- One cell contains a comment (`check with Peter - is Zone 5 still active?`)
- One duplicate `zone_id` (`Z028`) with two spellings

**Handling in the pipeline:**

- All columns loaded as STRING into `raw.ops_*`
- Cleaning happens in `stg_ops_zone_master`, `stg_ops_driver_roster`, `stg_ops_vehicle_log`
- Unknown zones flagged by `zone_unknown_flag` in the roster
- Duplicates deduplicated using `row_number()` in staging

**Access and security:**

- Sheet shared with the `dbt-runner` service account as Viewer
- Loader authenticates via the same service account used for BigQuery
- No PII in the sheet beyond driver names and phone numbers, which are internal operational data

**Integration plan:**

- **Load pattern:** Full replace each run (`WRITE_TRUNCATE`)
- **Destination:** `raw.ops_zone_master`, `raw.ops_driver_roster`, `raw.ops_vehicle_log`
- **Schedule:** Daily via Dagster (in progress)
- **Backfill:** Re-run the loader; the sheet is the source of truth