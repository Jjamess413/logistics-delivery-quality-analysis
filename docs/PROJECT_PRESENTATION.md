# Interview presentation

This is a personal public-data project, separate from employment experience. Source development was AI-assisted. Explain your own review, validation and understanding accurately.

## Project description

Built a public-data delivery-quality case study using SQL, Python and Power BI, covering 86,288 historical orders. Defined an eligible-delivery denominator, investigated delay concentration and customer-feedback associations, and prepared requirements, acceptance cases and a proposed operational review process.

The native three-page report is authored and structurally checked; Windows Desktop refresh is still pending. The offline interactive browser report has nineteen passing runtime checks.

## Sixty-second introduction

I analysed Olist's public marketplace data to explore how an operations team could prioritise delivery investigations. I selected an earlier purchase cohort and built one row per order, aggregating items and selecting a single valid review before joining.

The on-time baseline was 92.91% across 83,696 eligible delivered orders. A state-pair comparison identified SP to RJ as a useful high-volume investigation group, while the review analysis showed a strong association between long delays and low scores.

One important analytical decision was how to interpret the estimated delivery date. Comparing literal timestamps would classify an additional 956 same-day deliveries as late. I documented both results and the need to confirm the business rule.

The deliverable includes a review dashboard, requirements, acceptance tests and a proposed action workflow. It identifies evidence to collect next; it does not claim carrier responsibility or an implemented improvement.

## Likely discussion

| Question | Evidence to explain |
| --- | --- |
| What is one row? | One cohort order; pre-aggregated items and selected review |
| Why do order and eligible counts differ? | Final statuses, missing dates and chronology rules |
| Why not compare all state-pair percentages? | Small denominators, seller mix and minimum count |
| Does the longest stage identify the responsible team? | Elapsed time locates review effort; event/reason evidence is still required |
| Does a late delivery cause a low score? | The evidence is observational and confounded by other experience factors |
| How would this become a business process? | Requirement traceability, event validation, ownership, pilot and follow-up measures |
| What remains to validate? | Windows Desktop execution, native interactions, actual stakeholder requirements and operational data |
