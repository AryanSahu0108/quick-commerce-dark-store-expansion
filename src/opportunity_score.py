"""
Expansion Screening Score.

This is an ANALYST-DEFINED SCREENING framework built for this project, not a prediction of
where any company will or should build a store, and not a claim about the internal
methodology used by Blinkit, Zepto, Swiggy Instamart, or any other company. Every input is
grounded in the real, cited data in data_prep.py; no component here is invented or randomly
generated. The question this answers is:

    "Which markets deserve further investigation for dark-store expansion?"

not "where exactly should a store go?" See README Section 13, "From Market Screening to
Dark-Store Decision," for the funnel this project sits at the top of.

Scoring is restricted to cities with a real, published store count (load_covered_cities),
MINUS Navi Mumbai and Thane, which are excluded here (see data_prep.EXCLUDED_FROM_SCORING
and data_prep.EXCLUSION_REASON): the available Census geography assigns both the same
district-level population, so any population-based comparison involving either of them is
unreliable. They remain visible in every descriptive view of the dashboard. Cities without a
published store count are never scored either, see data_prep.build_market_screening().

Two components, deliberately, not three:

  Market Size Proxy (percentile, 0-100)     -> where a city's 2011 Census population ranks
                                                among the scored cities. Population is used as
                                                a consistent market-size proxy because
                                                comparable current city-level demand, order
                                                volume, or spending data is not publicly
                                                available. It is NOT called "market potential"
                                                anywhere in this project, since that would
                                                imply a stronger causal claim than population
                                                size alone supports.
  Coverage Opportunity (percentile, 0-100)  -> where a city's inverse stores-per-million-
                                                population ranks among the scored cities; a
                                                city with fewer dark stores relative to its
                                                population scores higher.

Percentile (rank-based) scoring is used instead of min-max normalization. Min-max scoring is
sensitive to a single extreme value stretching or compressing the whole scale (Delhi's
population is roughly 30x Dehradun's; a min-max score would let that one gap dominate the
scale). Percentile scoring instead asks "how does this city compare to the others in the
scored set," which is a fairer, more robust basis for a small, heterogeneous city list like
this one.

A "Competitive Intensity" factor (number of platforms present) was considered as a third
component. It is a genuinely different signal from Coverage Opportunity: a market can be
dense (many stores) but dominated by one platform (low intensity), or sparse but contested by
several. It is NOT folded into the score, because platform-level breakdown is only published
for 14 of the 20 confirmed cities; scoring 6 cities on an input they don't have would mean
silently imputing it. Competitive Intensity is instead shown as a separate decision lens
(Competitive Landscape tab, Market Explorer) wherever the underlying data exists.

A further factor, "Accessibility" (real-estate/road access) or a separate income/spending-
capacity layer, is still not included, because no public, non-fabricated per-city dataset for
either was available. See README limitations.
"""

import pandas as pd
from src.data_prep import load_covered_cities, EXCLUDED_FROM_SCORING, EXCLUSION_REASON

# Analyst-defined scenario weights. These are NOT company data and do not represent actual
# company strategy. They exist to test how sensitive expansion priorities are to management's
# strategic preference, not to force rankings to move.
SCENARIOS = {
    "Balanced": {"size": 0.50, "coverage": 0.50},
    "Demand-led": {"size": 0.80, "coverage": 0.20},
    "Coverage-led": {"size": 0.20, "coverage": 0.80},
}
SCENARIO_ORDER = ["Demand-led", "Balanced", "Coverage-led"]  # display order for movement charts

QUADRANT_LABELS = {
    "hi_size_lo_cov": "Expansion Screening Opportunity",
    "hi_size_hi_cov": "Mature / Competitive",
    "lo_size_lo_cov": "Emerging / Monitor",
    "lo_size_hi_cov": "Potentially Overserved",
}


def scoreable_universe() -> pd.DataFrame:
    """The 18-city scoring universe: confirmed count, minus Navi Mumbai and Thane."""
    df = load_covered_cities()
    return df[~df["city"].isin(EXCLUDED_FROM_SCORING)].copy()


def build_scored_table(scenario: str = "Balanced", tiers: list | None = None) -> pd.DataFrame:
    """Build the screened city table, restricted to the 18-city scoreable universe.

    Both components are computed as percentiles (0-100) within the filtered set, so a Tier 2
    city's score reflects its standing among other Tier 2 cities, not against Delhi, when
    `tiers` is used to narrow the scope.
    """
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario '{scenario}'. Options: {list(SCENARIOS)}")
    weights = SCENARIOS[scenario]

    df = scoreable_universe()
    if tiers:
        df = df[df["tier"].isin(tiers)].copy()

    n = len(df)
    if n <= 1:
        df["market_size_percentile"] = 50.0
        df["coverage_percentile"] = 50.0
    else:
        df["market_size_percentile"] = (df["population_2011_census"].rank(pct=True) * 100).round(1)
        # Lower stores-per-million = bigger coverage opportunity, so rank ascending before pct.
        df["coverage_percentile"] = (
            (-df["stores_per_million_2011pop"]).rank(pct=True) * 100
        ).round(1)

    df["market_size_score"] = (df["market_size_percentile"] / 100).round(3)
    df["coverage_opportunity_score"] = (df["coverage_percentile"] / 100).round(3)

    df["screening_score"] = (
        weights["size"] * df["market_size_score"]
        + weights["coverage"] * df["coverage_opportunity_score"]
    ).round(3)

    df["screening_tier"] = pd.cut(
        df["screening_score"],
        bins=[-0.01, 0.33, 0.66, 1.01],
        labels=["Lower priority", "Watch list", "High priority"],
    )

    # Implied Coverage Gap to Median
    # This is an analytical benchmark, NOT a demand forecast and NOT a recommendation that
    # the company should actually build that number of stores. It answers: "How many additional
    # stores would be implied if this market had the median observed coverage density of the
    # scored markets?" The benchmark is based on observed dark-store density only.
    # Formula: max(0, median_spm - city_spm) * population / 1_000_000, rounded to nearest store.
    median_spm = df["stores_per_million_2011pop"].median()
    df["median_spm_benchmark"] = round(median_spm, 2)
    df["implied_coverage_gap"] = (
        (median_spm - df["stores_per_million_2011pop"]) * df["population_2011_census"] / 1_000_000
    ).clip(lower=0).round(0).astype(int)

    df["scenario"] = scenario
    df["scenario_rank"] = df["screening_score"].rank(ascending=False, method="min").astype(int)
    return df.sort_values("screening_score", ascending=False).reset_index(drop=True)


