# Data

This folder contains all CSV datasets used in the project plus descriptive data reports.

## Files

- Base and cleaned datasets:
  - `staking_pools.csv`
  - `staking_pools_compact.csv`
  - `staking_pools_compact_ada.csv`
  - `staking_pools_not_active.csv`
  - `staking_pools_panel.csv`
  - `delegator_choice_panel.csv`
- Correlation input tables:
  - `chart_data_stake_minus_pledge_vs_pledge.csv`
  - `chart_data_stake_minus_pledge_vs_margin.csv`
  - `chart_data_stake_minus_pledge_vs_fixed_cost.csv`
  - `chart_data_stake_minus_pledge_vs_lifetime_luck.csv`
  - `chart_data_stake_minus_pledge_vs_recent_luck.csv`
  - `chart_data_stake_minus_pledge_vs_lifetime_roa.csv`
  - `chart_data_stake_minus_pledge_vs_recent_roa.csv`
- Descriptive reports:
  - `staking_pools_report.md`
  - `staking_pools_report_ada.md`
  - `staking_pools_report_ada.pdf`
  - `staking_pools_report_ada.tex`
  - `staking_pools_analysis.json`

## Key Descriptive Tables

### Pool Coverage

| Metric | Value |
|---|---:|
| Pools in source | 2941 |
| Excluded not active pools (`active_stake = 0`) | 224 |
| Active pools used in calculations | 2717 |

### Global Stake and Pledge Summary (Million ADA)

| Metric | Value |
|---|---:|
| Total active stake | 21568.605M |
| Total active pledge | 2931.539M |
| Average active stake | 7.938M |
| Average active pledge | 1.079M |

### Saturation and Pledge Diagnostics (Active Pools)

| Metric | Count | Percentage |
|---|---:|---:|
| Saturation >= 1 (100%) | 7 | 0.2576% |
| Active pledge = 0 | 224 | 8.2444% |
| Active stake = active pledge | 329 | 12.1089% |

For full descriptive outputs, see `staking_pools_report.md` and `staking_pools_report_ada.md`.
