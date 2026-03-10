#!/usr/bin/env python3
import csv
import json
import math
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PANEL_IN = ROOT / "data" / "delegator_choice_panel.csv"
POOLS_IN = ROOT / "data" / "staking_pools.csv"
PANEL_OUT = ROOT / "data" / "delegator_choice_panel.csv"
JSON_OUT = ROOT / "regression" / "delegator_choice_results.json"
MD_OUT = ROOT / "regression" / "delegator_choice_results.md"
TEX_OUT = ROOT / "regression" / "delegator_choice_results.tex"


def to_float(value):
    if value is None:
        return None
    text = str(value).strip()
    if text == "":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def read_pool_constants():
    pool_map = {}
    with POOLS_IN.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pool_id = (row.get("pool_id") or "").strip()
            if not pool_id:
                continue
            pool_map[pool_id] = {
                "margin": to_float(row.get("pool_update.active.margin")),
                "lifetime_roa": to_float(row.get("stats.lifetime.roa")),
            }
    return pool_map


def enrich_panel(pool_map):
    rows = []
    with PANEL_IN.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames or [])
        if "margin" not in fieldnames:
            fieldnames.append("margin")
        if "lifetime_roa" not in fieldnames:
            fieldnames.append("lifetime_roa")
        for row in reader:
            pool_id = (row.get("pool_id") or "").strip()
            constants = pool_map.get(pool_id, {})
            margin = constants.get("margin")
            lifetime_roa = constants.get("lifetime_roa")
            row["margin"] = "" if margin is None else f"{margin:.10g}"
            row["lifetime_roa"] = "" if lifetime_roa is None else f"{lifetime_roa:.10g}"
            rows.append(row)

    with PANEL_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return rows


def mean(vals):
    if not vals:
        return 0.0
    return sum(vals) / float(len(vals))


def twoway_within_transform(values, pool_ids, epochs, max_iter=200, tol=1e-11):
    z = values[:]
    for _ in range(max_iter):
        prev = z[:]
        by_pool = defaultdict(list)
        by_epoch = defaultdict(list)
        for i, val in enumerate(z):
            by_pool[pool_ids[i]].append(val)
            by_epoch[epochs[i]].append(val)
        pool_means = {k: mean(v) for k, v in by_pool.items()}
        epoch_means = {k: mean(v) for k, v in by_epoch.items()}
        grand = mean(z)
        for i in range(len(z)):
            z[i] = z[i] - pool_means[pool_ids[i]] - epoch_means[epochs[i]] + grand
        diff = max(abs(z[i] - prev[i]) for i in range(len(z)))
        if diff < tol:
            break
    return z


def transpose(m):
    return [list(col) for col in zip(*m)]


def matmul(a, b):
    out = [[0.0 for _ in range(len(b[0]))] for _ in range(len(a))]
    for i in range(len(a)):
        for k in range(len(b)):
            aik = a[i][k]
            if aik == 0.0:
                continue
            for j in range(len(b[0])):
                out[i][j] += aik * b[k][j]
    return out


def matvec(a, x):
    out = [0.0 for _ in range(len(a))]
    for i in range(len(a)):
        s = 0.0
        row = a[i]
        for j in range(len(x)):
            s += row[j] * x[j]
        out[i] = s
    return out


def invert_matrix(m):
    n = len(m)
    a = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(m)]
    for col in range(n):
        pivot = col
        best = abs(a[col][col])
        for r in range(col + 1, n):
            v = abs(a[r][col])
            if v > best:
                best = v
                pivot = r
        if best < 1e-14:
            raise ValueError("Singular matrix")
        if pivot != col:
            a[col], a[pivot] = a[pivot], a[col]
        div = a[col][col]
        for j in range(2 * n):
            a[col][j] /= div
        for r in range(n):
            if r == col:
                continue
            factor = a[r][col]
            if factor == 0.0:
                continue
            for j in range(2 * n):
                a[r][j] -= factor * a[col][j]
    return [row[n:] for row in a]


def normal_cdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def p_norm_two_sided(tval):
    z = abs(tval)
    return max(0.0, min(1.0, 2.0 * (1.0 - normal_cdf(z))))


