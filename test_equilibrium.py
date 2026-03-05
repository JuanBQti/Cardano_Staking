# Test script to check equilibrium with a=1, b=0, n=1
import math
import numpy as np
from scipy.optimize import root_scalar
import numdifftools as nd

# Parameters for test
B = 1
a = 1
b = 0
n = 1
PG = 0.5
PB = 1 - PG
mu = 1

# Cost function
def cost(x):
    return a * x

# Probability function depending on effort
def p(x):
    return 0.5 + x

# Helper function to compute components for a given k
def compute_payoff_components(n, k, x_i, x_j, b=b, K_R=None, PG=PG, PB=PB, mu=mu):
    if K_R is None:
        K_R = math.ceil(0.5 * (2*n + 1))

    p_j = p(x_j)
    comb = math.comb(2*n, k)

    if k >= n:
        fraction = x_i * B / (x_i + k * x_j) if (x_i + k * x_j) > 0 else 0
    else:
        fraction = 0

    binomial_term_1 = comb * (p_j ** k) * ((1 - p_j) ** (2*n - k))
    binomial_term_2 = comb * (p_j ** (2*n - k)) * ((1 - p_j) ** k)

    if k >= n:
        payoff_term_1 = binomial_term_1 * fraction
        payoff_term_2 = binomial_term_2 * fraction
        penalty_term_1 = 0
        penalty_term_2 = 0
    else:
        payoff_term_1 = 0
        payoff_term_2 = 0
        penalty_term_1 = binomial_term_1 * b
        penalty_term_2 = binomial_term_2 * b

    return (fraction,
            binomial_term_1, binomial_term_2,
            payoff_term_1, payoff_term_2,
            penalty_term_1, penalty_term_2)

# Define benefit function
def benefit_i(n, x_i, x_j, b=b, k_range_winning=None, k_range_losing=None, K_R=None, PG=PG, PB=PB):
    if k_range_winning is None:
        k_range_winning = range(n, 2*n+1)
    
    if k_range_losing is None:
        k_range_losing = range(0, n)

    p_i = p(x_i)
    p_j = p(x_j)

    total_sum_1_winning = 0
    total_sum_2_winning = 0
    total_sum_1_losing = 0
    total_sum_2_losing = 0

    for k in k_range_winning:
        (_, _, _, payoff_term_1, payoff_term_2, _, _) = compute_payoff_components(n, k, x_i, x_j, b, K_R, PG, PB, mu)
        total_sum_1_winning += payoff_term_1
        total_sum_2_winning += payoff_term_2

    for k in k_range_losing:
        (_, _, _, _, _, penalty_term_1, penalty_term_2) = compute_payoff_components(n, k, x_i, x_j, b, K_R, PG, PB, mu)
        total_sum_1_losing += penalty_term_1
        total_sum_2_losing += penalty_term_2

    result = p_i * (total_sum_1_winning - total_sum_1_losing) + (1 - p_i) * (total_sum_2_winning - total_sum_2_losing)
    return result

# Helper function to convert derivative result to scalar
def to_scalar(value):
    if hasattr(value, 'item'):
        return float(value.item())
    elif hasattr(value, '__iter__') and not isinstance(value, str):
        return float(value[0]) if len(value) > 0 else float(value)
    else:
        return float(value)

# Helper function to check if a root is a maximum
def is_maximum(n, x_star, b=b, k_range_winning=None, k_range_losing=None, K_R=None):
    def profit(x_i):
        return benefit_i(n, x_i, x_star, b=b, k_range_winning=k_range_winning, 
                         k_range_losing=k_range_losing, K_R=K_R, PG=PG, PB=PB) - cost(x_i)
    d2f = nd.Derivative(profit, n=2)
    second_deriv = to_scalar(d2f(x_star))
    return second_deriv < 0

