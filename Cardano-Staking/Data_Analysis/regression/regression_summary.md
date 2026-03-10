# Regression Summary

Sample size: **2339** pools (`active_stake > pledge`).

Dependent variable: `log(1 + (active_stake - pledge) in ADA)`

| Model | ROA term(s) | R² | Adj. R² |
|---|---|---:|---:|
| A | lifetime_roa | 0.6664 | 0.6656 |
| B | recent_roa | 0.6930 | 0.6922 |
| C | lifetime_roa + recent_roa | 0.7015 | 0.7006 |

## Model A

| Variable | Beta | Robust SE | p-value |
|---|---:|---:|---:|
| Intercept | 5.1656 | 0.1467 | 0.0000 |
| log_pledge | 0.1664 | 0.0182 | 0.0000 |
| margin | 1.7314 | 0.3763 | 0.0000 |
| fixed_cost_ada | 0.0000 | 0.0000 | 0.0002 |
| saturation | 5.5399 | 0.3864 | 0.0000 |
| log_delegators | 0.9535 | 0.0434 | 0.0000 |
| lifetime_roa | 0.5655 | 0.0592 | 0.0000 |

## Model B

| Variable | Beta | Robust SE | p-value |
|---|---:|---:|---:|
| Intercept | 5.8093 | 0.1498 | 0.0000 |
| log_pledge | 0.1304 | 0.0178 | 0.0000 |
| margin | 2.3094 | 0.3770 | 0.0000 |
| fixed_cost_ada | 0.0000 | 0.0000 | 0.0005 |
| saturation | 3.4660 | 0.3988 | 0.0000 |
| log_delegators | 0.8503 | 0.0399 | 0.0000 |
| recent_roa | 1.7600 | 0.1360 | 0.0000 |

## Model C

| Variable | Beta | Robust SE | p-value |
|---|---:|---:|---:|
| Intercept | 5.5541 | 0.1468 | 0.0000 |
| log_pledge | 0.1266 | 0.0177 | 0.0000 |
| margin | 2.6853 | 0.4033 | 0.0000 |
| fixed_cost_ada | 0.0000 | 0.0000 | 0.0004 |
| saturation | 3.6243 | 0.3997 | 0.0000 |
| log_delegators | 0.7505 | 0.0556 | 0.0000 |
| lifetime_roa | 0.3743 | 0.0730 | 0.0000 |
| recent_roa | 1.5650 | 0.1424 | 0.0000 |

