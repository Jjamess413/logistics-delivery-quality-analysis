# Acceptance cases and execution status

Automated checks below were executed against the delivered source and browser dashboard. The native Desktop rows remain pending. This is analyst-prepared UAT material, not a claim of business stakeholder sign-off.

| ID | Scenario | Expected result | Execution / evidence |
| --- | --- | --- | --- |
| UAT-01 | Full cohort, no filters | 86,288 orders; 83,696 eligible; 5,930 late; 92.91% on time; P90 24.05 days | PASS: pipeline + browser control checks |
| UAT-02 | Actual delivery is 23:59:59 on the estimated calendar date | Eligible and zero days late under the default convention | PASS: hand-calculated boundary test |
| UAT-03 | Delivered status with missing actual delivery timestamp | Excluded from service denominator; retained in order coverage and defect review | PASS: unit rule test; five real missing-date cases reconcile |
| UAT-04 | Two items and two reviews belong to one order | One order fact; item amounts retained once; latest valid response selected once | PASS: SQL fixture tests; actual child totals reconcile |
| UAT-05 | Handover occurs before purchase but actual delivery is valid | Delivery outcome stays eligible; stage durations are null | PASS: SQL fixture test |
| UAT-06 | Select March 2018, RJ and a category | Rates and counts match an independent SQL selection | PASS: browser runtime checks |
| UAT-07 | Select a state/category combination with no orders | Count zero; rates and quantiles show an unavailable marker rather than a fabricated zero | PASS: browser empty-selection check |
| UAT-08 | Raise the state-pair minimum eligible count to 5,000 | Every displayed group satisfies n >= 5,000; multi-seller orders are excluded | PASS: browser threshold and lane checks |
| UAT-09 | Compare low scores across late bands | Correct reviewed-eligible denominator and latest-response coverage shown | PASS: SQL outputs + browser reconciliation |
| UAT-10 | Search a case, inspect timeline, export and close by keyboard | Matching case, historical scope, selected export, accessible close behaviour | PASS: browser search/detail/export/Escape checks |
| UAT-11 | Open and refresh native project in Power BI Desktop | Three tabs load; overview matches UAT-01; stage means approximately 3.28 and 9.89 days | PENDING: owner Windows execution and actual screenshot |
| UAT-12 | Test native slicers, page tables and reset | Selected counts match SQL; rates use selected denominators; fixed top-eight-state rank is labelled | PENDING: native interaction review |

Browser runtime verification also checks pagination, absent search results, mobile width, JavaScript errors, no external runtime requests and CSV context labels. The checked-in browser screenshots are captured from the running HTML application.

Owner Desktop evidence should be recorded with the tested page, filter state, observed numbers and actual screenshot. Source schema validation is never substituted for native execution.
