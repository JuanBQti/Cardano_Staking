# Import necessary libraries
%pip install numdifftools

import math
import numpy as np
import pandas as pd
import sympy as sp
from scipy.optimize import root_scalar
import numdifftools as nd
import matplotlib.pyplot as plt

# Model with Payment conditional on being in the Winning Side
# This model considers two benefit components: one when supermajority accepts and one when it rejects

# Inputs and parameters
B   = 1                               # budget to distribute among those voters of the winning election
a   = 1                               # cost coefficient
R   = 2/3                             # threshold ratio R ∈ [0.5, 1] (e.g., 0.5 for 50%, 2/3 for 66.6%)
n_list = [1,3,6]                      # for the different cases as a function of the number of voters
PG  = 0.5                             # probability Good state/quality
PB  = 1 - PG                          # probability Bad state/quality

# Cost function
def cost(x):
    return a * x

# Threshold definition: K_R = ceil(R * (2n+1)) where R ∈ [0.5, 1]
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
def compute_payoff_components(n, k, x_i, x_j, K_R=None, PG=PG, PB=PB):
    """Compute fraction and binomial terms for given n, k, x_i, x_j

    Returns:
        fraction: payment fraction x_i / (x_i + k*x_j)
        binomial_term_1: comb * (p_j ** k) * ((1 - p_j) ** (2*n - k))
        binomial_term_2: comb * (p_j ** (2*n - k)) * ((1 - p_j) ** k)
    """
    if K_R is None:
        K_R = compute_K_R(n, R)

    p_j = p(x_j)
    comb = math.comb(2*n, k)

    # Payoff fraction (expected value E[f_i | i∈W, |W\{i}|=k])
    fraction = x_i * B / (x_i + k * x_j) if (x_i + k * x_j) > 0 else 0

    # Binomial probability terms
    binomial_term_1 = comb * (p_j ** k) * ((1 - p_j) ** (2*n - k))
    binomial_term_2 = comb * (p_j ** (2*n - k)) * ((1 - p_j) ** k)

    return (fraction, binomial_term_1, binomial_term_2)

# Define benefit function using the new mathematical formula
def benefit_i(n, x_i, x_j, K_R=None, PG=PG, PB=PB):
    """
    Benefit function based on the mathematical formula:

    π_i = P(G) * [p_i * Σ(k≥K_R-1) binom(2n,k) * p_j^k * (1-p_j)^(2n-k) * E[f_i | i∈W, |W\{i}|=k]
                + (1-p_i) * Σ(k≥2n+1-K_R) binom(2n,k) * p_j^(2n-k) * (1-p_j)^k * E[f_i | i∈W, |W\{i}|=k]]
         + P(B) * [p_i * Σ(k≥2n+1-K_R) binom(2n,k) * p_j^k * (1-p_j)^(2n-k) * E[f_i | i∈W, |W\{i}|=k]
                + (1-p_i) * Σ(k≥K_R-1) binom(2n,k) * p_j^(2n-k) * (1-p_j)^k * E[f_i | i∈W, |W\{i}|=k]]
         - c(x_i)

    Args:
        n: number of voters
        x_i: effort of voter i
        x_j: effort of other voters
        K_R: threshold for acceptance (if None, computed from global R)
        PG: probability of good state
        PB: probability of bad state
    """
    if K_R is None:
        K_R = compute_K_R(n, R)

    p_i = p(x_i)
    p_j = p(x_j)

    # Range for acceptance: k ≥ K_R - 1
    k_range_accept = range(max(0, K_R - 1), 2*n+1)
    # Range for rejection: k ≥ 2n+1-K_R
    k_range_reject = range(max(0, 2*n+1-K_R), 2*n+1)

    # P(G) components
    # p_i term: acceptance (k ≥ K_R - 1)
    sum_G_pi_accept = 0
    for k in k_range_accept:
        (fraction, bin_term_1, _) = compute_payoff_components(n, k, x_i, x_j, K_R, PG, PB)
        sum_G_pi_accept += bin_term_1 * fraction

    # (1-p_i) term: rejection (k ≥ 2n+1-K_R)
    sum_G_1pi_reject = 0
    for k in k_range_reject:
        (fraction, _, bin_term_2) = compute_payoff_components(n, k, x_i, x_j, K_R, PG, PB)
        sum_G_1pi_reject += bin_term_2 * fraction

    # P(B) components
    # p_i term: rejection (k ≥ 2n+1-K_R)
    sum_B_pi_reject = 0
    for k in k_range_reject:
        (fraction, bin_term_1, _) = compute_payoff_components(n, k, x_i, x_j, K_R, PG, PB)
        sum_B_pi_reject += bin_term_1 * fraction

    # (1-p_i) term: acceptance (k ≥ K_R - 1)
    sum_B_1pi_accept = 0
    for k in k_range_accept:
        (fraction, _, bin_term_2) = compute_payoff_components(n, k, x_i, x_j, K_R, PG, PB)
        sum_B_1pi_accept += bin_term_2 * fraction

    # Final formula
    result = PG * (p_i * sum_G_pi_accept + (1 - p_i) * sum_G_1pi_reject) + \
             PB * (p_i * sum_B_pi_reject + (1 - p_i) * sum_B_1pi_accept)

    return result

