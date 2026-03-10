# Delegator Choice FE Report

Method: **Two-way FE (pool + epoch), cluster-robust SE by pool**
Dependent variable: `delta_log_delegators = log(1+delegators_t) - log(1+delegators_{t-1})`

## Why lifetime ROA was not in prior FE equations

- In two-way FE, pool-level constants are absorbed by pool fixed effects (`alpha_i`).
- `lifetime_roa` is pool-constant in this dataset, so it is collinear with `alpha_i` and cannot be estimated in a pool-FE model.
- Using real `margin` as a fixed pool value has the same issue in two-way FE.
- To estimate their coefficients, we add an **epoch-FE-only** comparison model (no pool FE).

## Margin update requested

- Replaced `lag1_margin_proxy` with real pool `margin` from `pool_update.active.margin`.
- Assumption used: margin is fixed across observed epochs for each pool.
- In two-way FE specs, `margin` is dropped automatically for collinearity with pool FE.

## Model Definitions

- **S1 (two-way FE, lag1 core):** requested regressors are `lag1_luck`, `lag1_log_pledge`, `lag1_log_stake`, `margin`; `margin` is pool-fixed and absorbed by pool FE (`alpha_i`), so it is not estimated separately.
- **S2 (two-way FE, lag1 + persistence):** requested regressors are S1 + `lag1_log_delegators`; again `margin` is absorbed by pool FE.
- **S3 (two-way FE, lag2 robustness):** requested regressors are `lag2_luck`, `lag1_log_pledge`, `lag2_log_stake`, `margin`, `lag2_log_delegators`; `margin` is absorbed by pool FE.
- **S4 (epoch FE only, comparison):** requested regressors are `lag1_luck`, `lag1_log_pledge`, `lag1_log_stake`, `margin`, `lifetime_roa`, `lag1_log_delegators` + epoch FE; here `margin` and `lifetime_roa` are identifiable.

## Model equations and variable definitions

Outcome definition:

- `delta_log_delegators_it = log(1 + delegators_it) - log(1 + delegators_i,t-1)`

Specification equations:

- **S1 (two-way FE, estimable equation):**
  `Delta log(1+delegators_{i,t}) = beta1*luck_{i,t-1} + beta2*log(1+pledge_{i,t-1}) + beta3*log(1+stake_{i,t-1}) + alpha_i + gamma_t + error_{i,t}`
  Requested regressor `margin_i` is absorbed by `alpha_i` and therefore not shown in the estimable equation.
- **S2 (two-way FE, estimable equation):**
  `Delta log(1+delegators_{i,t}) = beta1*luck_{i,t-1} + beta2*log(1+pledge_{i,t-1}) + beta3*log(1+stake_{i,t-1}) + beta4*log(1+delegators_{i,t-1}) + alpha_i + gamma_t + error_{i,t}`
  Requested regressor `margin_i` is absorbed by `alpha_i` and therefore not shown in the estimable equation.
- **S3 (two-way FE, estimable equation):**
  `Delta log(1+delegators_{i,t}) = beta1*luck_{i,t-2} + beta2*log(1+pledge_{i,t-1}) + beta3*log(1+stake_{i,t-2}) + beta4*log(1+delegators_{i,t-2}) + alpha_i + gamma_t + error_{i,t}`
  Requested regressor `margin_i` is absorbed by `alpha_i` and therefore not shown in the estimable equation.
- **S4 (epoch FE only comparison):**
  `Delta log(1+delegators_{i,t}) = beta0 + beta1*luck_{i,t-1} + beta2*log(1+pledge_{i,t-1}) + beta3*log(1+stake_{i,t-1}) + beta4*margin_i + beta5*lifetime_roa_i + beta6*log(1+delegators_{i,t-1}) + gamma_t + error_{i,t}`

Variable definitions:

