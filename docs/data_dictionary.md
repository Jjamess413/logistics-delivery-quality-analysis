# Data dictionary

## Order-grain fact: fact_delivery.csv

| Field | Meaning |
| --- | --- |
| case_code | Stable analytical order reference; not the source order/customer identifier |
| purchase_date / purchase_month | Cohort and time-filter key |
| customer_state | Destination state from the customer lookup |
| origin_state | Single seller's recorded state; MULTI or UNKNOWN otherwise |
| route_type | Same state, Cross state, Multiple sellers or Unknown origin |
| category | One English category, Multiple categories or Unknown category |
| order_status | Final recorded source order status |
| item_count / seller_count | Aggregated child counts at one-order grain |
| eligible_flag / eligibility_reason | Delivery-metric inclusion and explicit reason |
| delivered_flag | Recorded status delivered, irrespective of missing required timestamps |
| late_flag / late_days | Calendar-date late indicator and days beyond estimate; null days outside eligibility |
| severe_late_flag | Eligible lateness greater than seven calendar days |
| delivery_seconds | Valid purchase-to-delivery elapsed seconds |
| processing_seconds / post_handover_seconds | Joint-valid timeline elapsed components; null when stage chronology is invalid |
| stage_valid_flag | Eligible and purchase <= handover <= delivery |
| review_score / valid_review_count | Selected latest valid score and available valid response count |
| reviewed_eligible_flag / poor_review_flag | Explicit review denominators and score 1–2 indicator |
| late_band | On time, 1–7 days late, Over 7 days late, Not eligible |
| review_priority / priority_rank | Historical review categorisation, not a current ticket status |
| merchandise_cents / freight_cents | Aggregated source amounts scaled by 100 for join reconciliation; not carrier cost or profit |

## Dimensions and lineage

- DimDate: one row per cohort purchase date, 546 rows. Connected to the fact purchase date.
- DimState: one row per destination state, 27 rows; includes full-cohort late-volume rank for the explicitly labelled native top-eight visual.
- DimCategory: one row per order category, 73 rows; display label expands underscores.
- SQL staging: stg_orders, stg_items and stg_reviews use analytical case codes and pre-aggregation views. Raw personal geography and free review text are not staged.
- Browser model: compact anonymised order facts; source IDs, postcode/city and review text are omitted. Promise days and timestamp arithmetic are display encodings for source wall-clock values, not an asserted UTC source timezone.

Raw publisher headers, file hashes and source URL are retained in the source manifest and configuration. The derived tables, CSV summaries and browser report follow the dataset's CC BY-NC-SA 4.0 terms.