# Function to print the profit function symbolically for n=1
def print_profit_function_n1(R=R):
    """Print the profit function for n=1 in symbolic form"""
    print("PROFIT FUNCTION FOR n=1:")
    print("=" * 60)
    n = 1
    K_R = compute_K_R(n, R)
    k_range_accept = range(max(0, K_R - 1), 2*n+1)
    k_range_reject = range(max(0, 2*n+1-K_R), 2*n+1)
    print(f"n = {n}")
    print(f"R = {R} ({R*100:.1f}% threshold)")
    print(f"K_R = {K_R}")
    print(f"k_range_accept = {list(k_range_accept)} (k ≥ K_R - 1)")
    print(f"k_range_reject = {list(k_range_reject)} (k ≥ 2n+1-K_R)")
    print(f"P(G) = {PG}, P(B) = {PB}")
    print()

    print("Mathematical formula:")
    print("π_i = P(G) * [p_i * Σ(k≥K_R-1) binom(2n,k) * p_j^k * (1-p_j)^(2n-k) * E[f_i | i∈W, |W\\{i}|=k]")
    print("                + (1-p_i) * Σ(k≥2n+1-K_R) binom(2n,k) * p_j^(2n-k) * (1-p_j)^k * E[f_i | i∈W, |W\\{i}|=k]]")
    print("     + P(B) * [p_i * Σ(k≥2n+1-K_R) binom(2n,k) * p_j^k * (1-p_j)^(2n-k) * E[f_i | i∈W, |W\\{i}|=k]")
    print("                + (1-p_i) * Σ(k≥K_R-1) binom(2n,k) * p_j^(2n-k) * (1-p_j)^k * E[f_i | i∈W, |W\\{i}|=k]]")
    print("     - c(x_i)")
    print()

    print("Where E[f_i | i∈W, |W\\{i}|=k] = x_i / (x_i + k*x_j)")
    print()

    print("When x_i = x_j = x, p_i = p_j = 0.5 + x:")
    print()

    print("ACCEPTANCE (k ≥ K_R - 1):")
    for k in k_range_accept:
        comb = math.comb(2*n, k)
        print(f"k = {k}:")
        print(f"  comb(2,{k}) = {comb}")
        print(f"  fraction = x / (x + {k}*x) = x / ({k+1}*x) = 1/{k+1}")
        print(f"  P(G) * p_i term:  {comb} * (0.5+x)^{k} * (0.5-x)^{2*n-k} * (1/{k+1})")
        print(f"                   = {comb/(k+1)} * (0.5+x)^{k} * (0.5-x)^{2*n-k}")
        print(f"  P(B) * (1-p_i) term: {comb} * (0.5+x)^{2*n-k} * (0.5-x)^{k} * (1/{k+1})")
        print(f"                       = {comb/(k+1)} * (0.5+x)^{2*n-k} * (0.5-x)^{k}")
        print()

    print("REJECTION (k ≥ 2n+1-K_R):")
    for k in k_range_reject:
        comb = math.comb(2*n, k)
        print(f"k = {k}:")
        print(f"  comb(2,{k}) = {comb}")
        print(f"  fraction = x / (x + {k}*x) = x / ({k+1}*x) = 1/{k+1}")
        print(f"  P(G) * (1-p_i) term: {comb} * (0.5+x)^{2*n-k} * (0.5-x)^{k} * (1/{k+1})")
        print(f"                      = {comb/(k+1)} * (0.5+x)^{2*n-k} * (0.5-x)^{k}")
        print(f"  P(B) * p_i term:  {comb} * (0.5+x)^{k} * (0.5-x)^{2*n-k} * (1/{k+1})")
        print(f"                    = {comb/(k+1)} * (0.5+x)^{k} * (0.5-x)^{2*n-k}")
        print()

    print("Final benefit function:")
    print("Benefit = P(G) * [p_i * (acceptance sum) + (1-p_i) * (rejection sum)]")
    print("         + P(B) * [p_i * (rejection sum) + (1-p_i) * (acceptance sum)]")
    print()

