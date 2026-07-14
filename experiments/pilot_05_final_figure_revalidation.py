from __future__ import annotations

import csv
import hashlib
import json
import re
import struct
import subprocess
from pathlib import Path
from typing import Any

TASK_ID = "05BG"
VERSION = "05BG-INDEPENDENT-FIGURE-REVALIDATION-V1"
EXPECTED_BRANCH = "main"
EXPECTED_HEAD = "120f05840f90e05c9b7101e50ff68f9fbde588e3"
EXPECTED_HEAD_MESSAGE = "Add Pilot 05 final figure repair"

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = Path(__file__).resolve()
SCRIPT_REL = "experiments/pilot_05_final_figure_revalidation.py"
OUTPUT_DIR = REPO_ROOT / "reports" / "pilot_05_final_figure_revalidation"

OUTPUT_PATHS = {
    "review": OUTPUT_DIR / "pilot_05BG_independent_figure_revalidation.md",
    "figure_01_register": OUTPUT_DIR / "pilot_05BG_figure_01_integrity_register.csv",
    "figure_04_register": OUTPUT_DIR / "pilot_05BG_figure_04_integrity_register.csv",
    "binding_report": OUTPUT_DIR / "pilot_05BG_manuscript_binding_integrity_report.md",
    "verdict": OUTPUT_DIR / "pilot_05BG_submission_readiness_verdict.md",
    "validation": OUTPUT_DIR / "pilot_05BG_internal_validation_report.md",
    "manifest": OUTPUT_DIR / "pilot_05BG_manifest.json",
}

EXPECTED_UNTRACKED = sorted([
    SCRIPT_REL,
    *[path.relative_to(REPO_ROOT).as_posix() for path in OUTPUT_PATHS.values()],
])

PATHS = {
    "bootstrap": REPO_ROOT / "reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_bootstrap_confidence_intervals.csv",
    "cascade": REPO_ROOT / "reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_cascade_sequence_metrics.csv",
    "source_manuscript": REPO_ROOT / "reports/pilot_05_final_manuscript/pilot_05BD_final_manuscript.md",
    "review_manifest": REPO_ROOT / "reports/pilot_05_final_integrity_reviewer_readiness/pilot_05BE_manifest.json",
    "repair_script": REPO_ROOT / "experiments/pilot_05_final_figure_repair.py",
    "repair_data_01": REPO_ROOT / "reports/pilot_05_final_figure_repair/pilot_05BF_figure_01_divergence_data.csv",
    "repair_figure_01": REPO_ROOT / "reports/pilot_05_final_figure_repair/pilot_05BF_figure_01_parser_vs_esr_divergence.png",
    "repair_data_04": REPO_ROOT / "reports/pilot_05_final_figure_repair/pilot_05BF_figure_04_failure_family_data.csv",
    "repair_figure_04": REPO_ROOT / "reports/pilot_05_final_figure_repair/pilot_05BF_figure_04_failure_family_counts.png",
    "repaired_manuscript": REPO_ROOT / "reports/pilot_05_final_figure_repair/pilot_05BF_repaired_final_manuscript.md",
    "repair_traceability": REPO_ROOT / "reports/pilot_05_final_figure_repair/pilot_05BF_figure_repair_traceability.md",
    "repair_contract": REPO_ROOT / "reports/pilot_05_final_figure_repair/pilot_05BF_revalidation_input_contract.csv",
    "repair_validation": REPO_ROOT / "reports/pilot_05_final_figure_repair/pilot_05BF_internal_validation_report.md",
    "repair_manifest": REPO_ROOT / "reports/pilot_05_final_figure_repair/pilot_05BF_manifest.json",
}

SOURCE_SHA256 = {
    "experiments/pilot_05_final_figure_repair.py":
        "176557BE4D8F6C1D57D231A14C1FD1D4E18FF570A4AAD93C783B4D2F6D245A6E",
    "reports/pilot_05_final_figure_repair/pilot_05BF_figure_01_divergence_data.csv":
        "BE397FF00A2EBABD96A6FC55941B00F92D8EC0826FA4769E502490EA3B8AF7C2",
    "reports/pilot_05_final_figure_repair/pilot_05BF_figure_01_parser_vs_esr_divergence.png":
        "7A3EA7C709E7F6DB47BA9FC383D8A0F13CA988F77FC6FDC5CD675CAACB33F0D8",
    "reports/pilot_05_final_figure_repair/pilot_05BF_figure_04_failure_family_data.csv":
        "D6B1C17DE316E9C5B8B520D949B29DB34AA7EAE59EAC3CD69EFB0A9ADCC62E15",
    "reports/pilot_05_final_figure_repair/pilot_05BF_figure_04_failure_family_counts.png":
        "6588B474A94B95DDF0389C2B2EE18CB4EF7BD10388E6ABD3E6290B7D090E0417",
    "reports/pilot_05_final_figure_repair/pilot_05BF_repaired_final_manuscript.md":
        "A6C3CD10B2C6A17D9687221FE44CC50D5691C82FF84987B096BBC578B2E4ECA0",
    "reports/pilot_05_final_figure_repair/pilot_05BF_figure_repair_traceability.md":
        "F382BABF25E2ABC6BD3007F86518E74C3150A221AEA7DCF37E2105C6DF580168",
    "reports/pilot_05_final_figure_repair/pilot_05BF_revalidation_input_contract.csv":
        "A854325E849548C0F042BA51A32156B3CFF9A0216C61F97047A067E2196B7AB0",
    "reports/pilot_05_final_figure_repair/pilot_05BF_internal_validation_report.md":
        "6D4E0270AE90DC55586D00E33769DFDB39AA7526A266BF4E2C15014889DC5AD6",
    "reports/pilot_05_final_figure_repair/pilot_05BF_manifest.json":
        "013CA01D8EEEFA9BB3264E7FE33777945F0C8E5A3DDC1FDDB5D1589184C9EACB",
    "reports/pilot_05_final_manuscript/pilot_05BD_final_manuscript.md":
        "ACB96B8400F598B65ACC0E3A4AD2BD133BFF82DE52494848E556F3C1B392A570",
    "reports/pilot_05_final_integrity_reviewer_readiness/pilot_05BE_manifest.json":
        "22D23D413D125F45E85EB60AE41F40FB64C472A1081CA75F7CDD7A901654694E",
}

