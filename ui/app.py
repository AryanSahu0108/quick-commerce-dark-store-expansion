"""
Quick-Commerce Dark Store Expansion Analysis, Dashboard

Run with:  streamlit run ui/app.py   (from the project root)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_prep import (
    load_covered_cities, load_named_growth_markets, load_unconfirmed_cities,
    build_market_screening, load_state_coverage, load_tier_benchmarks,
    EXCLUDED_FROM_SCORING, EXCLUSION_REASON,
)
from src.opportunity_score import (
    build_scored_table, explain_row, quadrant_label, scenario_rank_table,
    scenario_resilience, scoreable_universe, SCENARIOS,
)
from src.style import PLATFORM_COLORS, TIER_COLORS, SEQUENTIAL_SCALE, NEUTRAL_GREY, PLOTLY_TEMPLATE, QUADRANT_COLORS, CONFIDENCE_COLORS

st.set_page_config(page_title="Quick-Commerce Dark Store Expansion Analysis", layout="wide")
px.defaults.template = PLOTLY_TEMPLATE

PLATFORM_COLS = ["blinkit", "zepto", "swiggy_instamart", "flipkart_minutes", "bigbasket"]
PLATFORM_LABELS = {
    "blinkit": "Blinkit", "zepto": "Zepto", "swiggy_instamart": "Swiggy Instamart",
    "flipkart_minutes": "Flipkart Minutes", "bigbasket": "BigBasket",
}

# ----------------------------------------------------------------------------------
# Data (loaded once)
# ----------------------------------------------------------------------------------
covered = load_covered_cities()                      # all 20 confirmed-count cities, descriptive use
named_growth = load_named_growth_markets()
unconfirmed = load_unconfirmed_cities()
screening = build_market_screening()                  # 13 unscored markets
state_coverage = load_state_coverage()
tier_benchmarks = load_tier_benchmarks()
scored_balanced = build_scored_table("Balanced")       # 18-city scoreable universe

COVERAGE_MEDIAN = scored_balanced["stores_per_million_2011pop"].median()
POTENTIAL_MEDIAN = scored_balanced["population_2011_census"].median()
scored_balanced["quadrant"] = scored_balanced.apply(
    lambda r: quadrant_label(r, COVERAGE_MEDIAN, POTENTIAL_MEDIAN), axis=1
)

# ----------------------------------------------------------------------------------
# Reusable chart builders
# ----------------------------------------------------------------------------------

def quadrant_matrix_chart(df: pd.DataFrame, height: int = 520) -> go.Figure:
    """Market Size Proxy vs Dark-Store Coverage, the project's hero decision chart.

    X = coverage (stores per million population). Y = market size proxy (population).
    Bubble size = confirmed dark stores. Colour = analytical market segment (quadrant).
    """
    fig = px.scatter(
        df, x="stores_per_million_2011pop", y="population_2011_census",
        size="total_stores", color="quadrant", text="city",
        color_discrete_map=QUADRANT_COLORS, size_max=48,
        labels={
            "stores_per_million_2011pop": "Dark-Store Coverage (stores per million population)",
            "population_2011_census": "Market Size Proxy (2011 Census population)",
            "total_stores": "Confirmed dark stores",
            "quadrant": "Market Segment",
        },
        hover_data={"stores_per_million_2011pop": ":.1f", "population_2011_census": ":,",
                     "total_stores": True, "tier": True},
    )
    fig.update_traces(textposition="top center", textfont_size=10)
    fig.add_vline(x=COVERAGE_MEDIAN, line_dash="dot", line_color=NEUTRAL_GREY)
    fig.add_hline(y=POTENTIAL_MEDIAN, line_dash="dot", line_color=NEUTRAL_GREY)

    x_lo = df["stores_per_million_2011pop"].min() * 0.9
    x_hi = df["stores_per_million_2011pop"].max() * 1.08
    y_lo = df["population_2011_census"].min() * 0.9
    y_hi = df["population_2011_census"].max() * 1.05
    annots = [
        (x_lo, y_hi, "Expansion Opportunity"),
        (x_hi, y_hi, "Mature / Competitive"),
        (x_lo, y_lo, "Emerging / Monitor"),
        (x_hi, y_lo, "Potentially Overserved"),
    ]
    for x, y, label in annots:
        fig.add_annotation(x=x, y=y, text=f"<b>{label}</b>", showarrow=False,
                            font=dict(size=11, color=NEUTRAL_GREY), opacity=0.85)

    fig.update_layout(height=height, legend_title_text="Market Segment", margin=dict(t=20, b=10))
    return fig


def opportunity_map(scored_df: pd.DataFrame, screening_df: pd.DataFrame, height: int = 560) -> go.Figure:
    """India Market Opportunity Map. Bubbles are city-level markets, not exact dark-store locations."""
    fig = go.Figure()

    if len(screening_df) > 0:
        fig.add_trace(go.Scattergeo(
            lat=screening_df["latitude"], lon=screening_df["longitude"],
            text=screening_df["city"],
            customdata=screening_df[["confidence", "population_2011_census"]],
            hovertemplate=(
                "<b>%{text}</b><br>Status: Requires further investigation<br>"
                "%{customdata[0]}<br>Population (2011 Census): %{customdata[1]:,}<extra></extra>"
            ),
            marker=dict(
                size=(screening_df["population_2011_census"] / screening_df["population_2011_census"].max() * 32 + 6),
                color="rgba(0,0,0,0)", line=dict(width=1.5, color=NEUTRAL_GREY), symbol="circle",
            ),
            name="Requires further investigation",
        ))

    if len(scored_df) > 0:
        fig.add_trace(go.Scattergeo(
            lat=scored_df["latitude"], lon=scored_df["longitude"],
            text=scored_df["city"],
            customdata=scored_df[["screening_score", "total_stores", "population_2011_census", "tier"]],
            hovertemplate=(
                "<b>%{text}</b><br>Tier: %{customdata[3]}<br>Expansion Screening Score: %{customdata[0]:.2f}<br>"
                "Current stores: %{customdata[1]}<br>Population (2011 Census): %{customdata[2]:,}<extra></extra>"
            ),
            marker=dict(
                size=(scored_df["population_2011_census"] / scored_df["population_2011_census"].max() * 40 + 10),
                color=scored_df["screening_score"], colorscale=SEQUENTIAL_SCALE, showscale=True,
                colorbar=dict(title="Expansion<br>Screening<br>Score", len=0.6, thickness=14),
                line=dict(width=0.5, color="white"),
            ),
            name="Confirmed & scored",
        ))

    fig.update_geos(
        scope="asia", lataxis_range=[6, 35], lonaxis_range=[68, 92],
        showcountries=True, countrycolor=NEUTRAL_GREY, showland=True, landcolor="#F5F6F8",
        showocean=True, oceancolor="#EAF1F6",
    )
    fig.update_layout(
        height=height, margin=dict(l=0, r=0, t=10, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=0.02, xanchor="left", x=0.01,
                    bgcolor="rgba(255,255,255,0.7)"),
    )
    return fig


def platform_stack_chart(df: pd.DataFrame, height: int = 420) -> go.Figure:
    melted = df.melt(id_vars="city", value_vars=PLATFORM_COLS, var_name="platform_key", value_name="Stores").dropna()
    melted["Company"] = melted["platform_key"].map(PLATFORM_LABELS)
    fig = px.bar(melted, x="city", y="Stores", color="Company", barmode="stack",
                 color_discrete_map=PLATFORM_COLORS, labels={"city": ""})
    fig.update_layout(height=height, legend_title_text="", margin=dict(t=20, b=10))
    return fig


def platform_presence_heatmap(df: pd.DataFrame, height: int = 460) -> go.Figure:
    """Rows = cities, columns = companies, values = store count where available."""
    mat = df.set_index("city")[PLATFORM_COLS].rename(columns=PLATFORM_LABELS)
    fig = px.imshow(
        mat, color_continuous_scale=SEQUENTIAL_SCALE, aspect="auto",
        labels=dict(x="Company", y="", color="Stores"),
    )
    fig.update_layout(height=height, margin=dict(t=20, b=10))
    return fig


def scenario_rank_heatmap(pivot: pd.DataFrame, height: int = 520) -> go.Figure:
    """Lower rank number = higher priority, so a reversed scale keeps rank 1 the darkest cell."""
    mat = pivot.set_index("city")
    fig = px.imshow(
        mat, color_continuous_scale="Teal_r", aspect="auto", text_auto=True,
        labels=dict(x="Scenario", y="", color="Rank"),
    )
    fig.update_layout(height=height, margin=dict(t=20, b=10))
    return fig


# ----------------------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------------------
st.title("Quick-Commerce Dark Store Expansion Analysis")
st.caption("India-wide market screening and location intelligence for quick-commerce expansion.")

with st.expander("About this project (read first)", expanded=False):
    st.markdown(
        """
