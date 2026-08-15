"""
Data preparation for the Quick-Commerce Dark Store Expansion Analysis.

All inputs are real, publicly sourced data:
  - data/quickcommerce_city_coverage.csv       -> QuickCommerceMap, city-level store counts and
                                                   platform breakdowns, July 2026 compilation
  - data/census_population_2011.csv            -> Census of India 2011, district-level population
  - data/named_growth_markets_no_count.csv     -> Cities named as growing markets in source
                                                   reports, but with no published store count
  - data/unconfirmed_whitespace_cities.csv     -> Large cities not named in any source reviewed;
                                                   presence genuinely unconfirmed
  - data/state_coverage.csv                    -> State-level store totals, July 2026
  - data/tier_scaling_benchmarks.csv           -> Tier 1 vs Tier 2 wage and order-density figures
  - data/city_coordinates.csv                  -> Public city-centre coordinates (for mapping only)

No store-level coordinates, revenue, demand, or SKU data are fabricated anywhere in this
pipeline. Where the underlying public data does not exist, the corresponding field is left
null and flagged, rather than filled in with an invented number. Three explicit confidence
tiers are used for "expansion candidate" cities:

  1. Confirmed count       -> load_covered_cities()          (published store count)
  2. Confirmed presence    -> load_named_growth_markets()     (named as active, no count published)
  3. Unconfirmed           -> load_unconfirmed_cities()       (not mentioned in sources reviewed)

Collapsing these three into one undifferentiated "candidate" list would overstate how much
is actually known about cities in groups 2 and 3, so they are kept separate throughout.
"""

