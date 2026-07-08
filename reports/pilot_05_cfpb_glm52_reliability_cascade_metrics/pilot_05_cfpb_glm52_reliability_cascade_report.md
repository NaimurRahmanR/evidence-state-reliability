# Pilot 05 CFPB GLM-5.2 Reliability Cascade Metrics (Task 05AK)

Status: PASS  
Mode: no-call sanitized analysis  
Source commit: e1f039a  
Generated UTC: 2026-07-08T22:19:01.664553+00:00  

## Input accounting

- Approved call attempts accounted for: 36/36
- Persisted sanitized execution rows analyzed: 33
- Prior attempt rows accounted separately: 3
- Parser status rows analyzed: 33
- Runner plan rows available: 36

## Parser-validity snapshot

- Persisted parser-valid rows: 17
- Persisted parser-invalid rows: 16
- Persisted parser-unknown rows: 0
- Persisted parser-valid rate: 0.515152

## Cascade-sequence snapshot

- Cascade sequence rows generated: 12
- Sequences with all known stages parser-valid: 2
- Sequences with at least one known parser-invalid stage: 9

## Safety and claim boundary

Task 05AK made no API/model calls, did not read the API key, and wrote no raw prompt, raw response, or JSONL artifact. The metrics are descriptive reliability-cascade diagnostics from a small GLM-5.2 micro-pilot. They support analysis of parser/schema validity and stage/condition patterns, not broad claims about provider reliability, deployment safety, or final decision correctness.
