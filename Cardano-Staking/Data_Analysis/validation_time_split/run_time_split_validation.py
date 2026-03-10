#!/usr/bin/env python3
import csv
import json
import math
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INPUT_PANEL = ROOT / "data" / "delegator_choice_panel.csv"
OUT_DIR = ROOT / "validation_time_split"
JSON_OUT = OUT_DIR / "time_split_validation_results.json"
MD_OUT = OUT_DIR / "time_split_validation_report.md"
TEX_OUT = OUT_DIR / "time_split_validation_report.tex"
PDF_OUT = OUT_DIR / "time_split_validation_report.pdf"


def to_float(v):
    if v is None:
        return None
    s = str(v).strip()
    if s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def mean(vals):
    return sum(vals) / len(vals) if vals else 0.0


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
        for j in range(len(x)):
            s += a[i][j] * x[j]
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


def fit_ols(x, y):
    xt = transpose(x)
    xtx = matmul(xt, x)
    # small ridge to improve numerical stability
    for i in range(len(xtx)):
        xtx[i][i] += 1e-10
    xtx_inv = invert_matrix(xtx)
    xty = matvec(xt, y)
    beta = matvec(xtx_inv, xty)
    return beta


def metrics(y_true, y_pred):
    n = len(y_true)
    if n == 0:
        return {"n": 0, "rmse": None, "mae": None, "r2": None}
    mse = sum((y_true[i] - y_pred[i]) ** 2 for i in range(n)) / n
    mae = sum(abs(y_true[i] - y_pred[i]) for i in range(n)) / n
    ybar = mean(y_true)
    sst = sum((v - ybar) ** 2 for v in y_true)
    sse = sum((y_true[i] - y_pred[i]) ** 2 for i in range(n))
    r2 = 0.0 if sst <= 0 else 1.0 - (sse / sst)
    return {"n": n, "rmse": math.sqrt(mse), "mae": mae, "r2": r2}


def load_rows():
    rows = []
    with INPUT_PANEL.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            y = to_float(r.get("delta_log_delegators"))
            epoch = to_float(r.get("epoch_no"))
            if y is None or epoch is None:
                continue
            rows.append({"epoch_no": int(epoch), "raw": r, "y": y})
    return rows


def choose_time_split(rows, train_share=0.70):
    counts = {}
    for r in rows:
        e = r["epoch_no"]
        counts[e] = counts.get(e, 0) + 1
    epochs = sorted(counts.keys())
    total = len(rows)
    target = train_share * total
    best_epoch = epochs[0]
    best_gap = float("inf")
    running = 0
    for e in epochs[:-1]:
        running += counts[e]
        gap = abs(running - target)
        if gap < best_gap:
            best_gap = gap
            best_epoch = e
    train_epochs = [e for e in epochs if e <= best_epoch]
    valid_epochs = [e for e in epochs if e > best_epoch]
    if not valid_epochs:
        train_epochs = epochs[:-1]
        valid_epochs = [epochs[-1]]
    return train_epochs, valid_epochs, counts


def build_xy(rows, features):
    x, y = [], []
    for r in rows:
        vals = []
        miss = False
        for f in features:
            v = to_float(r["raw"].get(f))
            if v is None:
                miss = True
                break
            vals.append(v)
        if miss:
            continue
        x.append([1.0] + vals)
        y.append(r["y"])
    return x, y


def run_spec(spec_name, rows_train, rows_valid, features):
    x_train, y_train = build_xy(rows_train, features)
    x_valid, y_valid = build_xy(rows_valid, features)
    beta = fit_ols(x_train, y_train)
    yhat_train = matvec(x_train, beta)
    yhat_valid = matvec(x_valid, beta)
    return {
        "name": spec_name,
        "features": features,
        "coefficients": {"intercept": beta[0], **{features[i]: beta[i + 1] for i in range(len(features))}},
        "train_metrics": metrics(y_train, yhat_train),
        "validation_metrics": metrics(y_valid, yhat_valid),
        "n_train_used": len(y_train),
        "n_validation_used": len(y_valid),
    }


