# Panel FE Report

Panel dataset: `/Users/juancho/staking_pools_panel.csv`

Model: **Two-way fixed effects (pool FE + epoch FE), lagged regressors**
Dependent variable: `log(1+stake_t ADA) - log(1+stake_{t-1} ADA)`
Observations: **13536**, Pools: **2718**, Epochs: **5**
Within R²: **0.0035**

| Variable | Beta | Cluster SE (pool) | p-value |
|---|---:|---:|---:|
| lag_luck | 0.0013 | 0.0025 | 0.5905 |
| lag_log_pledge | 0.0014 | 0.0193 | 0.9423 |
| lag_log_delegators | -0.2116 | 0.2021 | 0.2951 |
| lag_member_pct | 0.0034 | 0.0007 | 0.0000 |
| lag_block_minted | -0.0042 | 0.0022 | 0.0581 |

## Notes
- Lagged covariates mitigate (but do not fully remove) simultaneity/reverse causality.
- SE are cluster-robust at pool level.