def run_ols_with_cluster(y, x, cluster_ids):
    xt = transpose(x)
    xtx = matmul(xt, x)
    xtx_inv = invert_matrix(xtx)
    xty = matvec(xt, y)
    beta = matvec(xtx_inv, xty)
    yhat = matvec(x, beta)
    resid = [y[i] - yhat[i] for i in range(len(y))]

    # Cluster-robust "meat"
    k = len(beta)
    cluster_vec = defaultdict(lambda: [0.0] * k)
    for i in range(len(y)):
        g = cluster_ids[i]
        ui = resid[i]
        row = x[i]
        gv = cluster_vec[g]
        for j in range(k):
            gv[j] += row[j] * ui

    meat = [[0.0 for _ in range(k)] for _ in range(k)]
    for gv in cluster_vec.values():
        for i in range(k):
            for j in range(k):
                meat[i][j] += gv[i] * gv[j]

    vcov = matmul(matmul(xtx_inv, meat), xtx_inv)
    se = [math.sqrt(max(0.0, vcov[i][i])) for i in range(k)]
    tstats = [beta[i] / se[i] if se[i] > 0.0 else 0.0 for i in range(k)]
    pvals = [p_norm_two_sided(t) for t in tstats]
    return beta, se, tstats, pvals, yhat, resid


def within_r2(y, yhat):
    ybar = mean(y)
    sst = sum((v - ybar) ** 2 for v in y)
    ssr = sum((y[i] - yhat[i]) ** 2 for i in range(len(y)))
    if sst <= 0.0:
        return 0.0
    return 1.0 - (ssr / sst)


def build_dataset(rows, needed_cols):
    data = []
    for r in rows:
        pool_id = (r.get("pool_id") or "").strip()
        epoch = r.get("epoch_no")
        y = to_float(r.get("delta_log_delegators"))
        if not pool_id or epoch is None or y is None:
            continue
        values = {}
        missing = False
        for c in needed_cols:
            v = to_float(r.get(c))
            if v is None:
                missing = True
                break
            values[c] = v
        if missing:
            continue
        data.append(
            {
                "pool_id": pool_id,
                "epoch_no": int(float(epoch)),
                "y": y,
                "x": values,
            }
        )
    return data


def run_twoway_fe_spec(rows, spec_name, regressors):
    data = build_dataset(rows, regressors)
    pool_ids = [d["pool_id"] for d in data]
    epochs = [d["epoch_no"] for d in data]
    y_raw = [d["y"] for d in data]
    x_raw = {c: [d["x"][c] for d in data] for c in regressors}

    y_tilde = twoway_within_transform(y_raw, pool_ids, epochs)
    x_tilde = {c: twoway_within_transform(vals, pool_ids, epochs) for c, vals in x_raw.items()}

    kept = []
    dropped = []
    for c in regressors:
        energy = sum(v * v for v in x_tilde[c])
        if energy < 1e-10:
            dropped.append(c)
        else:
            kept.append(c)

    x = []
    for i in range(len(data)):
        x.append([x_tilde[c][i] for c in kept])

    beta, se, tstats, pvals, yhat, _ = run_ols_with_cluster(y_tilde, x, pool_ids)
    coef = {}
    for i, c in enumerate(kept):
        coef[c] = {
            "beta": beta[i],
            "se_cluster_pool": se[i],
            "t": tstats[i],
            "p_norm_approx": pvals[i],
        }

    return {
        "type": "two_way_fe",
        "spec_name": spec_name,
        "regressors_requested": regressors,
        "regressors_estimated": kept,
        "regressors_dropped_collinear": dropped,
        "n_obs": len(data),
        "n_pools": len(set(pool_ids)),
        "n_epochs": len(set(epochs)),
        "within_r2": within_r2(y_tilde, yhat),
        "coefficients": coef,
    }


