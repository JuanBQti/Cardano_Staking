# Delegator Choice FE Report

Choice panel: `/Users/juancho/delegator_choice_panel.csv`

Method: **Two-way FE (pool + epoch), cluster-robust SE by pool**
Dependent variable: `delta_log_delegators = log(1+delegators_t) - log(1+delegators_{t-1})`

## Model Definitions

- **S1 (lag1 core):** `lag1_luck`, `lag1_log_pledge`, `lag1_log_stake`, `lag1_margin_proxy`.
- **S2 (lag1 + persistence):** S1 + `lag1_log_delegators`.
- **S3 (lag2 robustness):** `lag2_luck`, `lag1_log_pledge`, `lag2_log_stake`, `lag1_margin_proxy`, `lag2_log_delegators`.

All specs include **pool FE** and **epoch FE**, with **cluster-robust SE at pool level**.

| Spec | n_obs | n_pools | n_epochs | Within R² |
|---|---:|---:|---:|---:|
| S1 | 14635 | 2935 | 5 | 0.0192 |
| S2 | 14635 | 2935 | 5 | 0.5107 |
| S3 | 8782 | 2934 | 3 | 0.3009 |

## Interpretation (Pledge vs Stake)

- `log(stake)` is **consistently positive and statistically significant** across specifications.
- `log(pledge)` is **not robust**: significant only in S1 (small negative), and insignificant in S2 and S3.
- Practical reading: within-pool over-time delegator growth is more strongly associated with prior stake/popularity than with pledge in this dataset/specification.
- Caution: this does **not** prove pledge has zero causal effect; it means we do not find stable evidence after FE + lags + controls.

## Assumptions and Caveats

- Strict exogeneity of lagged regressors conditional on FE (strong assumption).
- Lagging helps with reverse causality but does not eliminate all endogeneity.
- `lag1_margin_proxy` uses lagged `reward.member_pct` (not direct historical margin).
- Remaining omitted time-varying factors may bias coefficients.
- p-values use normal approximation with cluster-robust SE.

## S1: lag1 core

| Variable | Beta | Cluster SE (pool) | p-value |
|---|---:|---:|---:|
| lag1_luck | -0.0002 | 0.0006 | 0.7785 |
| lag1_log_pledge | -0.0035 | 0.0016 | 0.0242 |
| lag1_log_stake | 0.0147 | 0.0036 | 0.0000 |
| lag1_margin_proxy | -0.0003 | 0.0003 | 0.2940 |

## S2: lag1 + persistence

| Variable | Beta | Cluster SE (pool) | p-value |
|---|---:|---:|---:|
| lag1_luck | -0.0017 | 0.0006 | 0.0021 |
| lag1_log_pledge | 0.0044 | 0.0031 | 0.1561 |
| lag1_log_stake | 0.0238 | 0.0050 | 0.0000 |
| lag1_margin_proxy | 0.0018 | 0.0005 | 0.0002 |
| lag1_log_delegators | -0.6534 | 0.1383 | 0.0000 |

## S3: lag2 robustness

| Variable | Beta | Cluster SE (pool) | p-value |
|---|---:|---:|---:|
| lag2_luck | 0.0001 | 0.0006 | 0.9188 |
| lag1_log_pledge | -0.0011 | 0.0015 | 0.4802 |
| lag2_log_stake | 0.0255 | 0.0041 | 0.0000 |
| lag1_margin_proxy | 0.0008 | 0.0001 | 0.0000 |
| lag2_log_delegators | -0.3575 | 0.0683 | 0.0000 |

## Equation (conceptual)

`Δlog(delegators_it) = βX_{i,t-k} + α_i + γ_t + ε_it`

where `α_i` are pool fixed effects, `γ_t` are epoch fixed effects, and `k` is 1 or 2 depending on specification.

## Notes
- Lagged regressors are used to reduce reverse-causality concerns.
- Margin is proxied by lagged reward.member_pct due panel availability in source epoch blocks.
- Interpretation remains associational/quasi-causal, not full causal identification.