# Function to print the FOC of benefits with respect to x_i for n=1
def print_foc_benefits_n1(R=R):
    """Print the First Order Condition (FOC) of benefits with respect to x_i for n=1"""
    print("FOC OF BENEFITS WITH RESPECT TO x_i FOR n=1:")
    print("=" * 60)
    n = 1
    K_R = compute_K_R(n, R)
    k_range_accept = range(max(0, K_R - 1), 2*n+1)
    k_range_reject = range(max(0, 2*n+1-K_R), 2*n+1)
    print(f"n = {n}")
    print(f"R = {R} ({R*100:.1f}% threshold)")
    print(f"K_R = {K_R}")
    print(f"k_range_accept = {list(k_range_accept)} (k ≥ K_R - 1)")
    print(f"k_range_reject = {list(k_range_reject)} (k ≥ 2n+1-K_R)")
    print(f"P(G) = {PG}, P(B) = {PB}")
    print()

    print("The FOC of benefits is: ∂benefit_i/∂x_i")
    print()

    print("Where benefit_i = P(G) * [p_i * (acceptance sum) + (1-p_i) * (rejection sum)]")
    print("                  + P(B) * [p_i * (rejection sum) + (1-p_i) * (acceptance sum)]")
    print()

    print("With p_i = 0.5 + x_i, so ∂p_i/∂x_i = 1")
    print()

    print("The derivative includes:")
    print("  1. The derivative of p_i (which is 1) times the sum terms")
    print("  2. p_i times the derivative of the fraction terms")
    print()

    print("The key derivative is ∂(fraction)/∂x_i where fraction = x_i / (x_i + k*x_j):")
    print("∂(x_i / (x_i + k*x_j))/∂x_i = (x_i + k*x_j - x_i) / (x_i + k*x_j)^2")
    print("                              = k*x_j / (x_i + k*x_j)^2")
    print()

    print("When x_i = x_j = x:")
    print("∂(fraction)/∂x_i = k*x / (x + k*x)^2 = k*x / ((k+1)*x)^2 = k / ((k+1)^2 * x)")
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

