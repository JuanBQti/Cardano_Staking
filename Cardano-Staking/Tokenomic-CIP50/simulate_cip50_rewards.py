#!/usr/bin/env python3
"""
Simulate and plot Cardano pool reward-share functions for:
1) Current framework
2) CIP-50 proposal (with leverage cap p * L inside sigma')

Assumptions requested by user:
- p = s
- p' = s'
- In the current formula, use multiplication (not exponentiation) in:
  s' * (z0 - sigma') / z0
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
import numpy as np

# Use a non-interactive backend for CLI/headless execution.
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def current_reward(
    sigma: np.ndarray,
    p: float,
    a0: float,
    z0: float,
    r: float,
) -> np.ndarray:
    """
    Current Cardano-style reward-share function f(sigma, p).
    """
    sigma_prime = np.minimum(sigma, z0)
    p_prime = min(p, z0)

    inner = sigma_prime - (p_prime * (z0 - sigma_prime) / z0)
    reward = (r / (1.0 + a0)) * (sigma_prime + (p_prime * a0 * inner / z0))
    return reward


def cip50_reward(
    sigma: np.ndarray,
    p: float,
    a0: float,
    z0: float,
    l_value: float,
    r: float,
) -> np.ndarray:
    """
    CIP-50 proposal reward-share function:
    sigma' = min(sigma, z0, p * L)
    """
    sigma_prime = np.minimum(np.minimum(sigma, z0), p * l_value)
    p_prime = min(p, z0)

    inner = sigma_prime - (p_prime * (z0 - sigma_prime) / z0)
    reward = (r / (1.0 + a0)) * (sigma_prime + (p_prime * a0 * inner / z0))
    return reward


def save_plot_rewards(
    sigma: np.ndarray,
    p_values: list[float],
    a0: float,
    z0: float,
    l_value: float,
    r: float,
    output_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5), constrained_layout=True)

    for p in p_values:
        f_current = current_reward(sigma=sigma, p=p, a0=a0, z0=z0, r=r)
        f_cip50 = cip50_reward(
            sigma=sigma,
            p=p,
            a0=a0,
            z0=z0,
            l_value=l_value,
            r=r,
        )

        axes[0].plot(sigma, f_current, label=f"Current, p={p:,.0f}")
        axes[0].plot(sigma, f_cip50, "--", label=f"CIP-50, p={p:,.0f}")

    axes[0].set_title("f(sigma): current vs CIP-50")
    axes[0].set_xlabel("Total stake sigma (ADA)")
    axes[0].set_ylabel("f(sigma)")
    axes[0].grid(alpha=0.25)
    axes[0].legend(fontsize=8, ncol=2)

    for p in p_values:
        f_current = current_reward(sigma=sigma, p=p, a0=a0, z0=z0, r=r)
        f_cip50 = cip50_reward(
            sigma=sigma,
            p=p,
            a0=a0,
            z0=z0,
            l_value=l_value,
            r=r,
        )

        ratio_current = np.divide(
            f_current,
            sigma,
            out=np.zeros_like(f_current),
            where=sigma > 0,
        )
        ratio_cip50 = np.divide(
            f_cip50,
            sigma,
            out=np.zeros_like(f_cip50),
            where=sigma > 0,
        )

        axes[1].plot(sigma, ratio_current, label=f"Current, p={p:,.0f}")
        axes[1].plot(sigma, ratio_cip50, "--", label=f"CIP-50, p={p:,.0f}")

    axes[1].set_title("f(sigma) / sigma: current vs CIP-50")
    axes[1].set_xlabel("Total stake sigma (ADA)")
    axes[1].set_ylabel("f(sigma) / sigma")
    axes[1].grid(alpha=0.25)
    axes[1].legend(fontsize=8, ncol=2)

    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def main() -> None:
    # Requested parameter values.
    a0 = 0.3
    z0 = 75_000_000.0
    l_value = 100.0
    r = 0.0024
    p_values = [10_000.0, 100_000.0, 750_000.0]

    # sigma range for plotting:
    # - start at 1 to avoid division by zero in ratio visualization
    # - end at 2*z0 to show post-saturation behavior
    sigma = np.linspace(1.0, 2.0 * z0, 2000)

    out_dir = Path(__file__).resolve().parent
    out_file = out_dir / "reward_comparison_current_vs_cip50.png"

    save_plot_rewards(
        sigma=sigma,
        p_values=p_values,
        a0=a0,
        z0=z0,
        l_value=l_value,
        r=r,
        output_path=out_file,
    )

    print("Saved plot to:", out_file)
    print("Parameters:")
    print(f"  a0 = {a0}")
    print(f"  z0 = {z0:,.0f}")
    print(f"  L  = {l_value}")
    print(f"  R  = {r}")
    print("  p values =", [f"{p:,.0f}" for p in p_values])


if __name__ == "__main__":
    main()
