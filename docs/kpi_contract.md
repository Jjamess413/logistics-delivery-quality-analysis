# KPI contract

All percentages are recomputed from their component counts under the current filter. State/category percentages are never averaged to obtain an overall rate.

| Metric | Numerator / calculation | Denominator / population | Boundary |
| --- | --- | --- | --- |
| Cohort orders | Count of order-grain facts | Purchased 2017-01-01 <= timestamp < 2018-07-01 | Final recorded outcomes, not an observation-date snapshot |
| Eligible deliveries | Recorded delivered status; known actual/estimated/purchase dates; actual >= purchase; estimated calendar date >= purchase calendar date | Cohort orders | Missing/contradictory delivery records excluded explicitly |
| On-time delivery % | Eligible orders with actual delivery calendar date <= estimated delivery calendar date | Eligible deliveries | Estimated date is a documented proxy promise; business contract is unavailable |
| Late % | Eligible orders with actual date > estimated date | Eligible deliveries | Same-day after midnight is on time under this convention |
| Severe late orders | Calendar days late > 7 | Eligible deliveries | Seven exactly belongs to the 1–7 band |
| Eligibility coverage | Eligible deliveries | All cohort orders | Completeness measure, not a parcel-success rate |
| Median / P90 delivery days | Median / inclusive linear-interpolated 90th percentile of elapsed seconds / 86,400 | Eligible deliveries | Uses timestamp duration; differs from calendar-day lateness |
| Mean purchase-to-handover days | Mean elapsed seconds purchase → carrier handover / 86,400 | Eligible records with purchase <= handover <= delivery | Both stages share the same valid-record population |
| Mean handover-to-delivery days | Mean elapsed seconds handover → delivery / 86,400 | Same complete stage population | Does not prove carrier responsibility |
| Low-score % | Selected valid score is 1–2 | Eligible deliveries with a selected valid review | Latest answer timestamp, then creation timestamp, then review-key tie-breaker |
| Review coverage | Reviewed eligible deliveries | Eligible deliveries | Missing reviews never become zero-star scores |
| Monthly OTD change | Current on-time % minus prior month on-time % | Consecutive purchase months | Reported in percentage points, not percent growth |
| Group rate interval | Wilson 95% reference interval on late count / eligible count | Group's eligible records | Illustrative stability reference; assumes independent Bernoulli outcomes and does not adjust seller clustering/mix |

Default group-comparison threshold: **100 eligible orders**. Browser users can change it; its current value is shown. Native category comparisons display rates only at n >= 100. The native top-eight state visual uses a fixed full-cohort late-volume rank and displays selected-context late counts; the browser re-ranks states within the selection.

Durations are not clipped to produce a more attractive rate. Missing or invalid stage records do not remove an otherwise eligible order from the delivery outcome metric. All timestamps are treated as recorded, with no asserted timezone or daylight-saving correction.

No loss, damage, delivery-attempt failure, carrier SLA compliance, actual backlog, financial saving or causal improvement metric is defined because the required evidence is absent.
