# Import necessary libraries
# %pip install numdifftools

# %matplotlib inline

import math
import numpy as np
import pandas as pd
import sympy as sp
from scipy.optimize import root_scalar  # for root finding
import numdifftools as nd               # Numerical differentiation package
import matplotlib.pyplot as plt

# Model with Penalty for Losing Side
# This model introduces a fixed penalty b that is paid when voter i is on the "losing" side (k < n)
# inputs and parameters
B   = 1                               #budget to distribute among those voters of the winning election
a   = 1                               #cost coeficient (SET TO 0 to match your mathematical expression)
b   = 0.1                             #fixed penalty paid when on the losing side (k < n)
n_list = [1,3,6]                      #for the different cases as a function of  the number of voters
PG  = 0.5                             #probability Good state/quality
PB  = 1 - PG                          #probability Bad state/quality
mu = 1                                #factor to reduce the Budget used to pay those in the minority group (e.g. 1/3 if the proposal needs 2/3 of votes)

# Cost function
def cost(x):
    return a * x

# Threshold definition: K_R = ceil(R * (2n+1)) where R ∈ [0.5, 1]
# Helper function to compute K_R from R
def compute_K_R(n, R):
    """
    Compute K_R = ceil(R * (2n+1)) where R ∈ [0.5, 1]

    Args:
        n: number of voters
        R: threshold ratio (e.g., 0.5 for 50%, 2/3 for 66.6%)

    Returns:
        K_R: threshold value
    """
    return math.ceil(R * (2*n + 1))

# Probability function depending on effort
def p(x):
    return 0.5 + x

# Helper function to compute components for a given k
def compute_payoff_components(n, k, x_i, x_j, b=b, K_R=None, PG=PG, PB=PB, mu=mu):
    """Compute fraction, binomial terms, payoff terms, and penalty terms for given n, k, x_i, x_j

    Returns:
        fraction: payment fraction (only for k >= n)
        binomial_term_1: comb * (p_j ** k) * ((1 - p_j) ** (2*n - k)) for first sum
        binomial_term_2: comb * (p_j ** (2*n - k)) * ((1 - p_j) ** k) for second sum
        payoff_term_1: binomial_term_1 * fraction (for p_i term, only if k >= n)
        payoff_term_2: binomial_term_2 * fraction (for (1-p_i) term, only if k >= n)
        penalty_term_1: binomial_term_1 * b (for p_i term, only if k < n)
        penalty_term_2: binomial_term_2 * b (for (1-p_i) term, only if k < n)
    """
    if K_R is None:
        K_R = compute_K_R(n, 0.5)  # Default: 50% threshold = n+1

    p_j = p(x_j)
    comb = math.comb(2*n, k)

    # Payoff fraction (expected value E[f_i | i∈W, |W\{i}|=k])
    # Only computed if k >= n (winning side)
    if k >= n:
        fraction = x_i * B / (x_i + k * x_j) if (x_i + k * x_j) > 0 else 0
    else:
        fraction = 0

    # Binomial probability terms for the correct mathematical formula
    # First sum: binom(2n,k) * p_j^k * (1-p_j)^(2n-k)
    binomial_term_1 = comb * (p_j ** k) * ((1 - p_j) ** (2*n - k))

    # Second sum: binom(2n,k) * p_j^(2n-k) * (1-p_j)^k
    binomial_term_2 = comb * (p_j ** (2*n - k)) * ((1 - p_j) ** k)

    # Payoff terms (only computed if k >= n for 50% threshold)
    if k >= n:
        payoff_term_1 = binomial_term_1 * fraction
        payoff_term_2 = binomial_term_2 * fraction
        penalty_term_1 = 0
        penalty_term_2 = 0
    else:
        # Penalty terms (only computed if k < n, i.e., losing side)
        payoff_term_1 = 0
        payoff_term_2 = 0
        penalty_term_1 = binomial_term_1 * b
        penalty_term_2 = binomial_term_2 * b

    return (fraction,
            binomial_term_1, binomial_term_2,
            payoff_term_1, payoff_term_2,
            penalty_term_1, penalty_term_2)

