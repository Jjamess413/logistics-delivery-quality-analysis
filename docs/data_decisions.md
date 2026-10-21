# Data decisions and reconciliation

## Publisher and cohort

The source archive is downloaded directly from Olist's Kaggle public dataset endpoint, with archive and member hashes recorded in reports/source_manifest.json. The archive includes nine CSVs; seven selected files support this model. Geolocation and payment tables are not required.

There are 99,441 source orders. The selected earlier purchase cohort contains 86,288; 13,153 are outside its date range. Cohort selection is by purchase timestamp, not delivery month. Final recorded statuses and deliveries are used, including later completion dates through October 2018. There is no source observation timestamp suitable for reconstructing a live backlog.

## Grain and join controls

- The orders, customer key, product key, seller key and category-translation key must be unique before joining.
- The order/item pair must be unique. Each order can contain several item and review rows.
- Items are aggregated to order grain before their join. Monetary values are converted to integer minor units for a reconciliation only; they are not a claimed logistics cost measure.
- Reviews with scores outside 1–5 are not selected. Valid reviews are ranked by answered timestamp descending, created timestamp descending and source review key descending. One response is selected per order; 521 cohort orders have more than one valid response.
- Child totals and order counts reconcile after joining. An executable SQL query contrasts the naive join with the one-row model.

## Exclusions and retained uncertainty

83,701 cohort orders have recorded delivered status. Five lack the delivery/promise information needed for the metric, leaving 83,696 eligible. Another 2,587 have other recorded statuses. They are retained in the cohort reconciliation and are not classified as parcel loss, damage or on-time delivery.

The full eligible cohort is used for delivery outcomes. Stage comparisons have a narrower 83,593-record joint valid timestamp cohort; its records satisfy purchase <= handover <= delivery. An invalid handover does not invalidate a separately valid delivery outcome.

Chronologically possible long durations remain visible as investigation candidates. Neither an operational exception nor a data-entry error can be proven from duration alone. Promise timestamps occur at date boundaries; the analytical calendar-date rule and literal-timestamp sensitivity are both documented.

## Geography, categories and source fields

Customer state is the destination grouping. Seller state is an origin proxy for single-seller orders; it is not a verified warehouse, route or carrier identity. The 1,065 multi-seller orders remain in overall metrics and are excluded from single-seller state-pair comparisons.

Orders containing more than one translated product category are labelled Multiple categories. Missing categories are labelled Unknown category. An order is never duplicated across category groups.

Customer/source order identifiers, customer city/postcode, geolocation coordinates and review text do not enter the portable fact CSV or browser model. Stable analytical case codes allow inspection. Raw source identifiers used transiently for joins are excluded from the public Git repository. The local SQLite staging review key is retained only as a deterministic review tie-breaker; it has no customer text.

## Statistical and business interpretation

Group comparisons show counts and use a minimum eligible-order threshold. Reference intervals are descriptive under their stated assumptions. The complete public history is not a random sample of today's market, and observations can cluster by seller or time.

Customer ratings are associated with many parts of the experience. This model does not identify the cause of a review score, estimate a treatment effect or evaluate an implemented improvement.