# Helper function to compute the FOC of benefits with respect to x_i explicitly
def benefit_foc_explicit(n, x_i, x_j, K_R=None, PG=PG, PB=PB):
    """
    Explicitly compute ∂benefit_i/∂x_i accounting for:

    1. The derivative of p_i (which is 1)
    2. The derivative of the fraction terms
    """
    if K_R is None:
        K_R = compute_K_R(n, R)

    p_i = p(x_i)
    p_j = p(x_j)

    # Range for acceptance: k ≥ K_R - 1
    k_range_accept = range(max(0, K_R - 1), 2*n+1)
    # Range for rejection: k ≥ 2n+1-K_R
    k_range_reject = range(max(0, 2*n+1-K_R), 2*n+1)

    # P(G) components - sums and derivatives
    sum_G_pi_accept = 0
    d_sum_G_pi_accept = 0
    sum_G_1pi_reject = 0
    d_sum_G_1pi_reject = 0

    for k in k_range_accept:
        comb = math.comb(2*n, k)
        bin_term_1 = comb * (p_j ** k) * ((1 - p_j) ** (2*n - k))
        if (x_i + k * x_j) > 0:
            fraction = x_i * B / (x_i + k * x_j)
            dfraction_dx = (k * x_j * B) / ((x_i + k * x_j) ** 2)
        else:
            fraction = 0
            dfraction_dx = 0
        sum_G_pi_accept += bin_term_1 * fraction
        d_sum_G_pi_accept += bin_term_1 * dfraction_dx

    for k in k_range_reject:
        comb = math.comb(2*n, k)
        bin_term_2 = comb * (p_j ** (2*n - k)) * ((1 - p_j) ** k)
        if (x_i + k * x_j) > 0:
            fraction = x_i * B / (x_i + k * x_j)
            dfraction_dx = (k * x_j * B) / ((x_i + k * x_j) ** 2)
        else:
            fraction = 0
            dfraction_dx = 0
        sum_G_1pi_reject += bin_term_2 * fraction
        d_sum_G_1pi_reject += bin_term_2 * dfraction_dx

    # P(B) components - sums and derivatives
    sum_B_pi_reject = 0
    d_sum_B_pi_reject = 0
    sum_B_1pi_accept = 0
    d_sum_B_1pi_accept = 0

    for k in k_range_reject:
        comb = math.comb(2*n, k)
        bin_term_1 = comb * (p_j ** k) * ((1 - p_j) ** (2*n - k))
        if (x_i + k * x_j) > 0:
            fraction = x_i * B / (x_i + k * x_j)
            dfraction_dx = (k * x_j * B) / ((x_i + k * x_j) ** 2)
        else:
            fraction = 0
            dfraction_dx = 0
        sum_B_pi_reject += bin_term_1 * fraction
        d_sum_B_pi_reject += bin_term_1 * dfraction_dx

    for k in k_range_accept:
        comb = math.comb(2*n, k)
        bin_term_2 = comb * (p_j ** (2*n - k)) * ((1 - p_j) ** k)
        if (x_i + k * x_j) > 0:
            fraction = x_i * B / (x_i + k * x_j)
            dfraction_dx = (k * x_j * B) / ((x_i + k * x_j) ** 2)
        else:
            fraction = 0
            dfraction_dx = 0
        sum_B_1pi_accept += bin_term_2 * fraction
        d_sum_B_1pi_accept += bin_term_2 * dfraction_dx

    # Compute the full derivative
    # ∂benefit_i/∂x_i = P(G) * [∂p_i/∂x_i * sum_G_pi_accept + p_i * d_sum_G_pi_accept
    #                            - ∂p_i/∂x_i * sum_G_1pi_reject + (1-p_i) * d_sum_G_1pi_reject]
    #                   + P(B) * [∂p_i/∂x_i * sum_B_pi_reject + p_i * d_sum_B_pi_reject
    #                            - ∂p_i/∂x_i * sum_B_1pi_accept + (1-p_i) * d_sum_B_1pi_accept]
    # Since ∂p_i/∂x_i = 1:
    result = PG * (sum_G_pi_accept + p_i * d_sum_G_pi_accept - sum_G_1pi_reject + (1 - p_i) * d_sum_G_1pi_reject) + \
             PB * (sum_B_pi_reject + p_i * d_sum_B_pi_reject - sum_B_1pi_accept + (1 - p_i) * d_sum_B_1pi_accept)

    return result

# Helper function to check if a root is a maximum using second order conditions
def is_maximum(n, x_star, K_R=None):
    """Check if x_star is a maximum by computing second derivative of profit"""
    def profit(x_i):
        return benefit_i(n, x_i, x_star, K_R=K_R, PG=PG, PB=PB) - cost(x_i)

    d2f = nd.Derivative(profit, n=2)
    second_deriv = to_scalar(d2f(x_star))

    return second_deriv < 0

# Helper function to find maximum x* where profit is approximately zero (positive)
def find_zero_profit_solution(n, K_R=None):
    """
    Find the maximum x* in [0.001, 0.5] where profit is zero or almost zero (but positive).

    Returns (x*, profit) or None if no such point exists.
    """
    def profit(x):
        return benefit_i(n, x, x, K_R=K_R, PG=PG, PB=PB) - cost(x)

    x_search = np.linspace(0.5, 0.001, 1000)
    for x in x_search:
        try:
            p_val = profit(x)
            if p_val >= 0:
                low = 0.001
                high = x
                tolerance = 1e-6
                max_iter = 100
                iter_count = 0
                while (high - low) > tolerance and iter_count < max_iter:
                    mid = (low + high) / 2
                    p_mid = profit(mid)
                    if p_mid >= 0:
                        low = mid
                    else:
                        high = mid
                    iter_count += 1
                final_x = low
                final_profit = profit(final_x)
                if final_profit >= -1e-6:
                    return (final_x, max(0.0, final_profit))
        except:
            continue
    return None

