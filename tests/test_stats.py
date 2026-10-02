import numpy as np
import pandas as pd
import pytest

from src import stats


def _panel(n_dates=40, n_stocks=60, signal=0.0, seed=0):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2020-01-03", periods=n_dates, freq="W-FRI")
    index = pd.MultiIndex.from_product([dates, [f"S{i}" for i in range(n_stocks)]])
    score = pd.Series(rng.normal(size=len(index)), index=index)
    ret = signal * score + rng.normal(size=len(index))
    return score, ret


def test_ic_is_near_zero_for_noise_and_high_for_signal():
    score, ret = _panel(signal=0.0)
    assert abs(stats.ic_summary(stats.weekly_rank_ic(score, ret))["mean_ic"]) < 0.05
    score, ret = _panel(signal=2.0)
    assert stats.ic_summary(stats.weekly_rank_ic(score, ret))["mean_ic"] > 0.5


def test_ic_matches_scipy_spearman_per_date():
    score, ret = _panel(n_dates=3, n_stocks=30)
    ic = stats.weekly_rank_ic(score, ret)
    date = ic.index[0]
    expected = pd.Series(score.loc[date]).corr(pd.Series(ret.loc[date]), method="spearman")
    assert ic.loc[date] == pytest.approx(expected, abs=1e-9)


def test_deciles_increase_with_signal():
    score, ret = _panel(signal=1.0, n_dates=80)
    deciles = stats.decile_returns(score, ret)
    assert deciles.iloc[-1] > deciles.iloc[0] and len(deciles) == 10


def test_alpha_beta_recovers_known_values():
    rng = np.random.default_rng(1)
    bench = pd.Series(rng.normal(0, 0.01, 2000))
    strat = 0.0002 + 0.8 * bench + rng.normal(0, 0.002, 2000)
    out = stats.alpha_beta(strat, bench)
    assert out["beta"] == pytest.approx(0.8, abs=0.03)
    assert out["alpha_annual"] == pytest.approx(0.0002 * 252, abs=0.02)


def test_psr_and_dsr_behaviour():
    rng = np.random.default_rng(2)
    good = pd.Series(rng.normal(0.002, 0.01, 1500))
    noise = pd.Series(rng.normal(0.0, 0.01, 1500))
    assert stats.probabilistic_sharpe(good) > 0.95
    assert stats.probabilistic_sharpe(noise) < 0.95
    assert stats.deflated_sharpe(good, 1) == pytest.approx(stats.probabilistic_sharpe(good))
    assert stats.deflated_sharpe(good, 20) < stats.deflated_sharpe(good, 5) < stats.deflated_sharpe(good, 1)


def test_dsr_benchmark_matches_formula():
    # Hand-computed: SR0 = sqrt(V) * ((1-g)*z(1-1/N) + g*z(1-1/(N*e))) for N=5, V=1/(T-1) at SR=0 (normal returns).
    from scipy.stats import norm
    n, t = 5, 1000
    g = 0.5772156649015329
    expected = np.sqrt(1 / (t - 1)) * ((1 - g) * norm.ppf(1 - 1 / n) + g * norm.ppf(1 - 1 / (n * np.e)))
    returns = pd.Series(np.random.default_rng(3).normal(0, 0.01, t))
    returns = (returns - returns.mean())  # zero Sharpe, near-normal moments
    sr, skew, kurt, _ = stats._moments(returns)
    variance = (1 - skew * sr + (kurt - 1) / 4 * sr**2) / (t - 1)
    assert np.sqrt(variance) == pytest.approx(np.sqrt(1 / (t - 1)), rel=0.05)
    assert 0.5 < expected * np.sqrt(t) < 2.5