# Define benefit function using the NEW mathematical formula with penalty
def benefit_i(n, x_i, x_j, b=b, k_range_winning=None, k_range_losing=None, K_R=None, PG=PG, PB=PB):
    """
    Benefit function based on the NEW mathematical formula with penalty:

    π_i = p_i * Σ(k≥n) binom(2n,k) * p_j^k * (1-p_j)^(2n-k) * E[f_i | i∈W, |W\{i}|=k]
        - p_i * Σ(k<n) binom(2n,k) * p_j^k * (1-p_j)^(2n-k) * b
        + (1-p_i) * Σ(k≥n) binom(2n,k) * p_j^(2n-k) * (1-p_j)^k * E[f_i | i∈W, |W\{i}|=k]
        - (1-p_i) * Σ(k<n) binom(2n,k) * p_j^(2n-k) * (1-p_j)^k * b
        - c(x_i)

    Args:
        n: number of voters
        x_i: effort of voter i
        x_j: effort of other voters
        b: fixed penalty for being on losing side
        k_range_winning: optional range override for winning side (if None, uses k ≥ n)
        k_range_losing: optional range override for losing side (if None, uses k < n)
        K_R: threshold for acceptance (not used in this formula, kept for compatibility)
        PG: probability of good state (not used in this simplified formula)
        PB: probability of bad state (not used in this simplified formula)
    """

    if k_range_winning is None:
        # For the mathematical formula: k ≥ n (winning side)
        k_range_winning = range(n, 2*n+1)
    
    if k_range_losing is None:
        # For the mathematical formula: k < n (losing side)
        k_range_losing = range(0, n)

    p_i = p(x_i)
    p_j = p(x_j)

    # Sums for winning side (k >= n): rewards
    total_sum_1_winning = 0   # First sum: p_i * Σ(k≥n) binom(2n,k) * p_j^k * (1-p_j)^(2n-k) * fraction
    total_sum_2_winning = 0   # Second sum: (1-p_i) * Σ(k≥n) binom(2n,k) * p_j^(2n-k) * (1-p_j)^k * fraction

    # Sums for losing side (k < n): penalties
    total_sum_1_losing = 0    # First sum: p_i * Σ(k<n) binom(2n,k) * p_j^k * (1-p_j)^(2n-k) * b
    total_sum_2_losing = 0    # Second sum: (1-p_i) * Σ(k<n) binom(2n,k) * p_j^(2n-k) * (1-p_j)^k * b

    # Compute winning side contributions
    for k in k_range_winning:
        (_, _, _, payoff_term_1, payoff_term_2, _, _) = compute_payoff_components(n, k, x_i, x_j, b, K_R, PG, PB, mu)
        total_sum_1_winning += payoff_term_1
        total_sum_2_winning += payoff_term_2

    # Compute losing side contributions (penalties)
    for k in k_range_losing:
        (_, _, _, _, _, penalty_term_1, penalty_term_2) = compute_payoff_components(n, k, x_i, x_j, b, K_R, PG, PB, mu)
        total_sum_1_losing += penalty_term_1
        total_sum_2_losing += penalty_term_2

    # Final formula: π_i = p_i * (sum_1_winning - sum_1_losing) + (1-p_i) * (sum_2_winning - sum_2_losing) - c(x_i)
    # But we return only the benefit part (without cost)
    result = p_i * (total_sum_1_winning - total_sum_1_losing) + (1 - p_i) * (total_sum_2_winning - total_sum_2_losing)

    return result

