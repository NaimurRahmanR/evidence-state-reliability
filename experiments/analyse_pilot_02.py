"""
Analyse Pilot 02 results.

Pilot 02 tests whether graded evidence degradation severity is associated
with lower evidence-state reliability and higher downstream failure.

This is still simulation-only evidence under current Pilot 02 assumptions.
"""

from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]

INPUT_PATH = ROOT_DIR / "data" / "outputs" / "pilot_02_results.csv"
OUTPUT_PATH = ROOT_DIR / "results" / "tables" / "pilot_02_severity_summary.csv"
RELATIONSHIP_OUTPUT_PATH = (
    ROOT_DIR / "results" / "tables" / "pilot_02_severity_relationships.csv"
)

SEVERITY_ORDER = {
    "none": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "severe": 4,
}

MEAN_METRICS_TO_SUMMARISE = [
    "evidence_state_reliability",
    "evidence_state_degradation",
    "final_failure",
    "undetected_failure",
    "audit_false_assurance",
    "escalation_contamination",
    "cost",
]

RELATIONSHIP_TESTS = [
    {
        "metric": "evidence_state_reliability",
        "expected_direction": "negative",
        "research_question": (
            "Does evidence-state reliability decrease as degradation severity increases?"
        ),
    },
    {
        "metric": "evidence_state_degradation",
        "expected_direction": "positive",
        "research_question": (
            "Does evidence-state degradation increase as degradation severity increases?"
        ),
    },
    {
        "metric": "final_failure",
        "expected_direction": "positive",
        "research_question": (
            "Does final failure increase as degradation severity increases?"
        ),
    },
    {
        "metric": "undetected_failure",
        "expected_direction": "positive",
        "research_question": (
            "Does undetected failure increase as degradation severity increases?"
        ),
    },
    {
        "metric": "audit_false_assurance",
        "expected_direction": "positive",
        "research_question": (
            "Does audit false assurance increase as degradation severity increases?"
        ),
    },
    {
        "metric": "escalation_contamination",
        "expected_direction": "positive",
        "research_question": (
            "Does escalation contamination increase as degradation severity increases?"
        ),
    },
]


def direction_from_correlation(correlation: float) -> str:
    if pd.isna(correlation):
        return "not_available"

    if correlation > 0:
        return "positive"

    if correlation < 0:
        return "negative"

    return "zero"


def matches_expected_direction(
    observed_direction: str,
    expected_direction: str,
) -> bool:
    return observed_direction == expected_direction


def calculate_spearman_without_scipy(
    df: pd.DataFrame,
    x_metric: str,
    y_metric: str,
) -> float:
    x_rank = df[x_metric].rank()
    y_rank = df[y_metric].rank()

    return x_rank.corr(y_rank, method="pearson")


def is_monotonic_in_expected_direction(
    ordered_values: list[float],
    expected_direction: str,
) -> bool:
    if expected_direction == "positive":
        return all(
            later >= earlier
            for earlier, later in zip(ordered_values, ordered_values[1:])
        )

    if expected_direction == "negative":
        return all(
            later <= earlier
            for earlier, later in zip(ordered_values, ordered_values[1:])
        )

    raise ValueError(f"Unknown expected direction: {expected_direction}")