SOURCE_BLOBS = {
    "reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_bootstrap_confidence_intervals.csv":
        "a2139720647b9750e77ce0e72e54aafd0767e224",
    "reports/pilot_05_cfpb_glm52_scaled_metrics/pilot_05AP_cascade_sequence_metrics.csv":
        "c756cd24734f4bac16ad9479c8ef0e4b8b87f95e",
    "reports/pilot_05_final_manuscript/pilot_05BD_final_manuscript.md":
        "8a8e5d0eadfc79071a46d2123ec3447c0023827b",
    "reports/pilot_05_final_integrity_reviewer_readiness/pilot_05BE_manifest.json":
        "005fdcfb621ce389b079b75cf4a1cf88a1d3660f",
    "reports/pilot_05_final_figure_repair/pilot_05BF_manifest.json":
        "2e6df8899b2710424ce1e874aa682cea0da3f8d9",
    "reports/pilot_05_final_figure_repair/pilot_05BF_figure_01_divergence_data.csv":
        "37077ea0b8fafd1c010208faa50ab1a58bcb7d1c",
    "reports/pilot_05_final_figure_repair/pilot_05BF_figure_04_failure_family_data.csv":
        "ab1b3ce5a316c7cb30eb8c0a11d583396fe4c9ed",
    "reports/pilot_05_final_figure_repair/pilot_05BF_repaired_final_manuscript.md":
        "3dbedf9ae538bfecf86ec1072bca2db08acfddb5",
}

OLD_FIGURE_01_PATH = (
    "../pilot_05_cfpb_glm52_paper_figures_tables/"
    "pilot_05AS_figure_01_parser_vs_evidence_state_divergence.png"
)
NEW_FIGURE_01_PATH = "pilot_05BF_figure_01_parser_vs_esr_divergence.png"
OLD_FIGURE_04_PATH = (
    "../pilot_05_cfpb_glm52_paper_figures_tables/"
    "pilot_05AS_figure_04_failure_family_interpretation.png"
)
NEW_FIGURE_04_PATH = "pilot_05BF_figure_04_failure_family_counts.png"

OLD_FIGURE_01_CAPTION = (
    "**Figure 1. Parser validity and evidence-sensitive reliability under controlled degradation.** "
    "The committed figure is integrated as the visual summary of the divergence analysis. "
    "All nine degraded parser-validity point estimates are positive, whereas all nine degraded "
    "stage-success estimates are negative; Tables 2 and 3 provide the exact values and intervals."
)
NEW_FIGURE_01_CAPTION = (
    "**Figure 1. Paired parser-validity and stage-success changes under controlled evidence degradation.** "
    "Points show degraded-minus-clean means and 95% bootstrap intervals from 2,000 resamples with seed "
    "5205 for all nine condition-stage comparisons. All parser-validity point estimates are positive, "
    "although three partial-dropout intervals include zero; all stage-success intervals remain below zero throughout sampling."
)
OLD_FIGURE_04_CAPTION = (
    "**Figure 4. Failure-family interpretation.** The committed diagnostic distinguishes "
    "detected-but-unrecovered degradation, parser-valid/evidence-unsuccessful divergence, and "
    "missing-sanitized-row accounting. Table 4 supplies the authoritative sequence counts; the "
    "figure is descriptive rather than a quantitative prevalence claim."
)
NEW_FIGURE_04_CAPTION = (
    "**Figure 4. Sequence-level failure-family composition.** Bars report 143 parser-failure cascades, "
    "71 detected-but-not-recovered patterns, 3 audit-false-assurance patterns, 6 incomplete sequences, "
    "and 17 preserved successes across 240 groups. This is not a deployment prevalence estimate."
)

