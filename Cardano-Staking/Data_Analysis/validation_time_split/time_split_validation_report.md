# Time-Split Validation Report

This is a predictive validation exercise (not a causal identification design).

## Split design

- Input panel: `/Users/juancho/Cardano-Staking/data/delegator_choice_panel.csv`
- Train epochs: `[609, 610, 613, 614]`
- Validation epochs: `[615]`
- Approx share by rows: train `79.95%`, validation `20.05%`

## Specifications

- **P1:** `lag1_luck`, `lag1_log_pledge`, `lag1_log_stake`, `margin`, `lifetime_roa`
- **P2:** P1 + `lag1_log_delegators`

## Model equations and variable definitions

Conceptual outcome equation:

- `delta_log_delegators_it = log(1 + delegators_it) - log(1 + delegators_i,t-1)`

Specification equations:

- **P1:**
  `delta_log_delegators_it = beta0 + beta1*lag1_luck_it + beta2*lag1_log_pledge_it + beta3*lag1_log_stake_it + beta4*margin_i + beta5*lifetime_roa_i + error_it`
- **P2:**
  `delta_log_delegators_it = beta0 + beta1*lag1_luck_it + beta2*lag1_log_pledge_it + beta3*lag1_log_stake_it + beta4*margin_i + beta5*lifetime_roa_i + beta6*lag1_log_delegators_it + error_it`

Variable definitions:

- `delegators_it`: number of delegators in pool `i` at epoch `t`
- `lag1_luck_it`: pool luck in epoch `t-1`
- `lag1_log_pledge_it`: `log(1 + pledged_lovelace_{i,t-1})` (as built in the panel)
- `lag1_log_stake_it`: `log(1 + epoch_stake_lovelace_{i,t-1})` (as built in the panel)
- `margin_i`: pool active margin (`pool_update.active.margin`), treated as time-invariant
- `lifetime_roa_i`: pool lifetime ROA (`stats.lifetime.roa`), treated as time-invariant
- `lag1_log_delegators_it`: `log(1 + delegators_{i,t-1})`
- `error_it`: residual term for pool `i`, epoch `t`

| Spec | Train n | Validation n | Train RMSE | Validation RMSE | Train R^2 | Validation R^2 |
|---|---:|---:|---:|---:|---:|---:|
| P1 | 11480 | 2879 | 0.0581 | 0.0529 | 0.0028 | 0.0011 |
| P2 | 11480 | 2879 | 0.0580 | 0.0529 | 0.0061 | 0.0027 |

## Interpretation

- This validates out-of-sample predictive stability across time.
- It does not, by itself, convert associations into causal effects.
- Causal claims still require an identification strategy (e.g., randomized treatment, IV, DiD/event design).

