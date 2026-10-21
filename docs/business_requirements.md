# Business requirements and traceability

This is an analyst-proposed requirements baseline for a public-data portfolio case. No real stakeholder interviews, approvals or production deployment are represented.

## Users and decision

The proposed reporting analyst owns reconciliation and metric definitions. A fulfilment lead and logistics operations representative validate source event evidence. A customer experience lead reviews promise wording and exception communication. A business sponsor would approve any proposed pilot and target.

The immediate decision is **which historical delivery groups merit investigation and what additional evidence is required**. Automatically assigning blame, placing carrier penalties or declaring realised improvement is outside scope.

| ID | Requirement | Rationale | Implementation | Acceptance evidence |
| --- | --- | --- | --- | --- |
| BR-01 | Maintain one fact row per cohort order | Multiple items/reviews must not multiply order KPIs | SQL item rollup, latest-review window and unique fact key | UAT-01, UAT-04, pipeline reconciliation |
| BR-02 | Publish denominator and exclusions with service rates | Missing and other-status orders cannot silently become successful deliveries | Eligibility reason, coverage strip, reconciliation CSV | UAT-01, UAT-03, UAT-07 |
| BR-03 | Define the delivery-promise boundary and show its sensitivity | Estimated midnight values may represent a date rather than a timed deadline | Calendar-date rule, literal-timestamp comparison query | UAT-02, SQL query 10 |
| BR-04 | Prioritise groups with counts, rates and minimum sample size | One late order in a tiny group can mislead percentage rankings | State volume table, single-seller state-pair review, reference intervals | UAT-06, UAT-08 |
| BR-05 | Compare stages on the same valid chronology population | Different timestamp coverage creates misleading mean-stage comparisons | Joint stage flag and explicit coverage | UAT-05, SQL query 5 |
| BR-06 | Describe review associations with coverage and one selected response | Multiple/missing reviews and confounding affect interpretation | Latest valid review, reviewed denominator, association notes | UAT-04, UAT-09 |
| BR-07 | Support traceable historical case review and proposed follow-up | A dashboard should lead to an evidence request and accountable action | Case detail, export, workflow and action-register template | UAT-10, proposed register |
| BR-08 | Make the analysis reproducible and its limits visible | Reviewers need lineage and a clear evidence boundary | Source hashes, SQL, tests, KPI contract and native-status record | UAT-11, UAT-12, validation reports |

## Proposed operational acceptance

Before a business uses this workflow operationally, its sponsor should confirm the promise convention, an observation date, ownership, scan-event quality, parcel/seller mapping and reason taxonomy. Agree the review threshold and escalation criteria. Pilot targets and due dates remain blank in the proposed register until those decisions are made.

Success measures should include completeness of required events, percentage of reviews closed with evidence, eligible-order volume, on-time rate, P90 duration and feedback coverage. An outcome comparison requires similar cohorts, an agreed baseline and investigation of mix/promise changes.