# Function to print the profit function symbolically for n=1
def print_profit_function_n1(b=b):
    """Print the profit function for n=1 in symbolic form with penalty"""
    print("PROFIT FUNCTION FOR n=1 (with penalty model):")
    print("=" * 60)

    n = 1
    k_range_winning = range(n, 2*n+1)  # k ≥ n, so k ∈ [1,2]
    k_range_losing = range(0, n)        # k < n, so k ∈ [0]

    print(f"n = {n}")
    print(f"k_range_winning = {list(k_range_winning)} (k ≥ n)")
    print(f"k_range_losing = {list(k_range_losing)} (k < n)")
    print(f"penalty b = {b}")
    print()

    print("Mathematical formula:")
    print("π_i = p_i * Σ(k≥n) binom(2n,k) * p_j^k * (1-p_j)^(2n-k) * E[f_i | i∈W, |W\\{i}|=k]")
    print("    - p_i * Σ(k<n) binom(2n,k) * p_j^k * (1-p_j)^(2n-k) * b")
    print("    + (1-p_i) * Σ(k≥n) binom(2n,k) * p_j^(2n-k) * (1-p_j)^k * E[f_i | i∈W, |W\\{i}|=k]")
    print("    - (1-p_i) * Σ(k<n) binom(2n,k) * p_j^(2n-k) * (1-p_j)^k * b")
    print("    - c(x_i)")
    print()
    print("Where E[f_i | i∈W, |W\\{i}|=k] = x_i / (x_i + k*x_j)")
    print()

    print("When x_i = x_j = x, p_i = p_j = 0.5 + x:")
    print()

    # For each k in winning side, show the terms
    print("WINNING SIDE (k ≥ n):")
    for k in k_range_winning:
        comb = math.comb(2*n, k)
        print(f"k = {k}:")
        print(f"  comb(2,{k}) = {comb}")
        print(f"  fraction = x / (x + {k}*x) = x / ({k+1}*x) = 1/{k+1}")
        print(f"  First sum term:  {comb} * (0.5+x)^{k} * (0.5-x)^{2*n-k} * (1/{k+1})")
        print(f"                 = {comb/(k+1)} * (0.5+x)^{k} * (0.5-x)^{2*n-k}")
        print(f"  Second sum term: {comb} * (0.5+x)^{2*n-k} * (0.5-x)^{k} * (1/{k+1})")
        print(f"                 = {comb/(k+1)} * (0.5+x)^{2*n-k} * (0.5-x)^{k}")
        print()

    # For each k in losing side, show the penalty terms
    print("LOSING SIDE (k < n):")
    for k in k_range_losing:
        comb = math.comb(2*n, k)
        print(f"k = {k}:")
        print(f"  comb(2,{k}) = {comb}")
        print(f"  First sum penalty term:  {comb} * (0.5+x)^{k} * (0.5-x)^{2*n-k} * b")
        print(f"                          = {comb} * (0.5+x)^{k} * (0.5-x)^{2*n-k} * {b}")
        print(f"  Second sum penalty term: {comb} * (0.5+x)^{2*n-k} * (0.5-x)^{k} * b")
        print(f"                          = {comb} * (0.5+x)^{2*n-k} * (0.5-x)^{k} * {b}")
        print()

    print("Final benefit function:")
    print("Benefit = (0.5+x) * [Winning sum - Losing penalty sum] + (0.5-x) * [Winning sum - Losing penalty sum]")
    print()

# Helper function to convert derivative result to scalar
def to_scalar(value):
    """Convert numpy array or array-like to scalar float"""
    if hasattr(value, 'item'):
        return float(value.item())
    elif hasattr(value, '__iter__') and not isinstance(value, str):
        return float(value[0]) if len(value) > 0 else float(value)
    else:
        return float(value)

# Helper function to check if a root is a maximum using second order conditions
def is_maximum(n, x_star, b=b, k_range_winning=None, k_range_losing=None, K_R=None):
    """Check if x_star is a maximum by computing second derivative of profit"""
    # Profit function: π_i = benefit_i - cost
    def profit(x_i):
        return benefit_i(n, x_i, x_star, b=b, k_range_winning=k_range_winning, 
                         k_range_losing=k_range_losing, K_R=K_R, PG=PG, PB=PB) - cost(x_i)

    # Compute second derivative of profit at x_star
    d2f = nd.Derivative(profit, n=2)  # n=2 means second derivative
    second_deriv = to_scalar(d2f(x_star))

    # For maximum: second derivative < 0
    # For minimum: second derivative > 0
    return second_deriv < 0

