import math
import numpy as np
import matplotlib.pyplot as plt

# Parameters
B = 1                               # budget to distribute among those voters of the winning election
a = 1                               # cost coefficient
b_list = [0, 1/10, 1/3]             # fixed penalty paid when on the losing side (k < n)
n = 1                                # number of voters
PG = 0.5                            # probability Good state/quality
PB = 1 - PG                          # probability Bad state/quality
mu = 1                               # factor to reduce the Budget used to pay those in the minority group

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
        K_R = compute_K_R(n, 0.5)  # Default: 50% threshold = n+1
    p_j = p(x_j)
    comb = math.comb(2*n, k)
    
    # Payoff fraction (expected value E[f_i | i∈W, |W\{i}|=k])
    # Only computed if k >= n (winning side)
    if k >= n:
        fraction = x_i * B / (x_i + k * x_j) if (x_i + k * x_j) > 0 else 0
    else:
        fraction = 0

    # Binomial probability terms
    binomial_term_1 = comb * (p_j ** k) * ((1 - p_j) ** (2*n - k))
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

# Helper function to compute K_R
def compute_K_R(n, R):
    """Compute K_R = ceil(R * (2n+1)) where R ∈ [0.5, 1]"""
    return math.ceil(R * (2*n + 1))

# Helper function to compute the FOC of benefits with respect to x_i explicitly
def benefit_foc_explicit(n, x_i, x_j, b, k_range_winning=None, k_range_losing=None, K_R=None, PG=PG, PB=PB):
    """
    Explicitly compute ∂benefit_i/∂x_i accounting for:
    1. The derivative of p_i (which is 1)
    2. The derivative of the fraction terms
    """
    if k_range_winning is None:
        k_range_winning = range(n, 2*n+1)
    if k_range_losing is None:
        k_range_losing = range(0, n)

    p_i = p(x_i)
    p_j = p(x_j)

    # Compute the sums (without p_i multiplier)
    sum_1_winning = 0  # Σ binom * p_j^k * (1-p_j)^(2n-k) * fraction
    sum_2_winning = 0  # Σ binom * p_j^(2n-k) * (1-p_j)^k * fraction
    sum_1_losing = 0   # Σ binom * p_j^k * (1-p_j)^(2n-k) * b
    sum_2_losing = 0   # Σ binom * p_j^(2n-k) * (1-p_j)^k * b

    # Compute derivatives of sums with respect to x_i
    d_sum_1_winning_dx = 0  # Σ binom * p_j^k * (1-p_j)^(2n-k) * ∂(fraction)/∂x_i
    d_sum_2_winning_dx = 0  # Σ binom * p_j^(2n-k) * (1-p_j)^k * ∂(fraction)/∂x_i
    d_sum_1_losing_dx = 0   # = 0 (penalty terms don't depend on x_i when x_i = x_j)
    d_sum_2_losing_dx = 0   # = 0 (penalty terms don't depend on x_i when x_i = x_j)

    # Compute winning side contributions
    for k in k_range_winning:
        comb = math.comb(2*n, k)
        binomial_term_1 = comb * (p_j ** k) * ((1 - p_j) ** (2*n - k))
        binomial_term_2 = comb * (p_j ** (2*n - k)) * ((1 - p_j) ** k)

        # Fraction: x_i / (x_i + k*x_j)
        if (x_i + k * x_j) > 0:
            fraction = x_i * B / (x_i + k * x_j)
            # Derivative of fraction with respect to x_i:
            # ∂(x_i / (x_i + k*x_j))/∂x_i = k*x_j / (x_i + k*x_j)^2
            dfraction_dx = (k * x_j * B) / ((x_i + k * x_j) ** 2)
        else:
            fraction = 0
            dfraction_dx = 0

        sum_1_winning += binomial_term_1 * fraction
        sum_2_winning += binomial_term_2 * fraction
        d_sum_1_winning_dx += binomial_term_1 * dfraction_dx
        d_sum_2_winning_dx += binomial_term_2 * dfraction_dx

    # Compute losing side contributions (penalties)
    for k in k_range_losing:
        comb = math.comb(2*n, k)
        binomial_term_1 = comb * (p_j ** k) * ((1 - p_j) ** (2*n - k))
        binomial_term_2 = comb * (p_j ** (2*n - k)) * ((1 - p_j) ** k)

        sum_1_losing += binomial_term_1 * b
        sum_2_losing += binomial_term_2 * b
        # Penalty terms don't depend on x_i (only on p_j = 0.5 + x_j)
        # So their derivatives with respect to x_i are 0 when x_i = x_j

    # Compute the full derivative
    # ∂benefit_i/∂x_i = (sum_1_winning - sum_1_losing) + p_i * d_sum_1_winning_dx
    #                   - (sum_2_winning - sum_2_losing) + (1-p_i) * d_sum_2_winning_dx
    result = (sum_1_winning - sum_1_losing) + p_i * d_sum_1_winning_dx \
             - (sum_2_winning - sum_2_losing) + (1 - p_i) * d_sum_2_winning_dx

    return result

# Plot First Order Conditions
x_vals = np.linspace(0.001, 0.5, 1000)
colors = ['blue', 'orange', 'green']

plt.figure(figsize=(8, 5))

# Plot marginal cost once (it's constant and doesn't depend on b)
cost_derivative_vals = [a] * len(x_vals)
plt.plot(x_vals, cost_derivative_vals, label="Marginal Cost (a=1)", linestyle="--")

# For each b, compute and plot marginal revenue
for idx, b in enumerate(b_list):
    # Compute derivative of benefits with respect to x_i, evaluated at x_i = x_j = x
    def benefit_derivative_func(x):
        return benefit_foc_explicit(n, x, x, b=b, k_range_winning=None, k_range_losing=None, K_R=None, PG=PG, PB=PB)

    # Compute derivatives for all x values
    benefit_derivative_vals = [benefit_derivative_func(x) for x in x_vals]

    # Plot marginal revenue
    plt.plot(x_vals, benefit_derivative_vals, label=f"Marginal Revenue, b={b}")

plt.xlabel("x")
plt.ylabel("FOCs")
plt.ylim(0, 2)
plt.legend()
plt.grid(True)
plt.show()

