# Import necessary libraries
import math
import numpy as np
import numdifftools as nd
import matplotlib.pyplot as plt

# Model parameters
B = 1                               # budget to distribute among those voters of the winning election
a = 1                               # cost coefficient
b_list = [0, 1/10]                  # list of penalty values to plot
n_list = [1, 3]                     # list of n values to plot
PG = 0.5                            # probability Good state/quality
PB = 1 - PG                         # probability Bad state/quality
mu = 1                              # factor to reduce the Budget used to pay those in the minority group

# Cost function
def cost(x):
    return a * x

# Probability function depending on effort
def p(x):
    return 0.5 + x

# Helper function to compute components for a given k
def compute_payoff_components(n, k, x_i, x_j, b, K_R=None, PG=PG, PB=PB, mu=mu):
    """Compute fraction, binomial terms, payoff terms, and penalty terms for given n, k, x_i, x_j"""
    if K_R is None:
        K_R = math.ceil(0.5 * (2*n + 1))  # Default: 50% threshold = n+1

    p_j = p(x_j)
    comb = math.comb(2*n, k)

    # Payoff fraction (only computed if k >= n)
    if k >= n:
        fraction = x_i * B / (x_i + k * x_j) if (x_i + k * x_j) > 0 else 0
    else:
        fraction = 0

    # Binomial probability terms
    binomial_term_1 = comb * (p_j ** k) * ((1 - p_j) ** (2*n - k))
    binomial_term_2 = comb * (p_j ** (2*n - k)) * ((1 - p_j) ** k)

    # Payoff terms (only computed if k >= n)
    if k >= n:
        payoff_term_1 = binomial_term_1 * fraction
        payoff_term_2 = binomial_term_2 * fraction
        penalty_term_1 = 0
        penalty_term_2 = 0
    else:
        # Penalty terms (only computed if k < n)
        payoff_term_1 = 0
        payoff_term_2 = 0
        penalty_term_1 = binomial_term_1 * b
        penalty_term_2 = binomial_term_2 * b

    return (fraction,
            binomial_term_1, binomial_term_2,
            payoff_term_1, payoff_term_2,
            penalty_term_1, penalty_term_2)

# Define benefit function
def benefit_i(n, x_i, x_j, b, k_range_winning=None, k_range_losing=None, K_R=None, PG=PG, PB=PB):
    """Benefit function with penalty"""
    if k_range_winning is None:
        k_range_winning = range(n, 2*n+1)
    
    if k_range_losing is None:
        k_range_losing = range(0, n)

    p_i = p(x_i)
    p_j = p(x_j)

    # Sums for winning side (k >= n): rewards
    total_sum_1_winning = 0
    total_sum_2_winning = 0

    # Sums for losing side (k < n): penalties
    total_sum_1_losing = 0
    total_sum_2_losing = 0

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

    # Final formula: benefit (without cost)
    result = p_i * (total_sum_1_winning - total_sum_1_losing) + (1 - p_i) * (total_sum_2_winning - total_sum_2_losing)

    return result

# Helper function to convert derivative result to scalar
def to_scalar(value):
    """Convert numpy array or array-like to scalar float"""
    if hasattr(value, 'item'):
        return float(value.item())
    elif hasattr(value, '__iter__') and not isinstance(value, str):
        return float(value[0]) if len(value) > 0 else float(value)
    else:
        return float(value)

# Plot marginal revenues and marginal costs
x_vals = np.linspace(0.01, 0.5, 1000)
colors = ['blue', 'orange', 'green', 'red']

# Create a single plot with all curves
plt.figure(figsize=(10, 6))

# Plot for each combination of n and b
for n in n_list:
    for b in b_list:
        # Compute derivative of benefits with respect to x_i (marginal revenue)
        def benefit_derivative_func(x):
            f = lambda x_i: benefit_i(n, x_i, x, b=b, k_range_winning=None, k_range_losing=None, K_R=None, PG=PG, PB=PB)
            dfdx = nd.Derivative(f, n=1, method='central', order=4)
            return to_scalar(dfdx(x))

        # Derivative of cost with respect to x_i (marginal cost)
        def cost_derivative_func(x):
            cost_derivative = nd.Derivative(cost, n=1, method='central', order=4)
            return to_scalar(cost_derivative(x))

        # Compute derivatives for all x values
        benefit_derivative_vals = [benefit_derivative_func(x) for x in x_vals]
        cost_derivative_vals = [cost_derivative_func(x) for x in x_vals]

        # Color scheme: n=1 uses blue, n=3 uses orange
        if n == 1:
            color = 'blue'
        else:  # n == 3
            color = colors[1]  # orange
        
        # Line style: b=0 uses solid, b=0.1 uses dashed
        linestyle = '-' if b == 0 else '--'

        # Plot marginal revenue (benefits)
        plt.plot(x_vals, benefit_derivative_vals, label=f"Benefits, n={n}, b={b}",
                 color=color, linestyle=linestyle, linewidth=2)
        
        # Plot marginal cost
        plt.plot(x_vals, cost_derivative_vals, label=f"Costs, n={n}, b={b}",
                 color=color, linestyle='--', linewidth=2)

plt.xlabel("Effort x")
plt.ylabel("Derivative")
plt.title(f"FOC: Benefits (solid) vs Cost (dashed) - Penalty Model")
plt.legend()
plt.grid(True)
plt.axhline(y=0, color='black', linestyle=':', linewidth=0.5)
plt.show()