- `delegators_it`: number of delegators in pool `i` at epoch `t`
- `luck_{i,t-1}`, `luck_{i,t-2}`: pool luck lagged by 1 or 2 epochs
- `log(1+pledge_{i,t-1})`: log pledge lagged by 1 epoch
- `log(1+stake_{i,t-1})`, `log(1+stake_{i,t-2})`: log stake lagged by 1 or 2 epochs
- `log(1+delegators_{i,t-1})`, `log(1+delegators_{i,t-2})`: log delegators lagged by 1 or 2 epochs
- `margin_i`: pool active margin (`pool_update.active.margin`), treated as fixed by pool
- `lifetime_roa_i`: pool lifetime ROA (`stats.lifetime.roa`), treated as fixed by pool
- `alpha_i`: pool fixed effects; `gamma_t`: epoch fixed effects; `error_it`: residual
- Dataset mapping: `lag1_luck_it = luck_{i,t-1}`, `lag2_luck_it = luck_{i,t-2}`, and similarly for other `lag1_`/`lag2_` fields

## Assumptions and caveats

- Observational data: results are associational/quasi-causal, not full causal identification.
- Two-way FE reduces bias from time-invariant pool heterogeneity, but time-varying omitted factors may remain.
- Lagged regressors reduce (but do not eliminate) reverse-causality/simultaneity concerns.
- `margin` and `lifetime_roa` are treated as pool-fixed; in two-way FE they are not identifiable and are absorbed by pool FE.
- Their coefficients are reported only in the epoch-FE-only comparison spec (S4), which is more vulnerable to pool-level confounding.
- Cluster-robust SE by pool address within-pool serial correlation and heteroskedasticity, but inference is still model-dependent.
- Epoch coverage is limited (available lag structure), so long-horizon dynamics are only partially captured.
- Functional form uses log transforms and linear terms; misspecification risk remains.

| Spec | Type | n_obs | n_pools | n_epochs | Fit | Dropped in estimation |
|---|---|---:|---:|---:|---:|---|
| S1 | two-way FE | 14635 | 2935 | 5 | 0.0187 (within R^2) | margin |
| S2 | two-way FE | 14635 | 2935 | 5 | 0.4966 (within R^2) | margin |
| S3 | two-way FE | 8782 | 2934 | 3 | 0.2922 (within R^2) | margin |
| S4 | epoch FE only | 14359 | 2879 | 5 | 0.0059 (R^2) | none |

## S1 Coefficients

| Variable | Beta | Cluster SE (pool) | p-value |
|---|---:|---:|---:|
| lag1_luck | -0.000433 | 0.000573 | 0.4493 |
| lag1_log_pledge | -0.003520 | 0.001550 | 0.0232 |
| lag1_log_stake | 0.014742 | 0.003616 | 0.0000 |

## S2 Coefficients

| Variable | Beta | Cluster SE (pool) | p-value |
|---|---:|---:|---:|
| lag1_luck | -0.000166 | 0.000305 | 0.5855 |
| lag1_log_pledge | 0.004249 | 0.003028 | 0.1605 |
| lag1_log_stake | 0.023207 | 0.004721 | 0.0000 |
| lag1_log_delegators | -0.631525 | 0.138631 | 0.0000 |

## S3 Coefficients

| Variable | Beta | Cluster SE (pool) | p-value |
|---|---:|---:|---:|
| lag2_luck | -0.000193 | 0.000693 | 0.7812 |
| lag1_log_pledge | -0.000917 | 0.001522 | 0.5470 |
| lag2_log_stake | 0.026424 | 0.004291 | 0.0000 |
| lag2_log_delegators | -0.369367 | 0.077609 | 0.0000 |

## S4 Coefficients (lifetime ROA + margin identifiable)

| Variable | Beta | Cluster SE (pool) | p-value |
|---|---:|---:|---:|
| lag1_luck | -0.000082 | 0.000518 | 0.8740 |
| lag1_log_pledge | -0.000512 | 0.000160 | 0.0013 |
| lag1_log_stake | 0.001417 | 0.000389 | 0.0003 |
| margin | -0.005387 | 0.001910 | 0.0048 |
| lifetime_roa | -0.000512 | 0.000308 | 0.0971 |
| lag1_log_delegators | -0.002301 | 0.000708 | 0.0012 |

## Interpretation

- Two-way FE answers a within-pool-over-time question; time-invariant regressors are not identifiable there.
- `lifetime_roa` and fixed `margin` should be interpreted from S4 (epoch FE only), not from S1-S3.
- `log(stake)` remains a strong predictor in FE specifications.
- Results remain associational/quasi-causal, not fully causal.

