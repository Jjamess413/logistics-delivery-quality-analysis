# Native Power BI report

Entry point: LogisticsDelivery.pbip. The report has three authored pages, 44 visual containers, a four-table import model, three single-direction relationships and 24 explicit DAX measures.

The shell was scaffolded with Microsoft report-authoring CLI 0.5.0. It includes content version 2.0.0, report platform metadata and the registered Fluent2-CY26SU10 base theme. MICROSOFT_LICENSE and MICROSOFT_NOTICE are retained. Dropdown slicers have explicit mode, padding and an 80px height.

The model reads fact_delivery.csv, dim_date.csv, dim_state.csv and dim_category.csv from pDataFolder. The root OPEN_POWERBI.cmd launcher configures this parameter for the extracted package. Empty CSV cells become null before type conversion.

## Scope and validation

Public JSON/schema, resource, page, field-reference and CSV checks pass. Official CLI offline conformance passes with zero diagnostics. These checks do not execute the Power BI DAX engine or render Desktop visuals.

**Windows Desktop refresh, interactions and actual screenshots are pending.** Use the root START_HERE.md for control totals. The browser dashboard is a separately validated deliverable.

The native top-eight-state chart uses a fixed full-cohort late-volume rank, with selected-context counts. The browser re-ranks states within the selection. Both label their scope. Category rates display only with at least 100 eligible orders. Static baseline notes are labelled as baseline examples.

Schema checks: python scripts/validate_powerbi.py with the optional jsonschema dependency. CLI checks: powerbi-report-author validate powerbi/LogisticsDelivery.pbip --no-schema. Obtain the official CLI through @microsoft/powerbi-report-authoring-cli; Node.js 20+ is required for development validation only.