def run_epoch_fe_only_spec(rows, spec_name, regressors):
    data = build_dataset(rows, regressors)
    epochs = sorted({d["epoch_no"] for d in data})
    base_epoch = epochs[0]

    x = []
    y = []
    pools = []
    reg_all = ["intercept"] + regressors + [f"epoch_{e}" for e in epochs if e != base_epoch]
    for d in data:
        row = [1.0]
        for c in regressors:
            row.append(d["x"][c])
        for e in epochs:
            if e == base_epoch:
                continue
            row.append(1.0 if d["epoch_no"] == e else 0.0)
        x.append(row)
        y.append(d["y"])
        pools.append(d["pool_id"])

    beta, se, tstats, pvals, yhat, _ = run_ols_with_cluster(y, x, pools)
    ybar = mean(y)
    sst = sum((v - ybar) ** 2 for v in y)
    ssr = sum((y[i] - yhat[i]) ** 2 for i in range(len(y)))
    r2 = 0.0 if sst <= 0 else 1.0 - ssr / sst

    coef = {}
    for i, name in enumerate(reg_all):
        if name == "intercept" or name.startswith("epoch_"):
            continue
        coef[name] = {
            "beta": beta[i],
            "se_cluster_pool": se[i],
            "t": tstats[i],
            "p_norm_approx": pvals[i],
        }
    return {
        "type": "epoch_fe_only",
        "spec_name": spec_name,
        "regressors_requested": regressors,
        "regressors_estimated": regressors,
        "regressors_dropped_collinear": [],
        "n_obs": len(data),
        "n_pools": len(set(pools)),
        "n_epochs": len(set(d["epoch_no"] for d in data)),
        "r2": r2,
        "coefficients": coef,
    }


def fmt4(x):
    return f"{x:.4f}"


