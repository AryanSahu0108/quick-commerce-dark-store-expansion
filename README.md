# Quick-Commerce Dark Store Expansion Analysis

> India-wide market screening and location intelligence for quick-commerce expansion.

**Project period:** December 2025 - January 2026  
**Project type:** Self-Project

## 1. Motivation

I was curious about how quick-commerce companies decide where to expand their dark-store network. I used publicly available market, demographic and dark-store coverage data to investigate where expansion opportunities may exist across India, not only in the largest metros, across Blinkit, Zepto, Swiggy Instamart, Flipkart Minutes and BigBasket.


## 2. Business Question

**Where should a quick-commerce company consider establishing its next dark store, and which markets deserve investigation first?**

This project answers eight sub-questions:

1. Where is quick commerce already concentrated?
2. What characteristics are associated with existing dark-store markets?
3. Which markets appear relatively underserved?
4. Which markets have strong potential relative to existing coverage?
5. How does competitive presence differ across markets?
6. Which markets should management investigate first?
7. How robust are these recommendations under different strategic priorities?
8. What additional data would be required to move from market screening to exact dark-store placement?

This project does not claim to reproduce the proprietary expansion decisions of Blinkit, Zepto, Swiggy Instamart, or any other company. Every score here is an analyst-defined estimate for this project, built on public data.

## 3. Why Dark Stores Matter

Dark stores are the physical infrastructure behind 10-minute grocery delivery: small, no-walk-in warehouses positioned so a rider can reach a customer within a few kilometres. Where a company places, or doesn't place, a dark store directly determines whether it can serve a neighbourhood at all, and at what delivery speed. With five national platforms competing for the same real estate and order volume, expansion decisions are a live strategic problem.

It would be easy to build this project around Bangalore, Delhi and Mumbai and call it done, since those are the cities with the richest public data. But roughly a third of India's mapped dark stores already sit outside the top 20 cities, and the source reports are explicit that Tier 2 build-out, not further metro saturation, is where the next phase of growth is expected. There is no metro-only filter anywhere in this project; the analytical universe includes every market for which sufficiently reliable data exists.

---

## 4. Data Sources

All data used here is real and cited. Nothing in this project fabricates store locations, coordinates, revenue, demand, or SKU-level information.

| Source | What it provides | Geography | Nature | Limitations |
|---|---|---|---|---|
| QuickCommerceMap, *"Top 10 Cities by Dark Store Density"*, *"India Quick Commerce Map 2026"*, *"Dark Store Expansion in Tier 2 Cities"* (July 2026) | City-level store counts, tier classification, platform breakdown for 14 of 20 cities, state totals | 20 cities, 9 states, national totals | **Observed / reporting-based**, third-party compiled from public store-locator and serviceability data | Explicitly described by the source as a lower bound, not a full census; a live, monthly-updated dataset (earlier snapshots showed different totals for the same cities, e.g. Bangalore reported anywhere from ~438 to ~629 stores). Every figure here is pinned to the July 2026 compilation. |
| Census of India 2011 | District-level population and households | 20 covered cities plus 12 additional cities | **Official government census** | Latest full public census available; India's urban population has grown materially since 2011. |
| Public city-centre coordinates | Latitude/longitude for map display | 32 cities | **Public geographic reference** | Used for city-level market mapping only, never implies an exact store address. |

This project separates cities into **confidence tiers** rather than one undifferentiated candidate list:

| Confidence | Meaning | Count |
|---|---|---|
| **High** | Confirmed store count + full platform breakdown | 14 cities |
| **Medium** | Confirmed store count, partial or no platform breakdown | 5 cities |
| **Low** | Named as an active/growing market in source reports, no store count published | 5 cities |
| **Unconfirmed** | Not named in any source reviewed; presence genuinely unknown, not confirmed absent | 8 cities |

**What this data is not:** individual dark-store street addresses (no platform publishes those; this project deliberately did not attempt to reverse-engineer app APIs to get them), company-disclosed figures, or sales/SKU data.

## 5. Analytical Framework

