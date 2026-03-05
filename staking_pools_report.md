# Staking Pools Analysis

Source file: `/Users/juancho/staking_pools.csv`
Compact file: `/Users/juancho/staking_pools_compact.csv`
Total pools: **2941**

## Saturation and Zero Pledge

| Metric | Count | Percentage |
|---|---:|---:|
| Saturation >= 1 (100%) | 7 | 0.2380% |
| Active pledge = 0 | 421 | 14.3149% |

## Pledge*L Calculations

Formulae per pool:
- If `active_stake > active_pledge * L`, add `active_stake - active_pledge * L` to excess sum.
- If `active_stake < active_pledge * L`, add `active_pledge * L - active_stake` to deficit sum.
- Also separately sum excess for pools with `active_pledge = 0`.

| L | # pools with stake > pledge*L | Sum(stake - pledge*L) | Sum(stake - pledge*L) for pledge=0 pools | # pools with stake < pledge*L | Sum(pledge*L - stake) |
|---:|---:|---:|---:|---:|---:|
| 100 | 998 | 13473519174517275 | 2747535008853776 | 1746 | 285070654195645022 |
| 500 | 687 | 9646321484529272 | 2747535008853776 | 2057 | 1453906417657004619 |
| 1000 | 571 | 8454003317853744 | 2747535008853776 | 2173 | 2918542800929513591 |
| 10000 | 361 | 5339547587403907 | 2747535008853776 | 2383 | 29300344971104384754 |
