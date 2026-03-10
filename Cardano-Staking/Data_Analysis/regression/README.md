# Regression

This folder contains the regression outputs used to evaluate stake and delegator dynamics.

## Why We Ran These Models

We wanted to move beyond descriptive statistics and test whether pool-level variables are associated with:
- larger `stake - pledge` gaps in cross-section,
- stake growth across epochs (panel FE),
- delegator growth across epochs (panel FE).

The goal is empirical association under controls and fixed effects, not full causal identification.

## Contents

- Cross-sectional OLS:
  - `regression_summary.md`
  - `regression_results.json`
- Stake growth panel FE:
  - `staking_pools_panel_fe_report.md`
  - `staking_pools_panel_fe_results.json`
  - `staking_pools_panel_fe_report.pdf`
  - `staking_pools_panel_fe_report.tex`
- Delegator growth panel FE:
  - `delegator_choice_results.md`
  - `delegator_choice_results.json`
  - `delegator_choice_results.pdf`
  - `delegator_choice_results.tex`
- Supporting TeX snippet:
  - `staking_pools_report_ada_snippet.tex`

## Cross-Sectional OLS (Stake Minus Pledge)

Dependent variable: `log(1 + (active_stake - pledge) in ADA)`  
Sample: `2339` pools with `active_stake > pledge`.

| Model | ROA term(s) | R^2 | Adj. R^2 |
|---|---|---:|---:|
| A | lifetime_roa | 0.6664 | 0.6656 |
| B | recent_roa | 0.6930 | 0.6922 |
| C | lifetime_roa + recent_roa | 0.7015 | 0.7006 |

Takeaway: model fit is strongest when both lifetime and recent ROA are included.

## Stake Growth Panel FE

From `staking_pools_panel_fe_report.md`:
- Model: two-way FE (pool FE + epoch FE), lagged regressors.
- Dependent variable: `log(1+stake_t) - log(1+stake_{t-1})`.
- Observations: `13536`, Pools: `2718`, Epochs: `5`.
- Within `R^2`: `0.0035`.

Selected coefficient table:

| Variable | Beta | Cluster SE (pool) | p-value |
|---|---:|---:|---:|
| lag_luck | 0.0013 | 0.0025 | 0.5905 |
| lag_log_pledge | 0.0014 | 0.0193 | 0.9423 |
| lag_log_delegators | -0.2116 | 0.2021 | 0.2951 |
| lag_member_pct | 0.0034 | 0.0007 | 0.0000 |
| lag_block_minted | -0.0042 | 0.0022 | 0.0581 |

## Delegator Growth Panel FE

From `delegator_choice_results.md`:
- Method: two-way FE (pool + epoch), cluster-robust SE by pool.
- Dependent variable: `delta_log_delegators`.

Model fit across specifications:

| Spec | n_obs | n_pools | n_epochs | Within R^2 |
|---|---:|---:|---:|---:|
| S1 | 14635 | 2935 | 5 | 0.0192 |
| S2 | 14635 | 2935 | 5 | 0.5107 |
| S3 | 8782 | 2934 | 3 | 0.3009 |

Interpretation:
- `log(stake)` is consistently positive and statistically significant.
- `log(pledge)` is not robust across all specifications.
