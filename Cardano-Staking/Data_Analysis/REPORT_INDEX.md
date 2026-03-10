# Report Index

This file centralizes the report outputs and related artifacts for GitHub publication.

## 1) Staking Pools Overview

- **Markdown:** `data/staking_pools_report.md`
- **Purpose:** initial descriptive analysis over all pools, including saturation, zero-pledge rates, and `stake` vs `pledge * L` comparisons.

## 2) Staking Pools (Million ADA Units)

- **Markdown:** `data/staking_pools_report_ada.md`
- **PDF:** `data/staking_pools_report_ada.pdf`
- **TeX:** `data/staking_pools_report_ada.tex`
- **Purpose:** cleaned active-pool analysis with metrics in million ADA and embedded regression section.

## 3) Regression Summary

- **Markdown:** `regression/regression_summary.md`
- **JSON:** `regression/regression_results.json`
- **Purpose:** multivariate regression table outputs for Models A/B/C on `log(1 + (active_stake - pledge))`.

## 4) Panel Fixed-Effects Report

- **Markdown:** `regression/staking_pools_panel_fe_report.md`
- **PDF:** `regression/staking_pools_panel_fe_report.pdf`
- **TeX:** `regression/staking_pools_panel_fe_report.tex`
- **JSON:** `regression/staking_pools_panel_fe_results.json`
- **Purpose:** two-way FE (pool + epoch) stake-growth model with cluster-robust SE.

## 5) Delegator Choice Fixed-Effects Report

- **Markdown:** `regression/delegator_choice_results.md`
- **PDF:** `regression/delegator_choice_results.pdf`
- **TeX:** `regression/delegator_choice_results.tex`
- **JSON:** `regression/delegator_choice_results.json`
- **Purpose:** FE specifications (S1/S2/S3) for delegator growth and robustness checks.

## Supporting Data Files

- Base and processed pool datasets:
  - `data/staking_pools.csv`
  - `data/staking_pools_compact.csv`
  - `data/staking_pools_compact_ada.csv`
  - `data/staking_pools_not_active.csv`
  - `data/staking_pools_panel.csv`
  - `data/delegator_choice_panel.csv`
- Chart-ready tables:
  - `data/chart_data_stake_minus_pledge_vs_pledge.csv`
  - `data/chart_data_stake_minus_pledge_vs_margin.csv`
  - `data/chart_data_stake_minus_pledge_vs_fixed_cost.csv`
  - `data/chart_data_stake_minus_pledge_vs_lifetime_luck.csv`
  - `data/chart_data_stake_minus_pledge_vs_recent_luck.csv`
  - `data/chart_data_stake_minus_pledge_vs_lifetime_roa.csv`
  - `data/chart_data_stake_minus_pledge_vs_recent_roa.csv`

## Correlation Charts

- `correlation/stake_minus_pledge_vs_pledge.svg`
- `correlation/stake_minus_pledge_vs_margin.svg`
- `correlation/stake_minus_pledge_vs_fixed_cost.svg`
- `correlation/stake_minus_pledge_vs_lifetime_luck.svg`
- `correlation/stake_minus_pledge_vs_recent_luck.svg`
- `correlation/stake_minus_pledge_vs_lifetime_roa.svg`
- `correlation/stake_minus_pledge_vs_recent_roa.svg`

## Notes for Publication

- Markdown files are the primary documentation layer for GitHub.
- PDF/TeX artifacts are optional but useful for archival and reproducibility.
- If repository size is a concern, prioritize `.md`, key `.csv`, and `.json` result files.