**Business question:** where should a quick-commerce company consider establishing its next
dark store, across metro, non-metro and Tier 2 markets, not only the largest cities? This is
a business-analytics exploration built on real, cited public data, not on Blinkit/Zepto/
Instamart internal data, and it does not claim to reproduce any company's actual decisions.

- Store-count data: **QuickCommerceMap**, a third-party, observed/reporting-based compilation
  from public store-locator and serviceability data, July 2026. Described by its own source as
  a lower bound, not a full census, and as a live, monthly-updated dataset.
- Population data: **Census of India 2011** (district-level, the latest publicly available
  full census).
- The **Expansion Priority** score covers 18 of the 20 confirmed-count cities. Navi Mumbai and
  Thane are excluded from scoring only, see the note below and the Limitations tab.
- Cities without a published store count sit in a separate, unscored **Market Screening**
  layer.

All city-level maps and bubbles represent **markets**, not exact dark-store addresses.
        """
    )
    st.info(f"**Scoring exclusion:** {EXCLUSION_REASON}")

tabs = st.tabs([
    "Executive Overview", "Market Landscape", "Competitive Landscape", "State View",
    "Tier 2 & Emerging Markets", "Expansion Priority", "Market Explorer", "Key Insights", "Limitations",
])
(tab_exec, tab_network, tab_competitive, tab_states, tab_tier2,
 tab_ranking, tab_explorer, tab_insights, tab_limits) = tabs

# ----------------------------------------------------------------------------------
# Executive Overview
# ----------------------------------------------------------------------------------
with tab_exec:
    # Two-layer analytical structure, made visible at the top of the overview
    a1, a2 = st.columns(2)
    with a1:
        st.info(
            f"**Market Screening Universe: {len(covered) + len(screening)} markets**  \n"
            "All Indian markets for which population or reported presence data is available, "
            "including Tier 1 Metro, Tier 1 Non-Metro, Tier 2 and emerging cities."
        )
    with a2:
        st.success(
            f"**Quantitative Expansion Screening: {len(scored_balanced)} markets**  \n"
            "The subset where confirmed store counts allow a defensible score: "
            "Market Size Score, Coverage Opportunity Score, Expansion Screening Score, "
            "and Implied Coverage Gap to Median."
        )

    # Data availability note, framed as an analytical decision not a weakness
    st.caption(
        "**Data availability:** quantitative expansion scoring is limited to 18 markets "
        "because confirmed store counts are publicly available for only 20 cities, of which "
        "Navi Mumbai and Thane are excluded due to incompatible Census geography (both share "
        "the same Thane district population figure, making population-based comparisons "
        "unreliable). An additional 13 markets remain in the screening layer but cannot be "
        "scored without confirmed store-count data. This separation is an analytical "
        "data-quality decision, not a deliberate exclusion of Tier 2 or smaller cities."
    )

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Markets screened", len(covered) + len(screening))
    k2.metric("Markets quantitatively scored", len(scored_balanced))
    k3.metric("Companies covered", 5)
    k4.metric("Dark stores observed", f"{int(covered['total_stores'].sum()):,}")
    high_opp = (scored_balanced["screening_tier"] == "High priority").sum()
    k5.metric("High-priority scored markets", int(high_opp))

    st.markdown("#### India Market Screening Map")
    st.caption(
        "City-level market screening, not exact dark-store locations. "
        "Scored markets (filled bubbles): bubble size = market population, colour = "
        "Expansion Screening Score (Balanced scenario). "
        "Markets requiring further investigation (hollow grey circles): population or "
        "presence information available, but no confirmed store count for quantitative scoring."
    )
    st.plotly_chart(opportunity_map(scored_balanced, screening), use_container_width=True)

    st.markdown("#### Market Size Proxy vs Dark-Store Coverage")
    st.caption(
        "Which scored markets combine a large market-size proxy with relatively low "
        "dark-store coverage? Quadrant labels are analytical interpretations relative to "
        "the median of the 18 scored markets, not absolute or company-verified categories."
    )
    st.plotly_chart(quadrant_matrix_chart(scored_balanced, height=480), use_container_width=True)

    st.markdown("#### Top Expansion Priority Markets (Balanced scenario)")
    top10 = scored_balanced.head(10).sort_values("screening_score")
    fig_top = px.bar(top10, x="screening_score", y="city", orientation="h", color="tier",
                      color_discrete_map=TIER_COLORS, labels={"screening_score": "Expansion Screening Score", "city": ""})
    fig_top.update_layout(height=420, legend_title_text="Tier", margin=dict(t=10, b=10))
    st.plotly_chart(fig_top, use_container_width=True)

    st.markdown("#### KEY TAKEAWAYS")
    top_city_desc = scored_balanced.iloc[0]
    resilient = scenario_resilience()
    fully_resilient = resilient[resilient["scenarios_in_top"] == resilient["n_scenarios"].iloc[0]]

    # Verify the "what this means" statement before displaying it
    demand_led_check = build_scored_table("Demand-led")
    demand_top5_metros = (demand_led_check.head(5)["tier"] == "Tier 1 Metro").sum()
    coverage_led_check = build_scored_table("Coverage-led")
    coverage_top5_metros = (coverage_led_check.head(5)["tier"] == "Tier 1 Metro").sum()
    what_this_means_supported = demand_top5_metros >= 3 and coverage_top5_metros == 0

    takeaways = [
        f"**{top_city_desc['city']}** ranks highest on the Balanced Expansion Screening "
        f"Score, driven by a large market-size proxy relative to its "
        f"{int(top_city_desc['total_stores'])} confirmed stores.",
        f"**{len(fully_resilient)} of {len(scored_balanced)}** scored markets stay in the "
        "top 10 under every scenario tested, a strategy-agnostic shortlist for further "
        "investigation (see Expansion Priority tab).",
        "Coverage headroom in the 18-city scored sample is not concentrated in India's "
        "largest metros: all five markets with the largest benchmark-based coverage gaps "
        "(Patna 106, Jaipur 98, Ahmedabad 84, Nagpur 83, Kanpur 81) are Tier 1 Non-Metro "
        "or Tier 2. This is a finding within the scored sample, not a claim about all "
        "Indian cities.",
        f"**{len(screening)} additional markets** in the screening layer lack a confirmed "
        "store count and cannot be quantitatively scored with the current public data.",
    ]
    if what_this_means_supported:
        takeaways.insert(3,
            "Large metros rank higher when market size is the primary driver (Demand-led "
            "scenario): the top 5 under Demand-led are predominantly Tier 1 Metro. Under "
            "Coverage-led, the top 5 shift entirely to Tier 1 Non-Metro and Tier 2 markets. "
            "This confirms that expansion opportunity is scenario-sensitive, not metro-only."
        )
    for t in takeaways:
        st.markdown(f"- {t}")

# ----------------------------------------------------------------------------------
# Market Landscape (descriptive, includes Navi Mumbai/Thane)
# ----------------------------------------------------------------------------------
with tab_network:
    st.subheader("Existing Quick-Commerce Market Landscape")
    st.caption(
        "Descriptive view of confirmed store counts. City-level, not individual store addresses. "
        "Includes Navi Mumbai and Thane, which are excluded only from scoring, see below."
    )
    company_filter = st.multiselect(
        "Filter by company (bubble size = total stores unless a single company is chosen)",
        ["All companies"] + list(PLATFORM_LABELS.values()), default=["All companies"],
    )

    plot_df = covered.dropna(subset=["latitude", "longitude"]).copy()
    if "All companies" in company_filter or not company_filter:
        plot_df["map_value"] = plot_df["total_stores"]
        size_label = "Total dark stores"
    else:
        rev_map = {v: k for k, v in PLATFORM_LABELS.items()}
        cols = [rev_map[c] for c in company_filter if c in rev_map]
        plot_df["map_value"] = plot_df[cols].sum(axis=1)
        size_label = " + ".join(company_filter)

    fig_map = px.scatter_geo(
        plot_df, lat="latitude", lon="longitude", size="map_value", hover_name="city", color="tier",
        color_discrete_map=TIER_COLORS,
        hover_data={"latitude": False, "longitude": False, "map_value": True, "population_2011_census": ":,"},
        scope="asia", size_max=40,
    )
    fig_map.update_geos(lataxis_range=[6, 35], lonaxis_range=[68, 92], showland=True, landcolor="#F5F6F8")
    fig_map.update_layout(height=520, margin=dict(l=0, r=0, t=10, b=0), legend_title_text="Tier")
    st.plotly_chart(fig_map, use_container_width=True)
    st.caption(f"Bubble size = {size_label}. City-level market bubbles, not exact store locations.")

    if any(c in plot_df["city"].values for c in EXCLUDED_FROM_SCORING):
        st.caption(f"Note: {EXCLUSION_REASON}")

    st.markdown("##### Named coverage hotspots (from source report)")
    st.dataframe(
        covered[["city", "tier", "total_stores", "data_confidence", "hotspot_localities"]].rename(columns={
            "city": "City", "tier": "Tier", "total_stores": "Total stores",
            "data_confidence": "Data confidence", "hotspot_localities": "Hotspot localities",
        }), use_container_width=True, hide_index=True,
    )

# ----------------------------------------------------------------------------------
# Competitive landscape
# ----------------------------------------------------------------------------------
with tab_competitive:
    st.subheader("Competitive Landscape")
    st.caption("Question: how does competitive presence differ across markets?")

    breakdown_cities = covered[covered["platforms_breakdown_available"] == "TRUE"].copy()

    # Compute observed dark-store share for each platform (denominator = sum of five platform
    # columns, NOT total_stores, so the shares sum to 100% within the platform breakdown).
    breakdown_cities["platform_total"] = breakdown_cities[PLATFORM_COLS].sum(axis=1)
    for col in PLATFORM_COLS:
        breakdown_cities[f"share_{col}"] = (
            breakdown_cities[col] / breakdown_cities["platform_total"] * 100
        ).round(1)
    share_cols = [f"share_{c}" for c in PLATFORM_COLS]
    breakdown_cities["leading_platform_col"] = (
        breakdown_cities[share_cols].idxmax(axis=1).str.replace("share_", "")
    )
    breakdown_cities["leading_platform"] = breakdown_cities["leading_platform_col"].map(PLATFORM_LABELS)
    breakdown_cities["leading_share_pct"] = breakdown_cities[share_cols].max(axis=1).round(1)
    breakdown_cities["market_structure"] = breakdown_cities["leading_share_pct"].apply(
        lambda x: "Majority-led" if x > 50 else "Fragmented / Contested"
    )

    # Summary stats (computed from data, not hardcoded)
    n_breakdown = len(breakdown_cities)
    n_majority = int((breakdown_cities["market_structure"] == "Majority-led").sum())
    n_fragmented = int((breakdown_cities["market_structure"] == "Fragmented / Contested").sum())
    top_leading_platform = (
        breakdown_cities.groupby("leading_platform")["city"].count().idxmax()
    )
    top_leading_count = int(
        breakdown_cities.groupby("leading_platform")["city"].count().max()
    )

    st.markdown("##### Platform Presence by City")
    st.plotly_chart(platform_presence_heatmap(breakdown_cities), use_container_width=True)
    st.caption(
        "Observed store counts across all five platforms, for the 14 cities where a full "
        "platform-level breakdown is publicly available."
    )

    st.markdown("##### Company Footprint")
    footprint = pd.DataFrame({
        "Company": list(PLATFORM_LABELS.values()),
        f"Markets present (of {n_breakdown} with breakdown)": [breakdown_cities[c].gt(0).sum() for c in PLATFORM_COLS],
        f"Total stores (of these {n_breakdown} markets)": [int(breakdown_cities[c].sum()) for c in PLATFORM_COLS],
    })
    fig_footprint = px.bar(
        footprint, x="Company", y=f"Markets present (of {n_breakdown} with breakdown)",
        color="Company", color_discrete_map=PLATFORM_COLORS,
    )
    fig_footprint.update_layout(height=320, showlegend=False, margin=dict(t=20, b=10))
    st.plotly_chart(fig_footprint, use_container_width=True)

    st.markdown("##### Competitive Intensity: How Many Platforms Compete in Each Market?")
    st.caption(
        "A separate decision lens, not part of the Expansion Screening Score, because platform "
        "breakdown is only published for 14 of the 20 confirmed cities."
    )
    intensity_df = breakdown_cities.copy()
    intensity_df["platforms_present_count"] = intensity_df["platforms_present_count"].astype(int)
    fig_intensity = px.bar(
        intensity_df.sort_values("platforms_present_count"), x="platforms_present_count", y="city",
        orientation="h", color="tier", color_discrete_map=TIER_COLORS,
        labels={"platforms_present_count": "Platforms present", "city": ""},
    )
    fig_intensity.update_layout(height=420, legend_title_text="Tier", margin=dict(t=20, b=10))
    st.plotly_chart(fig_intensity, use_container_width=True)

    # -----------------------------------------------------------------------
    # Observed dark-store share and market structure
    # -----------------------------------------------------------------------
    st.markdown("##### Observed Dark-Store Share and Market Structure")
    st.caption(
        "For each city, each platform's share of observed dark stores within the five-platform "
        "breakdown. This is **observed dark-store share**, not actual market share by customers "
        "or revenue."
    )

    # Share bar chart, sorted by leading share descending
    share_display = breakdown_cities.sort_values("leading_share_pct", ascending=False)
    share_melted = share_display.melt(
        id_vars="city", value_vars=share_cols, var_name="platform_key", value_name="share_pct",
    )
    share_melted["Company"] = share_melted["platform_key"].str.replace("share_", "").map(PLATFORM_LABELS)
    fig_share = px.bar(
        share_melted, x="share_pct", y="city", orientation="h", color="Company",
        barmode="stack", color_discrete_map=PLATFORM_COLORS,
        labels={"share_pct": "Observed dark-store share (%)", "city": ""},
        hover_data={"platform_key": False},
    )
    fig_share.update_layout(height=460, legend_title_text="", margin=dict(t=20, b=10))
    fig_share.add_vline(x=50, line_dash="dot", line_color=NEUTRAL_GREY,
                         annotation_text="50% threshold", annotation_position="top right")
    st.plotly_chart(fig_share, use_container_width=True)

    # Market structure summary table
    summary_cols = ["city", "tier", "leading_platform", "leading_share_pct", "market_structure"]
    st.dataframe(
        breakdown_cities[summary_cols].rename(columns={
            "city": "City", "tier": "Tier",
            "leading_platform": "Leading platform",
            "leading_share_pct": "Leading observed share (%)",
            "market_structure": "Market structure",
        }).sort_values("Leading observed share (%)", ascending=False),
        use_container_width=True, hide_index=True,
    )

    # Two data-backed business insights
    st.markdown("##### Business Insights")
    st.info(
        f"**{n_fragmented} of {n_breakdown}** markets with a published breakdown are classified as "
        f"**Fragmented / Contested**: no single platform exceeds 50% of observed dark stores in any "
        "of the 14 markets analysed. This suggests that even where one platform leads, the market "
        "remains structurally open to challenge."
    )
    st.info(
        f"**{top_leading_platform}** holds the largest observed dark-store share in "
        f"**{top_leading_count} of {n_breakdown}** markets, yet its leading share across those "
        f"cities peaks at {breakdown_cities['leading_share_pct'].max():.0f}%, short of majority "
        "control. Platform leadership in this market is broad but not dominant."
    )
    st.caption(
        "Source: QuickCommerceMap, July 2026 compilation. Platform breakdown available for "
        f"{n_breakdown} of 20 confirmed cities. Shares are computed from observed store counts "
        "only; they do not represent customer numbers, order volume, or revenue."
    )

# ----------------------------------------------------------------------------------
# State view
# ----------------------------------------------------------------------------------
with tab_states:
    st.subheader("State-Level Picture")
    st.caption(
        "Real, cited state-level totals. A state with more stores may simply have more large "
        "cities, raw store counts should not be read as market attractiveness on their own."
    )

    fig_state = px.bar(
        state_coverage.sort_values("total_stores", ascending=True),
        x="total_stores", y="state", orientation="h",
        labels={"total_stores": "Dark stores", "state": ""}, text="national_share_pct",
        color_discrete_sequence=[TIER_COLORS["Tier 1 Metro"]],
    )
    fig_state.update_traces(texttemplate="%{text}%", textposition="outside")
    fig_state.update_layout(height=380, margin=dict(t=20, b=10))
    st.plotly_chart(fig_state, use_container_width=True)

    st.dataframe(
        state_coverage[["state", "total_stores", "cities_count", "national_share_pct", "note"]].rename(columns={
            "state": "State", "total_stores": "Total stores", "cities_count": "Cities",
            "national_share_pct": "National share (%)", "note": "Note",
        }), use_container_width=True, hide_index=True,
    )

    state_cities = covered.groupby("state").agg(
        confirmed_markets=("city", "count"), avg_stores_per_million=("stores_per_million_2011pop", "mean"),
    ).reset_index().sort_values("confirmed_markets", ascending=False)
    st.markdown("##### Confirmed Markets and Average Coverage by State (this project's 20-city dataset)")
    st.dataframe(state_cities.rename(columns={
        "state": "State", "confirmed_markets": "Confirmed markets in this dataset",
        "avg_stores_per_million": "Avg. stores per million (2011 pop.)",
    }).round(1), use_container_width=True, hide_index=True)
    st.caption(
        "Karnataka's state total is 87% Bangalore alone; Tamil Nadu's spreads more evenly across "
        "Chennai and a Coimbatore-Madurai-Trichy corridor. Concentration in one metro is a "
        "structural signal, not necessarily a strength."
    )

# ----------------------------------------------------------------------------------
# Tier 2 and emerging markets
# ----------------------------------------------------------------------------------
with tab_tier2:
    st.subheader("Tier 2 and Emerging Markets")
    st.caption(
        "Question: are smaller and emerging markets simply smaller versions of metros, or do they "
        "show different expansion characteristics? Official tier framework: Tier 1 Metro (Delhi "
        "NCR, Mumbai, Bangalore, Hyderabad, Chennai, Kolkata, Pune). Tier 1 Non-Metro (Ahmedabad, "
        "Jaipur, Lucknow, Chandigarh, Kochi, Indore). Tier 2 (all other cities)."
    )

    t1, t2, t3 = st.columns(3)
    tier_counts = covered["tier"].value_counts()
    t1.metric("Confirmed Tier 2 cities", int(tier_counts.get("Tier 2", 0)))
    t2.metric("Named growth markets (no count)", len(named_growth))
    t3.metric("Unconfirmed cities flagged", len(unconfirmed))

    st.markdown("##### Chart 1: Dark Stores by Market Segment")
    dist_by_stores = covered.groupby("tier")["total_stores"].sum().reset_index()
    fig_d2 = px.pie(dist_by_stores, names="tier", values="total_stores", color="tier",
                     color_discrete_map=TIER_COLORS, hole=0.45)
    fig_d2.update_layout(height=340, margin=dict(t=20, b=10))
    st.plotly_chart(fig_d2, use_container_width=True)

    st.markdown("##### Chart 2: Tier 2 Market Comparison")
    tier2_cities = covered[covered["tier"] == "Tier 2"].sort_values("total_stores", ascending=False)
    fig_t2cmp = go.Figure()
    fig_t2cmp.add_trace(go.Bar(x=tier2_cities["city"], y=tier2_cities["total_stores"], name="Total stores",
                                marker_color=TIER_COLORS["Tier 2"]))
    fig_t2cmp.add_trace(go.Scatter(x=tier2_cities["city"], y=tier2_cities["stores_per_million_2011pop"],
                                    name="Stores per million pop.", yaxis="y2",
                                    mode="lines+markers", marker_color=TIER_COLORS["Tier 1 Metro"]))
    fig_t2cmp.update_layout(
        height=380, margin=dict(t=20, b=10),
        yaxis=dict(title="Total stores"), yaxis2=dict(title="Stores per million", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    st.plotly_chart(fig_t2cmp, use_container_width=True)

    st.markdown("##### Chart 3: Tier 2 Competitive Presence")
    breakdown_t2 = tier2_cities[tier2_cities["platforms_breakdown_available"].isin(["TRUE", "PARTIAL"])]
    st.plotly_chart(platform_stack_chart(breakdown_t2, height=360), use_container_width=True)
    st.caption(
        "Patna's Zepto count is confirmed zero, not missing data. Flipkart Minutes ranks second "
        "behind Blinkit there, a reversal of the national platform order."
    )

    st.markdown("##### Chart 4: Tier 2 Market Size Proxy vs Dark-Store Coverage")
    scored_t2 = build_scored_table("Balanced", tiers=["Tier 2"])
    cov_med_t2 = scored_t2["stores_per_million_2011pop"].median()
    pot_med_t2 = scored_t2["population_2011_census"].median()
    scored_t2["quadrant"] = scored_t2.apply(lambda r: quadrant_label(r, cov_med_t2, pot_med_t2), axis=1)
    if len(scored_t2) >= 2:
        st.plotly_chart(quadrant_matrix_chart(scored_t2, height=420), use_container_width=True)
    else:
        st.info("Not enough scored Tier 2 cities to plot a meaningful matrix.")

    st.markdown("##### What Does the Data Show?")
    if len(scored_t2) > 0:
        t2_avg_cov = scored_t2["stores_per_million_2011pop"].mean()
        metro_avg_cov = build_scored_table("Balanced", tiers=["Tier 1 Metro"])["stores_per_million_2011pop"].mean()
        direction = "higher" if t2_avg_cov > metro_avg_cov else "lower"
        st.write(
            f"Average coverage among scored Tier 2 cities is {t2_avg_cov:.1f} stores per million, "
            f"{direction} than the {metro_avg_cov:.1f} average among scored Tier 1 Metro cities. "
            "This is a descriptive comparison across a small sample and not a statistically "
            "validated claim about all Tier 2 markets nationally."
        )

    st.markdown("##### What It Takes a Tier 2 City to Scale")
    st.dataframe(
        tier_benchmarks[["metric", "tier_1_metro", "tier_2", "note"]].rename(columns={
            "metric": "Metric", "tier_1_metro": "Tier 1 Metro", "tier_2": "Tier 2", "note": "Note",
        }), use_container_width=True, hide_index=True,
    )

# ----------------------------------------------------------------------------------
# Expansion Priority
# ----------------------------------------------------------------------------------
with tab_ranking:
    st.subheader("Expansion Priority")
    st.caption(
        "Scored strictly within the 18-city scoreable universe (20 confirmed-count cities, minus "
        "Navi Mumbai and Thane). No fabricated counts, no fabricated scores."
    )
    st.info(f"**Scoring exclusion:** {EXCLUSION_REASON}")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        scenario = st.selectbox("Expansion strategy scenario", list(SCENARIOS.keys()), index=0)
    with col_b:
        scope = st.selectbox("Scope", ["All 18 scored cities", "Tier 2 cities only"], index=0)
    with col_c:
        top_n = st.selectbox("Show top", [10, 15, 25], index=0)

    tier_filter = ["Tier 2"] if scope == "Tier 2 cities only" else None
    scored = build_scored_table(scenario, tiers=tier_filter)
    scored["Why?"] = scored.apply(explain_row, axis=1)

    cm = scored["stores_per_million_2011pop"].median()
    pm = scored["population_2011_census"].median()
    scored["quadrant"] = scored.apply(lambda r: quadrant_label(r, cm, pm), axis=1)

    segment_filter = st.multiselect(
        "Filter matrix by market segment", sorted(scored["quadrant"].unique().tolist()),
        default=sorted(scored["quadrant"].unique().tolist()),
    )
    matrix_df = scored[scored["quadrant"].isin(segment_filter)] if segment_filter else scored

    st.markdown("##### Market Size Proxy vs Dark-Store Coverage")
    st.plotly_chart(quadrant_matrix_chart(matrix_df), use_container_width=True)

    st.markdown(f"##### Top {min(top_n, len(scored))} Scored Cities ({scenario} scenario)")
    display_cols = ["city", "tier", "data_confidence", "screening_score", "screening_tier", "quadrant",
                     "population_2011_census", "total_stores", "stores_per_million_2011pop",
                     "implied_coverage_gap", "Why?"]
    st.dataframe(
        scored.head(top_n)[display_cols].rename(columns={
            "city": "City", "tier": "Tier", "data_confidence": "Data confidence",
            "screening_score": "Expansion Screening Score", "screening_tier": "Priority", "quadrant": "Segment",
            "population_2011_census": "Population (2011 Census)", "total_stores": "Current stores",
            "stores_per_million_2011pop": "Stores per million (2011 pop.)",
            "implied_coverage_gap": "Implied Coverage Gap to Median",
        }),
        use_container_width=True, hide_index=True,
    )
    median_spm_val = scored["median_spm_benchmark"].iloc[0]
    n_at_median = int((scored["implied_coverage_gap"] == 0).sum())
    st.caption(
        f"**Implied Coverage Gap to Median:** a benchmark-based estimate of the additional stores "
        f"implied by bringing a market to the median observed dark-store density across the {len(scored)} "
        f"scored markets ({median_spm_val:.1f} stores per million, 2011 population). "
        f"{n_at_median} of {len(scored)} cities are already at or above the median (shown as 0). "
        "This is NOT a forecast of demand, NOT an optimal store count, and NOT a recommendation "
        "to build that number of stores. The benchmark is based on observed dark-store density only."
    )

    # ------------------------------------------------------------------
    # Coverage Headroom insight + chart
    # ------------------------------------------------------------------
    st.markdown("##### Coverage Headroom")
    st.caption(
        "Which markets combine relatively low current dark-store coverage with a large absolute "
        "implied coverage gap? Figures are implied additional stores required to reach the median "
        "observed dark-store density across the scored markets, not demand forecasts."
    )

    # Compute headroom stats from live data (no hardcoding)
    gap_positive = scored[scored["implied_coverage_gap"] > 0].copy()
    gap_at_median = scored[scored["implied_coverage_gap"] == 0].copy()
    n_positive = len(gap_positive)
    n_at_med = len(gap_at_median)
    n_total = len(scored)
    pct_positive = round(100 * n_positive / n_total)
    pct_at_med = round(100 * n_at_med / n_total)

    top5_gap = gap_positive.nlargest(5, "implied_coverage_gap")
    top5_tiers = top5_gap["tier"].unique().tolist()
    all_non_metro = all(t != "Tier 1 Metro" for t in top5_gap["tier"])

    c_stat1, c_stat2 = st.columns(2)
    c_stat1.metric(
        "Markets with positive coverage headroom",
        f"{n_positive} of {n_total} ({pct_positive}%)",
        help="Scored markets with observed density below the 18-city median (28.6 stores per million)."
    )
    c_stat2.metric(
        "Markets at or above median density",
        f"{n_at_med} of {n_total} ({pct_at_med}%)",
        help="Scored markets already meeting or exceeding the observed median coverage density."
    )

    # Horizontal bar chart, top 5 only, clearly labeled
    fig_headroom = px.bar(
        top5_gap.sort_values("implied_coverage_gap"),
        x="implied_coverage_gap", y="city", orientation="h",
        color="tier", color_discrete_map=TIER_COLORS,
        labels={"implied_coverage_gap": "Implied additional stores to reach median", "city": ""},
        text="implied_coverage_gap",
    )
    fig_headroom.update_traces(textposition="outside")
    fig_headroom.update_layout(
        height=300, legend_title_text="Tier", margin=dict(t=10, b=10, l=10, r=60),
        xaxis_title="Implied additional stores to reach observed median density",
    )
    st.plotly_chart(fig_headroom, use_container_width=True)

    # Business interpretation, only stated because the data supports it
    if all_non_metro:
        interp = (
            f"All five markets with the largest implied coverage headroom are Tier 1 Non-Metro "
            f"or Tier 2 ({', '.join(top5_gap['city'].tolist())}), with none from Tier 1 Metro. "
            "This is consistent with the broader pattern that expansion opportunity, measured by "
            "this benchmark, is not concentrated in the largest metros."
        )
    else:
        t1m_cities = top5_gap[top5_gap["tier"] == "Tier 1 Metro"]["city"].tolist()
        interp = (
            f"The top 5 markets by implied coverage headroom include "
            f"{', '.join(top5_gap['city'].tolist())}. "
            f"Tier 1 Metro markets present ({', '.join(t1m_cities)}) still show a gap to the "
            "median, indicating that even some larger metros are below the observed median density."
        )
    st.markdown(f"*{interp}*")
    st.caption(
        "Implied coverage headroom is an analytical benchmark based on observed dark-store "
        "density only. It does not represent unmet customer demand, economic viability, or a "
        "recommendation that any specific number of stores should be opened."
    )

    st.markdown("##### Scenario Rank Comparison")
    st.caption("Rows = cities, columns = scenarios, values = rank (1 = highest priority under that scenario).")
    pivot = scenario_rank_table(tiers=tier_filter)
    st.plotly_chart(scenario_rank_heatmap(pivot), use_container_width=True)

    st.markdown("##### Scenario-Resilient Markets")
    st.caption("Which expansion opportunities remain attractive even when strategic priorities change?")
    resilience = scenario_resilience(tiers=tier_filter, top_n=10)
    st.dataframe(
        resilience[["city", "resilience"]].rename(columns={"city": "City", "resilience": "Scenarios in top 10"}),
        use_container_width=True, hide_index=True,
    )

    st.markdown("---")
    st.markdown("### Market Screening: Cities Requiring Further Investigation")
    st.caption(
        "These 13 cities are deliberately not scored. Scoring needs a real store count as an "
        "input, and none exists for them in the sources reviewed. Two confidence levels are kept separate."
    )

    named_view = screening[screening["confidence"] == "Named active market, no published store count"]
    unconf_view = screening[screening["confidence"] == "Not named in any source reviewed"]

    st.markdown("**Confidence: Low, named as an active or growing market, no store count published**")
    st.dataframe(
        named_view[["city", "state", "tier", "population_2011_census", "requires"]].rename(columns={
            "city": "City", "state": "State", "tier": "Tier", "population_2011_census": "Population (2011 Census)",
            "requires": "Needed before scoring",
        }), use_container_width=True, hide_index=True,
    )

    st.markdown("**Confidence: Unconfirmed, not named in any source reviewed**")
    st.dataframe(
        unconf_view[["city", "state", "population_2011_census", "requires"]].rename(columns={
            "city": "City", "state": "State", "population_2011_census": "Population (2011 Census)",
            "requires": "Needed before scoring",
        }), use_container_width=True, hide_index=True,
    )

# ----------------------------------------------------------------------------------
# Market Explorer
# ----------------------------------------------------------------------------------
with tab_explorer:
    st.subheader("Market Explorer")
    st.caption("Select any market, confirmed or under investigation, for a full profile and an auto-generated read.")

    confirmed_names = sorted(covered["city"].tolist())
    screening_names = sorted(screening["city"].tolist())
    choice = st.selectbox(
        "Select a market",
        ["-- Confirmed markets --"] + confirmed_names + ["-- Requires further investigation --"] + screening_names,
    )

    if choice in confirmed_names:
        row = covered[covered["city"] == choice].iloc[0]
        is_scored = choice not in EXCLUDED_FROM_SCORING
        scored_all = build_scored_table("Balanced")
        rank_pivot = scenario_rank_table()

        st.markdown("#### Market Profile")
        p1, p2, p3 = st.columns(3)
        p1.markdown(f"**City:** {choice}")
        p2.markdown(f"**State:** {row['state']}")
        p3.markdown(f"**Market segment (tier):** {row['tier']}")

        st.markdown("#### Market Size")
        s1, s2 = st.columns(2)
        s1.metric("Population (2011 Census)", f"{row['population_2011_census']:,.0f}")
        s2.metric("Population rank (of 20 confirmed cities)", int(row["population_rank"]))

        st.markdown("#### Quick-Commerce Coverage")
        c1, c2 = st.columns(2)
        c1.metric("Dark stores", int(row["total_stores"]))
        c2.metric("Stores per million population", f"{row['stores_per_million_2011pop']:.1f}")

        st.markdown("#### Competition")
        if row["platforms_breakdown_available"] in ("TRUE", "PARTIAL"):
            plat_row = pd.DataFrame({
                "Company": [PLATFORM_LABELS[c] for c in PLATFORM_COLS],
                "Stores": [row[c] for c in PLATFORM_COLS],
            }).dropna()
            comp1, comp2 = st.columns([1, 2])
            comp1.metric("Platforms present", int(row["platforms_present_count"]) if pd.notna(row["platforms_present_count"]) else "N/A")
            with comp2:
                fig_city = px.bar(plat_row, x="Company", y="Stores", color="Company", color_discrete_map=PLATFORM_COLORS)
                fig_city.update_layout(height=280, showlegend=False, margin=dict(t=10, b=10))
                st.plotly_chart(fig_city, use_container_width=True)
        else:
            st.info("Platform-level breakdown not published for this city; only the total store count is confirmed.")

        st.markdown("#### Expansion")
        e1, e2, e3 = st.columns(3)
        if is_scored:
            srow = scored_all[scored_all["city"] == choice].iloc[0]
            e1.metric("Expansion Screening Score (Balanced)", f"{srow['screening_score']:.2f}", srow["screening_tier"])
            city_ranks = rank_pivot[rank_pivot["city"] == choice]
            rank_str = ", ".join(f"{s}: #{int(city_ranks[s].iloc[0])}" for s in SCENARIOS) if len(city_ranks) else "N/A"
            e2.markdown(f"**Scenario ranks**  \n{rank_str}")
            e3.metric("Data confidence", row["data_confidence"])

            gap = int(srow["implied_coverage_gap"])
            median_bench = float(srow["median_spm_benchmark"])
            if gap > 0:
                st.metric(
                    "Implied Coverage Gap to Median",
                    f"{gap} stores",
                    help=(
                        f"Benchmark-based estimate of additional stores implied by bringing this "
                        f"market to the scored-set median of {median_bench:.1f} stores per million "
                        f"(2011 population). Not a demand forecast, not an optimal store count, "
                        "and not a recommendation to build that number of stores."
                    ),
                )
            else:
                st.metric(
                    "Implied Coverage Gap to Median",
                    "At or above median",
                    help=(
                        f"This market's observed density ({row['stores_per_million_2011pop']:.1f} "
                        f"stores per million) already meets or exceeds the scored-set median of "
                        f"{median_bench:.1f} stores per million (2011 population)."
                    ),
                )
        else:
            e1.metric("Expansion Screening Score", "Excluded from scoring")
            e2.markdown(f"**Reason**  \n{EXCLUSION_REASON}")
            e3.metric("Data confidence", row["data_confidence"])

        st.markdown("#### Business Interpretation")
        insight_lines = []
        if is_scored:
            insight_lines.append(explain_row(srow))
        else:
            insight_lines.append(
                f"{choice} is excluded from Expansion Priority scoring. {EXCLUSION_REASON} It remains "
                "useful for descriptive network and competitive analysis."
            )
        if row["stores_per_million_2011pop"] > covered["stores_per_million_2011pop"].median():
            insight_lines.append("Dark-store density here is above the median of the 20 confirmed cities.")
        else:
            insight_lines.append("Dark-store density here is below the median of the 20 confirmed cities.")
        if pd.notna(row.get("platforms_present_count")) and row["platforms_present_count"] >= 4:
            insight_lines.append(f"Competitive intensity is high: {int(row['platforms_present_count'])} of 5 platforms are present.")
        for line in insight_lines:
            st.write(f"- {line}")
        st.caption(f"Named hotspot localities: {row['hotspot_localities']}")

    elif choice in screening_names:
        row = screening[screening["city"] == choice].iloc[0]
        st.markdown("#### Market Profile")
        p1, p2, p3 = st.columns(3)
        p1.markdown(f"**City:** {choice}")
        p2.markdown(f"**State:** {row['state']}")
        p3.markdown(f"**Market segment (tier):** {row['tier']}")

        st.markdown("#### Market Size")
        s1, s2 = st.columns(2)
        s1.metric("Population (2011 Census)", f"{row['population_2011_census']:,.0f}")
        s2.metric("Population rank (among screening markets)", int(row["population_rank"]))

        st.markdown("#### Quick-Commerce Coverage")
        st.info("Not available. This market has no published store count in the sources reviewed.")

        st.markdown("#### Expansion")
        st.metric("Expansion Screening Score", "Not scored")
        st.metric("Data confidence", row["data_confidence"])

        st.markdown("#### Business Interpretation")
        st.write(
            f"- {choice} is not part of the scored universe. Confidence level: {row['data_confidence']} "
            f"({row['confidence']})."
        )
        st.write(f"- Before this market could be scored, the project would need: {row['requires'].lower()}.")
        st.write(
            f"- Population alone ({row['population_2011_census']:,} per 2011 Census) does not "
            "substitute for a confirmed store count."
        )
        st.caption(f"Note: {row['note']}")

# ----------------------------------------------------------------------------------
# Key insights
# ----------------------------------------------------------------------------------
with tab_insights:
    st.subheader("Key Insights")
    top_density = covered.sort_values("stores_per_million_2011pop", ascending=True).iloc[0]
    dense_density = covered.sort_values("stores_per_million_2011pop", ascending=False).iloc[0]
    top_city = covered.sort_values("total_stores", ascending=False).iloc[0]
    top_priority = scored_balanced.iloc[0]
    resilient = scenario_resilience()
    fully_resilient = resilient[resilient["scenarios_in_top"] == resilient["n_scenarios"].iloc[0]]

    # Compute coverage gap insight from live data
    gap_series = scored_balanced[["city", "implied_coverage_gap"]].sort_values("implied_coverage_gap", ascending=False)
    top3_gap = gap_series[gap_series["implied_coverage_gap"] > 0].head(3)
    top3_str = "; ".join(
        f"{r['city']} ({int(r['implied_coverage_gap'])} stores)" for _, r in top3_gap.iterrows()
    )
    n_at_median_insight = int((gap_series["implied_coverage_gap"] == 0).sum())
    median_bench_insight = round(float(scored_balanced["median_spm_benchmark"].iloc[0]), 1)

    insights = [
        f"**Market concentration:** quick commerce is still overwhelmingly urban and top-heavy "
        f"nationally, the top 20 cities hold roughly two-thirds of all 5,625 mapped stores, and "
        "the remaining 388 cities average only about 5 stores each.",

        f"**Coverage gap:** **{top_priority['city']}** ranks highest on the Balanced Expansion "
        f"Priority score among the 18 scored cities, a large population base relative to its "
        f"current {int(top_priority['total_stores'])} confirmed stores.",

        f"**Coverage gap:** **{top_density['city']}** has the lowest dark-store density relative "
        f"to population among confirmed cities ({top_density['stores_per_million_2011pop']:.1f} "
        "stores per million), while **" + dense_density['city'] + f"** has the highest "
        f"({dense_density['stores_per_million_2011pop']:.1f}), closer to saturation.",

        f"**Implied coverage gap:** the three scored markets with the largest gap to the "
        f"observed median density ({median_bench_insight} stores per million, 2011 population) "
        f"are {top3_str}. {n_at_median_insight} of 18 scored cities are already at or above "
        "the median. This is a benchmark-based estimate using observed dark-store density only, "
        "not a forecast of demand or an optimal store count. It identifies which large markets "
        "appear relatively underpenetrated by the existing network, not whether customers or "
        "economics support additional stores.",

        "**Competitive maturity:** all 14 markets with a published platform breakdown are "
        "Fragmented / Contested, no single platform exceeds 50% of observed dark stores in any "
        "confirmed market. Blinkit leads in 11 of 14 markets by observed store count, but its "
        "highest observed share in any single market is 42%, leaving room for challengers in "
        "every city where data exists.",

        f"**Emerging markets:** Tier 2 cities are not a single story. Lucknow (135 stores) is "
        "nearly as contested as a small metro with all five platforms present, while Patna has "
        "zero confirmed Zepto stores and Flipkart Minutes, not Zepto or Swiggy, holds the "
        "second-largest fleet there, a genuinely different competitive pattern from the metros.",

        f"**Scenario robustness:** {len(fully_resilient)} of {len(scored_balanced)} scored "
        "markets remain in the top 10 across all three scenarios tested (Balanced, Demand-led, "
        "Coverage-led), a useful, strategy-agnostic shortlist for management to investigate first.",

        f"**Data quality:** {len(named_growth)} cities (Indore, Chandigarh, Kochi, Coimbatore, "
        "Bhopal) are named as active markets in the source reports but have no published store "
        "count, an honest gap this project keeps separate from the scored universe rather than "
        "guessing a number.",
    ]
    for i in insights:
        st.markdown(f"- {i}")

# ----------------------------------------------------------------------------------
# Limitations
# ----------------------------------------------------------------------------------
with tab_limits:
    st.subheader("Limitations")
    st.markdown(
        """