```
DATA
    ↓
MARKET LANDSCAPE (existing network, by city and by company)
    ↓
COMPETITIVE ANALYSIS (platform presence, leadership, competitive intensity)
    ↓
MARKET SIZE PROXY (population as a consistent market-size proxy)
    ↓
COVERAGE GAP (stores per million population)
    ↓
EXPANSION OPPORTUNITY (transparent, analyst-defined score, scored cities only)
    ↓
SCENARIO ANALYSIS (Balanced / Demand-led / Coverage-led, resilience across scenarios)
    ↓
BUSINESS RECOMMENDATION
```

This is a business-analytics workflow, not a predictive machine-learning pipeline. There is no ML model, no API layer, and no database anywhere in this project, just pandas, Plotly and Streamlit.

## 6. Market Landscape

Quick commerce nationally spans **5,625 dark stores across 408 cities and 26 states** (July 2026). This project has confirmed, city-level store counts for **20 of those cities**, spanning Tier 1 Metro, Tier 1 Non-Metro and Tier 2 markets, plus a further 13 markets flagged for investigation without a confirmed count (see Section 8).

The top 20 cities hold roughly two-thirds of all mapped stores nationally; the remaining 388 cities average only about 5 stores each, many likely single-store market tests rather than real coverage. Dark stores are highly concentrated: Bangalore, Delhi and Hyderabad alone account for over a quarter of all mapped stores. State-level totals can hide whether coverage is genuinely distributed or riding on a single metro, Karnataka's 724 stores are 87% Bangalore alone, while Tamil Nadu's 417 spread more evenly across Chennai and a Coimbatore-Madurai-Trichy corridor.

## 7. Competitive Landscape

Among the 14 cities with a published platform breakdown, all 14 are Fragmented / Contested, with no single platform exceeding 50% of observed dark-store share. Blinkit leads in 11 of 14 markets by observed store count, but its peak observed dark-store share is 41.8% (Jaipur), short of majority control in any market. Leadership is not uniform: Zepto leads in Hyderabad and Chennai. Tier 2 cities show genuinely different competitive patterns from the metros: Patna has zero confirmed Zepto stores, and Flipkart Minutes holds the second-largest observed store count there.

Competitive intensity (number of platforms present) is tracked as a **separate decision lens** in this project, not blended into the Expansion Priority score, see Section 8 for why.

---

## 8. Expansion Opportunity

A transparent, **analyst-defined** score, scored only for the cities with a real, published store count:

```
Expansion Priority Score (Balanced scenario)

Market Size Proxy         50%   (2011 Census population, percentile-ranked among scored markets)
Coverage Opportunity      50%   (inverse of stores per million population, normalized)
```

This is deliberately a **two-factor** score. A third component, Competitive Intensity (number of platforms present), was considered, it is a genuinely different signal from Coverage Opportunity, a market can be dense but dominated by one platform, or sparse but contested by several. It was **not** folded into the score because platform-level breakdown is only published for 14 of the 20 confirmed cities; scoring the other 6 on an input they don't have would mean silently imputing it. Competitive Intensity is instead shown as a separate decision lens in the Competitive Landscape tab and Market Explorer.

An earlier version of this project also scored a "Competitive Whitespace" factor built from the same stores-per-million figure as Coverage Gap, just inverted a second time under a different label. That double-counted one signal as if it were two independent inputs, and has been removed.

### Scoring exclusion: Navi Mumbai and Thane

**Navi Mumbai and Thane are excluded from Expansion Priority scoring and all ranked recommendations.** The available Census geography assigns both the same district-level population (Navi Mumbai is not a separate census district), making any population-based comparison involving either of them unreliable. This is an exclusion, not a warning label, they do not appear in the scored tables, the quadrant matrix, or any ranking. They remain fully visible in the Market Landscape, Competitive Landscape and Market Explorer views, where store counts and platform presence (not population comparisons) are the relevant facts.

After this exclusion, the **scored universe is 18 cities**. All scenarios and rankings are computed on this 18-city set.

### Market Size Proxy vs Dark-Store Coverage (hero visual)