# Helper function to compute FOC and find equilibrium(s)
def compute_equilibrium(n, b=b, k_range_winning=None, k_range_losing=None, K_R=None, find_all_roots=True):
    """
    Compute all equilibrium x* for given n and k_range.
    Returns a list of tuples: [(x*, profit, type), ...] where type is 'corner' or 'interior'
    """
    def first_order_condition(x):
        # Compute ∂benefit_i/∂x_i at (x_i=x, x_j=x)
        f = lambda x_i: benefit_i(n, x_i, x, b=b, k_range_winning=k_range_winning, 
                                 k_range_losing=k_range_losing, K_R=K_R, PG=PG, PB=PB)
        dfdx = nd.Derivative(f, n=1, method='central', order=4)
        benefit_deriv = to_scalar(dfdx(x))

        # Compute ∂cost/∂x_i
        cost_derivative = nd.Derivative(cost, n=1, method='central', order=4)
        cost_deriv = to_scalar(cost_derivative(x))

        # FOC: ∂benefit_i/∂x_i - ∂cost/∂x_i = 0
        return benefit_deriv - cost_deriv

    def profit(x):
        """Profit function for comparison"""
        return benefit_i(n, x, x, b=b, k_range_winning=k_range_winning, 
                        k_range_losing=k_range_losing, K_R=K_R, PG=PG, PB=PB) - cost(x)

    # First, check for corner solutions by examining FOC over the domain
    # Sample FOC at several points to determine if it's always positive or always negative
    test_x = np.linspace(0.01, 0.49, 50)
    foc_samples = []
    for x in test_x:
        try:
            foc_samples.append(first_order_condition(x))
        except:
            foc_samples.append(np.nan)
    
    # Remove NaN values
    foc_samples_clean = [f for f in foc_samples if not np.isnan(f)]
    
    if len(foc_samples_clean) > 0:
        min_foc = min(foc_samples_clean)
        max_foc = max(foc_samples_clean)
        
        # If FOC > 0 for all x, profit is increasing -> corner at x=0.5
        if min_foc > 0:
            profit_at_05 = profit(0.5)
            return [(0.5, profit_at_05, 'corner')]
        
        # If FOC < 0 for all x, profit is decreasing -> corner at x=0
        if max_foc < 0:
            profit_at_0 = profit(0.0)
            return [(0.0, profit_at_0, 'corner')]

    # Find interior roots (where FOC = 0)
    roots = []

    if find_all_roots:
        # Use a finer grid to find roots
        x_fine = np.linspace(0.001, 0.499, 1000)
        foc_fine = []
        for x in x_fine:
            try:
                foc_val = first_order_condition(x)
                foc_fine.append(foc_val)
            except:
                foc_fine.append(np.nan)

        # Find sign changes - this finds roots where FOC crosses zero
        for i in range(len(foc_fine) - 1):
            if not (np.isnan(foc_fine[i]) or np.isnan(foc_fine[i+1])):
                if foc_fine[i] * foc_fine[i+1] < 0:
                    try:
                        bracket = [x_fine[i], x_fine[i+1]]
                        sol = root_scalar(first_order_condition, bracket=bracket, method='brentq',
                                         xtol=1e-10, rtol=1e-10)
                        if sol.converged:
                            # Check if it's a maximum
                            if is_maximum(n, sol.root, b=b, k_range_winning=k_range_winning, 
                                        k_range_losing=k_range_losing, K_R=K_R):
                                roots.append(sol.root)
                    except (ValueError, RuntimeError) as e:
                        continue

        # Remove duplicates - use larger tolerance to avoid reporting essentially identical roots
        unique_roots = []
        for r in sorted(roots):
            if not unique_roots or abs(r - unique_roots[-1]) > 0.01:  # Increased from 0.001 to 0.01
                unique_roots.append(r)
        roots = unique_roots

    # Build list of all equilibria
    equilibria_list = []
    
    # Add interior roots
    for r in roots:
        profit_at_r = profit(r)
        foc_at_r = first_order_condition(r)
        if abs(foc_at_r) < 0.1:  # Verify FOC is close to zero
            equilibria_list.append((r, profit_at_r, 'interior'))
    
    # Check corner solutions - but only if FOC doesn't cross zero
    # (if FOC crosses zero, we already have interior solutions)
    if len(roots) == 0:
        profit_at_0 = profit(0.0)
        profit_at_05 = profit(0.5)
        
        # Check if x=0 is a corner (FOC < 0 near 0)
        foc_at_001 = first_order_condition(0.001)
        if foc_at_001 < 0:
            equilibria_list.append((0.0, profit_at_0, 'corner'))
        
        # Check if x=0.5 is a corner (FOC > 0 near 0.5)
        foc_at_049 = first_order_condition(0.49)
        if foc_at_049 > 0:
            equilibria_list.append((0.5, profit_at_05, 'corner'))

    # Sort by x value
    equilibria_list.sort(key=lambda x: x[0])
    
    # Return list of equilibria (even if only one)
    if len(equilibria_list) == 0:
        return None
    elif len(equilibria_list) == 1:
        return equilibria_list[0][0]  # Return just the x value for backward compatibility
    else:
        return equilibria_list  # Return list of tuples