EXPECTED_FIGURE_01_ROWS = [
    ("compressed_lossy", "decision", "parser_valid", 59, 0.338983, 0.169492, 0.491525),
    ("compressed_lossy", "decision", "stage_success", 59, -0.508475, -0.644068, -0.372881),
    ("compressed_lossy", "audit", "parser_valid", 58, 0.275862, 0.086207, 0.465517),
    ("compressed_lossy", "audit", "stage_success", 58, -0.517241, -0.637931, -0.396121),
    ("compressed_lossy", "escalation", "parser_valid", 60, 0.300000, 0.133333, 0.466667),
    ("compressed_lossy", "escalation", "stage_success", 60, -0.416667, -0.533333, -0.300000),
    ("partial_dropout", "decision", "parser_valid", 59, 0.067797, -0.118644, 0.271186),
    ("partial_dropout", "decision", "stage_success", 59, -0.508475, -0.644068, -0.372881),
    ("partial_dropout", "audit", "parser_valid", 58, 0.155172, -0.034483, 0.328017),
    ("partial_dropout", "audit", "stage_success", 58, -0.517241, -0.637931, -0.396121),
    ("partial_dropout", "escalation", "parser_valid", 60, 0.116667, -0.066667, 0.300000),
    ("partial_dropout", "escalation", "stage_success", 60, -0.416667, -0.533333, -0.300000),
    ("noisy_conflicting", "decision", "parser_valid", 57, 0.298246, 0.087719, 0.491228),
    ("noisy_conflicting", "decision", "stage_success", 57, -0.491228, -0.614035, -0.368421),
    ("noisy_conflicting", "audit", "parser_valid", 57, 0.368421, 0.210526, 0.526316),
    ("noisy_conflicting", "audit", "stage_success", 57, -0.508772, -0.631579, -0.385965),
    ("noisy_conflicting", "escalation", "parser_valid", 59, 0.220339, 0.033898, 0.406780),
    ("noisy_conflicting", "escalation", "stage_success", 59, -0.406780, -0.542373, -0.288136),
]

EXPECTED_FIGURE_04_COUNTS = {
    "parser_failure_cascade": 143,
    "detected_not_recovered": 71,
    "audit_false_assurance": 3,
    "incomplete_persisted_sequence": 6,
    "preserved_or_clean_success": 17,
}


class ContractError(RuntimeError):
    pass


