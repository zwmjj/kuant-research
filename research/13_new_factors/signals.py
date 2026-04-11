"""Macro-conditioned signals for the 13_new_factors study.

Unlike studies 01/03/05/06/07/08 which use only price-based signals,
this study blends FRED macro data into the signal construction to
show the template for adding an external regime layer.

All three signals are *time-series* conditioners applied to a
cross-sectional base — the long-short book still ranks assets
cross-sectionally, but the signal values are tilted by the macro
state.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def signal_vix_regime(monthly_rets: pd.DataFrame, macros: pd.DataFrame) -> pd.DataFrame:
    """VIX-regime-conditioned low-vol signal.

    Base signal: negative 12-month rolling std (low-vol factor).
    Conditioning: multiply signal by +1 when VIX is above its
    12-month expanding median (risk-off), -1 when below (risk-on).
    Intuition: low-vol pays in high-VIX regimes, not in calm ones.
    """
    base = (-monthly_rets.rolling(12).std()).shift(1)
    vix = macros["VIXCLS"]
    # Align monthly
    vix_m = vix.resample("ME").last()
    vix_med = vix_m.expanding(12).median()
    regime = pd.Series(np.where(vix_m >= vix_med, 1.0, -1.0), index=vix_m.index)
    regime_aligned = regime.reindex(base.index, method="ffill")
    return base.mul(regime_aligned, axis=0)


def signal_curve_signal(monthly_rets: pd.DataFrame, macros: pd.DataFrame) -> pd.DataFrame:
    """Yield-curve slope as a directional macro signal.

    Base: asset's own 6-month momentum.
    Conditioner: curve steepening (T10Y2Y positive momentum)
    favors cyclicals, curve flattening/inversion favors defensives.
    We approximate this by multiplying the base momentum by the
    sign of the 3-month change in T10Y2Y.
    """
    base = (1 + monthly_rets).rolling(6).apply(lambda x: np.prod(x) - 1, raw=True).shift(1)
    curve = macros["T10Y2Y"].resample("ME").last()
    curve_change = curve.diff(3)
    sign = np.sign(curve_change).reindex(base.index, method="ffill")
    return base.mul(sign, axis=0)


def signal_macro_blend(monthly_rets: pd.DataFrame, macros: pd.DataFrame) -> pd.DataFrame:
    """Unconditional macro blend: z-score each macro, flip sign so
    +1 means 'risk-on' universally, average, and use as a time-series
    regime tilt on top of a 12-month momentum base signal.

    Risk-on definition per macro:
      - VIX down  -> risk-on (use -z)
      - DGS10 down -> risk-on (use -z) [lower yields = more duration friendly]
      - T10Y2Y up -> risk-on (use +z)  [steeper curve = stronger economy]
      - UNRATE down -> risk-on (use -z)
    """
    base = (1 + monthly_rets).rolling(12).apply(lambda x: np.prod(x) - 1, raw=True).shift(1)

    def _z(s):
        s_m = s.resample("ME").last()
        return (s_m - s_m.expanding(12).mean()) / s_m.expanding(12).std().replace(0, np.nan)

    z_vix = -_z(macros["VIXCLS"])
    z_dgs = -_z(macros["DGS10"])
    z_curve = _z(macros["T10Y2Y"])
    z_unrate = -_z(macros["UNRATE"])

    blend = (z_vix + z_dgs + z_curve + z_unrate) / 4.0
    blend_aligned = blend.reindex(base.index, method="ffill").clip(-2, 2)

    # tilt the base signal by the macro blend: risk-on -> amplify, risk-off -> dampen
    tilt = 1.0 + 0.5 * blend_aligned
    return base.mul(tilt, axis=0)


SIGNAL_REGISTRY = {
    "vix_regime":   signal_vix_regime,
    "curve_signal": signal_curve_signal,
    "macro_blend":  signal_macro_blend,
}
