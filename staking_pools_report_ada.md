# Staking Pools Analysis (Million ADA Units)

Source file: `/Users/juancho/staking_pools.csv`
Active-only compact file: `/Users/juancho/staking_pools_compact.csv`
Not-active file: `/Users/juancho/staking_pools_not_active.csv`

Pools in source: **2941**
Excluded not active pools (`active_stake = 0`): **224**
Pools used in calculations (active only): **2717**

## Global Stake and Pledge Summary (M ADA)

| Metric | Value |
|---|---:|
| Total active stake | 21568.605M |
| Total active pledge | 2931.539M |
| Average active stake | 7.938M |
| Average active pledge | 1.079M |

## Saturation, Zero Pledge, and Stake=Pledge (active pools only)

| Metric | Count | Percentage |
|---|---:|---:|
| Saturation >= 1 (100%) | 7 | 0.2576% |
| Active pledge = 0 | 224 | 8.2444% |
| Active stake = active pledge | 329 | 12.1089% |

## Distribution for stake = pledge subgroup

### Margin distribution (12 groups)
| Margin group | Count | Percentage of subgroup |
|---|---:|---:|
| =0 | 49 | 14.89% |
| (0.0,0.1] | 223 | 67.78% |
| (0.1,0.2] | 22 | 6.69% |
| (0.2,0.3] | 1 | 0.30% |
| (0.3,0.4] | 0 | 0.00% |
| (0.4,0.5] | 0 | 0.00% |
| (0.5,0.6] | 0 | 0.00% |
| (0.6,0.7] | 0 | 0.00% |
| (0.7,0.8] | 0 | 0.00% |
| (0.8,0.9] | 1 | 0.30% |
| (0.9,1) | 3 | 0.91% |
| =1 | 30 | 9.12% |

### Fixed cost distribution (ADA groups)
| Fixed cost group (ADA) | Count | Percentage of subgroup |
|---|---:|---:|
| =0 | 0 | 0.00% |
| (0,340) | 31 | 9.42% |
| =340 | 218 | 66.26% |
| 340-500 | 79 | 24.01% |
| >500 | 1 | 0.30% |

## Pledge*L Calculations (M ADA, active pools only)

| L | # pools with stake > pledge*L | Sum(stake - pledge*L) | Sum(stake - pledge*L) for pledge=0 pools | # pools with stake < pledge*L | Sum(pledge*L - stake) |
|---:|---:|---:|---:|---:|---:|
| 1 | 2339 | 18726.811M | 2747.535M | 49 | 89.745M |
| 10 | 1511 | 17401.376M | 2747.535M | 1206 | 25148.164M |
| 25 | 1289 | 16195.18M | 2747.535M | 1428 | 67915.058M |
| 100 | 998 | 13473.519M | 2747.535M | 1719 | 285058.847M |

## Chart data for pools with stake > pledge

- `stake-pledge` vs `pledge`: `/Users/juancho/chart_data_stake_minus_pledge_vs_pledge.csv`
- `stake-pledge` vs `margin`: `/Users/juancho/chart_data_stake_minus_pledge_vs_margin.csv`
- `stake-pledge` vs `fixed cost` (binned ADA): `/Users/juancho/chart_data_stake_minus_pledge_vs_fixed_cost.csv`
- `stake-pledge` vs `lifetime luck`: `/Users/juancho/chart_data_stake_minus_pledge_vs_lifetime_luck.csv`
- `stake-pledge` vs `recent luck`: `/Users/juancho/chart_data_stake_minus_pledge_vs_recent_luck.csv`
- `stake-pledge` vs `lifetime roa`: `/Users/juancho/chart_data_stake_minus_pledge_vs_lifetime_roa.csv`
- `stake-pledge` vs `recent roa`: `/Users/juancho/chart_data_stake_minus_pledge_vs_recent_roa.csv`

<!-- REGRESSION_SECTION_START -->
## Multivariate Regression Results

Sample: **2339** pools with `active_stake > pledge`.

Dependent variable: `log(1 + (active_stake - pledge) in ADA)`

| Model | ROA term(s) | R² | Adj. R² |
|---|---|---:|---:|
| A | lifetime_roa | 0.6664 | 0.6656 |
| B | recent_roa | 0.6930 | 0.6922 |
| C | lifetime_roa + recent_roa | 0.7015 | 0.7006 |

### Model A

| Variable | Beta | Robust SE (HC1) | p-value |
|---|---:|---:|---:|
| Intercept | 5.1656 | 0.1467 | 0.0000 |
| log_pledge | 0.1664 | 0.0182 | 0.0000 |
| margin | 1.7314 | 0.3763 | 0.0000 |
| fixed_cost_ada | 0.0000 | 0.0000 | 0.0002 |
| saturation | 5.5399 | 0.3864 | 0.0000 |
| log_delegators | 0.9535 | 0.0434 | 0.0000 |
| lifetime_roa | 0.5655 | 0.0592 | 0.0000 |

### Model B

| Variable | Beta | Robust SE (HC1) | p-value |
|---|---:|---:|---:|
| Intercept | 5.8093 | 0.1498 | 0.0000 |
| log_pledge | 0.1304 | 0.0178 | 0.0000 |
| margin | 2.3094 | 0.3770 | 0.0000 |
| fixed_cost_ada | 0.0000 | 0.0000 | 0.0005 |
| saturation | 3.4660 | 0.3988 | 0.0000 |
| log_delegators | 0.8503 | 0.0399 | 0.0000 |
| recent_roa | 1.7600 | 0.1360 | 0.0000 |

### Model C

| Variable | Beta | Robust SE (HC1) | p-value |
|---|---:|---:|---:|
| Intercept | 5.5541 | 0.1468 | 0.0000 |
| log_pledge | 0.1266 | 0.0177 | 0.0000 |
| margin | 2.6853 | 0.4033 | 0.0000 |
| fixed_cost_ada | 0.0000 | 0.0000 | 0.0004 |
| saturation | 3.6243 | 0.3997 | 0.0000 |
| log_delegators | 0.7505 | 0.0556 | 0.0000 |
| lifetime_roa | 0.3743 | 0.0730 | 0.0000 |
| recent_roa | 1.5650 | 0.1424 | 0.0000 |

<!-- REGRESSION_SECTION_END -->
