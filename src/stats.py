"""Signal-quality and significance statistics: rank IC, deciles, alpha vs a benchmark, PSR/DSR."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as sps

EULER_GAMMA = 0.5772156649015329


def weekly_rank_ic(scores: pd.Series, forward_returns: pd.Series) -> pd.Series:
    """Spearman correlation between score and realized forward return, one value per date."""
    frame = pd.DataFrame({"s": scores, "r": forward_returns}).dropna()
    ranks = frame.groupby(level=0).rank()
    grouped = ranks.groupby(level=0)
    mean_s, mean_r = grouped["s"].transform("mean"), grouped["r"].transform("mean")
    cov = ((ranks["s"] - mean_s) * (ranks["r"] - mean_r)).groupby(level=0).mean()
    return cov / (grouped["s"].std(ddof=0) * grouped["r"].std(ddof=0))


def ic_summary(ic: pd.Series) -> dict:
    n = int(ic.notna().sum())
    mean, std = float(ic.mean()), float(ic.std())
    return {"mean_ic": mean, "ic_std": std, "t_stat": mean / (std / np.sqrt(n)) if n > 1 and std > 0 else float("nan"),
            "pct_positive": float((ic > 0).mean()), "weeks": n}


def decile_returns(scores: pd.Series, forward_returns: pd.Series, bins: int = 10) -> pd.Series:
    """Average realized forward return by predicted-score decile (1 = lowest scores)."""
    frame = pd.DataFrame({"s": scores, "r": forward_returns}).dropna()
    frame["bin"] = frame.groupby(level=0)["s"].transform(lambda x: pd.qcut(x.rank(method="first"), bins, labels=False)) + 1
    return frame.groupby("bin")["r"].mean()


def alpha_beta(strategy: pd.Series, benchmark: pd.Series, periods: int = 252) -> dict:
    """OLS of strategy on benchmark returns: annualized alpha, beta and the alpha's t-statistic."""
    both = pd.concat([strategy, benchmark], axis=1).dropna()
    y, x = both.iloc[:, 0].to_numpy(), both.iloc[:, 1].to_numpy()
    design = np.column_stack([np.ones_like(x), x])
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    resid = y - design @ coef
    sigma2 = resid @ resid / (len(y) - 2)
    cov = sigma2 * np.linalg.inv(design.T @ design)
    return {"alpha_annual": float(coef[0] * periods), "beta": float(coef[1]),
            "alpha_t": float(coef[0] / np.sqrt(cov[0, 0])), "n": int(len(y))}


def _moments(returns: pd.Series) -> tuple[float, float, float, int]:
    r = returns.dropna()
    sr = float(r.mean() / r.std())
    return sr, float(sps.skew(r)), float(sps.kurtosis(r, fisher=False)), len(r)


def probabilistic_sharpe(returns: pd.Series, benchmark_sr: float = 0.0) -> float:
    """P(true Sharpe > benchmark_sr), per-period Sharpe, adjusting for skew and kurtosis (Bailey & Lopez de Prado)."""
    sr, skew, kurt, n = _moments(returns)
    denom = np.sqrt(1 - skew * sr + (kurt - 1) / 4 * sr**2)
    return float(sps.norm.cdf((sr - benchmark_sr) * np.sqrt(n - 1) / denom))


def deflated_sharpe(returns: pd.Series, n_trials: int) -> float:
    """Probability the Sharpe is real after deflating for the best-of-`n_trials` selection effect.

    Simplification: the cross-trial Sharpe variance is taken to be the estimation variance of this
    one Sharpe (only one return series is available).
    """
    sr, skew, kurt, n = _moments(returns)
    if n_trials <= 1:
        return probabilistic_sharpe(returns, 0.0)
    variance = (1 - skew * sr + (kurt - 1) / 4 * sr**2) / (n - 1)
    sr0 = np.sqrt(variance) * ((1 - EULER_GAMMA) * sps.norm.ppf(1 - 1 / n_trials)
                               + EULER_GAMMA * sps.norm.ppf(1 - 1 / (n_trials * np.e)))
    return probabilistic_sharpe(returns, float(sr0))