def to_markdown(results):
    s1 = results["specifications"]["S1_lag1_core_real_margin"]
    s2 = results["specifications"]["S2_lag1_with_persistence_real_margin"]
    s3 = results["specifications"]["S3_lag2_robustness_real_margin"]
    s4 = results["specifications"]["S4_epochFE_lag1_with_lifetime_roa_margin"]

    lines = []
    lines.append("# Delegator Choice FE Report")
    lines.append("")
    lines.append("Method: **Two-way FE (pool + epoch), cluster-robust SE by pool**")
    lines.append("Dependent variable: `delta_log_delegators = log(1+delegators_t) - log(1+delegators_{t-1})`")
    lines.append("")
    lines.append("## Why lifetime ROA was not in prior FE equations")
    lines.append("")
    lines.append("- In two-way FE, pool-level constants are absorbed by pool fixed effects (`alpha_i`).")
    lines.append("- `lifetime_roa` is pool-constant in this dataset, so it is collinear with `alpha_i` and cannot be estimated in a pool-FE model.")
    lines.append("- Using real `margin` as a fixed pool value has the same issue in two-way FE.")
    lines.append("- To estimate their coefficients, we add an **epoch-FE-only** comparison model (no pool FE).")
    lines.append("")
    lines.append("## Margin update requested")
    lines.append("")
    lines.append("- Replaced `lag1_margin_proxy` with real pool `margin` from `pool_update.active.margin`.")
    lines.append("- Assumption used: margin is fixed across observed epochs for each pool.")
    lines.append("- In two-way FE specs, `margin` is dropped automatically for collinearity with pool FE.")
    lines.append("")
    lines.append("## Model Definitions")
    lines.append("")
    lines.append("- **S1 (two-way FE, lag1 core):** requested regressors are `lag1_luck`, `lag1_log_pledge`, `lag1_log_stake`, `margin`; `margin` is pool-fixed and absorbed by pool FE (`alpha_i`), so it is not estimated separately.")
    lines.append("- **S2 (two-way FE, lag1 + persistence):** requested regressors are S1 + `lag1_log_delegators`; again `margin` is absorbed by pool FE.")
    lines.append("- **S3 (two-way FE, lag2 robustness):** requested regressors are `lag2_luck`, `lag1_log_pledge`, `lag2_log_stake`, `margin`, `lag2_log_delegators`; `margin` is absorbed by pool FE.")
    lines.append("- **S4 (epoch FE only, comparison):** requested regressors are `lag1_luck`, `lag1_log_pledge`, `lag1_log_stake`, `margin`, `lifetime_roa`, `lag1_log_delegators` + epoch FE; here `margin` and `lifetime_roa` are identifiable.")
    lines.append("")
    lines.append("## Model equations and variable definitions")
    lines.append("")
    lines.append("Outcome definition:")
    lines.append("")
    lines.append("- `delta_log_delegators_it = log(1 + delegators_it) - log(1 + delegators_i,t-1)`")
    lines.append("")
    lines.append("Specification equations:")
    lines.append("")
    lines.append("- **S1 (two-way FE, estimable equation):**")
    lines.append("  `Delta log(1+delegators_{i,t}) = beta1*luck_{i,t-1} + beta2*log(1+pledge_{i,t-1}) + beta3*log(1+stake_{i,t-1}) + alpha_i + gamma_t + error_{i,t}`")
    lines.append("  Requested regressor `margin_i` is absorbed by `alpha_i` and therefore not shown in the estimable equation.")
    lines.append("- **S2 (two-way FE, estimable equation):**")
    lines.append("  `Delta log(1+delegators_{i,t}) = beta1*luck_{i,t-1} + beta2*log(1+pledge_{i,t-1}) + beta3*log(1+stake_{i,t-1}) + beta4*log(1+delegators_{i,t-1}) + alpha_i + gamma_t + error_{i,t}`")
    lines.append("  Requested regressor `margin_i` is absorbed by `alpha_i` and therefore not shown in the estimable equation.")
    lines.append("- **S3 (two-way FE, estimable equation):**")
    lines.append("  `Delta log(1+delegators_{i,t}) = beta1*luck_{i,t-2} + beta2*log(1+pledge_{i,t-1}) + beta3*log(1+stake_{i,t-2}) + beta4*log(1+delegators_{i,t-2}) + alpha_i + gamma_t + error_{i,t}`")
    lines.append("  Requested regressor `margin_i` is absorbed by `alpha_i` and therefore not shown in the estimable equation.")
    lines.append("- **S4 (epoch FE only comparison):**")
    lines.append("  `Delta log(1+delegators_{i,t}) = beta0 + beta1*luck_{i,t-1} + beta2*log(1+pledge_{i,t-1}) + beta3*log(1+stake_{i,t-1}) + beta4*margin_i + beta5*lifetime_roa_i + beta6*log(1+delegators_{i,t-1}) + gamma_t + error_{i,t}`")
    lines.append("")
    lines.append("Variable definitions:")
    lines.append("")
    lines.append("- `delegators_it`: number of delegators in pool `i` at epoch `t`")
    lines.append("- `luck_{i,t-1}`, `luck_{i,t-2}`: pool luck lagged by 1 or 2 epochs")
    lines.append("- `log(1+pledge_{i,t-1})`: log pledge lagged by 1 epoch")
    lines.append("- `log(1+stake_{i,t-1})`, `log(1+stake_{i,t-2})`: log stake lagged by 1 or 2 epochs")
    lines.append("- `log(1+delegators_{i,t-1})`, `log(1+delegators_{i,t-2})`: log delegators lagged by 1 or 2 epochs")
    lines.append("- `margin_i`: pool active margin (`pool_update.active.margin`), treated as fixed by pool")
    lines.append("- `lifetime_roa_i`: pool lifetime ROA (`stats.lifetime.roa`), treated as fixed by pool")
    lines.append("- `alpha_i`: pool fixed effects; `gamma_t`: epoch fixed effects; `error_it`: residual")
    lines.append("- Dataset mapping: `lag1_luck_it = luck_{i,t-1}`, `lag2_luck_it = luck_{i,t-2}`, and similarly for other `lag1_`/`lag2_` fields")
    lines.append("")
    lines.append("## Assumptions and caveats")
    lines.append("")
    lines.append("- Observational data: results are associational/quasi-causal, not full causal identification.")
    lines.append("- Two-way FE reduces bias from time-invariant pool heterogeneity, but time-varying omitted factors may remain.")
    lines.append("- Lagged regressors reduce (but do not eliminate) reverse-causality/simultaneity concerns.")
    lines.append("- `margin` and `lifetime_roa` are treated as pool-fixed; in two-way FE they are not identifiable and are absorbed by pool FE.")
    lines.append("- Their coefficients are reported only in the epoch-FE-only comparison spec (S4), which is more vulnerable to pool-level confounding.")
    lines.append("- Cluster-robust SE by pool address within-pool serial correlation and heteroskedasticity, but inference is still model-dependent.")
    lines.append("- Epoch coverage is limited (available lag structure), so long-horizon dynamics are only partially captured.")
    lines.append("- Functional form uses log transforms and linear terms; misspecification risk remains.")
    lines.append("")
    lines.append("| Spec | Type | n_obs | n_pools | n_epochs | Fit | Dropped in estimation |")
    lines.append("|---|---|---:|---:|---:|---:|---|")
    lines.append(f"| S1 | two-way FE | {s1['n_obs']} | {s1['n_pools']} | {s1['n_epochs']} | {fmt4(s1['within_r2'])} (within R^2) | {', '.join(s1['regressors_dropped_collinear']) or 'none'} |")
    lines.append(f"| S2 | two-way FE | {s2['n_obs']} | {s2['n_pools']} | {s2['n_epochs']} | {fmt4(s2['within_r2'])} (within R^2) | {', '.join(s2['regressors_dropped_collinear']) or 'none'} |")
    lines.append(f"| S3 | two-way FE | {s3['n_obs']} | {s3['n_pools']} | {s3['n_epochs']} | {fmt4(s3['within_r2'])} (within R^2) | {', '.join(s3['regressors_dropped_collinear']) or 'none'} |")
    lines.append(f"| S4 | epoch FE only | {s4['n_obs']} | {s4['n_pools']} | {s4['n_epochs']} | {fmt4(s4['r2'])} (R^2) | none |")
    lines.append("")

    def add_coef_table(title, spec):
        lines.append(f"## {title}")
        lines.append("")
        lines.append("| Variable | Beta | Cluster SE (pool) | p-value |")
        lines.append("|---|---:|---:|---:|")
        for k, v in spec["coefficients"].items():
            lines.append(f"| {k} | {v['beta']:.6f} | {v['se_cluster_pool']:.6f} | {v['p_norm_approx']:.4f} |")
        lines.append("")

    add_coef_table("S1 Coefficients", s1)
    add_coef_table("S2 Coefficients", s2)
    add_coef_table("S3 Coefficients", s3)
    add_coef_table("S4 Coefficients (lifetime ROA + margin identifiable)", s4)

    lines.append("## Interpretation")
    lines.append("")
    lines.append("- Two-way FE answers a within-pool-over-time question; time-invariant regressors are not identifiable there.")
    lines.append("- `lifetime_roa` and fixed `margin` should be interpreted from S4 (epoch FE only), not from S1-S3.")
    lines.append("- `log(stake)` remains a strong predictor in FE specifications.")
    lines.append("- Results remain associational/quasi-causal, not fully causal.")
    lines.append("")
    return "\n".join(lines) + "\n"


