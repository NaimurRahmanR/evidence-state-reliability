# Pilot 03 Anthropic validity-aware run selector

Generated at UTC: 2026-07-02T03:13:15+00:00

## Scope

Validity-aware Anthropic run selector for Pilot 03. This command makes no real API calls. It selects completed local run directories for aggregation and avoids known schema-invalid single-chain runs when a valid replacement exists.

Selector status: **PASS**

## Summary

- Baseline run dirs from planner: 46
- Candidate run dirs found: 48
- Selected run dirs: 46
- Selected unique task-condition keys: 60
- Required task-condition keys: 60
- Missing selected valid keys: 0
- Duplicate selected keys: 0
- Replacements: 0
- Unresolved issues: 0
- Invalid selected rows: 0

## Missing selected valid keys

None.

## Replacements

None.

## Unresolved issues

None.

## Outputs

- selected_run_dirs_txt: `reports\pilot_03_anthropic_validity_selector\selected_run_dirs.txt`
- selector_report_md: `reports\pilot_03_anthropic_validity_selector\anthropic_validity_selector_report.md`
- candidate_rows_csv: `reports\pilot_03_anthropic_validity_selector\candidate_rows.csv`
- selection_issues_csv: `reports\pilot_03_anthropic_validity_selector\selection_issues.csv`
- manifest_json: `reports\pilot_03_anthropic_validity_selector\manifest.json`