def f4(v):
    return "n/a" if v is None else f"{v:.4f}"


def write_markdown(report):
    split = report["split"]
    s1 = report["specifications"]["P1_lagged_core_with_margin_lifetime_roa"]
    s2 = report["specifications"]["P2_lagged_plus_persistence_with_margin_lifetime_roa"]

    lines = []
    lines.append("# Time-Split Validation Report")
    lines.append("")
    lines.append("This is a predictive validation exercise (not a causal identification design).")
    lines.append("")
    lines.append("## Split design")
    lines.append("")
    lines.append(f"- Input panel: `{INPUT_PANEL}`")
    lines.append(f"- Train epochs: `{split['train_epochs']}`")
    lines.append(f"- Validation epochs: `{split['validation_epochs']}`")
    lines.append(f"- Approx share by rows: train `{split['train_row_share']:.2%}`, validation `{split['validation_row_share']:.2%}`")
    lines.append("")
    lines.append("## Specifications")
    lines.append("")
    lines.append("- **P1:** `lag1_luck`, `lag1_log_pledge`, `lag1_log_stake`, `margin`, `lifetime_roa`")
    lines.append("- **P2:** P1 + `lag1_log_delegators`")
    lines.append("")
    lines.append("## Model equations and variable definitions")
    lines.append("")
    lines.append("Conceptual outcome equation:")
    lines.append("")
    lines.append("- `delta_log_delegators_it = log(1 + delegators_it) - log(1 + delegators_i,t-1)`")
    lines.append("")
    lines.append("Specification equations:")
    lines.append("")
    lines.append("- **P1:**")
    lines.append("  `delta_log_delegators_it = beta0 + beta1*lag1_luck_it + beta2*lag1_log_pledge_it + beta3*lag1_log_stake_it + beta4*margin_i + beta5*lifetime_roa_i + error_it`")
    lines.append("- **P2:**")
    lines.append("  `delta_log_delegators_it = beta0 + beta1*lag1_luck_it + beta2*lag1_log_pledge_it + beta3*lag1_log_stake_it + beta4*margin_i + beta5*lifetime_roa_i + beta6*lag1_log_delegators_it + error_it`")
    lines.append("")
    lines.append("Variable definitions:")
    lines.append("")
    lines.append("- `delegators_it`: number of delegators in pool `i` at epoch `t`")
    lines.append("- `lag1_luck_it`: pool luck in epoch `t-1`")
    lines.append("- `lag1_log_pledge_it`: `log(1 + pledged_lovelace_{i,t-1})` (as built in the panel)")
    lines.append("- `lag1_log_stake_it`: `log(1 + epoch_stake_lovelace_{i,t-1})` (as built in the panel)")
    lines.append("- `margin_i`: pool active margin (`pool_update.active.margin`), treated as time-invariant")
    lines.append("- `lifetime_roa_i`: pool lifetime ROA (`stats.lifetime.roa`), treated as time-invariant")
    lines.append("- `lag1_log_delegators_it`: `log(1 + delegators_{i,t-1})`")
    lines.append("- `error_it`: residual term for pool `i`, epoch `t`")
    lines.append("")
    lines.append("| Spec | Train n | Validation n | Train RMSE | Validation RMSE | Train R^2 | Validation R^2 |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    lines.append(
        f"| P1 | {s1['n_train_used']} | {s1['n_validation_used']} | {f4(s1['train_metrics']['rmse'])} | {f4(s1['validation_metrics']['rmse'])} | {f4(s1['train_metrics']['r2'])} | {f4(s1['validation_metrics']['r2'])} |"
    )
    lines.append(
        f"| P2 | {s2['n_train_used']} | {s2['n_validation_used']} | {f4(s2['train_metrics']['rmse'])} | {f4(s2['validation_metrics']['rmse'])} | {f4(s2['train_metrics']['r2'])} | {f4(s2['validation_metrics']['r2'])} |"
    )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- This validates out-of-sample predictive stability across time.")
    lines.append("- It does not, by itself, convert associations into causal effects.")
    lines.append("- Causal claims still require an identification strategy (e.g., randomized treatment, IV, DiD/event design).")
    lines.append("")
    MD_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def tex_escape(s):
    return (
        str(s)
        .replace("\\", "\\textbackslash{}")
        .replace("&", "\\&")
        .replace("%", "\\%")
        .replace("$", "\\$")
        .replace("#", "\\#")
        .replace("_", "\\_")
        .replace("{", "\\{")
        .replace("}", "\\}")
    )