def latex_escape(text):
    return (
        text.replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("$", "\\$")
        .replace("#", "\\#")
        .replace("_", "\\_")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("~", "\\textasciitilde{}")
        .replace("^", "\\textasciicircum{}")
    )


def tex_num(x, digits=4):
    return f"{x:.{digits}f}"


def to_tex(results):
    s1 = results["specifications"]["S1_lag1_core_real_margin"]
    s2 = results["specifications"]["S2_lag1_with_persistence_real_margin"]
    s3 = results["specifications"]["S3_lag2_robustness_real_margin"]
    s4 = results["specifications"]["S4_epochFE_lag1_with_lifetime_roa_margin"]

    def dropped(spec):
        d = spec["regressors_dropped_collinear"]
        return "none" if not d else ", ".join(d)

    def coef_table_lines(spec):
        rows = []
        for k, v in spec["coefficients"].items():
            rows.append(
                f"{latex_escape(k)} & {v['beta']:.6f} & {v['se_cluster_pool']:.6f} & {v['p_norm_approx']:.4f} \\\\"
            )
        return rows

    out = []
    out.append("\\documentclass[11pt]{article}")
    out.append("\\usepackage[margin=1in]{geometry}")
    out.append("\\usepackage{longtable}")
    out.append("\\usepackage{booktabs}")
    out.append("\\usepackage{array}")
    out.append("\\begin{document}")
    out.append("\\section*{Delegator Choice FE Report}")
    out.append("Method: two-way FE (pool + epoch), cluster-robust SE by pool.\\\\")
    out.append("Dependent variable: $\\Delta\\log(1+delegators_{it}) = \\log(1+delegators_t)-\\log(1+delegators_{t-1})$.")

    out.append("\\subsection*{Why lifetime ROA was not in prior FE equations}")
    out.append("\\begin{itemize}")
    out.append("\\item In two-way FE, pool-level constants are absorbed by pool fixed effects ($\\alpha_i$).")
    out.append("\\item $lifetime\\_roa$ is pool-constant in this dataset, so it is collinear with $\\alpha_i$ and cannot be estimated in a pool-FE model.")
    out.append("\\item Using real $margin$ as a fixed pool value has the same issue in two-way FE.")
    out.append("\\item To estimate coefficients for these variables, we add an epoch-FE-only comparison model (no pool FE).")
    out.append("\\end{itemize}")

    out.append("\\subsection*{Margin update requested}")
    out.append("\\begin{itemize}")
    out.append("\\item Replaced $lag1\\_margin\\_proxy$ with real pool $margin$ from $pool\\_update.active.margin$.")
    out.append("\\item Assumption: margin is fixed across observed epochs for each pool.")
    out.append("\\item In two-way FE specs, $margin$ is dropped automatically for collinearity with pool FE.")
    out.append("\\end{itemize}")

    out.append("\\subsection*{Model definitions}")
    out.append("\\begin{itemize}")
    out.append("\\item S1 (two-way FE, lag1 core): requested regressors are lag1 luck, lag1 log pledge, lag1 log stake, and margin; margin is pool-fixed and absorbed by pool FE ($\\alpha_i$), so it is not estimated separately.")
    out.append("\\item S2 (two-way FE, lag1 + persistence): requested regressors are S1 plus lag1 log delegators; margin is again absorbed by pool FE.")
    out.append("\\item S3 (two-way FE, lag2 robustness): requested regressors are lag2 luck, lag1 log pledge, lag2 log stake, margin, lag2 log delegators; margin is absorbed by pool FE.")
    out.append("\\item S4 (epoch FE only, comparison): requested regressors are lag1 luck, lag1 log pledge, lag1 log stake, margin, lifetime ROA, lag1 log delegators, plus epoch FE; here margin and lifetime ROA are identifiable.")
    out.append("\\end{itemize}")

    out.append("\\subsection*{Model equations and variable definitions}")
    out.append("Outcome definition:")
    out.append("\\begin{itemize}")
    out.append("\\item $\\Delta\\log(1+delegators_{it}) = \\log(1+delegators_{it}) - \\log(1+delegators_{i,t-1})$")
    out.append("\\end{itemize}")
    out.append("Specification equations:")
    out.append("\\begin{itemize}")
    out.append("\\item S1 (two-way FE, estimable equation): $\\Delta\\log(1+delegators_{i,t}) = \\beta_1 luck_{i,t-1} + \\beta_2 \\log(1+pledge_{i,t-1}) + \\beta_3 \\log(1+stake_{i,t-1}) + \\alpha_i + \\gamma_t + error_{i,t}$")
    out.append("\\item Requested regressor $margin_i$ is absorbed by $\\alpha_i$ and therefore not shown in the estimable equation.")
    out.append("\\item S2 (two-way FE, estimable equation): $\\Delta\\log(1+delegators_{i,t}) = \\beta_1 luck_{i,t-1} + \\beta_2 \\log(1+pledge_{i,t-1}) + \\beta_3 \\log(1+stake_{i,t-1}) + \\beta_4 \\log(1+delegators_{i,t-1}) + \\alpha_i + \\gamma_t + error_{i,t}$")
    out.append("\\item Requested regressor $margin_i$ is absorbed by $\\alpha_i$ and therefore not shown in the estimable equation.")
    out.append("\\item S3 (two-way FE, estimable equation): $\\Delta\\log(1+delegators_{i,t}) = \\beta_1 luck_{i,t-2} + \\beta_2 \\log(1+pledge_{i,t-1}) + \\beta_3 \\log(1+stake_{i,t-2}) + \\beta_4 \\log(1+delegators_{i,t-2}) + \\alpha_i + \\gamma_t + error_{i,t}$")
    out.append("\\item Requested regressor $margin_i$ is absorbed by $\\alpha_i$ and therefore not shown in the estimable equation.")
    out.append("\\item S4 (epoch FE only comparison): $\\Delta\\log(1+delegators_{i,t}) = \\beta_0 + \\beta_1 luck_{i,t-1} + \\beta_2 \\log(1+pledge_{i,t-1}) + \\beta_3 \\log(1+stake_{i,t-1}) + \\beta_4 margin_i + \\beta_5 lifetime\\_roa_i + \\beta_6 \\log(1+delegators_{i,t-1}) + \\gamma_t + error_{i,t}$")
    out.append("\\end{itemize}")
    out.append("Variable definitions:")
    out.append("\\begin{itemize}")
    out.append("\\item $delegators_{it}$: number of delegators in pool $i$ at epoch $t$")
    out.append("\\item $luck_{i,t-1}$, $luck_{i,t-2}$: pool luck lagged by 1 or 2 epochs")
    out.append("\\item $\\log(1+pledge_{i,t-1})$: log pledge lagged by 1 epoch")
    out.append("\\item $\\log(1+stake_{i,t-1})$, $\\log(1+stake_{i,t-2})$: log stake lagged by 1 or 2 epochs")
    out.append("\\item $\\log(1+delegators_{i,t-1})$, $\\log(1+delegators_{i,t-2})$: log delegators lagged by 1 or 2 epochs")
    out.append("\\item $margin_i$: pool active margin ($pool\\_update.active.margin$), treated as fixed by pool")
    out.append("\\item $lifetime\\_roa_i$: pool lifetime ROA ($stats.lifetime.roa$), treated as fixed by pool")
    out.append("\\item $\\alpha_i$: pool fixed effects; $\\gamma_t$: epoch fixed effects; $error_{it}$: residual")
    out.append("\\item Dataset mapping: $lag1\\_luck_{it}=luck_{i,t-1}$, $lag2\\_luck_{it}=luck_{i,t-2}$, and similarly for other $lag1\\_$/$lag2\\_$ fields")
    out.append("\\end{itemize}")

    out.append("\\subsection*{Assumptions and caveats}")
    out.append("\\begin{itemize}")
    out.append("\\item Observational data: results are associational/quasi-causal, not full causal identification.")
    out.append("\\item Two-way FE reduces bias from time-invariant pool heterogeneity, but time-varying omitted factors may remain.")
    out.append("\\item Lagged regressors reduce (but do not eliminate) reverse-causality/simultaneity concerns.")
    out.append("\\item $margin$ and $lifetime\\_roa$ are treated as pool-fixed; in two-way FE they are not identifiable and are absorbed by pool FE.")
    out.append("\\item Their coefficients are reported only in the epoch-FE-only comparison spec (S4), which is more vulnerable to pool-level confounding.")
    out.append("\\item Cluster-robust SE by pool address within-pool serial correlation and heteroskedasticity, but inference is still model-dependent.")
    out.append("\\item Epoch coverage is limited (available lag structure), so long-horizon dynamics are only partially captured.")
    out.append("\\item Functional form uses log transforms and linear terms; misspecification risk remains.")
    out.append("\\end{itemize}")

    out.append("\\subsection*{Specification summary}")
    out.append("\\begin{longtable}{l l r r r l p{3.2cm}}")
    out.append("\\toprule")
    out.append("Spec & Type & n\\_obs & n\\_pools & n\\_epochs & Fit & Dropped in estimation \\\\")
    out.append("\\midrule")
    out.append("\\endhead")
    out.append(f"S1 & two-way FE & {s1['n_obs']} & {s1['n_pools']} & {s1['n_epochs']} & {tex_num(s1['within_r2'])} (within $R^2$) & {latex_escape(dropped(s1))} \\\\")
    out.append(f"S2 & two-way FE & {s2['n_obs']} & {s2['n_pools']} & {s2['n_epochs']} & {tex_num(s2['within_r2'])} (within $R^2$) & {latex_escape(dropped(s2))} \\\\")
    out.append(f"S3 & two-way FE & {s3['n_obs']} & {s3['n_pools']} & {s3['n_epochs']} & {tex_num(s3['within_r2'])} (within $R^2$) & {latex_escape(dropped(s3))} \\\\")
    out.append(f"S4 & epoch FE only & {s4['n_obs']} & {s4['n_pools']} & {s4['n_epochs']} & {tex_num(s4['r2'])} ($R^2$) & none \\\\")
    out.append("\\bottomrule")
    out.append("\\end{longtable}")

    for title, spec in [
        ("S1 Coefficients", s1),
        ("S2 Coefficients", s2),
        ("S3 Coefficients", s3),
        ("S4 Coefficients (lifetime ROA + margin identifiable)", s4),
    ]:
        out.append(f"\\subsection*{{{latex_escape(title)}}}")
        out.append("\\begin{longtable}{l r r r}")
        out.append("\\toprule")
        out.append("Variable & Beta & Cluster SE (pool) & p-value \\\\")
        out.append("\\midrule")
        out.append("\\endhead")
        out.extend(coef_table_lines(spec))
        out.append("\\bottomrule")
        out.append("\\end{longtable}")

    out.append("\\subsection*{Interpretation}")
    out.append("\\begin{itemize}")
    out.append("\\item Two-way FE answers a within-pool-over-time question; time-invariant regressors are not identifiable there.")
    out.append("\\item $lifetime\\_roa$ and fixed $margin$ should be interpreted from S4 (epoch FE only), not from S1-S3.")
    out.append("\\item $\\log(stake)$ remains a strong predictor in FE specifications.")
    out.append("\\item Results remain associational/quasi-causal, not fully causal.")
    out.append("\\end{itemize}")
    out.append("\\end{document}")
    return "\n".join(out) + "\n"


