# Reports Index

This file centralizes the report outputs and related artifacts for GitHub publication.

## 1) Staking Pools Overview

- **Markdown:** `staking_pools_report.md`
- **Purpose:** initial descriptive analysis over all pools, including saturation, zero-pledge rates, and `stake` vs `pledge * L` comparisons.

## 2) Staking Pools (Million ADA Units)

- **Markdown:** `staking_pools_report_ada.md`
- **PDF:** `staking_pools_report_ada.pdf`
- **TeX:** `staking_pools_report_ada.tex`
- **Purpose:** cleaned active-pool analysis with metrics in million ADA and embedded regression section.

## 3) Regression Summary

- **Markdown:** `regression_summary.md`
- **JSON:** `regression_results.json`
- **Purpose:** multivariate regression table outputs for Models A/B/C on `log(1 + (active_stake - pledge))`.

## 4) Panel Fixed-Effects Report

- **Markdown:** `staking_pools_panel_fe_report.md`
- **PDF:** `staking_pools_panel_fe_report.pdf`
- **TeX:** `staking_pools_panel_fe_report.tex`
- **JSON:** `staking_pools_panel_fe_results.json`
- **Purpose:** two-way FE (pool + epoch) stake-growth model with cluster-robust SE.

## 5) Delegator Choice Fixed-Effects Report

- **Markdown:** `delegator_choice_results.md`
- **PDF:** `delegator_choice_results.pdf`
- **TeX:** `delegator_choice_results.tex`
- **JSON:** `delegator_choice_results.json`
- **Purpose:** FE specifications (S1/S2/S3) for delegator growth and robustness checks.

## Supporting Data Files

- Base and processed pool datasets:
  - `staking_pools.csv`
  - `staking_pools_compact.csv`
  - `staking_pools_compact_ada.csv`
  - `staking_pools_not_active.csv`
  - `staking_pools_panel.csv`
  - `delegator_choice_panel.csv`
- Chart-ready tables:
  - `chart_data_stake_minus_pledge_vs_pledge.csv`
  - `chart_data_stake_minus_pledge_vs_margin.csv`
  - `chart_data_stake_minus_pledge_vs_fixed_cost.csv`
  - `chart_data_stake_minus_pledge_vs_lifetime_luck.csv`
  - `chart_data_stake_minus_pledge_vs_recent_luck.csv`
  - `chart_data_stake_minus_pledge_vs_lifetime_roa.csv`
  - `chart_data_stake_minus_pledge_vs_recent_roa.csv`

## Notes for Publication

- Markdown files are the primary documentation layer for GitHub.
- PDF/TeX artifacts are optional but useful for archival and reproducibility.
- If repository size is a concern, prioritize `.md`, key `.csv`, and `.json` result files.