# Helper function to compute FOC and find equilibrium(s)
def compute_equilibrium(n, K_R=None, find_all_roots=True):
    """
    Compute all equilibrium x* for given n.

    Returns a list of tuples: [(x*, profit, type), ...] where type is 'corner' or 'interior'
    Also returns zero_profit_solution if x=0.5 corner has negative profit: (x*, profit) or None
    """
    if K_R is None:
        K_R = compute_K_R(n, R)

    def first_order_condition(x):
        benefit_deriv = benefit_foc_explicit(n, x, x, K_R=K_R, PG=PG, PB=PB)
        cost_deriv = a
        return benefit_deriv - cost_deriv

    def profit(x):
        return benefit_i(n, x, x, K_R=K_R, PG=PG, PB=PB) - cost(x)

    foc_at_05 = None
    try:
        foc_at_05 = first_order_condition(0.5)
    except:
        pass

    potential_corners = []
    zero_profit_solution = None

    # Check x=0.5 corner
    if foc_at_05 is not None and foc_at_05 >= 0:
        try:
            foc_at_just_below_05 = first_order_condition(0.499)
            if foc_at_just_below_05 >= 0:
                profit_at_05 = profit(0.5)
                potential_corners.append((0.5, profit_at_05, 'corner'))
                if profit_at_05 < 0:
                    zero_profit_solution = find_zero_profit_solution(n, K_R=K_R)
        except:
            if foc_at_05 > 1e-6:
                profit_at_05 = profit(0.5)
                potential_corners.append((0.5, profit_at_05, 'corner'))
                if profit_at_05 < 0:
                    zero_profit_solution = find_zero_profit_solution(n, K_R=K_R)

    # Check interior
    test_x = np.linspace(0.001, 0.49, 50)
    foc_samples = []
    for x in test_x:
        try:
            foc_samples.append(first_order_condition(x))
        except:
            foc_samples.append(np.nan)

    foc_samples_clean = [f for f in foc_samples if not np.isnan(f)]
    if len(foc_samples_clean) > 0:
        min_foc = min(foc_samples_clean)
        if min_foc > 0:
            profit_at_05 = profit(0.5)
            if not any(abs(x - 0.5) < 1e-6 for x, _, _ in potential_corners):
                potential_corners.append((0.5, profit_at_05, 'corner'))
                if profit_at_05 < 0:
                    zero_profit_solution = find_zero_profit_solution(n, K_R=K_R)

    # Find interior roots (where FOC = 0)
    roots = []
    if find_all_roots:
        x_fine = np.linspace(0.001, 0.499, 1000)
        foc_fine = []
        for x in x_fine:
            try:
                foc_val = first_order_condition(x)
                foc_fine.append(foc_val)
            except:
                foc_fine.append(np.nan)

        # Find sign changes
        for i in range(len(foc_fine) - 1):
            if not (np.isnan(foc_fine[i]) or np.isnan(foc_fine[i+1])):
                if foc_fine[i] * foc_fine[i+1] < 0:
                    try:
                        bracket = [x_fine[i], x_fine[i+1]]
                        sol = root_scalar(first_order_condition, bracket=bracket, method='brentq',
                                         xtol=1e-10, rtol=1e-10)
                        if sol.converged:
                            x_root = sol.root
                            profit_at_root = profit(x_root)
                            profit_left = profit(max(0.001, x_root - 0.01))
                            profit_right = profit(min(0.499, x_root + 0.01))
                            if profit_at_root >= profit_left and profit_at_root >= profit_right:
                                roots.append(x_root)
                            elif is_maximum(n, x_root, K_R=K_R):
                                roots.append(x_root)
                    except (ValueError, RuntimeError) as e:
                        continue

        # Remove duplicates
        unique_roots = []
        for r in sorted(roots):
            if not unique_roots or abs(r - unique_roots[-1]) > 0.01:
                unique_roots.append(r)
        roots = unique_roots

    # Build list of all equilibria
    equilibria_list = []

    # Add interior roots
    for r in roots:
        profit_at_r = profit(r)
        foc_at_r = first_order_condition(r)
        if abs(foc_at_r) < 0.1:
            equilibria_list.append((r, profit_at_r, 'interior'))

    # Add potential corner solutions
    for corner_x, corner_profit, corner_type in potential_corners:
        if not any(abs(x - corner_x) < 1e-6 for x, _, _ in equilibria_list):
            equilibria_list.append((corner_x, corner_profit, corner_type))

    # Sort by x value
    equilibria_list.sort(key=lambda x: x[0])

    # Return equilibria and zero_profit_solution
    result_equilibria = None
    if len(equilibria_list) == 0:
        result_equilibria = None
    elif len(equilibria_list) == 1:
        result_equilibria = equilibria_list[0][0]
    else:
        result_equilibria = equilibria_list

    return result_equilibria, zero_profit_solution

# Print the profit function for n=1
print_profit_function_n1(R=R)

# Print the FOC of benefits for n=1
print_foc_benefits_n1(R=R)

# Initialize equilibria dictionary
equilibria = {}
zero_profit_solutions = {}

