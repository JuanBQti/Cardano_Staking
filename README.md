# Cardano Staking Pools Analysis

This repository collects the analysis work done on Cardano staking pools, including:
- data extraction from Cexplorer,
- descriptive statistics and regression outputs,
- fixed-effects panel models,
- delegator-choice dynamics reports,
- supporting CSV/JSON/PDF artifacts.

## What Was Done

1. **Data collection**
   - Pulled staking pool data from Cexplorer using `download_cexplorer_pools_to_csv.py`.
   - Exported the base dataset as `staking_pools.csv`.

2. **Cross-sectional staking analysis**
   - Built active/non-active pool subsets and compact files.
   - Computed saturation and pledge/stake diagnostics.
   - Produced regression summaries and chart-ready CSV outputs.

3. **Panel fixed-effects model**
   - Estimated two-way FE model (pool FE + epoch FE) for stake growth dynamics.
   - Reported lagged-covariate coefficients with pool-clustered SE.

4. **Delegator-choice FE model**
   - Estimated multiple FE specifications for delegator growth.
   - Compared robustness of pledge vs. stake effects under lag structures.

## Key Results (High Level)

- Cross-sectional sample: `2339` pools with `active_stake > pledge`.
- Best multivariate spec (Model C) reaches about `R^2 = 0.7015`.
- In delegator-choice FE specs, lagged stake remains robustly significant; pledge is not robust across all specs.
- Panel FE stake-growth model has low within `R^2` (`0.0035`), with selected lagged controls significant (notably `lag_member_pct`).

## Main Deliverables

### Reports (Markdown)
- `staking_pools_report.md`
- `staking_pools_report_ada.md`
- `regression_summary.md`
- `staking_pools_panel_fe_report.md`
- `delegator_choice_results.md`
- `REPORTS.md` (index and quick guide)

### Data / Results Files
- `staking_pools.csv`
- `staking_pools_compact.csv`
- `staking_pools_compact_ada.csv`
- `staking_pools_not_active.csv`
- `staking_pools_panel.csv`
- `delegator_choice_panel.csv`
- `chart_data_stake_minus_pledge_vs_*.csv`
- `staking_pools_analysis.json`
- `regression_results.json`
- `staking_pools_panel_fe_results.json`
- `delegator_choice_results.json`

### Optional Publication Artifacts
- `staking_pools_report_ada.pdf`
- `staking_pools_panel_fe_report.pdf`
- `delegator_choice_results.pdf`
- Matching `.tex` sources

## Reproduce Data Download

Use your Cexplorer API key:

```bash
export CEXPLORER_API_KEY="your_api_key"
python3 download_cexplorer_pools_to_csv.py --output staking_pools.csv --limit 100
```

## Suggested GitHub Upload Scope

Include:
- all `.md` reports,
- core scripts used for collection/analysis,
- key `.csv` and `.json` results,
- optional `.pdf` report snapshots.

Do not include:
- local OS/config files,
- editor cache folders,
- large unrelated home-directory content.

This repo includes a restrictive `.gitignore` so you can safely stage only project artifacts even though the Git repo is initialized at your home directory root.