def check_required_columns(df: pd.DataFrame) -> None:
    required_columns = {
        "degradation_severity",
        "accepted_by_pipeline",
        "final_failure",
        *MEAN_METRICS_TO_SUMMARISE,
    }

    missing_columns = required_columns.difference(df.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required column(s): {missing}")


def make_severity_summary(df: pd.DataFrame) -> pd.DataFrame:
    mean_summary = (
        df.groupby("degradation_severity")[MEAN_METRICS_TO_SUMMARISE]
        .mean()
        .reset_index()
    )

    aggregate_summary = (
        df.assign(
            governable_output=(
                df["accepted_by_pipeline"]
                & ~df["final_failure"]
            ).astype(int)
        )
        .groupby("degradation_severity")
        .agg(
            total_cost=("cost", "sum"),
            governable_outputs=("governable_output", "sum"),
            total_outputs=("task_id", "count"),
        )
        .reset_index()
    )

    summary = mean_summary.merge(
        aggregate_summary,
        on="degradation_severity",
        how="left",
    )

    summary["cost_per_governable_output"] = (
        summary["total_cost"] / summary["governable_outputs"]
    )

    summary["severity_index"] = summary["degradation_severity"].map(SEVERITY_ORDER)
    summary = summary.sort_values("severity_index")

    column_order = [
        "degradation_severity",
        "severity_index",
        *MEAN_METRICS_TO_SUMMARISE,
        "total_cost",
        "governable_outputs",
        "total_outputs",
        "cost_per_governable_output",
    ]

    return summary[column_order].round(4)


def make_relationship_rows(
    df: pd.DataFrame,
    severity_summary: pd.DataFrame,
) -> list[dict]:
    rows = []

    for test in RELATIONSHIP_TESTS:
        metric = test["metric"]
        expected_direction = test["expected_direction"]

        clean_df = df[["severity_index", metric]].dropna()

        pearson_correlation = clean_df["severity_index"].corr(
            clean_df[metric],
            method="pearson",
        )

        spearman_correlation = calculate_spearman_without_scipy(
            df=clean_df,
            x_metric="severity_index",
            y_metric=metric,
        )

        observed_direction = direction_from_correlation(pearson_correlation)

        ordered_values = severity_summary[metric].tolist()

        none_mean = severity_summary.loc[
            severity_summary["degradation_severity"] == "none",
            metric,
        ].iloc[0]

        severe_mean = severity_summary.loc[
            severity_summary["degradation_severity"] == "severe",
            metric,
        ].iloc[0]

        rows.append(
            {
                "research_question": test["research_question"],
                "metric": metric,
                "expected_direction": expected_direction,
                "observed_direction_pearson": observed_direction,
                "matches_expected_direction": matches_expected_direction(
                    observed_direction,
                    expected_direction,
                ),
                "monotonic_by_severity_mean": is_monotonic_in_expected_direction(
                    ordered_values,
                    expected_direction,
                ),
                "pearson_correlation": round(pearson_correlation, 4),
                "spearman_correlation": round(spearman_correlation, 4),
                "none_mean": round(none_mean, 4),
                "severe_mean": round(severe_mean, 4),
                "severe_minus_none": round(severe_mean - none_mean, 4),
            }
        )

    return rows


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Could not find input file: {INPUT_PATH}\n"
            "Run Pilot 02 first before analysing it."
        )

    df = pd.read_csv(INPUT_PATH)
    check_required_columns(df)

    df["severity_index"] = df["degradation_severity"].map(SEVERITY_ORDER)

    if df["severity_index"].isna().any():
        unknown_levels = sorted(
            df.loc[df["severity_index"].isna(), "degradation_severity"].unique()
        )
        raise ValueError(f"Unknown degradation severity level(s): {unknown_levels}")

    severity_summary = make_severity_summary(df)
    relationship_df = pd.DataFrame(
        make_relationship_rows(
            df=df,
            severity_summary=severity_summary,
        )
    )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    severity_summary.to_csv(OUTPUT_PATH, index=False)
    relationship_df.to_csv(RELATIONSHIP_OUTPUT_PATH, index=False)

    print("\nPilot 02 Severity Summary")
    print("=" * 32)
    print(f"Input file:  {INPUT_PATH}")
    print(f"Output file: {OUTPUT_PATH}")
    print(f"Relationship output file: {RELATIONSHIP_OUTPUT_PATH}")
    print(f"Rows analysed: {len(df)}")

    print("\nSeverity-level summary:")
    print(severity_summary.to_string(index=False))

    print("\nSeverity relationship tests:")
    print(
        relationship_df[
            [
                "metric",
                "expected_direction",
                "observed_direction_pearson",
                "matches_expected_direction",
                "monotonic_by_severity_mean",
                "pearson_correlation",
                "spearman_correlation",
                "severe_minus_none",
            ]
        ].to_string(index=False)
    )

    print(
        "\nInterpretation note: these are observed simulation results "
        "under current Pilot 02 assumptions only."
    )


if __name__ == "__main__":
    main()