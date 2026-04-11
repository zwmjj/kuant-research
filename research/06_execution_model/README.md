# 06 · Execution Model Sensitivity

**Category:** Execution
**Data tier:** 🟡 B — yfinance, shared cache
**Runtime:** <15 seconds

---

## Research question

How much of a strategy's reported Sharpe is an artifact of its **cost
assumption**? Specifically: across seven reasonable execution
environments — from "no cost" fantasy to "crisis" (2020 March) levels
— how does each signal's Sharpe evolve?

This study isolates the *execution* axis that `01_signal_decay_vs_cost`
sweeps jointly with the turnover-penalty axis. Here we hold the penalty
fixed at the baseline 0.25 and vary the cost coefficients.

## Seven scenarios

| Name              | Commission | Spread | Impact coef | Description                      |
|-------------------|------------|--------|-------------|----------------------------------|
| `no_cost`         | 0 bp       | 0 bp   | 0.0         | Fantasy land                     |
| `commission_only` | 1 bp       | 0 bp   | 0.0         | Flat-fee broker, tight book      |
| `retail_flat`     | 1 bp       | 5 bp   | 0.0         | Retail with realistic half-spread |
| `institutional`   | 0.5 bp     | 2 bp   | 0.3         | Prime-broker flow                |
| `retail_full`     | 1 bp       | 5 bp   | 0.3         | Retail with sqrt impact          |
| `stressed`        | 2 bp       | 10 bp  | 0.6         | Wide spreads / mediocre execution|
| `crisis`          | 5 bp       | 20 bp  | 1.0         | March-2020 style illiquidity     |

## Method

For each of the four signals and each of the seven scenarios, rebuild
the L/S book with the new `CostConfig` and compute the Sharpe. Report
the full 4×7 grid plus a "cost drag" column (`no_cost - crisis`) that
measures how much each signal's Sharpe would fall in the worst case.

## Reproduce

```bash
cd research/06_execution_model
pip install -r requirements.txt
python run.py
```

## Key findings (reference run, 2015-12-31 → 2025-12-31, 10 sector ETFs)

### Sharpe × scenario × signal grid

| Scenario           | `mom12` | `mom1`   | `lowvol` | `mr5`    |
|--------------------|---------|----------|----------|----------|
| `no_cost`          | −0.239  | +0.325   | −0.254   | +0.403   |
| `commission_only`  | −0.242  | +0.314   | −0.256   | +0.397   |
| `retail_flat`      | −0.255  | +0.264   | −0.265   | +0.370   |
| `institutional`    | −0.247  | +0.296   | −0.259   | +0.387   |
| `retail_full`      | −0.256  | +0.260   | −0.265   | +0.368   |
| `stressed`         | −0.272  | +0.196   | −0.277   | +0.333   |
| `crisis`           | −0.306  | **+0.060** | −0.302   | +0.257   |
| **Cost drag**      | +0.067  | **+0.264** | +0.048   | +0.146   |

### What we learn

1. **`mom1` is a cost-sensitive disaster under stress.** Its Sharpe
   drops from +0.32 (no cost) → +0.06 (crisis), losing **81% of its
   gross edge** to execution. In the `retail_full` baseline (the
   realistic case for most retail-execution quant books) it's already
   down to +0.26, and any further deterioration pushes it near zero.
   This is the clearest cost-degradation curve in the study.

2. **`mr5` is cost-robust in relative terms.** It loses 36% of its
   gross Sharpe from no-cost to crisis, vs 81% for `mom1`. Even at
   crisis spreads it's still at +0.26 — roughly where `mom1` sits in
   the baseline. The z-score-based 5-month formulation updates
   slowly enough that crisis costs don't kill it, but still fast
   enough to generate alpha.

3. **Sharpe ordering is preserved across all 7 scenarios.** The
   rank order `{mr5 > mom1 > mom12 ≈ lowvol}` doesn't change even
   under crisis assumptions. That means no cost-regime change would
   have flipped which signal you should pick — the ranking is
   genuinely robust to cost model choice.

4. **The difference between `institutional` and `retail_full` is
   small** (~0.015 Sharpe, or ~5% of `mr5`'s gross). Even at a factor
   of 2 improvement in execution quality, you're not moving the
   needle much on an already cost-robust signal. **Execution upgrades
   matter for fast signals (`mom1`), not slow ones (`mr5` / `mom12`).**

### Takeaway

> **The rank ordering of signals is robust to cost assumptions, but
> the rank ordering of signals' *deployment viability* is not.** A
> signal with 0.3 Sharpe under "no cost" and 0.05 Sharpe under "crisis"
> is a research finding, not a strategy. Look at the bottom row of the
> grid before taking anything to live deployment.

## Files

```
README.md / run.py / config.yaml / signals.py /
requirements.txt / data_contract.md / expected_output.json
```
