# Detailed test to understand what's happening
import math
import numpy as np
from scipy.optimize import root_scalar, minimize_scalar
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
    return benefit_i(n, x, x, b=b) - cost(x)

def to_scalar(value):
    if hasattr(value, 'item'):
        return float(value.item())
    elif hasattr(value, '__iter__') and not isinstance(value, str):
        return float(value[0]) if len(value) > 0 else float(value)
    else:
        return float(value)

# Direct optimization to find maximum
print("Direct optimization to find maximum profit:")
result = minimize_scalar(lambda x: -profit(x), bounds=(0.001, 0.499), method='bounded')
x_opt = result.x
profit_opt = profit(x_opt)
print(f"Optimal x (by direct optimization): {x_opt:.6f}, profit = {profit_opt:.6f}")

# Check FOC
def first_order_condition(x):
    f = lambda x_i: benefit_i(n, x_i, x, b=b)
    dfdx = nd.Derivative(f, n=1, method='central', order=4)
    benefit_deriv = to_scalar(dfdx(x))
    cost_derivative = nd.Derivative(cost, n=1, method='central', order=4)
    cost_deriv = to_scalar(cost_derivative(x))
    return benefit_deriv - cost_deriv

foc_opt = first_order_condition(x_opt)
print(f"FOC at optimal x: {foc_opt:.6f}")

# Find root of FOC
print("\nFinding root of FOC:")
try:
    sol = root_scalar(first_order_condition, bracket=[0.1, 0.3], method='brentq')
    if sol.converged:
        x_root = sol.root
        profit_root = profit(x_root)
        foc_root = first_order_condition(x_root)
        print(f"Root found: x = {x_root:.6f}, profit = {profit_root:.6f}, FOC = {foc_root:.6f}")
    else:
        print("Root finding did not converge")
except Exception as e:
    print(f"Error in root finding: {e}")

# Check around x=0.22
print("\nDetailed check around x=0.22:")
for x_test in np.linspace(0.20, 0.24, 21):
    profit_val = profit(x_test)
    foc_val = first_order_condition(x_test)
    print(f"x={x_test:.4f}: profit={profit_val:.6f}, FOC={foc_val:.6f}")

# Check what the benefit function looks like
print("\nBenefit and cost breakdown at x=0.22:")
x_test = 0.22
benefit_val = benefit_i(n, x_test, x_test, b=b)
cost_val = cost(x_test)
profit_val = profit(x_test)
foc_val = first_order_condition(x_test)
print(f"Benefit = {benefit_val:.6f}")
print(f"Cost = {cost_val:.6f}")
print(f"Profit = {profit_val:.6f}")
print(f"FOC = {foc_val:.6f}")