def run_git(args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(REPO_ROOT),
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def rel(path: Path) -> str:
    return path.relative_to(REPO_ROOT).as_posix()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_text(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def png_header(path: Path) -> dict[str, int]:
    data = path.read_bytes()
    if len(data) < 33 or data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ContractError(f"Invalid PNG signature: {path}")
    if data[12:16] != b"IHDR":
        raise ContractError(f"PNG IHDR is missing: {path}")
    width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
        ">IIBBBBB", data[16:29]
    )
    return {
        "width": width,
        "height": height,
        "bit_depth": bit_depth,
        "color_type": color_type,
        "compression": compression,
        "filtering": filtering,
        "interlace": interlace,
    }


def verify_starting_state() -> None:
    if run_git(["branch", "--show-current"]) != EXPECTED_BRANCH:
        raise ContractError("Expected branch main.")
    if run_git(["rev-parse", "HEAD"]) != EXPECTED_HEAD:
        raise ContractError("Unexpected HEAD before 05BG.")
    if run_git(["log", "-1", "--format=%s"]) != EXPECTED_HEAD_MESSAGE:
        raise ContractError("Unexpected HEAD message before 05BG.")
    if run_git(["diff", "--name-only"]):
        raise ContractError("Tracked modifications are not allowed before 05BG.")
    if run_git(["diff", "--cached", "--name-only"]):
        raise ContractError("Staged files are not allowed before 05BG.")
    untracked = sorted(
        line.replace("\\", "/")
        for line in run_git(["ls-files", "--others", "--exclude-standard"]).splitlines()
        if line.strip()
    )
    if untracked != [SCRIPT_REL]:
        raise ContractError(f"Expected only the untracked 05BG generator, got: {untracked}")
    if OUTPUT_DIR.exists():
        raise ContractError("05BG output directory already exists.")

    local_origin = run_git(["rev-parse", "refs/remotes/origin/main"])
    remote_rows = run_git(["ls-remote", "--heads", "origin", "refs/heads/main"]).splitlines()
    if len(remote_rows) != 1:
        raise ContractError("Expected exactly one remote origin/main row.")
    remote_head = remote_rows[0].split()[0]
    if local_origin != EXPECTED_HEAD or remote_head != EXPECTED_HEAD:
        raise ContractError("Local or remote origin/main is not at the secured 05BF checkpoint.")


def verify_source_contracts() -> None:
    for relative_path, expected_hash in SOURCE_SHA256.items():
        path = REPO_ROOT / relative_path
        if not path.is_file():
            raise ContractError(f"Required source is missing: {relative_path}")
        actual = sha256_file(path)
        if actual != expected_hash:
            raise ContractError(
                f"SHA-256 mismatch for {relative_path}: expected {expected_hash}, got {actual}"
            )

    for relative_path, expected_blob in SOURCE_BLOBS.items():
        actual_blob = run_git(["rev-parse", f"{EXPECTED_HEAD}:{relative_path}"])
        if actual_blob != expected_blob:
            raise ContractError(
                f"Blob mismatch for {relative_path}: expected {expected_blob}, got {actual_blob}"
            )

    review_manifest = json.loads(PATHS["review_manifest"].read_text(encoding="utf-8"))
    if review_manifest["status"] != "PASS":
        raise ContractError("05BE audit execution did not pass.")
    if review_manifest["verdict"]["figure_integrity"] != "FAIL":
        raise ContractError("05BE figure-integrity finding is not preserved.")
    finding_ids = {item["finding_id"] for item in review_manifest["findings"]}
    if finding_ids != {"FIG-B01", "FIG-M01"}:
        raise ContractError(f"Unexpected 05BE finding set: {finding_ids}")

    repair_manifest = json.loads(PATHS["repair_manifest"].read_text(encoding="utf-8"))
    if repair_manifest["status"] != "PASS":
        raise ContractError("05BF repair generation did not pass.")
    if repair_manifest["verdict"]["required_next_gate"] != "05BG_INDEPENDENT_REVALIDATION":
        raise ContractError("05BF does not identify 05BG as the next gate.")


def validate_figure_01_data() -> list[dict[str, Any]]:
    authoritative = read_csv(PATHS["bootstrap"])
    repaired = read_csv(PATHS["repair_data_01"])

    authoritative_by_key = {
        (row["degraded_condition"], row["stage"], row["metric"]): row
        for row in authoritative
        if row["metric"] in {"parser_valid", "stage_success"}
    }
    repaired_by_key = {
        (row["evidence_condition"], row["stage"], row["metric"]): row
        for row in repaired
    }

    expected_keys = {(a, b, c) for a, b, c, *_ in EXPECTED_FIGURE_01_ROWS}
    if set(authoritative_by_key) != expected_keys:
        raise ContractError("Authoritative Figure 1 key set is not the exact expected 18 rows.")
    if set(repaired_by_key) != expected_keys:
        raise ContractError("Repaired Figure 1 key set is not the exact expected 18 rows.")

    rows: list[dict[str, Any]] = []
    for index, expected in enumerate(EXPECTED_FIGURE_01_ROWS, start=1):
        condition, stage, metric, paired_cases, mean, low, high = expected
        key = (condition, stage, metric)
        source = authoritative_by_key[key]
        repair = repaired_by_key[key]

        source_values = (
            int(source["paired_cases"]),
            float(source["mean_paired_delta_degraded_minus_clean"]),
            float(source["ci_95_low"]),
            float(source["ci_95_high"]),
            int(source["bootstrap_n"]),
            int(source["random_seed"]),
        )
        repair_values = (
            int(repair["paired_cases"]),
            float(repair["mean_delta_degraded_minus_clean"]),
            float(repair["ci_95_low"]),
            float(repair["ci_95_high"]),
            int(repair["bootstrap_n"]),
            int(repair["random_seed"]),
        )
        expected_values = (paired_cases, mean, low, high, 2000, 5205)

        if source_values != expected_values or repair_values != expected_values:
            raise ContractError(
                f"Figure 1 value mismatch for {condition}/{stage}/{metric}: "
                f"source={source_values}; repair={repair_values}; expected={expected_values}"
            )

        visibility = "PARTIALLY_OBSCURED_BY_LEGEND" if key == (
            "noisy_conflicting", "escalation", "parser_valid"
        ) else "CLEAR"

        rows.append({
            "check_id": f"F1-D{index:02d}",
            "check_type": "DATA_POINT_AND_INTERVAL",
            "evidence_condition": condition,
            "stage": stage,
            "metric": metric,
            "paired_cases": paired_cases,
            "mean_delta": f"{mean:.6f}",
            "ci_95_low": f"{low:.6f}",
            "ci_95_high": f"{high:.6f}",
            "source_match": "PASS",
            "visual_visibility": visibility,
            "status": "FAIL" if visibility != "CLEAR" else "PASS",
            "finding_id": "FIG-L01" if visibility != "CLEAR" else "",
        })

    parser_rows = [row for row in rows if row["metric"] == "parser_valid"]
    success_rows = [row for row in rows if row["metric"] == "stage_success"]
    if sum(float(row["mean_delta"]) > 0 for row in parser_rows) != 9:
        raise ContractError("Expected all nine parser-validity means above zero.")
    if sum(float(row["ci_95_low"]) <= 0 <= float(row["ci_95_high"]) for row in parser_rows) != 3:
        raise ContractError("Expected exactly three parser-validity intervals crossing zero.")
    if sum(float(row["ci_95_high"]) < 0 for row in success_rows) != 9:
        raise ContractError("Expected all nine stage-success intervals below zero.")

    visual_checks = [
        ("F1-V01", "PNG hash bound to reviewed asset", "PASS", ""),
        ("F1-V02", "Title is present and legible", "PASS", ""),
        ("F1-V03", "All nine condition-stage labels are present and legible", "PASS", ""),
        ("F1-V04", "X-axis label identifies paired degraded-minus-clean delta and 95% bootstrap interval", "PASS", ""),
        ("F1-V05", "Zero reference line is visible", "PASS", ""),
        ("F1-V06", "Parser-validity and stage-success series are visually distinct", "PASS", ""),
        ("F1-V07", "Legend labels both plotted series correctly", "PASS", ""),
        (
            "F1-V08",
            "Lower-right legend overlaps the noisy-conflicting escalation parser-validity interval and obscures its right segment/cap",
            "FAIL",
            "FIG-L01",
        ),
        ("F1-V09", "No title, axis-label, or y-label clipping is visible", "PASS", ""),
    ]
    for check_id, description, status, finding_id in visual_checks:
        rows.append({
            "check_id": check_id,
            "check_type": "VISUAL_REVIEW",
            "evidence_condition": "",
            "stage": "",
            "metric": "",
            "paired_cases": "",
            "mean_delta": "",
            "ci_95_low": "",
            "ci_95_high": "",
            "source_match": "NOT_APPLICABLE",
            "visual_visibility": description,
            "status": status,
            "finding_id": finding_id,
        })
    return rows


def validate_figure_04_data() -> list[dict[str, Any]]:
    cascade_rows = read_csv(PATHS["cascade"])
    repaired = read_csv(PATHS["repair_data_04"])
    all_rows = [row for row in cascade_rows if row["evidence_condition"] == "ALL"]
    if len(all_rows) != 1:
        raise ContractError("Expected one ALL row in cascade metrics.")
    authoritative_counts = json.loads(all_rows[0]["cascade_sequence_type_counts"])
    if authoritative_counts != EXPECTED_FIGURE_04_COUNTS:
        raise ContractError(f"Authoritative Figure 4 counts mismatch: {authoritative_counts}")
    if sum(authoritative_counts.values()) != 240:
        raise ContractError("Authoritative Figure 4 counts do not sum to 240.")

    repaired_counts = {row["failure_family_key"]: int(row["count"]) for row in repaired}
    if repaired_counts != EXPECTED_FIGURE_04_COUNTS:
        raise ContractError(f"Repaired Figure 4 counts mismatch: {repaired_counts}")

    rows: list[dict[str, Any]] = []
    labels = {
        "parser_failure_cascade": "Parser-failure cascade",
        "detected_not_recovered": "Detected but not recovered",
        "audit_false_assurance": "Audit false assurance",
        "incomplete_persisted_sequence": "Incomplete sequence",
        "preserved_or_clean_success": "Preserved success",
    }
    for index, key in enumerate(EXPECTED_FIGURE_04_COUNTS, start=1):
        rows.append({
            "check_id": f"F4-D{index:02d}",
            "check_type": "COUNT_AND_LABEL",
            "failure_family_key": key,
            "display_label": labels[key],
            "count": EXPECTED_FIGURE_04_COUNTS[key],
            "total_sequence_groups": 240,
            "source_match": "PASS",
            "visual_visibility": "CLEAR",
            "status": "PASS",
            "finding_id": "",
        })

    visual_checks = [
        ("F4-V01", "PNG hash bound to reviewed asset", "PASS"),
        ("F4-V02", "Title is present and legible", "PASS"),
        ("F4-V03", "All five failure-family labels are present and legible", "PASS"),
        ("F4-V04", "All five count annotations are present and unobstructed", "PASS"),
        ("F4-V05", "X-axis states total sequence groups equals 240", "PASS"),
        ("F4-V06", "No label, annotation, title, or bar is clipped", "PASS"),
    ]
    for check_id, description, status in visual_checks:
        rows.append({
            "check_id": check_id,
            "check_type": "VISUAL_REVIEW",
            "failure_family_key": "",
            "display_label": description,
            "count": "",
            "total_sequence_groups": "",
            "source_match": "NOT_APPLICABLE",
            "visual_visibility": "CLEAR",
            "status": status,
            "finding_id": "",
        })
    return rows


def validate_pngs() -> dict[str, dict[str, int]]:
    figure_01_header = png_header(PATHS["repair_figure_01"])
    figure_04_header = png_header(PATHS["repair_figure_04"])

    if figure_01_header != {
        "width": 3210,
        "height": 2006,
        "bit_depth": 8,
        "color_type": 6,
        "compression": 0,
        "filtering": 0,
        "interlace": 0,
    }:
        raise ContractError(f"Unexpected Figure 1 PNG header: {figure_01_header}")

    if figure_04_header != {
        "width": 2849,
        "height": 1645,
        "bit_depth": 8,
        "color_type": 6,
        "compression": 0,
        "filtering": 0,
        "interlace": 0,
    }:
        raise ContractError(f"Unexpected Figure 4 PNG header: {figure_04_header}")

    return {"figure_01": figure_01_header, "figure_04": figure_04_header}


def validate_manuscript_binding() -> dict[str, Any]:
    source = PATHS["source_manuscript"].read_text(encoding="utf-8")
    repaired = PATHS["repaired_manuscript"].read_text(encoding="utf-8")

    replacements = [
        (OLD_FIGURE_01_PATH, NEW_FIGURE_01_PATH),
        (OLD_FIGURE_01_CAPTION, NEW_FIGURE_01_CAPTION),
        (OLD_FIGURE_04_PATH, NEW_FIGURE_04_PATH),
        (OLD_FIGURE_04_CAPTION, NEW_FIGURE_04_CAPTION),
    ]
    expected = source
    for old, new in replacements:
        if expected.count(old) != 1:
            raise ContractError(f"Expected one source occurrence for replacement: {old[:80]}")
        expected = expected.replace(old, new, 1)

    if repaired != expected:
        raise ContractError("Repaired manuscript differs beyond the four approved replacements.")

    restored = repaired
    for old, new in reversed(replacements):
        if restored.count(new) != 1:
            raise ContractError(f"Expected one repaired occurrence: {new[:80]}")
        restored = restored.replace(new, old, 1)
    if restored != source:
        raise ContractError("Four inverse replacements do not restore byte-identical 05BD manuscript.")

    source_refs = source.split("## References", 1)[1]
    repaired_refs = repaired.split("## References", 1)[1]
    if repaired_refs != source_refs:
        raise ContractError("Reference block changed during figure repair.")

    figure_paths = [
        match.group(1)
        for match in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", repaired)
    ]
    expected_paths = [
        NEW_FIGURE_01_PATH,
        "../pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_02_audit_escalation_interpretation.png",
        "../pilot_05_cfpb_glm52_paper_figures_tables/pilot_05AS_figure_03_cascade_failure_rate.png",
        NEW_FIGURE_04_PATH,
    ]
    if figure_paths != expected_paths:
        raise ContractError(f"Repaired manuscript figure path/order mismatch: {figure_paths}")

    return {
        "approved_replacements": 4,
        "reversible_to_05BD": True,
        "references_preserved": sum(
            1 for line in repaired_refs.splitlines() if line.strip().startswith("- ")
        ),
        "tables_preserved": 4,
        "figures_preserved": len(figure_paths),
        "figure_paths": figure_paths,
    }


def build_independent_review(
    figure_01_rows: list[dict[str, Any]],
    figure_04_rows: list[dict[str, Any]],
    pngs: dict[str, dict[str, int]],
    binding: dict[str, Any],
) -> str:
    f1_failures = [row for row in figure_01_rows if row["status"] == "FAIL"]
    f4_failures = [row for row in figure_04_rows if row["status"] == "FAIL"]
    return f"""# Task 05BG Independent Corrected-Figure Revalidation

## Audit result

- Revalidation execution: **PASS**
- Source checkpoint: `{EXPECTED_HEAD}`
- Original 05BE finding `FIG-B01`: **CLOSED**
- Original 05BE finding `FIG-M01`: **CLOSED**
- New layout finding `FIG-L01`: **OPEN — mandatory before submission**
- Journal selection: **AUTHORIZED**
- Venue formatting: **AUTHORIZED**
- Final submission: **NOT YET AUTHORIZED**

## Independent evidence checks

The corrected Figure 1 data were compared row by row with the committed 05AP bootstrap table. All 18 plotted records match the authoritative paired-case counts, means, 95% intervals, 2,000-resample contract, and seed 5205. The original Figure 1 data-contract blocker is therefore closed.

The corrected Figure 4 data were compared with the `ALL` row of the committed cascade table. The five counts are 143, 71, 3, 6, and 17 and sum to 240. The original Figure 4 fallback-value finding is therefore closed.

## Rendered-asset review

Figure 1 is the exact SHA-256-reviewed PNG and has dimensions {pngs['figure_01']['width']} × {pngs['figure_01']['height']}. Its title, axis label, zero line, nine condition-stage labels, series distinction, and legend labels are readable. However, the legend occupies the lower-right data region and obscures the right segment and cap of the noisy-conflicting escalation parser-validity confidence interval. This is a presentation defect rather than a numerical or claim-integrity defect, but it must be repaired before final submission.

Figure 4 is the exact SHA-256-reviewed PNG and has dimensions {pngs['figure_04']['width']} × {pngs['figure_04']['height']}. All five labels, bars, and numerical annotations are clear and unobstructed.

## Manuscript binding

The derivative manuscript is an exact four-replacement transformation of committed 05BD and is reversible to it byte for byte. Figures 2 and 3 remain unchanged; all four tables, all {binding['references_preserved']} references, numerical prose, limitations, conclusions, and bounded claim language remain preserved.

## Finding accounting

- Figure 1 register failures: {len(f1_failures)}
- Figure 4 register failures: {len(f4_failures)}
- Original findings closed: 2/2
- New scientific-integrity blockers: 0
- New layout blockers for submission: 1

## Gate

The evidence package is sufficiently repaired to begin journal selection and venue-specific formatting. Final submission remains blocked until the Figure 1 legend is moved outside the data region or to a non-overlapping location and the final exported asset is checked against the unchanged 18-row data contract.
"""


def build_binding_report(binding: dict[str, Any]) -> str:
    paths = "\n".join(
        f"{index}. `{path}`"
        for index, path in enumerate(binding["figure_paths"], start=1)
    )
    return f"""# Task 05BG Manuscript Binding Integrity Report

## Result

- Binding integrity: **PASS**
- Approved changes relative to 05BD: {binding['approved_replacements']}/4
- Reverse restoration to byte-identical 05BD: YES
- References preserved: {binding['references_preserved']}
- Tables preserved: {binding['tables_preserved']}
- Figures preserved: {binding['figures_preserved']}
- Figures 2 and 3 preserved: YES
- Numerical prose changed: NO
- Citations or references changed: NO
- Limitations or conclusions changed: NO

## Bound figure paths

{paths}

## Exact approved differences

1. Figure 1 Markdown asset path.
2. Figure 1 caption.
3. Figure 4 Markdown asset path.
4. Figure 4 caption.

No other manuscript difference is permitted or observed.
"""


def build_verdict() -> str:
    return """# Task 05BG Submission Readiness Verdict

## Verdict

- Revalidation status: **PASS**
- Figure 1 data integrity: **PASS**
- Figure 1 caption/data alignment: **PASS**
- Figure 1 visual readability: **ACTION REQUIRED**
- Figure 4 data integrity: **PASS**
- Figure 4 visual readability: **PASS**
- Manuscript binding integrity: **PASS**
- Original 05BE figure findings closed: **2/2**
- Journal selection: **AUTHORIZED**
- Venue formatting: **AUTHORIZED**
- Final submission: **NOT READY**

## Open finding

`FIG-L01` — The Figure 1 legend overlaps the final parser-validity interval for noisy-conflicting escalation and obscures the interval's right segment and cap.

## Required next gate

`FIGURE_1_LEGEND_LAYOUT_REPAIR_AND_FINAL_EXPORT_VALIDATION`

The required correction is layout-only. It requires no new experiment, model run, provider comparison, literature search, numerical change, caption claim change, or manuscript rewrite.
"""


def build_validation_report(
    figure_01_rows: list[dict[str, Any]],
    figure_04_rows: list[dict[str, Any]],
    binding: dict[str, Any],
) -> str:
    return f"""# Task 05BG Internal Validation Report

## Result

- Status: **PASS**
- Source checkpoint: `{EXPECTED_HEAD}`
- Figure 1 register rows: {len(figure_01_rows)}
- Figure 1 failed rows: {sum(row['status'] == 'FAIL' for row in figure_01_rows)}
- Figure 4 register rows: {len(figure_04_rows)}
- Figure 4 failed rows: {sum(row['status'] == 'FAIL' for row in figure_04_rows)}
- Original 05BE findings closed: 2/2
- New layout finding: 1
- Manuscript binding: PASS
- Journal selection: AUTHORIZED
- Venue formatting: AUTHORIZED
- Final submission: NOT READY

## Integrity preservation

- Figure 1 authoritative rows: 18/18
- Figure 4 authoritative rows: 5/5
- Figure 4 count sum: 240/240
- Manuscript approved replacements: {binding['approved_replacements']}/4
- Manuscript reversible to 05BD: YES
- References preserved: {binding['references_preserved']}
- Tables preserved: {binding['tables_preserved']}
- Figures preserved: {binding['figures_preserved']}

## Safety

- Manuscript or figures modified: NO
- README or earlier reports modified: NO
- Experiments run: NO
- Model or API calls: NO
- New literature search: NO
- Raw CFPB data accessed: NO
- `.env` accessed: NO
- Raw prompts or responses accessed: NO
- JSONL accessed or written: NO
- Word or PDF conversion: NO
- Files staged, committed, or pushed: NO
"""


def materialize_outputs(
    output_dir: Path,
    script_path: Path,
    figure_01_rows: list[dict[str, Any]],
    figure_04_rows: list[dict[str, Any]],
    pngs: dict[str, dict[str, int]],
    binding: dict[str, Any],
) -> dict[str, str]:
    output_dir.mkdir(parents=False, exist_ok=False)

    output_paths = {
        "review": output_dir / "pilot_05BG_independent_figure_revalidation.md",
        "figure_01_register": output_dir / "pilot_05BG_figure_01_integrity_register.csv",
        "figure_04_register": output_dir / "pilot_05BG_figure_04_integrity_register.csv",
        "binding_report": output_dir / "pilot_05BG_manuscript_binding_integrity_report.md",
        "verdict": output_dir / "pilot_05BG_submission_readiness_verdict.md",
        "validation": output_dir / "pilot_05BG_internal_validation_report.md",
        "manifest": output_dir / "pilot_05BG_manifest.json",
    }

    write_text(
        output_paths["review"],
        build_independent_review(figure_01_rows, figure_04_rows, pngs, binding),
    )
    write_csv(
        output_paths["figure_01_register"],
        [
            "check_id", "check_type", "evidence_condition", "stage", "metric",
            "paired_cases", "mean_delta", "ci_95_low", "ci_95_high",
            "source_match", "visual_visibility", "status", "finding_id",
        ],
        figure_01_rows,
    )
    write_csv(
        output_paths["figure_04_register"],
        [
            "check_id", "check_type", "failure_family_key", "display_label",
            "count", "total_sequence_groups", "source_match",
            "visual_visibility", "status", "finding_id",
        ],
        figure_04_rows,
    )
    write_text(output_paths["binding_report"], build_binding_report(binding))
    write_text(output_paths["verdict"], build_verdict())
    write_text(
        output_paths["validation"],
        build_validation_report(figure_01_rows, figure_04_rows, binding),
    )

    output_hashes = {
        SCRIPT_REL: sha256_file(script_path),
        **{
            f"reports/pilot_05_final_figure_revalidation/{path.name}": sha256_file(path)
            for key, path in output_paths.items()
            if key != "manifest"
        },
    }

    manifest = {
        "task_id": TASK_ID,
        "version": VERSION,
        "status": "PASS",
        "secured_branch": EXPECTED_BRANCH,
        "secured_head": EXPECTED_HEAD,
        "counts": {
            "expected_uncommitted_files": 8,
            "source_sha256_contracts": len(SOURCE_SHA256),
            "source_blob_contracts": len(SOURCE_BLOBS),
            "figure_01_authoritative_rows": 18,
            "figure_01_register_rows": len(figure_01_rows),
            "figure_01_register_pass": sum(row["status"] == "PASS" for row in figure_01_rows),
            "figure_01_register_fail": sum(row["status"] == "FAIL" for row in figure_01_rows),
            "figure_04_authoritative_rows": 5,
            "figure_04_register_rows": len(figure_04_rows),
            "figure_04_register_pass": sum(row["status"] == "PASS" for row in figure_04_rows),
            "figure_04_register_fail": sum(row["status"] == "FAIL" for row in figure_04_rows),
            "original_findings_closed": 2,
            "new_layout_findings": 1,
            "new_scientific_integrity_findings": 0,
            "manuscript_replacements_verified": binding["approved_replacements"],
            "references_preserved": binding["references_preserved"],
            "tables_preserved": binding["tables_preserved"],
            "figures_preserved": binding["figures_preserved"],
        },
        "findings": [
            {
                "finding_id": "FIG-B01",
                "origin": "05BE",
                "status": "CLOSED",
                "summary": "Corrected Figure 1 data now match all 18 authoritative bootstrap records.",
            },
            {
                "finding_id": "FIG-M01",
                "origin": "05BE",
                "status": "CLOSED",
                "summary": "Corrected Figure 4 now uses the five authoritative sequence-family counts.",
            },
            {
                "finding_id": "FIG-L01",
                "origin": "05BG",
                "status": "OPEN",
                "severity": "LAYOUT_BLOCKER_FOR_SUBMISSION",
                "summary": "Figure 1 legend obscures part of the final parser-validity interval.",
            },
        ],
        "verdict": {
            "revalidation_execution": "PASS",
            "figure_01_data_integrity": "PASS",
            "figure_01_visual_readability": "ACTION_REQUIRED",
            "figure_04_integrity": "PASS",
            "manuscript_binding_integrity": "PASS",
            "original_05BE_findings": "CLOSED_2_OF_2",
            "reviewer_readiness": "READY_FOR_JOURNAL_SELECTION_AND_VENUE_FORMATTING",
            "journal_selection": "AUTHORIZED",
            "venue_formatting": "AUTHORIZED",
            "submission_readiness": "NOT_READY_FOR_FINAL_SUBMISSION",
            "required_next_gate": "FIGURE_1_LEGEND_LAYOUT_REPAIR_AND_FINAL_EXPORT_VALIDATION",
            "new_empirical_evidence_required": False,
            "new_model_run_required": False,
            "new_literature_search_required": False,
        },
        "safety": {
            "api_calls": False,
            "model_calls": False,
            "experiments_run": False,
            "new_literature_search": False,
            "raw_cfpb_data_accessed": False,
            "env_accessed": False,
            "raw_prompt_response_accessed": False,
            "jsonl_accessed_or_written": False,
            "word_or_pdf_conversion": False,
            "manuscript_or_figures_modified": False,
            "readme_or_earlier_reports_modified": False,
            "files_staged_committed_or_pushed": False,
        },
        "visual_review_binding": {
            "figure_01_sha256": SOURCE_SHA256[
                "reports/pilot_05_final_figure_repair/pilot_05BF_figure_01_parser_vs_esr_divergence.png"
            ],
            "figure_04_sha256": SOURCE_SHA256[
                "reports/pilot_05_final_figure_repair/pilot_05BF_figure_04_failure_family_counts.png"
            ],
            "figure_01_dimensions": pngs["figure_01"],
            "figure_04_dimensions": pngs["figure_04"],
        },
        "source_sha256": SOURCE_SHA256,
        "source_blobs": SOURCE_BLOBS,
        "output_sha256": output_hashes,
    }
    write_text(
        output_paths["manifest"],
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
    )

    return {
        SCRIPT_REL: sha256_file(script_path),
        **{
            f"reports/pilot_05_final_figure_revalidation/{path.name}": sha256_file(path)
            for path in output_paths.values()
        },
    }


def verify_final_state() -> None:
    if run_git(["rev-parse", "HEAD"]) != EXPECTED_HEAD:
        raise ContractError("HEAD changed during 05BG.")
    if run_git(["diff", "--name-only"]):
        raise ContractError("Tracked files changed during 05BG.")
    if run_git(["diff", "--cached", "--name-only"]):
        raise ContractError("Files were staged during 05BG.")
    untracked = sorted(
        line.replace("\\", "/")
        for line in run_git(["ls-files", "--others", "--exclude-standard"]).splitlines()
        if line.strip()
    )
    if untracked != EXPECTED_UNTRACKED:
        raise ContractError(f"Expected exactly eight 05BG untracked files, got: {untracked}")


def main() -> None:
    verify_starting_state()
    verify_source_contracts()
    figure_01_rows = validate_figure_01_data()
    figure_04_rows = validate_figure_04_data()
    pngs = validate_pngs()
    binding = validate_manuscript_binding()

    final_hashes = materialize_outputs(
        OUTPUT_DIR,
        SCRIPT_PATH,
        figure_01_rows,
        figure_04_rows,
        pngs,
        binding,
    )
    verify_final_state()

    print("=== TASK 05BG GENERATION RESULT ===")
    print("status: PASS")
    print(f"version: {VERSION}")
    print(f"source_HEAD: {EXPECTED_HEAD}")
    print("original_05BE_findings_closed: 2/2")
    print("figure_01_authoritative_rows: 18/18")
    print("figure_01_data_integrity: PASS")
    print("figure_01_visual_readability: ACTION_REQUIRED")
    print("figure_04_authoritative_rows: 5/5")
    print("figure_04_integrity: PASS")
    print("manuscript_binding_integrity: PASS")
    print("new_scientific_integrity_findings: 0")
    print("new_layout_findings: 1")
    print("journal_selection: AUTHORIZED")
    print("venue_formatting: AUTHORIZED")
    print("submission_readiness: NOT_READY_FOR_FINAL_SUBMISSION")
    print("required_next_gate: FIGURE_1_LEGEND_LAYOUT_REPAIR_AND_FINAL_EXPORT_VALIDATION")
    print("new_empirical_evidence_required: NO")
    print("new_model_run_required: NO")
    print("new_literature_search_required: NO")
    print("uncommitted_files: 8")
    print("tracked_files_modified: 0")
    print("staged_files: 0")
    print("")
    print("OUTPUT SHA-256")
    for path in sorted(final_hashes):
        print(f"{path} = {final_hashes[path]}")
    print("")
    print(
        "STOP: Paste the complete terminal output before staging, committing, pushing, "
        "repairing the legend, or beginning venue-specific manuscript formatting."
    )


if __name__ == "__main__":
    main()
