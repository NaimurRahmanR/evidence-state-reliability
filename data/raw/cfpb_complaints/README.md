# Local CFPB complaint raw-data folder

This folder is for local-only CFPB Consumer Complaint Database exports used by Pilot 05.

Raw CFPB complaint files must not be committed.

The folder-level `.gitignore` ignores everything in this folder except:
- README.md
- .gitignore

Allowed local-only examples:
- cfpb_complaints_filtered_raw.csv
- cfpb_complaints_filtered_raw.json
- cfpb_complaints_filtered_raw.xlsx
- cfpb_complaints_filtered_raw.zip

Do not commit:
- raw CFPB complaint CSV files
- raw CFPB complaint JSON files
- raw CFPB complaint XLS/XLSX files
- raw ZIP exports
- raw row-level records
- raw full complaint narratives
- API/download cache files
- secrets
- .env files

Committed Pilot 05 outputs must be sanitized aggregate outputs only, such as:
- dataset audit summaries
- column inventory
- missingness summaries
- target distribution summaries
- sensitive/claim-risk inventory
- temporal field audit
- leakage-risk notes
- validation manifests

No model API calls are approved by this folder.
