# Data storage and derivation

raw/ is a local publisher download cache; it is excluded from Git and the portable bundle. processed/ contains the local SQLite model and four Power BI CSV inputs; it is excluded from Git and supplied in the portable bundle.

The source archive URL, archive/member hashes, licence and cohort are recorded in config.json and reports/source_manifest.json. The SQL model uses analytical case codes and retains one order per fact. The browser embeds a compact derived order model under the same data licence.

See docs/data_dictionary.md and docs/data_decisions.md for lineage, exclusions, join controls, review selection and the evidence boundary. Customer IDs, source order IDs, review text and fine customer geography are absent from the portable fact CSV and browser model.