The dashboard's central chart plots coverage (stores per million population) on the x-axis against market-size proxy (population) on the y-axis, bubble size = confirmed dark stores, colour = one of four analytical market segments:

- **High potential, low coverage → "Expansion Opportunity"**
- **High potential, high coverage → "Mature / Competitive"**
- **Low potential, low coverage → "Emerging / Monitor"**
- **Low potential, high coverage → "Potentially Overserved"**

These labels are analytical interpretations relative to the median of the scored cities, not absolute or company-verified categories.

Two commonly used store-placement factors, **accessibility** (real-estate/road access) and a separate **income/spending-capacity** layer, are intentionally **not** scored, because no public, non-fabricated per-city dataset for either was available.

### Market Screening (unscored)

Thirteen cities appear in the source reports or in Census data but don't have a published store count, so they are **never** given an Expansion Screening Score:

- **Low confidence, named as active/growing markets, no count published:** Indore, Chandigarh, Kochi, Coimbatore, Bhopal
- **Unconfirmed, not named in any source reviewed:** Surat, Nashik, Visakhapatnam, Vadodara, Varanasi, Rajkot, Ludhiana, Amritsar

Each entry states plainly what would be needed before it could enter the scored universe. This is a deliberate demonstration that an analyst knows when there is insufficient data to make a quantitative recommendation, rather than a gap to be papered over.

## 9. Scenario Analysis

Two further scenarios reweight Market Size Proxy and Coverage Opportunity to test how the ranking shifts under different business priorities:

| Scenario | Market Size Proxy | Coverage Opportunity |
|---|---|---|
| Balanced | 50% | 50% |
| Demand-led | 80% | 20% |
| Coverage-led | 20% | 80% |

A fourth, Competition-led scenario was considered but not built, per the rule above: Competitive Intensity isn't measurable for all 18 scored cities, so it can't independently drive a scenario without imputing missing data for 5 of them.

The dashboard's Expansion Priority tab includes a **Scenario Rank Comparison** heatmap (cities × scenarios, cell values = rank) and a **Scenario-Resilient Markets** view: of the 18 scored cities, **9 remain in the top 10 across all three scenarios**, a strategy-agnostic shortlist that answers "which opportunities remain attractive even when management changes strategic priorities?"

## 10. Key Findings

