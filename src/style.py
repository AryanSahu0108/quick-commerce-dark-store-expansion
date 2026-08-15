"""
Shared visual style for the dashboard. Kept in one place so every chart uses the same
restrained palette instead of Plotly's default rainbow qualitative colors.
"""

PLATFORM_COLORS = {
    "Blinkit": "#F4B400",
    "Zepto": "#8E44AD",
    "Swiggy Instamart": "#E8604C",
    "Flipkart Minutes": "#2874A6",
    "BigBasket": "#27AE60",
}

TIER_COLORS = {
    "Tier 1 Metro": "#1F3B57",
    "Tier 1 Non-Metro": "#3E7CB1",
    "Tier 2": "#8FB8DE",
    "Unclassified": "#C9CDD3",
}

CONFIDENCE_COLORS = {
    "High": "#1F3B57",
    "Medium": "#3E7CB1",
    "Low": "#E0A458",
    "Unconfirmed": "#C9CDD3",
}

SEQUENTIAL_SCALE = "Teal"  # used for opportunity-score colouring
NEUTRAL_GREY = "#9AA1AC"

PLOTLY_TEMPLATE = "plotly_white"

QUADRANT_COLORS = {
    "Expansion Opportunity": "#1F3B57",
    "Mature / Competitive": "#8FB8DE",
    "Emerging / Monitor": "#C9CDD3",
    "Potentially Overserved": "#E0A458",
}
