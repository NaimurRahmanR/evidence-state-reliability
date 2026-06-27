from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]

INPUT_PATH = ROOT_DIR / "data" / "outputs" / "pilot_results.csv"
OUTPUT_PATH = (
    ROOT_DIR
    / "results"
    / "tables"
    / "pilot_01_relationship_sensitivity.csv"
)


RELATIONSHIP_TESTS = [
    {
        "x_metric": "evidence_state_reliability",
        "y_metric": "final_failure",
        "expected_direction": "negative",
    },
    {
        "x_metric": "evidence_state_reliability",
        "y_metric": "undetected_failure",
        "expected_direction": "negative",
    },
    {
        "x_metric": "evidence_state_degradation",
        "y_metric": "final_failure",
        "expected_direction": "positive",
    },
    {
        "x_metric": "evidence_state_degradation",
        "y_metric": "audit_false_assurance",
        "expected_direction": "positive",
    },
]


def calculate_spearman_without_scipy(
    df: pd.DataFrame,
    x_metric: str,
    y_metric: str,
) -> float:
    x_rank = df[x_metric].rank()
    y_rank = df[y_metric].rank()

    return x_rank.corr(y_rank, method="pearson")


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


def round_if_available(value: float) -> float:
    if pd.isna(value):
        return value

    return round(value, 4)


def make_sensitivity_row(
    df: pd.DataFrame,
    sensitivity_view: str,
    x_metric: str,
    y_metric: str,
    expected_direction: str,
) -> dict:
    clean_df = df[[x_metric, y_metric]].dropna()

    pearson_correlation = clean_df[x_metric].corr(
        clean_df[y_metric],
        method="pearson",
    )

    spearman_correlation = calculate_spearman_without_scipy(
        df=clean_df,
        x_metric=x_metric,
        y_metric=y_metric,
    )

    observed_direction = direction_from_correlation(pearson_correlation)

    return {
        "sensitivity_view": sensitivity_view,
        "x_metric": x_metric,
        "y_metric": y_metric,
        "expected_direction": expected_direction,
        "observed_direction_pearson": observed_direction,
        "matches_expected_direction": matches_expected_direction(
            observed_direction,
            expected_direction,
        ),
        "pearson_correlation": round_if_available(pearson_correlation),
        "spearman_correlation": round_if_available(spearman_correlation),
        "n_rows": len(clean_df),
        "x_mean": round_if_available(clean_df[x_metric].mean()),
        "y_mean": round_if_available(clean_df[y_metric].mean()),
    }


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Could not find input file: {INPUT_PATH}\n"
            "Run Pilot 01 first before running this analysis."
        )

    df = pd.read_csv(INPUT_PATH)

    required_columns = {
        "condition",
        "evidence_state_reliability",
        "evidence_state_degradation",
        "final_failure",
        "undetected_failure",
        "audit_false_assurance",
    }

    missing_columns = required_columns.difference(df.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required column(s): {missing}")

    sensitivity_views = {
        "all_rows": df,
        "exclude_perfect_control_conditions": df[
            ~df["condition"].isin(["direct_answer", "evidence_preserving"])
        ],
        "degraded_evidence_only": df[df["evidence_state_degradation"] > 0],
        "audit_related_conditions_only": df[
            df["condition"].isin(["visible_audit", "blind_audit"])
        ],
    }

    rows = []

    for sensitivity_view, view_df in sensitivity_views.items():
        for test in RELATIONSHIP_TESTS:
            rows.append(
                make_sensitivity_row(
                    df=view_df,
                    sensitivity_view=sensitivity_view,
                    x_metric=test["x_metric"],
                    y_metric=test["y_metric"],
                    expected_direction=test["expected_direction"],
                )
            )

    sensitivity_df = pd.DataFrame(rows)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    sensitivity_df.to_csv(OUTPUT_PATH, index=False)

    print("\nPilot 01 Relationship Sensitivity Analysis")
    print("=" * 52)
    print(f"Input file:  {INPUT_PATH}")
    print(f"Output file: {OUTPUT_PATH}")
    print(f"Total rows in input: {len(df)}")

    print("\nSensitivity results:")
    print(
        sensitivity_df[
            [
                "sensitivity_view",
                "x_metric",
                "y_metric",
                "expected_direction",
                "observed_direction_pearson",
                "matches_expected_direction",
                "pearson_correlation",
                "spearman_correlation",
                "n_rows",
            ]
        ].to_string(index=False)
    )

    print(
        "\nInterpretation note: this is a simulation-only sensitivity check. "
        "It tests whether the observed Pilot 01 relationship direction remains "
        "visible after removing perfect/control conditions."
    )


if __name__ == "__main__":
    main()