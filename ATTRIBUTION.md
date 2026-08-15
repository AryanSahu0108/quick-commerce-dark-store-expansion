# Attribution

This project builds upon an existing open-source repository:

**Original repository:** [BLINKIT-store-placement-prediction-project-](https://github.com/Ronit049/BLINKIT-store-placement-prediction-project-) by [Ronit Raj](https://github.com/Ronit049), licensed under the MIT License (see `LICENSE`).

## What was carried over
- The MIT License and the general problem framing (store placement / location intelligence for quick commerce).
- The general idea of a scored, mapped view of candidate locations (the original `src/visualization.py` used a simple weighted score and a Folium map on placeholder data).

## What was newly built for this project
Almost everything else. Specifically:
- **All data.** The original repository's `data/raw_locations.csv` was empty, and `src/visualization.py` ran on five hardcoded, non-real "Zone A/B/C/D/E" rows. None of that data is used here. This project instead sources real, cited data: Census of India 2011 district-level population, and city-level dark-store counts from a third-party public compilation (QuickCommerceMap, July 2026). See `README.md` for full sourcing.
- **The business framing** (the central expansion question, the seven sub-questions, the scenario-analysis approach, the transparent opportunity-score methodology).
- **The analysis code** (`src/data_prep.py`, `src/opportunity_score.py`) and the dashboard (`ui/app.py`) are new implementations, not modifications of the original (mostly empty) `ui/app.py` and `src/ronit_raj.py` files.
- **The README**, reframed around the business question rather than the technical implementation.

## Why this note exists
The brief for this project (and good practice generally) requires not claiming independent authorship of a project we built on top of, and requires distinguishing original components from newly added ones. This file is that disclosure.