# Plot First Order Conditions
x_vals = np.linspace(0.001, 0.5, 1000)
colors = ['blue', 'orange', 'green', 'red']

# For each n, compute and plot derivatives
for idx, n in enumerate(n_list):
    K_R_n = compute_K_R(n, R)
    
    def benefit_derivative_func(x):
        return benefit_foc_explicit(n, x, x, K_R=K_R_n, PG=PG, PB=PB)

    def cost_derivative_func(x):
        return a

    benefit_derivative_vals = [benefit_derivative_func(x) for x in x_vals]
    cost_derivative_vals = [cost_derivative_func(x) for x in x_vals]

    plt.plot(x_vals, benefit_derivative_vals, label=f"Benefits, n={n} (K_R={K_R_n})",
             color=colors[idx], linestyle='-', linewidth=2)
    plt.plot(x_vals, cost_derivative_vals, label=f"Costs, n={n}",
             color=colors[idx], linestyle='--', linewidth=2)

plt.xlabel("Effort x")
plt.ylabel("Derivative")
plt.title(f"FOC: Benefits (solid) vs Cost (dashed) - Model (R={R}, {R*100:.1f}% threshold)")
plt.legend()
plt.ylim(0, 3)
plt.grid(True)
plt.axhline(y=0, color='black', linestyle=':', linewidth=0.5)
plt.show()

# Find equilibrium x* where FOC = 0
print("\nFinding equilibrium x* where FOC = 0 (derivatives cross):")
print("=" * 60)
for n in n_list:
    K_R_n = compute_K_R(n, R)
    eq, zero_prof = compute_equilibrium(n, K_R=K_R_n, find_all_roots=True)
    equilibria[n] = eq
    zero_profit_solutions[n] = zero_prof
    
    if eq is not None:
        if isinstance(eq, list) and len(eq) > 0 and isinstance(eq[0], tuple):
            print(f"\nFor n={n}, R={R} ({R*100:.1f}%), K_R={K_R_n}: Found {len(eq)} equilibrium(ia):")
            print("-" * 60)
            print(f"{'Equilibrium':<15} {'x*':<15} {'Profit':<15} {'Type':<15}")
            print("-" * 60)
            for i, (x_star, profit_at_eq, eq_type) in enumerate(eq):
                eq_label = f"x*{i+1}" if len(eq) > 1 else "x*"
                type_label = "corner" if eq_type == 'corner' else "interior"
                print(f"{eq_label:<15} {x_star:<15.6f} {profit_at_eq:<15.6f} {type_label:<15}")
            if zero_prof is not None:
                z_x, z_profit = zero_prof
                print(f"{'x* (zero profit)':<15} {z_x:<15.6f} {z_profit:<15.6f} {'zero profit':<15}")
            print("-" * 60)
        elif isinstance(eq, (int, float)):
            x_star = eq
            profit_at_eq = benefit_i(n, x_star, x_star, K_R=K_R_n, PG=PG, PB=PB) - cost(x_star)
            eq_type = 'corner' if (abs(x_star - 0.5) < 1e-6) else 'interior'
            print(f"\nFor n={n}, R={R} ({R*100:.1f}%), K_R={K_R_n}: Found 1 equilibrium:")
            print("-" * 60)
            print(f"{'Equilibrium':<15} {'x*':<15} {'Profit':<15} {'Type':<15}")
            print("-" * 60)
            print(f"{'x*':<15} {x_star:<15.6f} {profit_at_eq:<15.6f} {eq_type:<15}")
            if zero_prof is not None:
                z_x, z_profit = zero_prof
                print(f"{'x* (zero profit)':<15} {z_x:<15.6f} {z_profit:<15.6f} {'zero profit':<15}")
            print("-" * 60)
    else:
        print(f"For n={n}, R={R} ({R*100:.1f}%), K_R={K_R_n}: No equilibrium found")
    print()