import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Navi Mumbai and Thane share one Census district population figure (Navi Mumbai is not a
# separate census district), which makes population-based comparisons involving either city
# unreliable. They stay in every descriptive view (network, competitive, Market Explorer) but
# are excluded from Expansion Priority scoring and all ranked recommendations. See README.
EXCLUDED_FROM_SCORING = ["Navi Mumbai", "Thane"]
EXCLUSION_REASON = (
    "Navi Mumbai and Thane are excluded from expansion scoring because the available Census "
    "geography assigns both the same district-level population, making population-based "
    "comparisons unreliable."
)


def load_covered_cities() -> pd.DataFrame:
    """Cities with a real, cited quick-commerce store count (QuickCommerceMap top 20)."""
    coverage = pd.read_csv(DATA_DIR / "quickcommerce_city_coverage.csv")
    population = pd.read_csv(DATA_DIR / "census_population_2011.csv")
    coords = pd.read_csv(DATA_DIR / "city_coordinates.csv")

    df = coverage.merge(population[["city", "population_2011_census", "households_2011_census"]],
                         on="city", how="left")
    df = df.merge(coords, on="city", how="left")

    # Coverage ratio: dark stores per million residents (2011 population baseline,
    # see README limitations re: population growth since 2011).
    df["stores_per_million_2011pop"] = (df["total_stores"] / (df["population_2011_census"] / 1_000_000)).round(2)

    # Ranks used for descriptive context (NOT fed into the score itself, to avoid
    # double-counting the same population/coverage signal under two labels).
    df["population_rank"] = df["population_2011_census"].rank(ascending=False, method="min").astype(int)
    df["store_count_rank"] = df["total_stores"].rank(ascending=False, method="min").astype(int)

    platform_cols = ["blinkit", "zepto", "swiggy_instamart", "flipkart_minutes", "bigbasket"]
    df["platforms_present_count"] = df[platform_cols].notna().sum(axis=1)
    df.loc[df["platforms_breakdown_available"] == "FALSE", "platforms_present_count"] = pd.NA

    # First-mover-monopoly flag: cities where Blinkit is the only confirmed platform among
    # those actually broken out (a real pattern the source data calls out for smaller cities).
    other_platforms = ["zepto", "swiggy_instamart", "flipkart_minutes", "bigbasket"]
    has_breakdown = df["platforms_breakdown_available"].isin(["TRUE", "PARTIAL"])
    df["blinkit_only_market"] = has_breakdown & (df[other_platforms].fillna(0).sum(axis=1) == 0) & df["blinkit"].notna()

    # Data confidence, categorical, not a fabricated numeric score. High = confirmed count and
    # a full platform breakdown. Medium = confirmed count, but no or only partial platform
    # breakdown, so competitive detail is incomplete.
    df["data_confidence"] = df["platforms_breakdown_available"].map({
        "TRUE": "High", "PARTIAL": "Medium", "FALSE": "Medium",
    })

    df["excluded_from_scoring"] = df["city"].isin(EXCLUDED_FROM_SCORING)

    return df


def load_named_growth_markets() -> pd.DataFrame:
    """Cities the source reports name as active/growing markets, with no store count published.

    Data confidence: Low, presence is confirmed by the source text, the count is not.
    """
    df = pd.read_csv(DATA_DIR / "named_growth_markets_no_count.csv")
    coords = pd.read_csv(DATA_DIR / "city_coordinates.csv")
    df = df.merge(coords, on="city", how="left")
    df["population_rank_overall"] = df["population_2011_census"].rank(ascending=False, method="min").astype(int)
    df["data_confidence"] = "Low"
    return df


def load_unconfirmed_cities() -> pd.DataFrame:
    """Large-population cities not named in any source reviewed for this project.

    Data confidence: Unconfirmed. Absence from our sources is NOT evidence of absence of
    quick-commerce stores. These are analyst-flagged candidates worth checking with primary
    data, not confirmed gaps. See README limitations.
    """
    df = pd.read_csv(DATA_DIR / "unconfirmed_whitespace_cities.csv")
    coords = pd.read_csv(DATA_DIR / "city_coordinates.csv")
    df = df.merge(coords, on="city", how="left")
    df["population_rank_overall"] = df["population_2011_census"].rank(ascending=False, method="min").astype(int)
    df["data_confidence"] = "Unconfirmed"
    return df


def build_market_screening() -> pd.DataFrame:
    """Market Screening layer: cities outside the 20-city confirmed-count universe.

    These cities are deliberately NOT given an Expansion Screening Score. Scoring requires a real
    store count as an input, and none exists for these cities in the sources reviewed.
    Assigning them a score anyway would look more complete while quietly fabricating the
    input the whole framework depends on. Instead each city carries a confidence label and
    a plain-language note on what would need to be confirmed before it could be scored.
    """
    named = load_named_growth_markets().copy()
    named["confidence"] = "Named active market, no published store count"
    named["requires"] = "A published store count to enter the scored universe"

    unconfirmed = load_unconfirmed_cities().copy()
    unconfirmed["confidence"] = "Not named in any source reviewed"
    unconfirmed["requires"] = "Confirmation of quick-commerce presence, then a store count"
    unconfirmed["tier"] = "Unclassified"

    cols = ["city", "state", "tier", "population_2011_census", "confidence", "requires", "note",
            "data_confidence", "latitude", "longitude"]
    combined = pd.concat([named[cols], unconfirmed[cols]], ignore_index=True)
    combined["population_rank"] = combined["population_2011_census"].rank(ascending=False, method="min").astype(int)
    return combined.sort_values("population_2011_census", ascending=False).reset_index(drop=True)


def load_state_coverage() -> pd.DataFrame:
    """Real, cited state-level dark store totals (July 2026)."""
    return pd.read_csv(DATA_DIR / "state_coverage.csv")


def load_tier_benchmarks() -> pd.DataFrame:
    """Real, cited Tier 1 vs Tier 2 operational benchmarks (wages, order density)."""
    return pd.read_csv(DATA_DIR / "tier_scaling_benchmarks.csv")


def normalize(series: pd.Series) -> pd.Series:
    """Min-max normalize a series to 0-1, safe against a zero-range column."""
    lo, hi = series.min(), series.max()
    if hi == lo:
        return series * 0 + 0.5
    return (series - lo) / (hi - lo)


if __name__ == "__main__":
    covered = load_covered_cities()
    named = load_named_growth_markets()
    unconfirmed = load_unconfirmed_cities()
    print(covered[["city", "tier", "population_2011_census", "total_stores",
                    "stores_per_million_2011pop", "data_confidence", "excluded_from_scoring"]].to_string(index=False))
    print("\nNamed growth markets (confirmed presence, no published count):")
    print(named[["city", "tier", "population_2011_census"]].to_string(index=False))
    print("\nUnconfirmed whitespace cities (population only, no source mentions found):")
    print(unconfirmed[["city", "population_2011_census", "population_rank_overall"]].to_string(index=False))
