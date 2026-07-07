# Local HMDA raw-data folder

This folder is for local-only HMDA raw files used by Pilot 05.

Raw HMDA files must not be committed.

The folder-level `.gitignore` ignores everything in this folder except:
- README.md
- .gitignore

Allowed local-only examples:
- hmda_2025_option_b_filtered_raw.csv
- hmda_2025_option_b_filtered_raw.zip

Do not commit:
- raw HMDA CSV files
- raw HMDA ZIP files
- raw HMDA parquet files
- raw HMDA JSON/JSONL files
- browser exports
- row-level raw extracts
- API/download cache files
- secrets
- .env files

Committed Pilot 05 outputs must be sanitized aggregate outputs only, such as:
- dataset audit summaries
- column inventory
- missingness summaries
- target distribution summaries
- sensitive-field inventory
- leakage-risk notes
- validation manifests

No model API calls are approved by this folder.