# Plot profits for each voter when efforts are symmetric
plt.figure(figsize=(8,6))
for idx, n in enumerate(n_list):
    K_R_n = compute_K_R(n, R)
    x_vals_plot = np.linspace(0.001, 0.5, 1000)
    benefits = [benefit_i(n, x, x, K_R=K_R_n, PG=PG, PB=PB) for x in x_vals_plot]
    costs = [cost(x) for x in x_vals_plot]
    profits = [b - c for b, c in zip(benefits, costs)]
    plt.plot(x_vals_plot, profits, label=f"Profit (n={n}, K_R={K_R_n})", color=colors[idx])

    # Mark equilibrium(ia) from computed values
    if n not in equilibria:
        eq, zero_prof = compute_equilibrium(n, K_R=K_R_n, find_all_roots=True)
        equilibria[n] = eq
        zero_profit_solutions[n] = zero_prof

    if n in equilibria and equilibria[n] is not None:
        eq_result = equilibria[n]
        x_stars = []
        if isinstance(eq_result, list) and len(eq_result) > 0 and isinstance(eq_result[0], tuple):
            x_stars = [(x, profit, eq_type) for x, profit, eq_type in eq_result]
        elif isinstance(eq_result, (int, float)):
            profit_at_eq = benefit_i(n, eq_result, eq_result, K_R=K_R_n, PG=PG, PB=PB) - cost(eq_result)
            eq_type = 'corner' if (abs(eq_result - 0.5) < 1e-6) else 'interior'
            x_stars = [(eq_result, profit_at_eq, eq_type)]

        for x_star, profit_at_eq, eq_type in x_stars:
            plt.plot(x_star, profit_at_eq, 'o', color=colors[idx], markersize=10)
            plt.axvline(x=x_star, color=colors[idx], linestyle=':', linewidth=1.5, alpha=0.7)
            label = f'  x*={x_star:.4f}'
            if abs(x_star - 0.5) < 1e-6:
                label += '\n(corner)'
            else:
                label += '\n(max)'
            plt.text(x_star, profit_at_eq, label,
                    color=colors[idx], fontsize=9, verticalalignment='bottom')

        if n in zero_profit_solutions and zero_profit_solutions[n] is not None:
            z_x, z_profit = zero_profit_solutions[n]
            plt.plot(z_x, z_profit, 's', color=colors[idx], markersize=10, markerfacecolor='none', markeredgewidth=2)
            plt.axvline(x=z_x, color=colors[idx], linestyle='--', linewidth=1.5, alpha=0.7)
            plt.text(z_x, z_profit, f'  x*={z_x:.4f}\n(zero profit)',
                    color=colors[idx], fontsize=9, verticalalignment='bottom')

plt.xlabel("Effort x")
plt.ylabel("Profit")
plt.title(f"Profit (Benefits - Costs) as a function of effort x - Model (R={R}, {R*100:.1f}% threshold)\n(Equilibria marked)")
plt.legend()
plt.grid(True)
plt.show()

# Plot components for each n and k
print("\n" + "=" * 60)
print("Plotting components (fraction, binomial term, payoff term) for each n and k")
print("Using ACTUAL equilibrium values")
print(f"R = {R} ({R*100:.1f}% threshold)")
print("=" * 60)

fig, axes = plt.subplots(len(n_list), 1, figsize=(12, 5*len(n_list)))
if len(n_list) == 1:
    axes = [axes]