- **No store-level coordinates.** Blinkit, Zepto and Swiggy Instamart do not publish store
  locations. This project deliberately does not attempt to reverse-engineer their apps, so all
  analysis here is at the **city level**, not individual dark-store addresses. Every map in
  this dashboard is explicitly labeled as a market map, not a store-location map.
- **Third-party, observed/reporting-based store counts, not company-disclosed data.** The
  QuickCommerceMap figures are described by their own source as a lower bound compiled from
  public store-locator and serviceability data as of July 2026, not an official company
  disclosure or a guaranteed full census of every store.
- **This is a live, monthly-updated dataset, not a fixed truth.** Earlier snapshots of the same
  report series showed different totals for the same cities (Bangalore has been reported
  anywhere from roughly 438 to 629 stores depending on the snapshot). Every figure here is
  pinned to the July 2026 compilation specifically.
- **Population data is from the 2011 Census**, the most recent full public census available.
  India's urban population has grown materially since 2011; current rankings could differ.
- **Navi Mumbai and Thane are excluded from Expansion Priority scoring**, not merely flagged.
  """ + EXCLUSION_REASON + """
  They remain visible in Market Landscape, Competitive Landscape and Market Explorer.
- **The Expansion Priority score covers 18 cities.** Cities without a published store count sit
  in the unscored Market Screening layer, not with an estimated or interpolated score.
- **Coverage Opportunity and stores-per-million measure the same underlying signal.** A separate
  "Competitive Whitespace" factor built the same way was removed rather than kept, to avoid
  double-counting one signal under two labels.
- **Competitive Intensity (platform count) is a decision lens, not a scored factor**, because
  platform breakdown is only published for 14 of the 20 confirmed cities.
- **No accessibility or income data** used or invented.
- **No SKU/assortment or sales data** used or invented. See the README's Future Work section
  for what a location-specific assortment analysis would require.
- **Correlation, not causation.** This project describes where stores and population/coverage
  patterns coincide; it does not claim to know why a company chose a given location, or to
  reproduce any company's actual site-selection process.
- **City-level screening is not site selection.** This project identifies which markets deserve
  further investigation. It does not identify which exact street or address should receive a
  store, see the README's "From Market Screening to Dark-Store Decision" section for the fuller
  decision funnel.
        """
    )
