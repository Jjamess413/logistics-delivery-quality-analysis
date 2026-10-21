# Offline browser dashboard

Open index.html in a browser. The self-contained file embeds a compact one-order model without source customer/order/seller identifiers, free review text or fine geography.

Pages: Service overview, Delay investigation, Review & actions, Definitions & evidence. Global month/state/category/route filters recompute rates from selected counts and recompute P90 from selected eligible durations. The state-pair review excludes multi-seller orders and supports a minimum eligible-order threshold. Historical case search, pagination, timeline detail, keyboard close and filtered CSV export are implemented.

The nineteen browser checks are recorded in [browser_validation.json](../reports/browser_validation.json). The numerical filter checks use independent SQLite queries. The three PNGs in screenshots are actual browser captures; the native Power BI report has a separate validation boundary.

To rebuild: python scripts/build.py, then python scripts/build_dashboard.py. Optional runtime QA requires Node.js and Playwright. Run node scripts/verify_dashboard.cjs after installing a Playwright browser, or set PORTFOLIO_CHROMIUM_PATH to an available Chromium executable. This development dependency is not needed to open the delivered HTML.

Browser content derives from Olist data under CC BY-NC-SA 4.0. See the root attribution file.
