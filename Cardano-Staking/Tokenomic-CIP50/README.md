# Tokenomic-CIP50 simulations

This folder contains a Python script to compare:

- current Cardano reward-share framework
- CIP-50 proposal (adds leverage cap through `p * L` in `sigma'`)

Implemented assumptions:

- `p = s`
- `p' = s'`
- use multiplication in the current formula term  
  `s' * (z0 - sigma') / z0` (not exponentiation)

## Parameters used

- `a0 = 0.3`
- `z0 = 75,000,000`
- `L = 100`
- `R = 0.0024`
- `p in {10,000; 100,000; 750,000}`

## Output

Running the script produces:

- `reward_comparison_current_vs_cip50.png`

The image has two panels:

1. `f(sigma)` for current vs CIP-50
2. `f(sigma) / sigma` for current vs CIP-50

## Run

From this folder:

```bash
python3 simulate_cip50_rewards.py
```

If needed:

```bash
python3 -m pip install numpy matplotlib
```
