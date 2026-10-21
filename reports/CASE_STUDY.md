# Delivery promises to an investigation plan

James You · Personal portfolio · October 2026

## Business problem

Operations needs a defensible way to prioritise delivery review effort. A headline on-time percentage hides the difference between service exceptions, incomplete records, different promise windows and low-volume groups. The proposed users are a reporting analyst, fulfilment lead, logistics operations and customer experience lead. These roles are recommendations, not interviewed stakeholders.

## Scope and method

The source is Olist's public Brazilian marketplace data. The project selects 86,288 orders purchased from January 2017 through June 2018, using final recorded outcomes. This earlier cohort avoids the latest purchase months; it does not create an as-of snapshot or eliminate every source-quality risk.

One order is one fact row. Item rows are aggregated before joining; the latest valid review response is selected deterministically. Multi-seller orders stay in overall service metrics, while single-seller state-pair comparisons have a narrower population. There are 83,696 eligible delivered orders, 83,593 with a complete valid two-stage timeline, and 83,112 eligible orders with a valid selected review.

## Evidence and proposed decisions

| Finding | Evidence | Proposed action and owner |
| --- | --- | --- |
| Service baseline needs an explicit denominator | 77,766 on-time / 83,696 eligible deliveries = 92.91%; 2,592 cohort orders are outside that denominator | Reporting analyst confirms the metric contract and keeps exclusions visible |
| Volume and failure rate tell different stories | RJ: 1,436 late / 10,891 eligible, 13.19%; SP: 1,432 / 34,523, 4.15% | Review RJ's higher relative risk alongside SP's large service volume; avoid choosing groups by percentage alone |
| A single-seller state pair is a useful starting group | SP → RJ: 1,120 late / 7,201 eligible, 15.55%, reference interval about 14.7–16.4% | Fulfilment and logistics leads inspect event/reason records for this group and compare product/seller/promise mix |
| Long delays coincide with much poorer feedback | 2,124 low scores / 2,659 reviewed orders over seven days late = 79.88%, versus 7,315 / 77,319 on-time reviewed orders = 9.46% | Customer experience reviews promise wording and exception communications; investigate other experience factors before claiming a causal effect |
| Date interpretation materially changes the headline | Literal timestamp comparison yields 6,886 late orders; calendar-date comparison yields 5,930. The 956-record difference is same-date delivery after midnight | Business owner verifies whether the promise is a date or a timed contractual deadline |
| Speed and promise generosity must be reviewed together | March 2018 has 81.04% on-time delivery; the monthly report also shows actual elapsed days and estimated promise lead time | Review comparable cohorts and event context; do not infer an intervention or carrier failure from a monthly change |

## Proposed review

Start with source and metric reconciliation, then review the highest late-volume groups meeting the stated sample threshold. Obtain parcel identifiers, seller-to-parcel mapping, carrier scan events, reason codes and the agreed promise definition. Record the evidence, assigned owner, proposed action, due date and closure criteria.

A small future pilot should compare like-for-like cohorts and track eligible-order volumes, on-time rate, P90 duration, timestamp completeness, review closure and selected customer-feedback measures. Seasonality, product mix, seller mix and promise-window changes require review before attributing any change to the pilot.

## Delivered evidence and limits

The project supplies SQL/Python source, eleven analytical queries, an offline dashboard, a native Power BI source project, requirements, UAT and a proposed action-register template. Pipeline, business-rule, browser and native-format validations are recorded separately. Actual Windows Power BI refresh and interactions remain to be confirmed.

There is no reliable carrier identity, parcel damage/loss event, cost baseline or implemented intervention in the chosen model. A cancelled or unavailable order is not labelled as a lost parcel. Extreme but chronologically possible durations are retained for source verification. Review associations are observational; no savings, operational improvement or approved stakeholder decision is claimed.

Development was AI-assisted. This is a public-data portfolio case, separate from employment achievements.
