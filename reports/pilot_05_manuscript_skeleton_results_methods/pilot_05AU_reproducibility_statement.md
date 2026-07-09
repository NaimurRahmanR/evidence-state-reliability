# Pilot 05AU Reproducibility Statement

## Repository checkpoint

- latest_commit: `725c8dd Add Pilot 05 repo validation audit`
- latest_hash: `725c8dd`
- latest_subject: `Add Pilot 05 repo validation audit`
- origin_main_alignment: `0 behind, 0 ahead`

## Source artifacts

05AU is derived from committed 05AR, 05AS, and 05AT outputs only.

### 05AR

05AR provides scaled results interpretation outputs, including headline empirical findings, main results tables, parser-versus-evidence-state divergence, audit/escalation interpretation, cascade-failure interpretation, failure-family interpretation, claim boundaries, limitations, figure specifications, and metric validation.

### 05AS

05AS provides paper-ready tables, figure data, four committed figure PNGs, claim-boundary tables, limitations, metric-validation summaries, caption packs, table packs, and paper-asset reporting.

### 05AT

05AT provides the repo-wide validation and reproducibility audit, including committed file contracts, manifest safety checks, operation-aware script safety scanning, forbidden-file audit, figure-integrity audit, input-index validation, and claim-boundary audit.

## Safety boundary

05AU made:

- no API/model calls;
- no `.env` reads;
- no raw prompt/response access;
- no raw CFPB access;
- no JSONL writing.

## Reproduction boundary

05AU is a synthesis layer. It does not regenerate the empirical run. It organizes committed outputs into manuscript-ready structure and wording.