# Print the profit function for n=1
print_profit_function_n1(b=b)

# Initialize equilibria dictionary
equilibria = {}

# Plot First Order Conditions
x_vals = np.linspace(0.01, 0.5, 1000)
colors = ['blue', 'orange', 'green', 'red']

# For each n, compute and plot derivatives
for idx, n in enumerate(n_list):
    # Compute derivative of benefits with respect to x_i, evaluated at x_i = x_j = x
    def benefit_derivative_func(x):
        f = lambda x_i: benefit_i(n, x_i, x, b=b, k_range_winning=None, k_range_losing=None, K_R=None, PG=PG, PB=PB)
        dfdx = nd.Derivative(f, n=1, method='central', order=4)
        return to_scalar(dfdx(x))

    # Derivative of cost with respect to x_i
    def cost_derivative_func(x):
        cost_derivative = nd.Derivative(cost, n=1, method='central', order=4)
        return to_scalar(cost_derivative(x))

    # Compute derivatives for all x values
    benefit_derivative_vals = [benefit_derivative_func(x) for x in x_vals]
    cost_derivative_vals = [cost_derivative_func(x) for x in x_vals]

    # Plot both derivatives
    plt.plot(x_vals, benefit_derivative_vals, label=f"Benefits, n={n}",
             color=colors[idx], linestyle='-', linewidth=2)
    plt.plot(x_vals, cost_derivative_vals, label=f"Costs, n={n}",
             color=colors[idx], linestyle='--', linewidth=2)

plt.xlabel("Effort x")
plt.ylabel("Derivative")
plt.title(f"FOC: Benefits (solid) vs Cost (dashed) - Penalty Model (b={b})")
plt.legend()
plt.grid(True)
plt.axhline(y=0, color='black', linestyle=':', linewidth=0.5)
plt.show()

