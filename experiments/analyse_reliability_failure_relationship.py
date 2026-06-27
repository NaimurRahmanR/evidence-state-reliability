from pathlib import Path

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[1]

INPUT_PATH = ROOT_DIR / "data" / "outputs" / "pilot_results.csv"
OUTPUT_PATH = (
    ROOT_DIR
    / "results"
    / "tables"
    / "pilot_01_reliability_failure_relationship.csv"
)


RELATIONSHIP_TESTS = [
    {
        "x_metric": "evidence_state_reliability",
        "y_metric": "final_failure",
        "expected_direction": "negative",
        "research_question": (
            "Is lower evidence-state reliability associated with higher final failure?"
        ),
    },
    {
        "x_metric": "evidence_state_reliability",
        "y_metric": "undetected_failure",
        "expected_direction": "negative",
        "research_question": (
            "Is lower evidence-state reliability associated with higher undetected failure?"
        ),
    },
    {
        "x_metric": "evidence_state_degradation",
        "y_metric": "final_failure",
        "expected_direction": "positive",
        "research_question": (
            "Is higher evidence-state degradation associated with higher final failure?"
        ),
    },
    {
        "x_metric": "evidence_state_degradation",
        "y_metric": "audit_false_assurance",
        "expected_direction": "positive",
        "research_question": (
            "Is higher evidence-state degradation associated with higher audit false assurance?"
        ),
    },
]


def check_required_columns(df: pd.DataFrame) -> None:
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


def direction_from_correlation(correlation: float) -> str:
    if pd.isna(correlation):
        return "not_available"

    if correlation > 0:
        return "positive"

    if correlation < 0:
        return "negative"

    return "zero"


def expectation_match(observed_direction: str, expected_direction: str) -> bool:
    return observed_direction == expected_direction


def calculate_spearman_without_scipy(
    df: pd.DataFrame,
    x_metric: str,
    y_metric: str,
) -> float:
    """
    Spearman correlation is Pearson correlation applied to ranked values.

    We do this manually so the project does not need scipy yet.
    """
    x_rank = df[x_metric].rank()
    y_rank = df[y_metric].rank()

    return x_rank.corr(y_rank, method="pearson")


def make_relationship_row(
    df: pd.DataFrame,
    x_metric: str,
    y_metric: str,
    expected_direction: str,
    research_question: str,
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

    low_x_threshold = clean_df[x_metric].quantile(0.25)
    high_x_threshold = clean_df[x_metric].quantile(0.75)

    low_x_group = clean_df[clean_df[x_metric] <= low_x_threshold]
    high_x_group = clean_df[clean_df[x_metric] >= high_x_threshold]

    low_x_y_mean = low_x_group[y_metric].mean()
    high_x_y_mean = high_x_group[y_metric].mean()

    return {
        "research_question": research_question,
        "x_metric": x_metric,
        "y_metric": y_metric,
        "expected_direction": expected_direction,
        "observed_direction_pearson": observed_direction,
        "matches_expected_direction": expectation_match(
            observed_direction,
            expected_direction,
        ),
        "pearson_correlation": round(pearson_correlation, 4),
        "spearman_correlation": round(spearman_correlation, 4),
        "n_rows": len(clean_df),
        "x_min": round(clean_df[x_metric].min(), 4),
        "x_mean": round(clean_df[x_metric].mean(), 4),
        "x_max": round(clean_df[x_metric].max(), 4),
        "y_mean_when_x_lowest_quartile": round(low_x_y_mean, 4),
        "y_mean_when_x_highest_quartile": round(high_x_y_mean, 4),
        "difference_high_minus_low": round(high_x_y_mean - low_x_y_mean, 4),
    }


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Could not find input file: {INPUT_PATH}\n"
            "Run Pilot 01 first before running this analysis."
        )

    df = pd.read_csv(INPUT_PATH)
    check_required_columns(df)

    relationship_rows = []

    for test in RELATIONSHIP_TESTS:
        relationship_rows.append(
            make_relationship_row(
                df=df,
                x_metric=test["x_metric"],
                y_metric=test["y_metric"],
                expected_direction=test["expected_direction"],
                research_question=test["research_question"],
            )
        )

    relationship_df = pd.DataFrame(relationship_rows)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    relationship_df.to_csv(OUTPUT_PATH, index=False)

    print("\nPilot 01 Reliability-Failure Relationship Analysis")
    print("=" * 56)
    print(f"Input file:  {INPUT_PATH}")
    print(f"Output file: {OUTPUT_PATH}")
    print(f"Rows analysed: {len(df)}")

    print("\nRelationship tests:")
    print(
        relationship_df[
            [
                "x_metric",
                "y_metric",
                "expected_direction",
                "observed_direction_pearson",
                "matches_expected_direction",
                "pearson_correlation",
                "spearman_correlation",
                "difference_high_minus_low",
            ]
        ].to_string(index=False)
    )

    print("\nCondition-level context:")
    print(
        df.groupby("condition")[
            [
                "evidence_state_reliability",
                "evidence_state_degradation",
                "final_failure",
                "undetected_failure",
                "audit_false_assurance",
            ]
        ]
        .mean()
        .round(4)
        .to_string()
    )

    print(
        "\nInterpretation note: these are observed simulation relationships "
        "under current Pilot 01 assumptions only."
    )


if __name__ == "__main__":
    main()