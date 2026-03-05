# Quick test for corner solution detection
import math
import numpy as np
from scipy.optimize import root_scalar
import numdifftools as nd

# Parameters
B = 1
a = 0.75
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
    return benefit_i(n, x, x, b=b) - cost(x)

def to_scalar(value):
    if hasattr(value, 'item'):
        return float(value.item())
    elif hasattr(value, '__iter__') and not isinstance(value, str):
        return float(value[0]) if len(value) > 0 else float(value)
    else:
        return float(value)

def first_order_condition(x):
    f = lambda x_i: benefit_i(n, x_i, x, b=b)
    dfdx = nd.Derivative(f, n=1, method='central', order=4)
    benefit_deriv = to_scalar(dfdx(x))
    cost_derivative = nd.Derivative(cost, n=1, method='central', order=4)
    cost_deriv = to_scalar(cost_derivative(x))
    return benefit_deriv - cost_deriv

print("Testing corner solution detection with n=1, a=0.75, b=0")
print("=" * 60)

# Check FOC at various points
test_points = [0.0, 0.01, 0.1, 0.2, 0.3, 0.4, 0.49, 0.5]
print("\nFOC values at different points:")
for x in test_points:
    try:
        foc = first_order_condition(x)
        profit_val = profit(x)
        print(f"x={x:.2f}: FOC={foc:+.6f}, profit={profit_val:.6f}")
    except Exception as e:
        print(f"x={x:.2f}: Error - {e}")

# Check what the current logic would return
test_x = np.linspace(0.01, 0.49, 50)
foc_samples = []
for x in test_x:
    try:
        foc_samples.append(first_order_condition(x))
    except:
        foc_samples.append(np.nan)

foc_samples_clean = [f for f in foc_samples if not np.isnan(f)]

if len(foc_samples_clean) > 0:
    min_foc = min(foc_samples_clean)
    max_foc = max(foc_samples_clean)
    print(f"\nFOC range in [0.01, 0.49]: min={min_foc:.6f}, max={max_foc:.6f}")
    
    if min_foc > 0:
        print("Current logic: Would return x=0.5 (corner)")
    elif max_foc < 0:
        print("Current logic: Would return x=0.0 (corner)")
    else:
        print("Current logic: Would look for interior roots")