# Find equilibrium x* where FOC = 0
print("\nFinding equilibrium x* where FOC = 0 (derivatives cross):")
print("=" * 60)
for n in n_list:
    eq = compute_equilibrium(n, b=b, k_range_winning=None, k_range_losing=None, K_R=None, find_all_roots=True)
    equilibria[n] = eq

    if eq is not None:
        # Handle new return format: can be single x value or list of tuples
        if isinstance(eq, list) and len(eq) > 0 and isinstance(eq[0], tuple):
            # Multiple equilibria returned as list of tuples
            print(f"\nFor n={n}: Found {len(eq)} equilibrium(ia):")
            print("-" * 60)
            print(f"{'Equilibrium':<15} {'x*':<15} {'Profit':<15} {'Type':<15}")
            print("-" * 60)
            for i, (x_star, profit_at_eq, eq_type) in enumerate(eq):
                eq_label = f"x*{i+1}" if len(eq) > 1 else "x*"
                type_label = "corner" if eq_type == 'corner' else "interior"
                print(f"{eq_label:<15} {x_star:<15.6f} {profit_at_eq:<15.6f} {type_label:<15}")
            print("-" * 60)
        elif isinstance(eq, (int, float)):
            # Single equilibrium returned as x value
            x_star = eq
            profit_at_eq = benefit_i(n, x_star, x_star, b=b, k_range_winning=None, k_range_losing=None, K_R=None, PG=PG, PB=PB) - cost(x_star)
            # Determine type
            eq_type = 'corner' if (x_star == 0.0 or x_star == 0.5) else 'interior'
            print(f"\nFor n={n}: Found 1 equilibrium:")
            print("-" * 60)
            print(f"{'Equilibrium':<15} {'x*':<15} {'Profit':<15} {'Type':<15}")
            print("-" * 60)
            print(f"{'x*':<15} {x_star:<15.6f} {profit_at_eq:<15.6f} {eq_type:<15}")
            print("-" * 60)
        else:
            # Old format compatibility
            x_star = eq
            profit_at_eq = benefit_i(n, x_star, x_star, b=b, k_range_winning=None, k_range_losing=None, K_R=None, PG=PG, PB=PB) - cost(x_star)
            corner_note = " (corner)" if (x_star == 0.0 or x_star == 0.5) else ""
            print(f"For n={n}: x* = {x_star:.6f}{corner_note}, profit = {profit_at_eq:.6f}")
    else:
        print(f"For n={n}: No equilibrium found")
    print()

# Plot profits for each voter when efforts are symmetric
plt.figure(figsize=(8,6))
for idx, n in enumerate(n_list):
    benefits = [benefit_i(n, x, x, b=b, k_range_winning=None, k_range_losing=None, K_R=None, PG=PG, PB=PB) for x in x_vals]
    costs = [cost(x) for x in x_vals]
    profits = [b - c for b, c in zip(benefits, costs)]
    plt.plot(x_vals, profits, label=f"Profit (n={n})", color=colors[idx])

    # Mark equilibrium(ia) from computed values
    if n not in equilibria:
        equilibria[n] = compute_equilibrium(n, b=b, k_range_winning=None, k_range_losing=None, K_R=None, find_all_roots=True)

    if n in equilibria and equilibria[n] is not None:
        eq_result = equilibria[n]
        
        # Extract x values from the result (could be single x, or list of tuples)
        x_stars = []
        if isinstance(eq_result, list) and len(eq_result) > 0 and isinstance(eq_result[0], tuple):
            # List of tuples: [(x, profit, type), ...]
            x_stars = [x for x, _, _ in eq_result]
        elif isinstance(eq_result, (int, float)):
            # Single x value
            x_stars = [eq_result]
        else:
            # Old format compatibility
            x_stars = [eq_result] if not isinstance(eq_result, (list, tuple)) else list(eq_result)

        for x_star in x_stars:
            profit_at_eq = benefit_i(n, x_star, x_star, b=b, k_range_winning=None, k_range_losing=None, K_R=None, PG=PG, PB=PB) - cost(x_star)
            plt.plot(x_star, profit_at_eq, 'o', color=colors[idx], markersize=10)
            plt.axvline(x=x_star, color=colors[idx], linestyle=':', linewidth=1.5, alpha=0.7)
            label = f'  x*={x_star:.4f}'
            if x_star == 0.0 or x_star == 0.5:
                label += '\n(corner)'
            else:
                label += '\n(max)'
            plt.text(x_star, profit_at_eq, label,
                    color=colors[idx], fontsize=9, verticalalignment='bottom')

plt.xlabel("Effort x")
plt.ylabel("Profit")
plt.title(f"Profit (Benefits - Costs) as a function of effort x - Penalty Model (b={b})\n(Equilibria marked)")
plt.legend()
plt.grid(True)
plt.show()

# Plot components for each n and k
# We'll use the ACTUAL equilibrium x* values
print("\n" + "=" * 60)
print("Plotting components (fraction, binomial term, payoff term, penalty term) for each n and k")
print("Using ACTUAL equilibrium values")
print("=" * 60)