def quadrant_label(row: pd.Series, coverage_median: float, size_median: float) -> str:
    """Market Size Proxy vs Dark-Store Coverage quadrant label.

    X-axis = coverage (stores per million). Y-axis = market size proxy (population).
    These are analyst-defined interpretations relative to the median of the scored markets,
    not official market classifications.
    """
    high_size = row["population_2011_census"] >= size_median
    high_coverage = row["stores_per_million_2011pop"] >= coverage_median
    if high_size and not high_coverage:
        return QUADRANT_LABELS["hi_size_lo_cov"]
    if high_size and high_coverage:
        return QUADRANT_LABELS["hi_size_hi_cov"]
    if not high_size and not high_coverage:
        return QUADRANT_LABELS["lo_size_lo_cov"]
    return QUADRANT_LABELS["lo_size_hi_cov"]


def explain_row(row: pd.Series) -> str:
    """Short, business-facing explanation of why a city screens the way it does."""
    reasons = []
    if row["market_size_percentile"] >= 60:
        reasons.append(f"large market-size proxy ({row['population_2011_census']:,} population, "
                        f"{row['market_size_percentile']:.0f}th percentile among scored markets)")
    if row["coverage_percentile"] >= 60:
        reasons.append(f"relatively low observed dark-store coverage "
                        f"({row['stores_per_million_2011pop']:.1f} stores per million, "
                        f"{row['coverage_percentile']:.0f}th percentile for coverage opportunity)")
    if row["market_size_percentile"] < 40:
        reasons.append("comparatively smaller market-size proxy among the scored markets")
    if row["coverage_percentile"] < 40:
        reasons.append("already relatively dense with existing dark stores")
    if row.get("blinkit_only_market"):
        reasons.append("currently a single-platform (Blinkit-only) market among the platforms broken out")
    return "; ".join(reasons) if reasons else "Mixed / near-median signals on both factors"


def scenario_rank_table(tiers: list | None = None) -> pd.DataFrame:
    """Pivot table: rows = cities, columns = scenarios, values = rank (1 = highest priority)."""
    frames = []
    for scenario in SCENARIOS:
        t = build_scored_table(scenario, tiers=tiers)[["city", "scenario_rank"]].rename(columns={"scenario_rank": scenario})
        frames.append(t.set_index("city"))
    pivot = pd.concat(frames, axis=1)
    pivot = pivot[SCENARIO_ORDER]
    pivot = pivot.sort_values("Balanced")
    return pivot.reset_index()


def scenario_resilience(tiers: list | None = None, top_n: int = 10) -> pd.DataFrame:
    """For each city, how many of the scenarios place it in that scenario's own top N."""
    n_scenarios = len(SCENARIOS)
    counts = {}
    for scenario in SCENARIOS:
        t = build_scored_table(scenario, tiers=tiers).head(top_n)
        for city in t["city"]:
            counts[city] = counts.get(city, 0) + 1
    out = pd.DataFrame({"city": list(counts.keys()), "scenarios_in_top": list(counts.values())})
    out["resilience"] = out["scenarios_in_top"].astype(str) + f"/{n_scenarios}"
    out["n_scenarios"] = n_scenarios
    return out.sort_values("scenarios_in_top", ascending=False).reset_index(drop=True)


def scenario_movement(tiers: list | None = None) -> pd.DataFrame:
    """Long-form table for a rank movement / slope chart: city, scenario (ordered), rank."""
    pivot = scenario_rank_table(tiers=tiers)
    long_df = pivot.melt(id_vars="city", value_vars=SCENARIO_ORDER, var_name="scenario", value_name="rank")
    long_df["scenario"] = pd.Categorical(long_df["scenario"], categories=SCENARIO_ORDER, ordered=True)
    return long_df.sort_values(["city", "scenario"])


if __name__ == "__main__":
    print(f"Excluded from scoring: {EXCLUDED_FROM_SCORING}")
    print(EXCLUSION_REASON)
    for scenario in SCENARIOS:
        print(f"\n=== {scenario} ===")
        table = build_scored_table(scenario)
        cols = ["city", "market_size_percentile", "coverage_percentile", "screening_score", "screening_tier"]
        print(table[cols].head(8).to_string(index=False))
    print("\n=== Scenario rank comparison ===")
    print(scenario_rank_table().to_string(index=False))
    print("\n=== Scenario resilience (top 10) ===")
    print(scenario_resilience().to_string(index=False))
    print("\n=== Scenario movement (long form, head) ===")
    print(scenario_movement().head(12).to_string(index=False))