def main():
    pool_map = read_pool_constants()
    rows = enrich_panel(pool_map)

    specs = {}
    specs["S1_lag1_core_real_margin"] = run_twoway_fe_spec(
        rows, "S1_lag1_core_real_margin", ["lag1_luck", "lag1_log_pledge", "lag1_log_stake", "margin"]
    )
    specs["S2_lag1_with_persistence_real_margin"] = run_twoway_fe_spec(
        rows,
        "S2_lag1_with_persistence_real_margin",
        ["lag1_luck", "lag1_log_pledge", "lag1_log_stake", "margin", "lag1_log_delegators"],
    )
    specs["S3_lag2_robustness_real_margin"] = run_twoway_fe_spec(
        rows,
        "S3_lag2_robustness_real_margin",
        ["lag2_luck", "lag1_log_pledge", "lag2_log_stake", "margin", "lag2_log_delegators"],
    )
    specs["S4_epochFE_lag1_with_lifetime_roa_margin"] = run_epoch_fe_only_spec(
        rows,
        "S4_epochFE_lag1_with_lifetime_roa_margin",
        ["lag1_luck", "lag1_log_pledge", "lag1_log_stake", "margin", "lifetime_roa", "lag1_log_delegators"],
    )

    output = {
        "goal": "Explain delegator pool choice dynamics with real margin and lifetime ROA treatment",
        "dependent_variable": "delta_log_delegators = log(1+delegators_t) - log(1+delegators_{t-1})",
        "method": "Two-way FE (pool + epoch), cluster-robust SE by pool; plus epoch-FE-only comparison for time-invariant variables",
        "input_files": {
            "source_panel": str(PANEL_OUT),
            "source_pools": str(POOLS_IN),
        },
        "specifications": specs,
        "notes": [
            "Real margin is sourced from pool_update.active.margin and treated as fixed across epochs.",
            "In two-way FE models, pool-constant regressors (margin, lifetime_roa) are collinear with pool fixed effects and cannot be estimated.",
            "Epoch-FE-only comparison model is included to obtain coefficients for lifetime_roa and margin.",
            "Interpretation remains associational/quasi-causal, not full causal identification.",
        ],
    }

    JSON_OUT.write_text(json.dumps(output, indent=2), encoding="utf-8")
    md = to_markdown(output)
    MD_OUT.write_text(md, encoding="utf-8")
    TEX_OUT.write_text(to_tex(output), encoding="utf-8")
    print("Updated:")
    print("-", PANEL_OUT)
    print("-", JSON_OUT)
    print("-", MD_OUT)
    print("-", TEX_OUT)


if __name__ == "__main__":
    main()