# Create a figure with subplots for each n
fig, axes = plt.subplots(len(n_list), 1, figsize=(12, 5*len(n_list)))
if len(n_list) == 1:
    axes = [axes]  # Make it iterable

for idx, n in enumerate(n_list):
    # Use ACTUAL equilibrium x* from computed values
    x_used = None

    # If equilibria not computed yet, compute it now
    if n not in equilibria:
        equilibria[n] = compute_equilibrium(n, b=b, k_range_winning=None, k_range_losing=None, K_R=None, find_all_roots=True)

    if n in equilibria and equilibria[n] is not None:
        eq_result = equilibria[n]
        
        # Extract x values and find the one with highest profit
        if isinstance(eq_result, list) and len(eq_result) > 0 and isinstance(eq_result[0], tuple):
            # List of tuples: [(x, profit, type), ...]
            # Use the one with highest profit (already computed in the tuple)
            best_eq = max(eq_result, key=lambda x: x[1])
            x_used = best_eq[0]
        elif isinstance(eq_result, (int, float)):
            # Single x value
            x_used = eq_result
        else:
            # Old format compatibility
            if isinstance(eq_result, (list, tuple)):
                # If multiple equilibria, use the one with highest profit
                profits = [benefit_i(n, x, x, b=b, k_range_winning=None, k_range_losing=None, K_R=None, PG=PG, PB=PB) - cost(x) for x in eq_result]
                best_idx = np.argmax(profits)
                x_used = eq_result[best_idx]
            else:
                x_used = eq_result

    # If no equilibrium found or x_used is None, try to find one
    if x_used is None:
        try:
            def first_order_condition(x):
                f = lambda x_i: benefit_i(n, x_i, x, b=b, k_range_winning=None, k_range_losing=None, K_R=None, PG=PG, PB=PB)
                dfdx = nd.Derivative(f, n=1, method='central', order=4)
                benefit_deriv = to_scalar(dfdx(x))
                cost_derivative = nd.Derivative(cost, n=1, method='central', order=4)
                cost_deriv = to_scalar(cost_derivative(x))
                return benefit_deriv - cost_deriv
            sol = root_scalar(first_order_condition, bracket=[0.01, 0.5], method='brentq')
            if sol.converged and is_maximum(n, sol.root, b=b, k_range_winning=None, k_range_losing=None, K_R=None):
                x_used = sol.root
        except:
            pass

    # If still no equilibrium, check corner solutions
    if x_used is None:
        profit_at_0 = benefit_i(n, 0.0, 0.0, b=b, k_range_winning=None, k_range_losing=None, K_R=None, PG=PG, PB=PB) - cost(0.0)
        profit_at_05 = benefit_i(n, 0.5, 0.5, b=b, k_range_winning=None, k_range_losing=None, K_R=None, PG=PG, PB=PB) - cost(0.5)
        profit_at_01 = benefit_i(n, 0.1, 0.1, b=b, k_range_winning=None, k_range_losing=None, K_R=None, PG=PG, PB=PB) - cost(0.1)

        if profit_at_0 >= profit_at_01:
            x_used = 0.0
        elif profit_at_05 >= profit_at_01:
            x_used = 0.5
        else:
            x_used = 0.1  # Fallback

    print(f"n={n}: Using x* = {x_used:.6f} for component plots")

    # Get k values for both winning and losing sides
    k_values_winning = list(range(n, 2*n+1))
    k_values_losing = list(range(0, n))
    k_values_all = k_values_losing + k_values_winning

    # Compute components for each k
    fractions = []
    binomial_terms_1 = []
    binomial_terms_2 = []
    payoff_terms_1 = []
    payoff_terms_2 = []
    penalty_terms_1 = []
    penalty_terms_2 = []

    p_i = p(x_used)

    for k in k_values_all:
        # Use the shared component computation function
        (frac, bin_term_1, bin_term_2,
         payoff_term_1, payoff_term_2,
         penalty_term_1, penalty_term_2) = compute_payoff_components(n, k, x_used, x_used, b, None, PG, PB, mu)

        fractions.append(frac)
        binomial_terms_1.append(bin_term_1)
        binomial_terms_2.append(bin_term_2)
        payoff_terms_1.append(payoff_term_1)
        payoff_terms_2.append(payoff_term_2)
        penalty_terms_1.append(penalty_term_1)
        penalty_terms_2.append(penalty_term_2)

    # Create bar plot
    x_pos = np.arange(len(k_values_all))
    width = 0.12  # Width of bars (reduced to fit more bars)

    axes[idx].bar(x_pos - 3*width, fractions, width, label='Fraction', alpha=0.8)
    axes[idx].bar(x_pos - 2*width, binomial_terms_1, width, label='Binomial term 1', alpha=0.8)
    axes[idx].bar(x_pos - width, binomial_terms_2, width, label='Binomial term 2', alpha=0.8)
    axes[idx].bar(x_pos, payoff_terms_1, width, label='Payoff term 1', alpha=0.8)
    axes[idx].bar(x_pos + width, payoff_terms_2, width, label='Payoff term 2', alpha=0.8)
    axes[idx].bar(x_pos + 2*width, penalty_terms_1, width, label='Penalty term 1', alpha=0.8, color='red')
    axes[idx].bar(x_pos + 3*width, penalty_terms_2, width, label='Penalty term 2', alpha=0.8, color='darkred')

    axes[idx].set_xlabel('k (number of correct votes)')
    axes[idx].set_ylabel('Value')
    corner_note = " (corner)" if (x_used == 0.0 or x_used == 0.5) else ""
    axes[idx].set_title(f'n = {n} (x_i = x_j = {x_used:.4f}{corner_note}, b={b}, k < n: losing, k ≥ n: winning)')
    axes[idx].set_xticks(x_pos)
    axes[idx].set_xticklabels([f'k={k}' for k in k_values_all])
    axes[idx].legend()
    axes[idx].grid(True, alpha=0.3, axis='y')
    
    # Add vertical line to separate losing and winning sides
    axes[idx].axvline(x=len(k_values_losing)-0.5, color='black', linestyle='--', linewidth=1, alpha=0.5)
    axes[idx].text(len(k_values_losing)-0.5, axes[idx].get_ylim()[1]*0.9, 'Losing/Winning\nboundary', 
                   ha='center', fontsize=8, rotation=90, verticalalignment='top')

    # Add value labels on bars (only if values are significant)
    for i, (frac, bin1, bin2, pay1, pay2, pen1, pen2) in enumerate(zip(fractions, binomial_terms_1, binomial_terms_2, 
                                                                       payoff_terms_1, payoff_terms_2,
                                                                       penalty_terms_1, penalty_terms_2)):
        if abs(frac) > 1e-6:
            axes[idx].text(i - 3*width, frac, f'{frac:.3f}', ha='center', va='bottom', fontsize=6, rotation=90)
        if abs(bin1) > 1e-6:
            axes[idx].text(i - 2*width, bin1, f'{bin1:.3f}', ha='center', va='bottom', fontsize=6, rotation=90)
        if abs(bin2) > 1e-6:
            axes[idx].text(i - width, bin2, f'{bin2:.3f}', ha='center', va='bottom', fontsize=6, rotation=90)
        if abs(pay1) > 1e-6:
            axes[idx].text(i, pay1, f'{pay1:.3f}', ha='center', va='bottom', fontsize=6, rotation=90)
        if abs(pay2) > 1e-6:
            axes[idx].text(i + width, pay2, f'{pay2:.3f}', ha='center', va='bottom', fontsize=6, rotation=90)
        if abs(pen1) > 1e-6:
            axes[idx].text(i + 2*width, pen1, f'{pen1:.3f}', ha='center', va='bottom', fontsize=6, rotation=90)
        if abs(pen2) > 1e-6:
            axes[idx].text(i + 3*width, pen2, f'{pen2:.3f}', ha='center', va='bottom', fontsize=6, rotation=90)

plt.tight_layout()
plt.show()