# Compute equilibrium
def compute_equilibrium(n, b=b, k_range_winning=None, k_range_losing=None, K_R=None, find_all_roots=True):
    def first_order_condition(x):
        f = lambda x_i: benefit_i(n, x_i, x, b=b, k_range_winning=k_range_winning, 
                                 k_range_losing=k_range_losing, K_R=K_R, PG=PG, PB=PB)
        dfdx = nd.Derivative(f, n=1, method='central', order=4)
        benefit_deriv = to_scalar(dfdx(x))
        cost_derivative = nd.Derivative(cost, n=1, method='central', order=4)
        cost_deriv = to_scalar(cost_derivative(x))
        return benefit_deriv - cost_deriv

    def profit(x):
        return benefit_i(n, x, x, b=b, k_range_winning=k_range_winning, 
                        k_range_losing=k_range_losing, K_R=K_R, PG=PG, PB=PB) - cost(x)

    # Find roots (interior solutions) FIRST
    roots = []

    if find_all_roots:
        x_fine = np.linspace(0.001, 0.499, 500)
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
                            if is_maximum(n, sol.root, b=b, k_range_winning=k_range_winning, 
                                        k_range_losing=k_range_losing, K_R=K_R):
                                roots.append(sol.root)
                    except (ValueError, RuntimeError) as e:
                        continue
        
        # Also check for points where FOC is very close to zero
        for i, foc_val in enumerate(foc_fine):
            if not np.isnan(foc_val) and abs(foc_val) < 0.001:
                x_candidate = x_fine[i]
                if is_maximum(n, x_candidate, b=b, k_range_winning=k_range_winning, 
                            k_range_losing=k_range_losing, K_R=K_R):
                    roots.append(x_candidate)

        # Remove duplicates
        unique_roots = []
        for r in sorted(roots):
            if not unique_roots or abs(r - unique_roots[-1]) > 0.001:
                unique_roots.append(r)
        roots = unique_roots

    # Check corner solutions
    profit_at_0 = profit(0.0)
    profit_at_05 = profit(0.5)
    
    best_interior_profit = max([profit(r) for r in roots]) if len(roots) > 0 else None
    
    profit_at_01 = profit(0.01)
    is_corner_at_0 = False
    if best_interior_profit is None:
        is_corner_at_0 = (profit_at_0 >= profit_at_01) and (profit_at_0 > profit(0.001))
    else:
        is_corner_at_0 = (profit_at_0 > best_interior_profit) and (profit_at_0 > profit_at_01)
    
    profit_at_049 = profit(0.49)
    is_corner_at_05 = False
    if best_interior_profit is None:
        is_corner_at_05 = (profit_at_05 >= profit_at_049) and (profit_at_05 > profit(0.499))
    else:
        is_corner_at_05 = (profit_at_05 > best_interior_profit) and (profit_at_05 > profit_at_049)

    # Compare all candidates
    candidates = []
    if is_corner_at_0:
        candidates.append((0.0, profit_at_0, 'corner'))
    if is_corner_at_05:
        candidates.append((0.5, profit_at_05, 'corner'))
    for r in roots:
        candidates.append((r, profit(r), 'interior'))

    if len(candidates) == 0:
        # Fallback: direct search for maximum profit
        test_x = np.linspace(0.001, 0.499, 1000)
        test_profits = [profit(x) for x in test_x]
        max_idx = np.argmax(test_profits)
        best_x = test_x[max_idx]
        try:
            foc_at_best = first_order_condition(best_x)
            if abs(foc_at_best) < 0.01:
                return best_x
        except:
            pass
        return best_x

    # Return the candidate with highest profit
    max_profit = max(c[1] for c in candidates)
    best_candidates = [c[0] for c in candidates if abs(c[1] - max_profit) < 1e-6]

    if len(best_candidates) == 1:
        return best_candidates[0]
    else:
        return sorted(best_candidates)

# Test
print(f"Testing with n={n}, a={a}, b={b}")
print("=" * 60)

eq = compute_equilibrium(n, b=b, k_range_winning=None, k_range_losing=None, K_R=None, find_all_roots=True)

if eq is not None:
    if isinstance(eq, (list, tuple)):
        print(f"Multiple equilibria found:")
        for i, x_star in enumerate(eq):
            profit_at_eq = benefit_i(n, x_star, x_star, b=b) - cost(x_star)
            print(f"  x*{i+1} = {x_star:.6f}, profit = {profit_at_eq:.6f}")
    else:
        x_star = eq
        profit_at_eq = benefit_i(n, x_star, x_star, b=b) - cost(x_star)
        print(f"Equilibrium found: x* = {x_star:.6f}, profit = {profit_at_eq:.6f}")
        print(f"Expected: x* ≈ 0.22")
        print(f"Difference: {abs(x_star - 0.22):.6f}")
else:
    print("No equilibrium found")

# Also check FOC at x=0.22
print("\nChecking FOC at x=0.22:")
def first_order_condition(x):
    f = lambda x_i: benefit_i(n, x_i, x, b=b)
    dfdx = nd.Derivative(f, n=1, method='central', order=4)
    benefit_deriv = to_scalar(dfdx(x))
    cost_derivative = nd.Derivative(cost, n=1, method='central', order=4)
    cost_deriv = to_scalar(cost_derivative(x))
    return benefit_deriv - cost_deriv

foc_at_022 = first_order_condition(0.22)
print(f"FOC(0.22) = {foc_at_022:.6f}")

# Check profit at different points
print("\nProfit at different points:")
for x_test in [0.1, 0.2, 0.22, 0.25, 0.3]:
    profit_val = benefit_i(n, x_test, x_test, b=b) - cost(x_test)
    foc_val = first_order_condition(x_test)
    print(f"x={x_test:.2f}: profit={profit_val:.6f}, FOC={foc_val:.6f}")

