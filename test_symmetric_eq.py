# Test symmetric equilibrium with better root finding
import math
import numpy as np
from scipy.optimize import root_scalar
import numdifftools as nd

# Parameters
B = 1
a = 1
b = 0
n = 1
PG = 0.5
PB = 1 - PG
mu = 1

def cost(x):
    return a * x

def p(x):
    return 0.5 + x

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
    return (fraction, binomial_term_1, binomial_term_2,
            payoff_term_1, payoff_term_2, penalty_term_1, penalty_term_2)

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

def profit(x):
    """Profit at symmetric equilibrium: x_i = x_j = x"""
    return benefit_i(n, x, x, b=b) - cost(x)

def to_scalar(value):
    if hasattr(value, 'item'):
        return float(value.item())
    elif hasattr(value, '__iter__') and not isinstance(value, str):
        return float(value[0]) if len(value) > 0 else float(value)
    else:
        return float(value)

# First-order condition: ∂π/∂x_i evaluated at x_i = x_j = x
def first_order_condition(x):
    """FOC for symmetric equilibrium: ∂benefit_i/∂x_i - ∂cost/∂x_i = 0 at x_i = x_j = x"""
    # Compute ∂benefit_i/∂x_i at (x_i=x, x_j=x)
    # Note: In symmetric equilibrium, we need to account for the fact that x_j also depends on x
    # But since we're computing ∂benefit_i/∂x_i keeping x_j fixed, then evaluating at x_i=x_j=x,
    # this should be correct for the symmetric equilibrium FOC
    f = lambda x_i: benefit_i(n, x_i, x, b=b)
    dfdx = nd.Derivative(f, n=1, method='central', order=4)
    benefit_deriv = to_scalar(dfdx(x))
    
    # Compute ∂cost/∂x_i
    cost_derivative = nd.Derivative(cost, n=1, method='central', order=4)
    cost_deriv = to_scalar(cost_derivative(x))
    
    return benefit_deriv - cost_deriv

print("Testing symmetric equilibrium with n=1, a=1, b=0")
print("=" * 60)

# Check FOC around x=0.22
print("\nFOC values around x=0.22:")
x_test_range = np.linspace(0.15, 0.25, 21)
for x_test in x_test_range:
    foc_val = first_order_condition(x_test)
    profit_val = profit(x_test)
    print(f"x={x_test:.4f}: FOC={foc_val:+.6f}, profit={profit_val:.6f}")

# Find root using scipy
print("\nFinding root of FOC:")
try:
    # Try bracket around 0.22
    sol = root_scalar(first_order_condition, bracket=[0.20, 0.25], method='brentq')
    if sol.converged:
        x_root = sol.root
        profit_root = profit(x_root)
        foc_root = first_order_condition(x_root)
        print(f"Root found: x* = {x_root:.6f}")
        print(f"  Profit at x*: {profit_root:.6f}")
        print(f"  FOC at x*: {foc_root:.6f}")
        print(f"  Expected: x* ≈ 0.22")
        print(f"  Difference: {abs(x_root - 0.22):.6f}")
    else:
        print("Root finding did not converge")
except Exception as e:
    print(f"Error: {e}")

# Also try a finer search
print("\nFine-grained search for FOC = 0:")
x_fine = np.linspace(0.20, 0.25, 1000)
foc_fine = [first_order_condition(x) for x in x_fine]
# Find where FOC changes sign
for i in range(len(foc_fine) - 1):
    if foc_fine[i] * foc_fine[i+1] <= 0:
        x_candidate = x_fine[i]
        foc_candidate = foc_fine[i]
        profit_candidate = profit(x_candidate)
        print(f"Sign change at x ≈ {x_candidate:.6f}: FOC={foc_candidate:.6f}, profit={profit_candidate:.6f}")
        break