*(See the dashboard's Key Insights tab for the full, data-generated list.)*

- **Market concentration:** the top 20 cities hold roughly two-thirds of all 5,625 mapped stores nationally; the remaining 388 cities average about 5 stores each.
- **Coverage gap:** Delhi ranks highest on the Balanced Expansion Priority score among the 18 scored cities, a large population base relative to its confirmed store count.
- **Competitive maturity:** all 14 cities with a published platform breakdown are Fragmented / Contested; no single platform exceeds 50% of observed dark-store share in any confirmed market. Blinkit leads by observed store count in 11 of 14 markets, with a peak observed dark-store share of 41.8%.
- **Implied coverage gap:** the three scored markets with the largest gap to the observed median density (28.6 stores per million, 2011 population) are Patna (106 stores), Jaipur (98 stores) and Ahmedabad (84 stores). This is a benchmark-based estimate using observed dark-store density only, not a forecast of demand or an optimal store count. 9 of 18 scored cities are already at or above the median.
- **Emerging markets:** Tier 2 cities are not simply smaller metros. Lucknow is nearly as contested as a small metro with all five platforms present; Patna's competitive order (Flipkart Minutes second, Zepto absent) is unlike any metro in this dataset.
- **Scenario robustness:** 9 of 18 scored markets remain in the top 10 under all three scenarios tested, a useful shortlist for management regardless of whether the near-term priority is demand or coverage.
- **Data quality:** 5 named markets have no published store count and are deliberately kept unscored rather than estimated.

## 11. Dashboard

Run locally:

```bash
pip install -r requirements.txt
streamlit run ui/app.py
```

Tabs: **Executive Overview** (KPI cards, India Market Opportunity Map, Market Size Proxy vs Coverage matrix, Top Expansion Markets, key takeaways) · **Market Landscape** (map, filterable by company) · **Competitive Landscape** (platform-presence heatmap, company footprint, competitive intensity) · **State View** · **Tier 2 & Emerging Markets** (four charts: segment split, Tier 2 comparison, Tier 2 competitive presence, Tier 2 market-size-vs-coverage) · **Expansion Priority** (scenario selector, Top 10/15/25 toggle, quadrant matrix with segment filter, scenario rank heatmap, scenario resilience, Market Screening layer) · **Market Explorer** (pick any of 33 markets for a full profile) · **Key Insights** · **Limitations**.

Built with a restrained, consulting-style palette (muted blues and greys, one colour per platform, one colour per tier, used consistently across every chart) rather than default rainbow colours, and consistent hover tooltips throughout. Every map is explicitly labeled as a market map, not a store-location map.

## 12. Limitations

- **No store-level coordinates.** All analysis is at the city level, not individual dark-store addresses.
- **Third-party, observed/reporting-based store counts**, described by their own source as a lower bound, not an official disclosure or full census.
- **Live, monthly-updated source data**, not a fixed truth; every figure here is pinned to the July 2026 compilation specifically.
- **2011 Census population**, the most recent full public census; current rankings could differ given population growth since then.
- **Navi Mumbai and Thane are excluded from scoring**, not merely flagged, because they share one Census district population figure. See Section 8.
- **Competitive Intensity is a decision lens, not a scored factor**, because platform breakdown is only published for 14 of 20 confirmed cities.
- **No accessibility or income data** used or invented.
- **No SKU/assortment or sales data** used or invented.
- **Implied Coverage Gap to Median is a benchmark estimate, not a demand figure.** It calculates how many additional stores would be implied if a market reached the median observed dark-store density of the 18-city scored set. It is not a forecast of customer demand, an economically optimal store count, or a recommendation to build that number of stores.
- **Correlation, not causation.** This project describes where stores and population/coverage patterns coincide; it does not claim to know why a company chose a given location.
- **City-level screening is not site selection**, see Section 13.

## 13. Future Work

### From Market Screening to Dark-Store Decision

This project can identify **which markets deserve further investigation**. It cannot identify **which exact street or address should receive a store**. Making that distinction explicit is part of what makes this project credible rather than overstated:

```
India
  ↓
Market Screening        <- this project
  ↓
City Prioritisation     <- this project
  ↓
Locality-Level Demand Analysis
  ↓
Candidate Sites
  ↓
Store Economics
  ↓
Final Site Selection
```

This project addresses the first two or three stages of that funnel, not the whole thing.

### Dark-Store Feasibility Framework (proposed next stage, not calculated here)

To move from a scored market to an economic go/no-go on a specific site would require real data this project does not have, and none of the figures below are calculated or estimated anywhere in this project:

```
Market Size Proxy → Expected Orders → Revenue → Operating Cost → Contribution → Payback
```

Variables that stage would need: expected orders/day, average order value, gross margin, rent, labour cost, delivery cost, inventory cost, contribution margin, and payback period.

### Location-Specific Assortment (future analysis, not implemented)

The original curiosity behind this project included: *"which SKUs should each dark store carry?"* No public, store-level SKU or sales dataset exists to answer this honestly, so it is documented here as a logical next step rather than implemented with invented data. A real version would use transaction data, basket data, SKU velocity, margin, inventory holding cost, and stockout frequency to determine location-specific assortment, none of which are fabricated or approximated in this project.

### Other data that would strengthen this project

Real store-level addresses (with a company's permission or licensed data), current (2024+) population estimates, commercial real-estate availability by locality, and order-level demand data.

---

## Tech Stack

Python, pandas, Plotly, Streamlit. Kept intentionally lean: no database, no API layer, no deployment infrastructure, no ML model beyond a transparent weighted score. The analysis and the dashboard are the deliverable, not the software engineering around them.

## 14. Attribution & License

This project builds on an existing open-source repository, see `ATTRIBUTION.md` for exactly what was carried over versus newly built. Licensed under the MIT License (`LICENSE`), inherited from the original repository.
