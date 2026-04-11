# 08 · IS vs OOS Stability

**Category:** Validation
**Data tier:** 🟡 B — yfinance default, shares cache with study 01
**Runtime:** <15 seconds

---

## Research question

For each of the four reference signals from `01_signal_decay_vs_cost`,
what fraction of the full-sample Sharpe is **in-sample** vs **out-of-sample**?
Did any signal *improve* after 2020, and which ones decayed?

This is the classic over-fitting gate: an in-sample Sharpe with a steep
OOS decay is a red flag for curve-fitting; a signal whose IS and OOS
Sharpes line up is a candidate for actually running.

## Method

1. Pull the 10 sector ETFs (same as study 01).
2. Build the same four signals: `mom12`, `mom1`, `lowvol`, `mr5`.
3. Run the quintile L/S backtest with baseline cost / penalty.
4. Split each signal's returns at 2020-12-31.
5. Compute full, IS, OOS Sharpe / CAGR / MDD and a **decay ratio**
   `(OOS_sharpe − IS_sharpe) / |IS_sharpe|`.
6. Also compute three non-overlapping 3-year rolling windows to show
   the trajectory: 2016–2018, 2019–2021, 2022–2025.

## Reproduce

```bash
cd research/08_is_oos_stability
pip install -r requirements.txt
python run.py
```

## Key findings (reference run, 2015-12-31 → 2025-12-31, 10-ETF universe)

| Signal   | Full SR | IS SR   | OOS SR  | Δ (OOS − IS) | Decay %   | Verdict               |
|----------|---------|---------|---------|--------------|-----------|------------------------|
| `mom12`  | −0.256  | +0.002  | −0.505  | **−0.506**   | n/a       | 💥 Collapsed           |
| `mom1`   | +0.260  | −0.135  | +0.586  | **+0.721**   | +533%     | 🎲 Reversed sign       |
| `lowvol` | −0.265  | +0.444  | −0.873  | **−1.317**   | −297%     | 💥 Reversed & crashed  |
| `mr5`    | +0.378  | +0.325  | +0.407  | **+0.082**   | +25%      | ✅ Stable              |

### Reading the table

- **`mr5` is the only signal that generalized.** IS Sharpe 0.32, OOS
  0.41 — a mild *improvement*, not decay. This is the signal you'd
  actually want to run forward.

- **`mom12` collapsed.** IS Sharpe effectively zero (0.002), OOS
  −0.505. The "Decay %" column is shown as n/a because dividing by a
  near-zero IS produces nonsense ratios; the absolute delta
  (−0.506) tells the real story. 2021–2025 saw sector-ETF momentum
  turn into anti-momentum.

- **`lowvol` reversed.** IS 0.44 → OOS −0.87. The pre-2020 low-vol
  premium in sector ETFs disappeared post-COVID as utilities / staples
  underperformed tech persistently through the AI rally.

- **`mom1` is the only signal with a negative IS that turned positive
  OOS** (−0.135 → +0.586). Short-term reversal got *stronger* post-2020,
  possibly reflecting higher-frequency volatility and more mean-reverting
  sector rotation. But a sign flip is a sign flip — you would not
  reasonably deploy a signal whose pre-2020 track record was negative
  and whose post-2020 track record is positive without additional
  causal argumentation.

### What it means

The study's real finding is that **three of the four signals are
research artifacts of their IS period**, not stable alphas. The decay
column would look better if we had picked a larger universe and a longer
history — both are addressable with WRDS CRSP — but the qualitative
point stands: a 2015–2020 backtest overstated three of these four
signals' prospects, and a naive 2020 deployment would have destroyed
capital.

The one survivor (`mr5`, medium-term mean reversion) is the same signal
that came out best in `01_signal_decay_vs_cost` for cost robustness.
Two independent stability criteria selecting the same signal is as
close to OOS validation as a small-universe study gets.

## Files

```
README.md / run.py / config.yaml / signals.py /
requirements.txt / data_contract.md / expected_output.json
```