for idx, n in enumerate(n_list):
    K_R_n = compute_K_R(n, R)
    x_used = None

    if n not in equilibria:
        eq, zero_prof = compute_equilibrium(n, K_R=K_R_n, find_all_roots=True)
        equilibria[n] = eq
        zero_profit_solutions[n] = zero_prof

    if n in equilibria and equilibria[n] is not None:
        eq_result = equilibria[n]
        if isinstance(eq_result, list) and len(eq_result) > 0 and isinstance(eq_result[0], tuple):
            best_eq = max(eq_result, key=lambda x: x[1])
            x_used = best_eq[0]
        elif isinstance(eq_result, (int, float)):
            x_used = eq_result

    if x_used is None:
        try:
            def first_order_condition(x):
                f = lambda x_i: benefit_i(n, x_i, x, K_R=K_R_n, PG=PG, PB=PB)
                dfdx = nd.Derivative(f, n=1, method='central', order=4)
                benefit_deriv = to_scalar(dfdx(x))
                cost_derivative = nd.Derivative(cost, n=1, method='central', order=4)
                cost_deriv = to_scalar(cost_derivative(x))
                return benefit_deriv - cost_deriv

            sol = root_scalar(first_order_condition, bracket=[0.001, 0.5], method='brentq')
            if sol.converged and is_maximum(n, sol.root, K_R=K_R_n):
                x_used = sol.root
        except:
            pass

    if x_used is None:
        x_used = 0.1

    print(f"n={n}, K_R={K_R_n}: Using x* = {x_used:.6f} for component plots")

    # Get k values for acceptance and rejection ranges
    k_values_accept = list(range(max(0, K_R_n - 1), 2*n+1))
    k_values_reject = list(range(max(0, 2*n+1-K_R_n), 2*n+1))
    # Combine and sort, removing duplicates
    k_values_all = sorted(set(k_values_accept + k_values_reject))

    # Compute components for each k
    fractions = []
    binomial_terms_1 = []
    binomial_terms_2 = []
    payoff_terms_G_pi_accept = []
    payoff_terms_G_1pi_reject = []
    payoff_terms_B_pi_reject = []
    payoff_terms_B_1pi_accept = []

    for k in k_values_all:
        (frac, bin_term_1, bin_term_2) = compute_payoff_components(n, k, x_used, x_used, K_R_n, PG, PB)

        fractions.append(frac)
        binomial_terms_1.append(bin_term_1)
        binomial_terms_2.append(bin_term_2)

        # P(G) components
        if k in k_values_accept:
            payoff_terms_G_pi_accept.append(bin_term_1 * frac)
        else:
            payoff_terms_G_pi_accept.append(0)

        if k in k_values_reject:
            payoff_terms_G_1pi_reject.append(bin_term_2 * frac)
        else:
            payoff_terms_G_1pi_reject.append(0)

        # P(B) components
        if k in k_values_reject:
            payoff_terms_B_pi_reject.append(bin_term_1 * frac)
        else:
            payoff_terms_B_pi_reject.append(0)

        if k in k_values_accept:
            payoff_terms_B_1pi_accept.append(bin_term_2 * frac)
        else:
            payoff_terms_B_1pi_accept.append(0)

    # Create bar plot
    x_pos = np.arange(len(k_values_all))
    width = 0.12

    axes[idx].bar(x_pos - 3*width, fractions, width, label='Fraction', alpha=0.8)
    axes[idx].bar(x_pos - 2*width, binomial_terms_1, width, label='Binomial term 1', alpha=0.8)
    axes[idx].bar(x_pos - width, binomial_terms_2, width, label='Binomial term 2', alpha=0.8)
    axes[idx].bar(x_pos, payoff_terms_G_pi_accept, width, label='P(G)*p_i*accept', alpha=0.8, color='green')
    axes[idx].bar(x_pos + width, payoff_terms_G_1pi_reject, width, label='P(G)*(1-p_i)*reject', alpha=0.8, color='lightgreen')
    axes[idx].bar(x_pos + 2*width, payoff_terms_B_pi_reject, width, label='P(B)*p_i*reject', alpha=0.8, color='orange')
    axes[idx].bar(x_pos + 3*width, payoff_terms_B_1pi_accept, width, label='P(B)*(1-p_i)*accept', alpha=0.8, color='darkorange')

    axes[idx].set_xlabel('k (number of correct votes)')
    axes[idx].set_ylabel('Value')
    corner_note = " (corner)" if (abs(x_used - 0.5) < 1e-6) else ""
    axes[idx].set_title(f'n = {n}, R = {R} ({R*100:.1f}%), K_R = {K_R_n} (x_i = x_j = {x_used:.4f}{corner_note}, accept: k≥K_R-1, reject: k≥2n+1-K_R)')
    axes[idx].set_xticks(x_pos)
    axes[idx].set_xticklabels([f'k={k}' for k in k_values_all])
    axes[idx].legend()
    axes[idx].grid(True, alpha=0.3, axis='y')

    # Add vertical lines to separate acceptance and rejection ranges
    if len(k_values_accept) > 0 and len(k_values_reject) > 0:
        accept_start = k_values_all.index(k_values_accept[0]) if k_values_accept[0] in k_values_all else 0
        reject_start = k_values_all.index(k_values_reject[0]) if k_values_reject[0] in k_values_all else 0
        if accept_start > 0:
            axes[idx].axvline(x=accept_start-0.5, color='blue', linestyle='--', linewidth=1, alpha=0.5)
            axes[idx].text(accept_start-0.5, axes[idx].get_ylim()[1]*0.9, 'Accept\nboundary',
                           ha='center', fontsize=8, rotation=90, verticalalignment='top')
        if reject_start > 0 and reject_start != accept_start:
            axes[idx].axvline(x=reject_start-0.5, color='red', linestyle='--', linewidth=1, alpha=0.5)
            axes[idx].text(reject_start-0.5, axes[idx].get_ylim()[1]*0.8, 'Reject\nboundary',
                           ha='center', fontsize=8, rotation=90, verticalalignment='top')

plt.tight_layout()
plt.show()
