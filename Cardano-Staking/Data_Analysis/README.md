# Cardano Staking Pools Analysis

This repository documents the Cardano staking pool analysis and organizes outputs into three folders:
- `data/` for all CSV datasets and descriptive report files,
- `correlation/` for correlation charts,
- `regression/` for regression and fixed-effects outputs.

## Repository Structure

- `data/README.md`: data inventory plus key descriptive tables.
- `correlation/README.md`: chart gallery for `stake - pledge` correlations.
- `regression/README.md`: model setup, motivation, and key results tables.
- `REPORT_INDEX.md`: full report artifact index.
- `download_cexplorer_pools_to_csv.py`: Cexplorer extraction script.

## What We Did

1. Downloaded staking pool data from Cexplorer.
2. Built cleaned/compact datasets and panel datasets.
3. Produced descriptive diagnostics for saturation, pledge, and stake gaps.
4. Built correlation datasets and visualization charts.
5. Ran multivariate and fixed-effects regressions:
   - cross-sectional OLS models for `log(1 + (active_stake - pledge))`,
   - panel FE model for stake growth,
   - panel FE model for delegator growth.

## Quick Highlights

- Cross-sectional sample for OLS: `2339` pools (`active_stake > pledge`).
- Best OLS specification reaches about `R^2 = 0.7015`.
- Delegator-choice FE: lagged `log(stake)` is robustly significant; `log(pledge)` is not robust across specifications.
- Stake-growth FE: low within `R^2` (`0.0035`), with `lag_member_pct` statistically significant.

## Reproduce Data Download

```bash
export CEXPLORER_API_KEY="your_api_key"
python3 download_cexplorer_pools_to_csv.py --output data/staking_pools.csv --limit 100
```

The API key is read from the environment and is not hardcoded in the repository.