def write_tex(report):
    split = report["split"]
    s1 = report["specifications"]["P1_lagged_core_with_margin_lifetime_roa"]
    s2 = report["specifications"]["P2_lagged_plus_persistence_with_margin_lifetime_roa"]
    out = []
    out.append("\\documentclass[11pt]{article}")
    out.append("\\usepackage[margin=1in]{geometry}")
    out.append("\\usepackage{booktabs}")
    out.append("\\begin{document}")
    out.append("\\section*{Time-Split Validation Report}")
    out.append("This is a predictive validation exercise (not a causal identification design).")
    out.append("\\subsection*{Split design}")
    out.append("\\begin{itemize}")
    out.append(f"\\item Input panel: {tex_escape(INPUT_PANEL)}")
    out.append(f"\\item Train epochs: {tex_escape(split['train_epochs'])}")
    out.append(f"\\item Validation epochs: {tex_escape(split['validation_epochs'])}")
    out.append(f"\\item Approx share by rows: train {split['train_row_share']:.2%}, validation {split['validation_row_share']:.2%}")
    out.append("\\end{itemize}")
    out.append("\\subsection*{Specifications}")
    out.append("\\begin{itemize}")
    out.append("\\item P1: lag1 luck, lag1 log pledge, lag1 log stake, margin, lifetime ROA")
    out.append("\\item P2: P1 plus lag1 log delegators")
    out.append("\\end{itemize}")
    out.append("\\subsection*{Model equations and variable definitions}")
    out.append("Conceptual outcome equation:")
    out.append("\\begin{itemize}")
    out.append("\\item $\\Delta\\log(1+delegators_{it}) = \\log(1+delegators_{it}) - \\log(1+delegators_{i,t-1})$")
    out.append("\\end{itemize}")
    out.append("Specification equations:")
    out.append("\\begin{itemize}")
    out.append("\\item P1: $\\Delta\\log(1+delegators_{it}) = \\beta_0 + \\beta_1 lag1\\_luck_{it} + \\beta_2 lag1\\_log\\_pledge_{it} + \\beta_3 lag1\\_log\\_stake_{it} + \\beta_4 margin_i + \\beta_5 lifetime\\_roa_i + error_{it}$")
    out.append("\\item P2: $\\Delta\\log(1+delegators_{it}) = \\beta_0 + \\beta_1 lag1\\_luck_{it} + \\beta_2 lag1\\_log\\_pledge_{it} + \\beta_3 lag1\\_log\\_stake_{it} + \\beta_4 margin_i + \\beta_5 lifetime\\_roa_i + \\beta_6 lag1\\_log\\_delegators_{it} + error_{it}$")
    out.append("\\end{itemize}")
    out.append("Variable definitions:")
    out.append("\\begin{itemize}")
    out.append("\\item $delegators_{it}$: number of delegators in pool $i$ at epoch $t$")
    out.append("\\item $lag1\\_luck_{it}$: pool luck in epoch $t-1$")
    out.append("\\item $lag1\\_log\\_pledge_{it}$: $\\log(1 + pledged\\_lovelace_{i,t-1})$ (as built in the panel)")
    out.append("\\item $lag1\\_log\\_stake_{it}$: $\\log(1 + epoch\\_stake\\_lovelace_{i,t-1})$ (as built in the panel)")
    out.append("\\item $margin_i$: pool active margin ($pool\\_update.active.margin$), treated as time-invariant")
    out.append("\\item $lifetime\\_roa_i$: pool lifetime ROA ($stats.lifetime.roa$), treated as time-invariant")
    out.append("\\item $lag1\\_log\\_delegators_{it}$: $\\log(1 + delegators_{i,t-1})$")
    out.append("\\item $error_{it}$: residual term for pool $i$, epoch $t$")
    out.append("\\end{itemize}")
    out.append("\\subsection*{Performance summary}")
    out.append("\\begin{tabular}{lrrrrrr}")
    out.append("\\toprule")
    out.append("Spec & Train n & Validation n & Train RMSE & Validation RMSE & Train $R^2$ & Validation $R^2$ \\\\")
    out.append("\\midrule")
    out.append(
        f"P1 & {s1['n_train_used']} & {s1['n_validation_used']} & {f4(s1['train_metrics']['rmse'])} & {f4(s1['validation_metrics']['rmse'])} & {f4(s1['train_metrics']['r2'])} & {f4(s1['validation_metrics']['r2'])} \\\\"
    )
    out.append(
        f"P2 & {s2['n_train_used']} & {s2['n_validation_used']} & {f4(s2['train_metrics']['rmse'])} & {f4(s2['validation_metrics']['rmse'])} & {f4(s2['train_metrics']['r2'])} & {f4(s2['validation_metrics']['r2'])} \\\\"
    )
    out.append("\\bottomrule")
    out.append("\\end{tabular}")
    out.append("\\subsection*{Interpretation}")
    out.append("\\begin{itemize}")
    out.append("\\item This checks out-of-sample stability across time.")
    out.append("\\item It does not imply causality by itself.")
    out.append("\\item Causal identification still needs randomization, IV, or quasi-experimental design.")
    out.append("\\end{itemize}")
    out.append("\\end{document}")
    TEX_OUT.write_text("\n".join(out) + "\n", encoding="utf-8")


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = load_rows()
    train_epochs, valid_epochs, counts = choose_time_split(rows, train_share=0.70)

    rows_train = [r for r in rows if r["epoch_no"] in train_epochs]
    rows_valid = [r for r in rows if r["epoch_no"] in valid_epochs]

    s1 = run_spec(
        "P1_lagged_core_with_margin_lifetime_roa",
        rows_train,
        rows_valid,
        ["lag1_luck", "lag1_log_pledge", "lag1_log_stake", "margin", "lifetime_roa"],
    )
    s2 = run_spec(
        "P2_lagged_plus_persistence_with_margin_lifetime_roa",
        rows_train,
        rows_valid,
        ["lag1_luck", "lag1_log_pledge", "lag1_log_stake", "margin", "lifetime_roa", "lag1_log_delegators"],
    )

    report = {
        "goal": "Validate predictive stability with time-based train/validation split",
        "split": {
            "train_epochs": train_epochs,
            "validation_epochs": valid_epochs,
            "epoch_row_counts": counts,
            "train_rows_raw": len(rows_train),
            "validation_rows_raw": len(rows_valid),
            "train_row_share": len(rows_train) / len(rows) if rows else 0.0,
            "validation_row_share": len(rows_valid) / len(rows) if rows else 0.0,
        },
        "specifications": {
            "P1_lagged_core_with_margin_lifetime_roa": s1,
            "P2_lagged_plus_persistence_with_margin_lifetime_roa": s2,
        },
        "notes": [
            "Time split uses earlier epochs for train and later epochs for validation.",
            "This evaluates predictive generalization, not causal identification.",
        ],
    }

    JSON_OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report)
    write_tex(report)

    # Compile PDF if LaTeX is available.
    try:
        subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                f"-output-directory={OUT_DIR}",
                str(TEX_OUT),
            ],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
    except Exception:
        pass

    print("Created:")
    print("-", JSON_OUT)
    print("-", MD_OUT)
    print("-", TEX_OUT)
    print("-", PDF_OUT)


if __name__ == "__main__":
    main()
